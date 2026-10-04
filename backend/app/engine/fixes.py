"""Gap-closing plan: which single action unlocks which schemes."""


def fix_plan(evals: dict, schemes: dict) -> list:
    """For each fix action, list the schemes whose ONLY failing criteria use that fix.

    Grants are summed. For credit we report the largest single option instead of a sum:
    several loans for the same need are alternatives, and adding them would overstate it.
    """
    steps = {}
    for sid, e in evals.items():
        if e["status"] != "NEAR_MISS":
            continue
        failing = [c for c in e["criteria"] if c["result"] == "FALSE" and c["hard"]]
        actions = {c["fix"]["action_id"] for c in failing if c.get("fix")}
        if len(actions) != 1 or any(not c.get("fix") for c in failing):
            continue
        action_id = actions.pop()
        step = steps.setdefault(action_id, {
            "action_id": action_id, "label": failing[0]["fix"]["label"],
            "unlocks": [], "grant_unlocked": 0, "credit_unlocked_max": 0,
        })
        step["unlocks"].append(sid)
        step["grant_unlocked"] += e["estimate"]["grant_max"]
        step["credit_unlocked_max"] = max(step["credit_unlocked_max"], e["estimate"]["credit"])
    return sorted(steps.values(),
                  key=lambda s: (-s["grant_unlocked"], -len(s["unlocks"]), -s["credit_unlocked_max"]))
