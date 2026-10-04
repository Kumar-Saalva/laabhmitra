"""Benefit estimators. Grants and credit are separate numbers and are never added.

Every estimate is an "estimated maximum": the implementing agency decides the final amount.
"""
from app.money import format_inr

LAKH = 100_000

PMEGP_CAP = {"manufacturing": 50 * LAKH}   # anything else (service / business): 20 lakh
PMEGP_CAP_OTHER = 20 * LAKH
UDYOGINI_MAX_LOAN = 3 * LAKH
MUDRA_MAX = 20 * LAKH


def mudra_tier(amount: int) -> str:
    if amount <= 50_000:
        return "Shishu"
    if amount <= 5 * LAKH:
        return "Kishore"
    if amount <= 10 * LAKH:
        return "Tarun"
    return "Tarun Plus"


def pmegp(scheme, d):
    cost = d.get("project_cost_inr")
    if not cost:
        return {"how": "Needs the project cost to estimate the subsidy."}
    cap = PMEGP_CAP.get(d.get("business_activity"), PMEGP_CAP_OTHER)
    base = min(cost, cap)
    rates, special, area = scheme["rates"], d.get("pmegp_special"), d.get("area_type")
    # If the area is not known yet, show the range from urban (lower) to rural (higher).
    lo_area, hi_area = (area, area) if area else ("urban", "rural")
    lo = rates["special"][lo_area] if special is True else rates["general"][lo_area]
    hi = rates["general"][hi_area] if special is False else rates["special"][hi_area]
    own = rates["own_contribution"]["special" if special is True else "general"]
    return {
        "grant_min": round(base * lo),
        "grant_max": round(base * hi),
        "credit": round(base * (1 - own)),
        "how": f"Subsidy rate {round(lo * 100)}%" + (f" to {round(hi * 100)}%" if hi != lo else "")
               + f" of project cost {format_inr(base)} (cap {format_inr(cap)}). Bank finance is the cost minus your own"
               + f" contribution of {round(own * 100)}%.",
    }


def udyogini(scheme, d):
    loan = min(d.get("loan_amount_needed_inr") or UDYOGINI_MAX_LOAN, UDYOGINI_MAX_LOAN)
    general = min(round(loan * 0.30), 90_000)
    scst = min(round(loan * 0.50), 150_000)
    category = d.get("social_category")
    if category in ("sc", "st"):
        lo = hi = scst
    elif category in ("general", "obc", "minority"):
        lo = hi = general
    else:
        lo, hi = general, scst      # category not shared: show the range
    return {"grant_min": lo, "grant_max": hi, "credit": loan,
            "how": f"30% of a loan of {format_inr(loan)} (max {format_inr(90_000)}); 50% (max {format_inr(150_000)}) for SC/ST women."}


def estimate(scheme, d) -> dict:
    """Return {grant_min, grant_max, credit, tier_name, how} in integer rupees."""
    out = {"grant_min": 0, "grant_max": 0, "credit": 0, "tier_name": None, "how": None}
    need = d.get("loan_amount_needed_inr") or 0
    sid = scheme["id"]
    if sid == "pmegp":
        out.update(pmegp(scheme, d))
    elif sid == "ka_udyogini":
        out.update(udyogini(scheme, d))
    elif sid == "pm_vishwakarma":
        out.update(grant_min=15_000, grant_max=15_000, credit=3 * LAKH,
                   how=f"Toolkit e-voucher {format_inr(15_000)}; loans of ₹1 lakh then ₹2 lakh at 5% interest.")
    elif sid == "mudra":
        credit = min(need, MUDRA_MAX)
        out.update(credit=credit, tier_name=mudra_tier(credit) if credit else None,
                   how="Your loan need, limited to ₹20 lakh. The tier is set by the amount.")
    elif sid == "pm_svanidhi":
        out.update(credit=15_000, how=f"First loan tranche of {format_inr(15_000)}; later tranches after on-time repayment.")
    elif sid == "me_card":
        out.update(credit=5 * LAKH, how="Card limit of up to ₹5 lakh, set by your bank.")
    elif sid == "cgtmse":
        out.update(credit=need, how="Your loan need. The guarantee goes to your bank, not to you.")
    return out
