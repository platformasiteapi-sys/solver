import json
from ranges import RFI_RANGES, ISO_RAISE_RANGES, VS_RAISE_RANGES, OPPONENT_BB_DEFENSE
from range_expander import expand_range

def test_all_ranges():
    print("--- RFI Ranges ---")
    for pos, r in RFI_RANGES.items():
        expanded = expand_range(r)
        print(f"[{pos}]: {expanded[:50]}... ({len(expanded.split(','))} combos)")

    print("\n--- OPPONENT BB DEFENSE (vs BTN) ---")
    for opp_type, actions in OPPONENT_BB_DEFENSE.items():
        print(f"[{opp_type}]:")
        for action, r in actions.items():
            expanded = expand_range(r)
            print(f"  {action}: {expanded[:50]}... ({len(expanded.split(','))} combos)")

if __name__ == "__main__":
    test_all_ranges()
