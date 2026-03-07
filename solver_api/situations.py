# situations.py
from ranges import RFI_RANGES, ISO_RAISE_RANGES, VS_RAISE_RANGES, OPPONENT_BB_DEFENSE

# Define the Matchups (Game Situations) we want to precalculate for the 184 flops.
# A situation is defined by:
#  - id: Unique name for the situation
#  - pot: Starting pot size
#  - effective_stack: Remaining stack size (100bb starting stack assumed)
#  - range_ip: Range of the In-Position player
#  - range_oop: Range of the Out-of-Position player
#  - spr (optional): Stack-to-Pot ratio to help adjust bet sizes (SRP, 3BP, 4BP)

# Standard SRP (Single Raised Pot) size
SRP_POT = 6.5  # e.g., 3bb raise + 1bb call + 0.5bb SB = ~6.5bb (ignoring rake for now)
SRP_STACK = 100 - 3 # 97bb

# 3BP (3-bet Pot) size
THREE_BET_POT = 22.5 # e.g. 3bb RFI + 10bb 3-bet + call + 0.5bb SB = ~22-23bb
THREE_BET_STACK = 100 - 10 # 90bb

SITUATIONS = [
    # 1. BTN RFI vs BB Call (The most common situation)
    # We will compute three separate trees for each opponent type
    {
        "id": "SRP_BTN_vs_BB_Reg",
        "description": "BTN Raise First In vs BB Call (Regular)",
        "pot": SRP_POT,
        "effective_stack": SRP_STACK,
        "range_ip": RFI_RANGES["BTN"], # BTN is IP
        "range_oop": OPPONENT_BB_DEFENSE["Regular"]["call"], # BB is OOP
        "type": "SRP"
    },
    {
        "id": "SRP_BTN_vs_BB_Fish",
        "description": "BTN Raise First In vs BB Call (Fish)",
        "pot": SRP_POT,
        "effective_stack": SRP_STACK,
        "range_ip": RFI_RANGES["BTN"],
        "range_oop": OPPONENT_BB_DEFENSE["Fish_CallingStation"]["call"],
        "type": "SRP"
    },
    {
        "id": "SRP_BTN_vs_BB_Nit",
        "description": "BTN Raise First In vs BB Call (Nit)",
        "pot": SRP_POT,
        "effective_stack": SRP_STACK,
        "range_ip": RFI_RANGES["BTN"],
        "range_oop": OPPONENT_BB_DEFENSE["Nit"]["call"],
        "type": "SRP"
    },
    
    # 2. Hero (BB) Defending vs Villain RFI (e.g. BTN)
    # BTN opens, BB calls. BB is OOP, BTN is IP.
    {
        "id": "SRP_BB_Defend_vs_BTN_RFI",
        "description": "BB Defends (Calls) vs BTN Open",
        "pot": SRP_POT,
        "effective_stack": SRP_STACK,
        "range_ip": RFI_RANGES["BTN"], # Assuming BTN opens
        "range_oop": VS_RAISE_RANGES["BB_vs_Raise"]["call"], # Hero's BB flatting range
        "type": "SRP"
    },

    # 3. 3-Bet Pots: Hero (BB) 3-bets BTN RFI, BTN Calls
    # BB 3-bets (OOP), BTN calls (IP)
    {
        "id": "3BP_BB_3Bet_vs_BTN_Call",
        "description": "BB 3-Bets BTN, BTN Calls",
        "pot": THREE_BET_POT,
        "effective_stack": THREE_BET_STACK,
        "range_ip": "22-JJ, AQo, AJo, KQo, KJo, QJo, JTo, T9o, 98o, A2s-AJs, KJs, QJs, JTs, T9s, 98s, 87s, 76s", # Approximate BTN Call vs 3bet (capped range)
        "range_oop": VS_RAISE_RANGES["BB_vs_Raise"]["3_bet"], # Hero BB 3-Bet range
        "type": "3BP"
    },

    # 4. Iso Raises: BTN Iso vs Fish Limper
    {
        "id": "SRP_BTN_Iso_vs_Limper",
        "description": "BTN Iso-Raises Limper(MP), Limper Calls",
        "pot": 9.5, # 4bb iso + 1bb limp + 4bb call + 0.5bb = ~9.5bb
        "effective_stack": 100 - 4, # 96bb
        "range_ip": ISO_RAISE_RANGES["BTN"], # Hero's Iso Range
        "range_oop": "22-99, A2s-ATs, K2s-KJs, Q2s-QJs, J7s-JTs, T7s-T9s, 97s-98s, 86s-87s, 75s-76s, 65s, A2o-AJo, K7o-KQo, Q7o-QJo, J8o-JTo, T8o-T9o, 98o", # Typical wide calling station limping range
        "type": "SRP"
    }
]
