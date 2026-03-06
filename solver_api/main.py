import os
import json
import uuid
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import logging

from solver_config import GameState, generate_solver_config_content

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TexasSolver API Wrapper")

# Path to the TexasSolver executable, configurable via environment variable
SOLVER_EXECUTABLE = os.getenv("SOLVER_PATH", "../console_solver") # Defaulting to linux binary

# Directory to temporarily store generated config and output json
TEMP_DIR = os.path.abspath("temp_runs")
os.makedirs(TEMP_DIR, exist_ok=True)

@app.post("/api/solve")
async def solve_poker_state(state: GameState):
    """
    Receives current poker state, runs TexasSolver, and returns the calculated strategy.
    """
    # Create unique IDs for this run to avoid collisions if multiple requests happen
    run_id = str(uuid.uuid4())
    config_file_path = os.path.join(TEMP_DIR, f"config_{run_id}.txt")
    output_json_path = os.path.join(TEMP_DIR, f"output_{run_id}.json")
    
    # 1. Generate Configuration
    try:
        config_content = generate_solver_config_content(state, output_json_path)
        with open(config_file_path, "w") as f:
            f.write(config_content)
        logger.info(f"Generated configuration for run {run_id}")
    except Exception as e:
         logger.error(f"Failed to generate configuration: {e}")
         raise HTTPException(status_code=500, detail=f"Failed to generate configuration: {str(e)}")

    # 2. Run Solver
    try:
        # Run subprocess
        # Working directory should be where the console_solver binary is located to avoid resource loading issues
        logger.info(f"Starting solver for run {run_id}...")
        
        # Determine the directory where the solver executable is located
        solver_cwd = os.path.dirname(os.path.abspath(SOLVER_EXECUTABLE))
        
        process = subprocess.Popen(
            [os.path.abspath(SOLVER_EXECUTABLE), "-i", config_file_path],
            cwd=solver_cwd,  # Run from the directory where console_solver lives
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Solver run failed with code {process.returncode}:\n{stderr}")
            raise HTTPException(status_code=500, detail="Solver execution failed.")
            
        logger.info(f"Solver completed for run {run_id}")

    except Exception as e:
        logger.error(f"Error executing solver subprocess: {e}")
        raise HTTPException(status_code=500, detail=f"Solver execution error: {str(e)}")
        
    # 3. Read and Return Results
    try:
        if not os.path.exists(output_json_path):
             raise HTTPException(status_code=500, detail="Solver finished but output JSON was not found.")
             
        with open(output_json_path, 'r') as f:
            strategy_data = json.load(f)
            
        # Optional Cleanup
        # os.remove(config_file_path)
        # os.remove(output_json_path)
            
        return JSONResponse(content={"status": "success", "run_id": run_id, "strategy": strategy_data})

    except json.JSONDecodeError:
         logger.error(f"Failed to parse output JSON for run {run_id}")
         raise HTTPException(status_code=500, detail="Invalid JSON output from solver.")
    except Exception as e:
        logger.error(f"Error reading solver output: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading solver output: {str(e)}")

@app.get("/health")
def health_check():
    return {"status": "ok"}
