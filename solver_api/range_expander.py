def expand_range(compact_range: str) -> str:
    """
    Expands shorthand poker notation (like 22+, A2s+) into an explicit 
    comma-separated list for TexasSolver (22,33,44...).
    Handles weights as well (e.g., 22+:0.5).
    """
    ranks = '23456789TJQKA'
    expanded = []
    
    # Remove all spaces and newlines
    compact_range = compact_range.replace(' ', '').replace('\n', '')
    if not compact_range:
        return ""
        
    combos = compact_range.split(',')
    
    for combo in combos:
        if not combo:
            continue
            
        weight = ""
        # Extract weight if present
        if ':' in combo:
            parts = combo.split(':')
            combo = parts[0]
            weight = ":" + str(parts[1])
            
        if '+' in combo:
            base = combo.replace('+', '')
            
            # Pairs: 22+ -> 22, 33, 44... AA
            if len(base) == 2 and base[0] == base[1]:
                start_idx = ranks.find(base[0])
                for i in range(start_idx, len(ranks)):
                    expanded.append(ranks[i] + ranks[i] + weight)
                    
            # Suited/Offsuit: A2s+ -> A2s, A3s.. AKs
            elif len(base) == 3 and base[2] in ['s', 'o']:
                r1 = base[0]
                r2 = base[1]
                suit = base[2]
                
                idx1 = ranks.find(r1)
                start_idx2 = ranks.find(r2)
                
                # Iterate the lower card up to just below the higher card
                for i in range(start_idx2, idx1):
                    expanded.append(r1 + ranks[i] + suit + weight)
            else:
                # If unsupported format with '+', just add it directly (might fail but best effort)
                expanded.append(combo + weight)
        else:
            # Explicit combo: AA or AKs
            expanded.append(combo + weight)
            
    return ','.join(expanded)

# Test
if __name__ == "__main__":
    test_str = "22+,A2s+,K2s+,Q2s+,J2s+,T2s+,92s+,84s+,74s+,63s+,53s+,43s,A2o+,K5o+,Q7o+,J7o+,T7o+,97o+,87o"
    print(expand_range(test_str))
