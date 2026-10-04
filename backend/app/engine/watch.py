"""Opportunity Watch: compare the previous and new results and say what got better."""

RANK = {"NOT_ELIGIBLE": 0, "NEAR_MISS": 1, "LIKELY": 2, "ELIGIBLE": 3}


def snapshot(evals: dict, schemes: dict) -> dict:
    """The small record we store per profile: status per scheme + the scheme's own status."""
    return {sid: {"status": e["status"], "scheme_status": schemes[sid]["status"]}
            for sid, e in evals.items() if sid in schemes}


def diff(previous: dict, current: dict) -> list:
    """Return notifications: a status improved, a 'verify' badge appeared,
    or a watchlisted scheme became active."""
    notes = []
    for sid, new in current.items():
        old = previous.get(sid)
        if not old:
            continue
        if old["status"] == "WATCHLIST" and new["status"] != "WATCHLIST":
            notes.append({"scheme_id": sid, "kind": "now_active", "old": old["status"], "new": new["status"]})
        elif RANK.get(new["status"], -1) > RANK.get(old["status"], 99):
            notes.append({"scheme_id": sid, "kind": "improved", "old": old["status"], "new": new["status"]})
        if new["scheme_status"] == "verify" and old["scheme_status"] == "active":
            notes.append({"scheme_id": sid, "kind": "verify_badge", "old": old["status"], "new": new["status"]})
    return notes
