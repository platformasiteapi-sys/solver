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
                    line = raw.decode(errors="replace").rstrip()
                    if line:
                        log_lines.append(line)
                        logger.info(f"[solver] {line}")
            except asyncio.TimeoutError:
                pass  # No more pending output
            break
        # Try to read a line of output (short timeout so we keep polling the file)
        try:
            raw = await asyncio.wait_for(solver_process.stdout.readline(), timeout=0.15)
            line = raw.decode(errors="replace").rstrip()
            if line:
                log_lines.append(line)
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
            line = raw.decode(errors="replace").rstrip()
            if line:
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
        limit=10 * 1024 * 1024  # Increase limit to 10MB to prevent LimitOverrunError on huge ranges
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
