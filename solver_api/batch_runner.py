import os
import json
import logging
import asyncio
from typing import List, Dict
from range_expander import expand_range

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Paths configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FLOP_FILENAME = "kuba_184_flops_5_11_2015.txt"
# In Docker, the flop file is in the same dir as the script (/app/).
# Locally, it's one level up (../). Check both locations.
_flop_same_dir = os.path.join(SCRIPT_DIR, FLOP_FILENAME)
_flop_parent_dir = os.path.join(SCRIPT_DIR, "..", FLOP_FILENAME)
FLOP_FILE_PATH = _flop_same_dir if os.path.exists(_flop_same_dir) else _flop_parent_dir
SCENARIOS_DIR = os.path.join(SCRIPT_DIR, "scenarios")
DB_DIR = os.path.join(SCRIPT_DIR, "precalculated_db")
SOLVER_EXE = os.getenv("SOLVER_PATH", os.path.join(SCRIPT_DIR, "..", "linux_bin", "console_solver"))

def load_flops() -> List[Dict]:
    """Parse the flop file and return a list of dictionaries with cards and weights."""
    flops = []
    if not os.path.exists(FLOP_FILE_PATH):
        logging.error(f"Flop file not found: {FLOP_FILE_PATH}")
        return flops
        
    with open(FLOP_FILE_PATH, 'r') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            parts = line.split(':')
            if len(parts) == 2:
                # e.g., "TsTdTc" -> "Ts,Td,Tc"
                cards_str = parts[0]
                board = f"{cards_str[0:2]},{cards_str[2:4]},{cards_str[4:6]}"
                weight = float(parts[1])
                flops.append({"board": board, "weight": weight, "raw_string": cards_str})
                
    logging.info(f"Loaded {len(flops)} flops from {FLOP_FILE_PATH}")
    return flops

def load_scenarios() -> List[Dict]:
    """Load all JSON scenarios from the scenarios directory."""
    scenarios = []
    if not os.path.exists(SCENARIOS_DIR):
        logging.error(f"Scenarios directory not found: {SCENARIOS_DIR}")
        return scenarios
        
    for filename in os.listdir(SCENARIOS_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(SCENARIOS_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                scenarios.append(json.load(f))
                
    logging.info(f"Loaded {len(scenarios)} scenarios from {SCENARIOS_DIR}")
    return scenarios

def generate_solver_commands(scenario: Dict, flop: str, dump_path: str) -> List[str]:
    # expand_range returns a comma-separated STRING (e.g. "AA,KK,QQ")
    clean_ip = expand_range(scenario['range_ip'])
    clean_oop = expand_range(scenario['range_oop'])
    
    settings = scenario.get("solver_settings", {})
    tree = settings.get("tree_config", {})
    
    cmds = []
    cmds.append(f"set_pot {scenario['pot']}")
    cmds.append(f"set_effective_stack {scenario['effective_stack']}")
    cmds.append(f"set_board {flop}")
    cmds.append(f"set_range_ip {clean_ip}")
    cmds.append(f"set_range_oop {clean_oop}")
    
    # Generate Tree Betting Structure (Flop, Turn, River)
    for position in ["oop", "ip"]:
        for street in ["flop", "turn", "river"]:
            
            # Group all bet sizes for this position/street into a single list
            # TexasSolver expects: set_bet_sizes ip,flop,bet,33,75
            current_bets = []
            
            # Explicit bet sizes: keys like "ip_flop_bet", "oop_turn_bet"
            bet_key = f"{position}_{street}_bet"
            if bet_key in tree:
                for siz in tree[bet_key]:
                    current_bets.append(str(siz))
            
            # Action arrays: keys like "oop_flop", "oop_turn", "oop_river"
            action_key = f"{position}_{street}"
            if action_key in tree:
                for action in tree[action_key]:
                    if isinstance(action, str) and action.startswith("bet_"):
                        bet_size = action.split("_", 1)[1]
                        if bet_size not in current_bets:
                            current_bets.append(bet_size)
                            
            if current_bets:
                cmds.append(f"set_bet_sizes {position},{street},bet,{','.join(current_bets)}")
            
            # Raises: TexasSolver expects: set_bet_sizes ip,flop,raise,50,100
            raise_key = f"{position}_{street}_raise"
            if raise_key in tree:
                raises = [str(siz) for siz in tree[raise_key]]
                if raises:
                    cmds.append(f"set_bet_sizes {position},{street},raise,{','.join(raises)}")
    
    # All-ins
    for street in ["turn", "river"]:
        allin_key = f"{street}_allin"
        if tree.get(allin_key, False):
            cmds.append(f"set_bet_sizes oop,{street},allin")
            cmds.append(f"set_bet_sizes ip,{street},allin")

    cmds.append(f"set_allin_threshold {settings.get('allin_threshold', 0.67)}")
    # NOTE: set_raise_limit is NOT a valid console command in TexasSolver.
    # We must let the solver use its default internal raise limit heuristics.
    
    cmds.append("build_tree")
    cmds.append(f"set_thread_num {settings.get('thread_num', 6)}")
    cmds.append(f"set_accuracy {settings.get('accuracy', 0.5)}")
    cmds.append(f"set_max_iteration {settings.get('max_iteration', 200)}")
    cmds.append("set_print_interval 1")
    cmds.append("set_use_isomorphism 1")
    cmds.append("start_solve")
    
    # Dump flop-level strategy (rounds: 1 = flop, 2 = flop+turn+river)
    # Note: set_dump_rounds 0 produces null — must be at least 1
    cmds.append("set_dump_rounds 1")
    cmds.append(f"dump_result {dump_path}")
    
    return cmds

import subprocess

def run_solver_instance(commands: List[str]) -> str:
    """Spawns TexasSolver as a subprocess safely and pipes the sequence of commands via STDIN."""
    process = subprocess.Popen(
        [SOLVER_EXE],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    command_str = "\n".join(commands) + "\n"
    stdout, stderr = process.communicate(input=command_str.encode("utf-8"))
    
    if process.returncode != 0:
        logging.error(f"Solver process exited with code {process.returncode}")
        logging.error(f"STDERR: {stderr.decode('utf-8')}")
        
    return stdout.decode('utf-8', errors='replace')

import sys

def main():
    flops = load_flops()
    scenarios = load_scenarios()
    
    if not flops or not scenarios:
        logging.error("Missing flops or scenarios. Cannot proceed.")
        return
        
    # If args are provided, filter the scenarios to only those requested
    requested_scenarios = sys.argv[1:]
    if requested_scenarios:
        scenarios = [s for s in scenarios if s['scenario_id'] in requested_scenarios]
        if not scenarios:
            logging.error(f"None of the requested scenarios {requested_scenarios} were found.")
            return

    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)

    # Process every scenario loaded from the JSON configs
    for scenario in scenarios:
        scenario_id = scenario['scenario_id']
        logging.info(f"========== Starting batch run for scenario: {scenario_id} ==========")
        
        for f_data in flops:
            board_str = f_data["board"]
            raw_board_name = f_data["raw_string"]
            dump_filepath = os.path.join(DB_DIR, scenario_id, f"{raw_board_name}.json")
            
            os.makedirs(os.path.dirname(dump_filepath), exist_ok=True)
            
            # Skip if already computed (allows resuming if server restarts)
            if os.path.exists(dump_filepath):
                logging.info(f"Skipping {board_str} for {scenario_id} (already solved).")
                continue
                
            logging.info(f"Generating commands for board: {board_str}...")
            cmds = generate_solver_commands(scenario, board_str, dump_filepath)
            
            logging.info(f"Executing solver... (ETA depends on hardware)")
            output = run_solver_instance(cmds)
            
            if os.path.exists(dump_filepath):
                logging.info(f"SUCCESS! Result saved to {dump_filepath}")
                # Save solver log for convergence verification (same name, .log extension)
                log_filepath = dump_filepath.replace(".json", ".log")
                with open(log_filepath, "w", encoding="utf-8") as lf:
                    lf.write(output)
            else:
                logging.error(f"Failed to generate dump file for {board_str}")
                # Save error log for debugging
                err_log_path = dump_filepath.replace(".json", ".error.log")
                with open(err_log_path, "w", encoding="utf-8") as lf:
                    lf.write(output)
                lines = output.split('\n')
                logging.error("Last 10 lines of solver output:")
                for line in lines[-10:]:
                    print(line)

if __name__ == "__main__":
    main()
