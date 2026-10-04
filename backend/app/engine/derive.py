"""Derived fields: facts we compute from the profile and never ask the merchant.

Each derived field is True / False / a value, or None when we cannot tell yet.
None matters: the engine treats None as UNKNOWN instead of guessing.
"""
from datetime import date

CRORE = 10_000_000
LAKH = 100_000

# Which profile fields each derived field depends on (used to pick the next best question).
DERIVED_INPUTS = {
    "enterprise_size": ["investment_plant_machinery_inr", "annual_turnover_inr"],
    "female_or_scst": ["owner_gender", "social_category"],
    "pmegp_special": ["owner_gender", "social_category"],
    "similar_loan_last_5y": [],
    "udyogini_income_ok": ["family_annual_income_inr", "social_category"],
}


def enterprise_size(investment, turnover):
    """MSME size by the limits in force from 1 Apr 2025 (investment AND turnover)."""
    if investment is None or turnover is None:
        return None
    if investment <= 2.5 * CRORE and turnover <= 10 * CRORE:
        return "micro"
    if investment <= 25 * CRORE and turnover <= 100 * CRORE:
        return "small"
    if investment <= 125 * CRORE and turnover <= 500 * CRORE:
        return "medium"
    return "large"


def female_or_scst(gender, category):
    if gender == "female" or category in ("sc", "st"):
        return True
    if gender in (None, "prefer_not") or category in (None, "prefer_not"):
        return None
    return False


def pmegp_special(p):
    gender, category = p.get("owner_gender"), p.get("social_category")
    if (gender in ("female", "transgender") or category in ("sc", "st", "obc", "minority")
            or p.get("is_ex_serviceman") or p.get("is_differently_abled")):
        return True
    if category in (None, "prefer_not") or gender in (None, "prefer_not"):
        return None
    return False


def similar_loan_last_5y(loans, current_year):
    """PM Vishwakarma: no PMEGP / Mudra / PM SVANidhi loan in the last 5 years."""
    recent = [l for l in loans or []
              if l.get("scheme") in ("pmegp", "mudra", "pm_svanidhi") and l.get("year", 0) >= current_year - 5]
    if not recent:
        return False
    if all(l.get("repaid") for l in recent):
        return None  # an exception may apply for fully repaid loans -> unknown
    return True


def udyogini_income_ok(p):
    income, category = p.get("family_annual_income_inr"), p.get("social_category")
    if p.get("is_widow") or p.get("is_differently_abled"):
        return True  # no income limit
    if income is None:
        return None
    if category in ("sc", "st"):
        return income < 2 * LAKH
    if category in ("general", "obc", "minority"):
        return income < 1.5 * LAKH
    # category unknown: sure below 1.5 lakh, sure not at 2 lakh or above, unknown in between
    if income < 1.5 * LAKH:
        return True
    if income >= 2 * LAKH:
        return False
    return None


def derive(profile: dict, current_year: int | None = None) -> dict:
    """Return a copy of the profile with the derived fields added."""
    year = current_year or date.today().year
    d = dict(profile)
    d["enterprise_size"] = enterprise_size(profile.get("investment_plant_machinery_inr"),
                                           profile.get("annual_turnover_inr"))
    d["female_or_scst"] = female_or_scst(profile.get("owner_gender"), profile.get("social_category"))
    d["pmegp_special"] = pmegp_special(profile)
    d["similar_loan_last_5y"] = similar_loan_last_5y(profile.get("existing_govt_loans"), year)
    d["udyogini_income_ok"] = udyogini_income_ok(profile)
    return d
