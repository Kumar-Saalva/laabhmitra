"""Tri-state eligibility evaluation. This file is the heart of "Rules decide".

A criterion gives TRUE, FALSE, UNKNOWN or N/A. A scheme status is worked out from
those results in a fixed order. No LLM is involved anywhere in this package.
"""
from datetime import date

T, F, U, NA = "TRUE", "FALSE", "UNKNOWN", "N/A"

STALE_AFTER_DAYS = 90

TIER_BY_STATUS = {
    "ELIGIBLE": "ready",
    "LIKELY": "likely",
    "NEAR_MISS": "one_step",
    "NOT_ELIGIBLE": "not_now",
    "WATCHLIST": "watchlist",
    "NOT_APPLICABLE": "hidden",
}


def apply_op(value, op, target):
    """Apply one operator. A missing value (None) is always UNKNOWN."""
    if value is None:
        return U
    if op == "is_true":
        return T if value is True else F
    if op == "is_false":
        return T if value is False else F
    if op == "eq":
        return T if value == target else F
    if op == "neq":
        return T if value != target else F
    if op == "in":
        return T if value in target else F
    if op == "not_in":
        return T if value not in target else F
    if op == "gt":
        return T if value > target else F
    if op == "gte":
        return T if value >= target else F
    if op == "lt":
        return T if value < target else F
    if op == "lte":
        return T if value <= target else F
    if op == "between":
        return T if target[0] <= value <= target[1] else F
    raise ValueError(f"unknown operator: {op}")


def evaluate_condition(cond, d):
    """A 'when' condition: a single test, or {"all": [...]} where every test must hold."""
    if "all" in cond:
        results = [evaluate_condition(c, d) for c in cond["all"]]
        if F in results:
            return F
        return U if U in results else T
    return apply_op(d.get(cond["field"]), cond["op"], cond.get("value"))


def evaluate_criterion(criterion, d):
    when = criterion.get("when")
    if when:
        applies = evaluate_condition(when, d)
        if applies == F:
            return NA          # the rule does not apply to this merchant
        if applies == U:
            return U           # we cannot tell yet whether it applies
    value = d.get(criterion["field"])
    if value is not None and value in (criterion.get("unknown_values") or []):
        return U               # official sources disagree about this value
    return apply_op(value, criterion["op"], criterion.get("value"))


def evaluate_scheme(scheme, d):
    """Evaluate every criterion, then decide the scheme status in the spec's order."""
    results = [(c, evaluate_criterion(c, d)) for c in scheme["criteria"]]
    hard = [(c, r) for c, r in results if c.get("hard", True) and r != NA]
    fails = [c for c, r in hard if r == F]
    unknown = [c for c, r in hard if r == U]

    already_registered = any(c["field"] == "udyam_registered" and r == F for c, r in results)
    if scheme["status"] == "announced":
        status = "WATCHLIST"
    elif scheme["kind"] == "registration" and already_registered:
        status = "NOT_APPLICABLE"
    elif fails and all(c.get("fix") for c in fails) and len(fails) <= 2:
        status = "NEAR_MISS"
    elif fails:
        status = "NOT_ELIGIBLE"
    elif unknown:
        status = "LIKELY"
    else:
        status = "ELIGIBLE"

    return {
        "scheme_id": scheme["id"],
        "status": status,
        "tier": TIER_BY_STATUS[status],
        "met": sum(1 for _, r in hard if r == T),
        "total": len(hard),
        "unknown": len(unknown),
        "fails": [c["id"] for c in fails],
        "criteria": [
            {"id": c["id"], "label": c["label"], "result": r, "hard": c.get("hard", True),
             "field": c["field"], "fix": c.get("fix"), "note": c.get("note"),
             "source_ref": c.get("source_ref")}
            for c, r in results
        ],
    }


def is_stale(last_verified: str, today: date | None = None) -> bool:
    """True when the scheme was last checked more than 90 days ago (amber 'Re-verify' badge)."""
    today = today or date.today()
    return (today - date.fromisoformat(last_verified)).days > STALE_AFTER_DAYS


def is_visible(scheme, result, profile) -> bool:
    """Display rules (spec 2.4.9)."""
    if result["status"] == "NOT_APPLICABLE":
        return False
    if scheme["id"] == "udyam_assist" and profile.get("pan_available") is not False:
        return False               # with a PAN, full Udyam Registration is the better route
    if result["status"] == "WATCHLIST" and result["fails"]:
        return False
    return True
