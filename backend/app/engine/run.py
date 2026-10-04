"""Runs the whole engine for one profile and shapes the result for the API."""
from datetime import date

from app.engine import affordability
from app.engine.derive import DERIVED_INPUTS, derive
from app.engine.estimate import estimate
from app.engine.evaluate import evaluate_scheme, is_stale, is_visible
from app.engine.fixes import fix_plan
from app.engine.paths import CANDIDATE_STATUSES, best_paths

TIER_ORDER = ["ready", "likely", "one_step", "not_now", "watchlist", "hidden"]

# Fields we are willing to ask about, in a sensible fallback order.
ASKABLE = [
    "state", "business_activity", "area_type", "is_new_project", "trade", "owner_age",
    "loan_amount_needed_inr", "project_cost_inr", "udyam_registered", "pan_available",
    "annual_turnover_inr", "investment_plant_machinery_inr", "ownership_type", "gst_registered",
    "self_employed", "has_vending_proof", "owner_gender", "family_annual_income_inr",
    "social_category", "prior_govt_subsidy", "govt_employee_in_family", "education_8th_pass",
    "previous_mudra_tarun_repaid",
]


AFFORDABILITY_FIELDS = ["monthly_sales_inr", "monthly_costs_inr", "existing_emis_inr"]


def evaluate_all(profile: dict, schemes: dict, today: date | None = None) -> dict:
    """{scheme_id: result}. Each result carries its estimate, visibility and staleness."""
    d = derive(profile)
    evals = {}
    for sid, scheme in schemes.items():
        e = evaluate_scheme(scheme, d)
        e["estimate"] = estimate(scheme, d)
        # Warning badge only: computed after the status and never fed back into it.
        e["affordability"] = affordability.check(profile, sid, e["estimate"]["credit"])
        e["visible"] = is_visible(scheme, e, profile)
        e["stale"] = is_stale(scheme["last_verified"], today)
        evals[sid] = e
    return evals


def sort_key(e):
    """Tier first, then grant value, then credit value."""
    return (TIER_ORDER.index(e["tier"]), -e["estimate"]["grant_max"], -e["estimate"]["credit"])


def next_questions(profile: dict, schemes: dict, evals: dict) -> list:
    """Information-gain heuristic: rank missing fields by how many UNKNOWN hard criteria
    they would settle. The chat asks the top one next."""
    gain = {}
    for sid, e in evals.items():
        if e["status"] in ("NOT_APPLICABLE",):
            continue
        by_id = {c["id"]: c for c in schemes[sid]["criteria"]}
        for c in e["criteria"]:
            if c["result"] != "UNKNOWN" or not c["hard"]:
                continue
            fields = [c["field"]]
            when = by_id[c["id"]].get("when")
            if when:
                fields += [w["field"] for w in when.get("all", [when])]
            for field in fields:
                for f in DERIVED_INPUTS.get(field, [field]):
                    if profile.get(f) is None:
                        gain[f] = gain.get(f, 0) + 1
    for required in ("state", "business_activity"):
        if profile.get(required) is None:
            gain[required] = gain.get(required, 0) + 100
    ranked = sorted((f for f in gain if f in ASKABLE), key=lambda f: (-gain[f], ASKABLE.index(f)))
    questions = [{"field": f, "settles": gain[f]} for f in ranked]
    # Affordability questions come last: they settle no eligibility rule. A new unit has no
    # monthly cash yet (it uses the project report instead), so we do not ask it these.
    if profile.get("is_new_project") is not True and any(e.get("affordability") for e in evals.values()):
        questions += [{"field": f, "settles": 0} for f in AFFORDABILITY_FIELDS if profile.get(f) is None]
    return questions


def opportunity_map(evals: dict, schemes: dict, conflicts: list) -> dict:
    """Four honest buckets + best paths + fix plan. Grants and credit are never added."""
    open_ids = [sid for sid, e in evals.items() if e["visible"] and e["status"] in CANDIDATE_STATUSES]
    paths = best_paths(evals, schemes, conflicts)
    plan = fix_plan(evals, schemes)

    def item(sid, **extra):
        e = evals[sid]
        return {"scheme_id": sid, "short_name": schemes[sid]["short_name"], "status": e["status"],
                "tier": e["tier"], "scheme_status": schemes[sid]["status"], **extra}

    grants = [item(sid, grant_min=evals[sid]["estimate"]["grant_min"],
                   grant_max=evals[sid]["estimate"]["grant_max"], how=evals[sid]["estimate"]["how"])
              for sid in open_ids if evals[sid]["estimate"]["grant_max"] > 0]
    credit = [item(sid, credit=evals[sid]["estimate"]["credit"],
                   tier_name=evals[sid]["estimate"]["tier_name"], how=evals[sid]["estimate"]["how"],
                   kind=schemes[sid]["kind"])
              for sid in open_ids if evals[sid]["estimate"]["credit"] > 0]
    fee, non_monetary = [], []
    for sid in open_ids:
        for b in schemes[sid]["benefits"]:
            if b["type"] == "fee_subsidy":
                fee.append(item(sid, label=b["label"]))
            elif b["type"] == "non_monetary":
                non_monetary.append(item(sid, label=b["label"]))

    best = paths[0] if paths else None
    return {
        "headline": {
            # The best non-conflicting combination, not a sum of everything.
            "grant_min": best["grant_min"] if best else 0,
            "grant_max": best["grant_max"] if best else 0,
            "credit_options": len(credit),
            "credit_largest": max((c["credit"] for c in credit), default=0),
        },
        "buckets": {"grants": grants, "credit": credit, "fee_savings": fee, "non_monetary": non_monetary},
        "best_paths": paths,
        "fix_plan": plan,
        "conflicts": conflicts,
        "label": "Estimated maximum. Final amount is decided by the implementing agency.",
    }


def full_result(profile: dict, schemes: dict, conflicts: list, today: date | None = None) -> dict:
    evals = evaluate_all(profile, schemes, today)
    ordered = sorted(evals.values(), key=sort_key)
    return {
        "results": ordered,
        "opportunity_map": opportunity_map(evals, schemes, conflicts),
        "next_questions": next_questions(profile, schemes, evals),
    }
