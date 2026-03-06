from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class GameState(BaseModel):
    pot: float = Field(..., description="Current pot size")
    effective_stack: float = Field(..., description="Effective stack size")
    board: str = Field(..., description="Board cards separated by commas, e.g., 'Qs,Jh,2h'")
    range_ip: str = Field(..., description="In-position player's range string")
    range_oop: str = Field(..., description="Out-of-position player's range string")
    
    # Optional advanced settings with defaults
    allin_threshold: float = Field(0.67, description="All-in threshold for the solver")
    thread_num: int = Field(6, description="Number of CPU threads to use")
    accuracy: float = Field(0.5, description="Target exploitability accuracy (percent)")
    max_iteration: int = Field(200, description="Maximum number of solver iterations")

def generate_solver_commands(state: GameState) -> list:
    """
    Returns a list of solver commands for the given game state.
    The dump_result path is NOT included — it is added by the caller.
    """
    lines = []
    lines.append(f"set_pot {state.pot}")
    lines.append(f"set_effective_stack {state.effective_stack}")
    lines.append(f"set_board {state.board}")
    lines.append(f"set_range_ip {state.range_ip}")
    lines.append(f"set_range_oop {state.range_oop}")

    lines.extend([
        # Minimal Flop
        "set_bet_sizes oop,flop,bet,50",
        "set_bet_sizes oop,flop,raise,50",
        "set_bet_sizes oop,flop,allin",
        "set_bet_sizes ip,flop,bet,50",
        "set_bet_sizes ip,flop,raise,50",
        "set_bet_sizes ip,flop,allin",

        # Minimal Turn
        "set_bet_sizes oop,turn,bet,50",
        "set_bet_sizes oop,turn,raise,50",
        "set_bet_sizes oop,turn,allin",
        "set_bet_sizes ip,turn,bet,50",
        "set_bet_sizes ip,turn,raise,50",
        "set_bet_sizes ip,turn,allin",

        # Minimal River
        "set_bet_sizes oop,river,bet,50",
        "set_bet_sizes oop,river,raise,50",
        "set_bet_sizes oop,river,allin",
        "set_bet_sizes ip,river,bet,50",
        "set_bet_sizes ip,river,raise,50",
        "set_bet_sizes ip,river,allin"
    ])

    lines.append(f"set_allin_threshold {state.allin_threshold}")
    lines.append("build_tree")
    lines.append(f"set_thread_num {state.thread_num}")
    lines.append(f"set_accuracy {state.accuracy}")
    lines.append(f"set_max_iteration {state.max_iteration}")
    lines.append("set_print_interval 1")
    lines.append("set_use_isomorphism 1")
    lines.append("start_solve")
    lines.append("set_dump_rounds 2")
    return lines
