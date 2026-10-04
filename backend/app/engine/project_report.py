"""Project report for a new unit (PMEGP first). Every number here is computed in code.

The LLM only writes the short narrative sections afterwards, and guard.py rejects any
narrative that contains a number not found in these figures.
"""
from app.engine import project_report_config as cfg
from app.engine.affordability import emi
from app.engine.derive import derive
from app.engine.estimate import estimate

REQUIRED = ["machinery_inr", "building_or_civil_inr", "working_capital_inr", "monthly_sales_year1_inr",
            "annual_sales_growth", "raw_material_pct_of_sales", "monthly_fixed_costs_inr"]


def missing_inputs(project: dict | None) -> list:
    project = project or {}
    return [f for f in REQUIRED if project.get(f) is None]


def dscr_band(dscr):
    """Assumed bands. Banks set their own minimum."""
    if dscr is None:
        return "Unknown", "unknown"
    if dscr < cfg.DSCR_THIN_MIN:
        return "Cannot cover repayments", "cannot_cover"
    if dscr < cfg.DSCR_COMFORTABLE_MIN:
        return "Thin", "thin"
    return "Comfortable", "comfortable"


def loan_schedule(principal: float, annual_rate: float, months: int) -> list:
    """Monthly amortisation, added up per year: [{year, interest, principal, closing_balance}]."""
    payment = emi(principal, annual_rate, months)
    balance, years = float(principal), []
    for month in range(months):
        if month % 12 == 0:
            years.append({"year": month // 12 + 1, "interest": 0.0, "principal": 0.0})
        interest = balance * annual_rate / 12
        repaid = payment - interest
        balance -= repaid
        years[-1]["interest"] += interest
        years[-1]["principal"] += repaid
        years[-1]["closing_balance"] = max(balance, 0.0)
    return [{k: (v if k == "year" else round(v)) for k, v in y.items()} for y in years]


def projection(project: dict, principal: float, annual_rate: float, months: int) -> dict:
    """Three-year projection for a given loan. Rupee figures are whole rupees, so the table adds up."""
    schedule = {y["year"]: y for y in loan_schedule(principal, annual_rate, months)}
    depreciation = round(project["machinery_inr"] * cfg.MACHINERY_DEPRECIATION
                         + project["building_or_civil_inr"] * cfg.BUILDING_DEPRECIATION)
    years = []
    for y in range(1, cfg.YEARS + 1):
        sales = round(project["monthly_sales_year1_inr"] * 12 * (1 + project["annual_sales_growth"]) ** (y - 1))
        raw_material = round(project["raw_material_pct_of_sales"] * sales)
        fixed = project["monthly_fixed_costs_inr"] * 12
        interest = schedule.get(y, {}).get("interest", 0)
        principal_repaid = schedule.get(y, {}).get("principal", 0)
        profit = sales - raw_material - fixed - depreciation - interest
        cash_accrual = profit + depreciation
        debt_due = principal_repaid + interest
        years.append({
            "year": y, "sales": sales, "raw_material": raw_material, "fixed_costs": fixed,
            "depreciation": depreciation, "interest": interest, "principal_repaid": principal_repaid,
            "profit_before_tax": profit, "cash_accrual": cash_accrual,
            "dscr": round((cash_accrual + interest) / debt_due, 2) if debt_due else None,
        })
    ratios = [(y["cash_accrual"] + y["interest"]) / (y["principal_repaid"] + y["interest"])
              for y in years if y["dscr"] is not None]
    average = round(sum(ratios) / len(ratios), 2) if ratios else None
    band, band_key = dscr_band(average)
    return {"emi": round(emi(principal, annual_rate, months)), "years": years,
            "average_dscr": average, "band": band, "band_key": band_key}


def build(profile: dict, pmegp: dict, annual_rate: float | None = None, tenure_months: int | None = None) -> dict:
    """The whole report as JSON: cost of project, means of finance, projection, schedule, assumptions."""
    project = profile.get("project") or {}
    missing = missing_inputs(project)
    if missing:
        return {"complete": False, "missing": missing}

    rate = annual_rate if annual_rate is not None else cfg.DEFAULT_ANNUAL_RATE
    months = tenure_months or cfg.DEFAULT_TENURE_MONTHS
    total = project["machinery_inr"] + project["building_or_civil_inr"] + project["working_capital_inr"]
    stated = profile.get("project_cost_inr")
    mismatch = None if stated in (None, total) else {"from_details": total, "from_profile": stated}

    # PMEGP own contribution: special 5% / general 10% (10% if the category is not known).
    d = derive({**profile, "project_cost_inr": total})
    category = "special" if d["pmegp_special"] is True else cfg.DEFAULT_OWN_CONTRIBUTION
    own_rate = pmegp["rates"]["own_contribution"][category]
    own = round(total * own_rate)
    loan = total - own
    subsidy = estimate(pmegp, d)["grant_min"]

    proj = projection(project, loan, rate, months)
    return {
        "complete": True,
        "scheme_id": pmegp["id"],
        "cost_of_project": {"machinery": project["machinery_inr"], "building_or_civil": project["building_or_civil_inr"],
                            "working_capital": project["working_capital_inr"], "total": total},
        "cost_mismatch": mismatch,
        "means_of_finance": {"own_contribution_rate": own_rate, "own_contribution": own, "bank_loan": loan,
                             "subsidy_estimate": subsidy, "subsidy_label": cfg.SUBSIDY_LABEL},
        "loan": {"principal": loan, "annual_rate": rate, "tenure_months": months, "emi": proj["emi"]},
        "loan_schedule": loan_schedule(loan, rate, months),
        "years": proj["years"],
        "average_dscr": proj["average_dscr"],
        "band": proj["band"],
        "band_key": proj["band_key"],
        "assumptions": [
            f"Interest rate {round(rate * 100, 2):g}% a year and tenure {months} months are assumed. Your bank sets the real terms.",
            f"Sales grow {round(project['annual_sales_growth'] * 100, 2):g}% a year. Raw material is "
            f"{round(project['raw_material_pct_of_sales'] * 100, 2):g}% of sales. Fixed costs stay the same each year.",
            f"Depreciation is straight-line: machinery {round(cfg.MACHINERY_DEPRECIATION * 100):g}% and "
            f"building {round(cfg.BUILDING_DEPRECIATION * 100):g}% of cost each year.",
            "Taxes are ignored. All profits are before tax.",
            f"Own contribution is {round(own_rate * 100):g}% of the project cost, from the PMEGP rates.",
            "The subsidy is shown as a separate line. This report does not model how the bank adjusts the "
            "subsidy against the loan.",
            "DSCR bands (below 1.0 cannot cover repayments, 1.0 to 1.5 thin, 1.5 and above comfortable) are "
            "our assumption. Banks set their own minimum.",
        ],
    }
