"""Benefit Path Planner: the best sets of grant schemes that do not conflict."""
from itertools import combinations

CANDIDATE_STATUSES = ("ELIGIBLE", "LIKELY", "NEAR_MISS")


def forbidden_pairs(conflicts) -> dict:
    """Map each forbidden pair of scheme ids to the conflict that forbids it."""
    pairs = {}
    for c in conflicts:
        if c["type"] == "mutually_exclusive":
            for a, b in combinations(c["schemes"], 2):
                pairs[tuple(sorted((a, b)))] = c
        elif c["type"] == "anchor_excludes":
            for other in c["schemes"]:
                if other != c["anchor"]:
                    pairs[tuple(sorted((c["anchor"], other)))] = c
    return pairs


def best_paths(evals: dict, schemes: dict, conflicts: list, top: int = 3) -> list:
    """evals: {scheme_id: result with "status" and "estimate"}. Returns up to `top` paths.

    Only grants are summed. Credit is listed separately and never added to grants.
    """
    candidates = [sid for sid, e in evals.items()
                  if e["status"] in CANDIDATE_STATUSES
                  and schemes[sid]["kind"] != "registration"
                  and e["estimate"]["grant_max"] > 0]
    forbidden = forbidden_pairs(conflicts)

    allowed = []
    for size in range(len(candidates), 0, -1):
        for combo in combinations(candidates, size):
            if any(tuple(sorted(pair)) in forbidden for pair in combinations(combo, 2)):
                continue
            allowed.append(combo)
    allowed.sort(key=lambda combo: (-sum(evals[s]["estimate"]["grant_max"] for s in combo), -len(combo)))

    maximal = []            # drop any set that is fully contained in a better one
    for combo in allowed:
        if not any(set(combo) <= set(kept) for kept in maximal):
            maximal.append(combo)
    maximal = maximal[:top]

    paths = []
    for combo in maximal:
        # Conflicts that separate this path from the others: a scheme here vs a scheme left out.
        left_out = {s for other in maximal for s in other} - set(combo)
        messages = []
        for a in combo:
            for b in left_out:
                c = forbidden.get(tuple(sorted((a, b))))
                if c and c["message"] not in messages:
                    messages.append(c["message"])
        paths.append({
            "schemes": list(combo),
            "grant_min": sum(evals[s]["estimate"]["grant_min"] for s in combo),
            "grant_max": sum(evals[s]["estimate"]["grant_max"] for s in combo),
            "conflicts": messages,
        })
    return paths
