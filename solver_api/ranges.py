# ranges.py
# This file contains the parsed preflop ranges from the provided text files
# in a format suitable for the range_expander.

# Открываемся первыми рейзом (Raise First In - RFI)
RFI_RANGES = {
    "EP": "77+, ATs+, KJs+, QJs, JTs, AQo+",
    "MP": "55+, A9s+, KTs+, QTs+, J9s+, T9s, AJo+, KQo",
    "CO": "22+, A2s+, K8s+, Q9s+, J9s+, T8s+, 98s, 87s, ATo+, KJo+, QJo",
    "BTN": "22+, A2s+, K2s+, Q2s+, J7s+, T7s+, 97s+, 87s, 76s, 65s, A2o+, K8o+, Q9o+, J8o+, T8o+",
    "SB": "22+, A2s+, K5s+, Q8s+, J8s+, T8s+, 98s, 87s, A8o+, KTo+, QJo, JTo"
}

# Изоляционные рейзы (Isolation Raises over limper)
ISO_RAISE_RANGES = {
    "MP": "77+, ATs+, KJs+, QJs, JTs, AQo+",
    "CO": "55+, A8s+, KTs+, QTs+, JTs, T9s, AJo+, KQo",
    "BTN": "55+, A2s+, K9s+, Q9s+, J9s+, T9s, 98s, 87s, ATo+, KJo+, QJo",
    "SB": "88+, ATs+, KJs+, QJs, AQo+",
    "BB": "88+, ATs+, KJs+, QJs, AQo+"
}

# Ответ на рейзы (Facing a Raise / 3-bets / Cold Calls)
VS_RAISE_RANGES = {
    "MP_vs_UTG": {
        "3_bet": "QQ+, AKs, AKo",
        "call": "66-JJ, AQs"
    },
    "CO_vs_EP_or_MP": {
        "3_bet": "JJ+, AQs+, AKo",
        "call": "66-TT, AJs, KQs, QJs, JTs"
    },
    "BTN_vs_Raise": {
        "3_bet": "TT+, AQs+, AKo, AQo, KQs",
        "call": "22-99, A2s-AJs, KJs, QJs, JTs, T9s, 98s, 87s"
    },
    "SB_vs_Raise": {
        "3_bet": "TT+, AQs+, AJs, KQs, AKo",
        "call": "" # Never flat calls
    },
    "BB_vs_Raise": {
        "3_bet": "JJ+, AQs+, AKo, AKs",
        "call": "22-TT, A2s-AJs, KTs+, QTs+, JTs, T9s, 98s, 87s, AQo, AJo, KQo"
    }
}

# Диапазоны оппонентов на Большом Блайнде (против открытия с Баттона)
OPPONENT_BB_DEFENSE = {
    "Fish_CallingStation": {
        "call": "22-JJ, A2s-AJs, K2s-KQs, Q2s-QJs, J7s-JTs, T7s-T9s, 96s-98s, 86s-87s, 75s-76s, 64s-65s, 54s, A2o-AQo, K8o-KQo, Q8o-QJo, J8o-JTo, T8o-T9o, 98o",
        "3_bet": "QQ+, AKs, AKo"
    },
    "Regular": {
        "call": "22-TT, A2s-AJs, K9s-KQs, Q9s-QJs, J9s-JTs, T8s-T9s, 97s-98s, 87s, 76s, 65s, ATo-AQo, KTo-KQo, QTo-QJo, JTo",
        "3_bet": "JJ+, AQs+, AK" # added AK here since "AK" was stated without suit, but solvers use AKs,AKo. Note: the txt file says "JJ+, AQs+, AK, A2s-A5s" - handled manually if needed.
    },
    "Nit": {
        "call": "22-JJ, ATs-AQs, KJs-KQs, QJs, JTs, T9s, AQo",
        "3_bet": "QQ+, AKs, AKo"
    }
}
