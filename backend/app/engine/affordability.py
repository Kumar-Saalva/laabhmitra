"""Loan affordability check: does the monthly repayment fit the merchant's cash?

This only adds a warning badge. It never changes a status, a tier or the path planner.
"""
from app.engine import affordability_config as cfg

MISSING_CASH = "Add monthly sales and costs to check affordability"
NEEDS_REPORT = "Unknown: needs a project report"
NO_FIXED_EMI = "No fixed EMI; interest depends on usage"


def emi(principal: float, annual_rate: float, months: int) -> float:
    """Equal monthly instalment: P*r*(1+r)^n / ((1+r)^n - 1), where r is the monthly rate.
    Returned unrounded; round to whole rupees only for display."""
    if months <= 0:
        raise ValueError("months must be positive")
    r = annual_rate / 12
    if r == 0:
        return principal / months
    growth = (1 + r) ** months
    return principal * r * growth / (growth - 1)


def cash_band(ratio):
    """Band from EMI / monthly surplus."""
    if ratio <= cfg.COMFORTABLE_MAX:
        return "Comfortable", "comfortable"
    if ratio <= cfg.TIGHT_MAX:
        return "Tight", "tight"
    return "May strain your cash", "strain"


def check(profile: dict, scheme_id: str, principal: int, annual_rate: float | None = None,
          tenure_months: int | None = None):
    """Return the affordability result for one scheme, or None if the scheme has no loan.

    principal is the scheme's estimated credit from estimate.py (for PMEGP: bank finance).
    """
    if not principal or principal <= 0:
        return None
    rate = annual_rate if annual_rate is not None else cfg.SCHEME_RATE_OVERRIDES.get(scheme_id, cfg.DEFAULT_ANNUAL_RATE)
    months = tenure_months or cfg.DEFAULT_TENURE_MONTHS
    note = cfg.ASSUMPTIONS_NOTE + (" " + cfg.PMEGP_NOTE if scheme_id == "pmegp" else "")
    out = {
        "scheme_id": scheme_id, "principal": principal, "annual_rate": rate, "tenure_months": months,
        "emi": None, "monthly_surplus": None, "ratio": None, "dscr": None,
        "band": "Unknown", "band_key": "unknown", "basis": "current_cash", "message": None,
        "assumptions_note": note,
    }
    if scheme_id in cfg.NO_FIXED_EMI:
        out.update(band="No fixed EMI", band_key="no_fixed_emi", message=NO_FIXED_EMI)
        return out

    payment = emi(principal, rate, months)
    out["emi"] = round(payment)

    if profile.get("is_new_project") is True:
        # A new unit has no current cash to compare with: use the project report's year-1 DSCR.
        from app.engine import project_report        # local import: project_report uses emi() above
        out["basis"] = "project_report"
        project = profile.get("project") or {}
        if project_report.missing_inputs(project):
            out["message"] = NEEDS_REPORT
            return out
        projection = project_report.projection(project, principal, rate, months)
        out["dscr"] = projection["years"][0]["dscr"]
        out["band"], out["band_key"] = project_report.dscr_band(out["dscr"])
        return out

    sales, costs, emis = (profile.get(k) for k in ("monthly_sales_inr", "monthly_costs_inr", "existing_emis_inr"))
    if sales is None or costs is None or emis is None:
        out["message"] = MISSING_CASH
        return out
    surplus = sales - costs - emis
    out["monthly_surplus"] = surplus
    if surplus <= 0:
        out.update(band="May strain your cash", band_key="strain")
        return out
    out["ratio"] = round(payment / surplus, 3)
    out["band"], out["band_key"] = cash_band(payment / surplus)
    return out
