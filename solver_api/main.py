import os
import json
import uuid
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from solver_config import GameState, generate_solver_commands

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to the TexasSolver executable, configurable via environment variable
SOLVER_EXECUTABLE = os.getenv("SOLVER_PATH", "../console_solver")

# Directory to temporarily store output JSON files
TEMP_DIR = os.path.abspath("temp_runs")
os.makedirs(TEMP_DIR, exist_ok=True)

# --- Persistent Solver State ---
solver_process: asyncio.subprocess.Process = None
solver_lock = asyncio.Lock()  # Only one solve at a time


async def _collect_log_until_file(output_path: str, timeout: int = 600) -> str:
    """
    Read solver stdout while polling for the output file to appear.
    The dump_result command writes the file AFTER all iterations are done,
    so file presence is our reliable completion signal.
    """
    log_lines = []
    start = asyncio.get_event_loop().time()
    while True:
        elapsed = asyncio.get_event_loop().time() - start
        if elapsed > timeout:
            raise TimeoutError("Solver timed out after waiting for output file")
        # Check if the result file exists and is non-empty
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            # Wait for the file size to stabilize (solver may still be writing)
            size_before = os.path.getsize(output_path)
            await asyncio.sleep(0.2)
            size_after = os.path.getsize(output_path)
            if size_before != size_after:
                # Still writing — keep waiting
                continue
            # Drain any remaining stdout lines briefly
            try:
                while True:
                    raw = await asyncio.wait_for(solver_process.stdout.readline(), timeout=0.1)
                    if not raw:
                        break
                    line = raw.decode(errors="replace").rstrip()
                    if line:
                        log_lines.append(line)
                        if len(line) < 1000:
                            logger.info(f"[solver] {line}")
            except asyncio.TimeoutError:
                pass  # No more pending output
            break
        # Try to read a line of output (short timeout so we keep polling the file)
        try:
            raw = await asyncio.wait_for(solver_process.stdout.readline(), timeout=0.15)
            if not raw:
                await asyncio.sleep(0.05)
                continue
            line = raw.decode(errors="replace").rstrip()
            if line:
                log_lines.append(line)
                if len(line) < 1000:
                    logger.info(f"[solver] {line}")
        except asyncio.TimeoutError:
            await asyncio.sleep(0.05)  # Brief wait before next file poll
    return "\n".join(log_lines)



async def _drain_startup(timeout_idle: float = 1.0) -> str:
    """Read and discard solver startup output until 0.5s of silence (solver is ready)."""
    lines = []
    while True:
        try:
            raw = await asyncio.wait_for(solver_process.stdout.readline(), timeout=timeout_idle)
            if not raw:
                break
            line = raw.decode(errors="replace").rstrip()
            if line:
                if len(line) < 1000:
                    logger.info(f"[solver startup] {line}")
                lines.append(line)
        except asyncio.TimeoutError:
            break  # Nothing more to read — solver is idle and ready
    return "\n".join(lines)


async def start_solver_process():
    global solver_process
    solver_cwd = os.path.dirname(os.path.abspath(SOLVER_EXECUTABLE))
    logger.info("Starting persistent solver process...")
    solver_process = await asyncio.create_subprocess_exec(
        os.path.abspath(SOLVER_EXECUTABLE),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,  # merge stderr into stdout
        cwd=solver_cwd,
        limit=100 * 1024 * 1024  # Increase limit to 100MB to prevent LimitOverrunError on massive range dumps
    )
    await _drain_startup(timeout_idle=2.0)
    logger.info("Solver process is ready.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_solver_process()
    yield
    if solver_process and solver_process.returncode is None:
        solver_process.terminate()
        logger.info("Solver process terminated.")


app = FastAPI(title="TexasSolver API Wrapper", lifespan=lifespan)

# Allow requests from any origin (needed for the local HTML file tester and the poker bot)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/solve")
async def solve_poker_state(state: GameState):
    """
    Receives current poker state, runs TexasSolver via the persistent process,
    and returns the calculated strategy.
    """
    run_id = str(uuid.uuid4())
    output_json_path = os.path.join(TEMP_DIR, f"output_{run_id}.json")

    if solver_process is None or solver_process.returncode is not None:
        raise HTTPException(status_code=503, detail="Solver process is not running.")

    # Serialize requests so we don't mix up stdin/stdout between concurrent calls
    async with solver_lock:
        commands = generate_solver_commands(state)
        commands.append(f"dump_result {output_json_path}")

        logger.info(f"Run {run_id}: sending {len(commands)} commands to solver")

        try:
            # Write all commands to the solver's stdin
            for cmd in commands:
                solver_process.stdin.write((cmd + "\n").encode())
            await solver_process.stdin.drain()

            # Wait for solving to finish by polling for the output file.
            # dump_result writes the file AFTER all iterations are done — reliable completion signal.
            solver_log = await _collect_log_until_file(output_json_path, timeout=600)


        except TimeoutError as e:
            logger.error(f"Run {run_id}: solver timeout — {e}")
            raise HTTPException(status_code=504, detail=f"Solver timeout: {str(e)}")
        except Exception as e:
            logger.error(f"Run {run_id}: unexpected error — {e}")
            raise HTTPException(status_code=500, detail=f"Solver error: {str(e)}")

    # Read the result
    try:
        if not os.path.exists(output_json_path):
            raise HTTPException(status_code=500, detail="Solver finished but output JSON was not found.")

        with open(output_json_path, "r") as f:
            strategy_data = json.load(f)

        return JSONResponse(content={
            "status": "success",
            "run_id": run_id,
            "solver_log": solver_log,
            "strategy": strategy_data
        })

    except json.JSONDecodeError:
        logger.error(f"Run {run_id}: failed to parse output JSON")
        raise HTTPException(status_code=500, detail="Invalid JSON output from solver.")
    except Exception as e:
        logger.error(f"Run {run_id}: error reading output — {e}")
        raise HTTPException(status_code=500, detail=f"Error reading solver output: {str(e)}")


@app.get("/health")
def health_check():
    alive = solver_process is not None and solver_process.returncode is None
    return {"status": "ok", "solver_alive": alive}

# --- Distributed Batch Processing Endpoints ---

import glob
import subprocess

batch_process = None

from pydantic import BaseModel
from typing import List, Optional

class BatchRequest(BaseModel):
    target_scenarios: Optional[List[str]] = []

@app.post("/api/batch/start")
async def start_batch(req: BatchRequest = None):
    """Starts the background calculation of requested scenarios."""
    global batch_process
    
    if batch_process is not None and batch_process.poll() is None:
        raise HTTPException(status_code=400, detail="Batch process is already running.")
        
    cmd = ["python", "batch_runner.py"]
    if req and req.target_scenarios:
        cmd.extend(req.target_scenarios)

    # Start the batch_runner.py in a separate, detached process
    # It will use its own TexasSolver instances and won't block the real-time API
    batch_process = subprocess.Popen(
        cmd,  # Uses relative path from WORKDIR
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    msg = f"Batch computation started for scenarios: {req.target_scenarios}" if req and req.target_scenarios else "Batch computation started for ALL scenarios."
    return JSONResponse(content={"status": "success", "message": msg})

@app.get("/api/batch/status")
async def get_batch_status():
    """Returns the current progress of the batch computation."""
    global batch_process
    
    status = "running" if (batch_process and batch_process.poll() is None) else "idle"
    
    db_dir = os.path.abspath("precalculated_db")
    progress = {}
    
    if os.path.exists(db_dir):
        for scenario_dir in os.listdir(db_dir):
            path = os.path.join(db_dir, scenario_dir)
            if os.path.isdir(path):
                files = glob.glob(os.path.join(path, "*.json"))
                progress[scenario_dir] = f"{len(files)} / 184"
                
    return JSONResponse(content={"status": status, "progress": progress})

@app.get("/api/batch/download/{scenario_id}")
async def download_batch_result(scenario_id: str):
    """Zips the resulting scenario folder and sends it to the user."""
    import shutil
    from fastapi.responses import FileResponse
    
    db_dir = os.path.abspath("precalculated_db")
    target_dir = os.path.join(db_dir, scenario_id)
    
    if not os.path.exists(target_dir):
        raise HTTPException(status_code=404, detail="Scenario directory not found or not computed yet.")
        
    zip_path = os.path.abspath(f"temp_runs/{scenario_id}.zip")
    shutil.make_archive(zip_path.replace('.zip', ''), 'zip', target_dir)
    
    return FileResponse(zip_path, media_type="application/zip", filename=f"{scenario_id}.zip")

@app.get("/admin")
async def get_admin_ui():
    """Serves the mini admin dashboard."""
    from fastapi.responses import FileResponse
    admin_path = os.path.abspath("admin.html")
    if not os.path.exists(admin_path):
        raise HTTPException(status_code=404, detail="Admin UI file not found.")
    return FileResponse(admin_path)
