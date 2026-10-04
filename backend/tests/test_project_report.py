"""M9: project report generator. The Lakshmi sample is built here; data files are never edited."""
import pytest
from fastapi.testclient import TestClient

from app.engine import project_report
from app.engine.paths import best_paths
from app.engine.run import evaluate_all
from app.llm import guard, provider, templates
from app.main import app
from app.models import Profile

PROJECT = {
    "machinery_inr": 500000, "building_or_civil_inr": 0, "working_capital_inr": 300000,
    "monthly_sales_year1_inr": 120000, "annual_sales_growth": 0.10, "raw_material_pct_of_sales": 0.50,
    "monthly_fixed_costs_inr": 25000, "business_description": "A small garment unit stitching school uniforms.",
}


@pytest.fixture
def lakshmi(personas):
    return Profile(**{**personas["lakshmi"], "project": PROJECT}).model_dump(exclude={"consent"})


@pytest.fixture
def report(lakshmi, schemes):
    return project_report.build(lakshmi, schemes["pmegp"], annual_rate=0.12, tenure_months=60)


def test_means_of_finance(report):
    assert report["complete"] and report["cost_mismatch"] is None
    assert report["cost_of_project"]["total"] == 800000
    finance = report["means_of_finance"]
    assert finance["own_contribution"] == 40000            # special category (female): 5%
    assert finance["bank_loan"] == 760000
    assert finance["subsidy_estimate"] == 280000
    assert "adjusted by the bank" in finance["subsidy_label"]
    assert report["loan"]["emi"] == 16906


def test_three_year_projection(report):
    y1, y2, y3 = report["years"]
    assert (y1["sales"], y1["raw_material"], y1["fixed_costs"], y1["depreciation"]) == (1440000, 720000, 300000, 50000)
    assert (y1["interest"], y1["principal_repaid"]) == (84849, 118021)
    assert (y1["profit_before_tax"], y1["cash_accrual"], y1["dscr"]) == (285151, 335151, 2.07)
    assert (y2["sales"], y2["interest"], y2["principal_repaid"], y2["profit_before_tax"], y2["dscr"]) == \
           (1584000, 69881, 132989, 372119, 2.43)
    assert (y3["sales"], y3["interest"], y3["principal_repaid"], y3["profit_before_tax"], y3["dscr"]) == \
           (1742400, 53015, 149855, 468185, 2.82)
    assert report["average_dscr"] == 2.44 and report["band"] == "Comfortable"


def test_loan_schedule_repays_the_whole_loan(report):
    schedule = report["loan_schedule"]
    assert len(schedule) == 5 and schedule[-1]["closing_balance"] == 0
    assert abs(sum(y["principal"] for y in schedule) - 760000) <= 3     # yearly rounding only


def test_own_contribution_is_general_when_category_unknown(personas, schemes):
    profile = Profile(**{**personas["lakshmi"], "owner_gender": "male", "project": PROJECT}).model_dump()
    finance = project_report.build(profile, schemes["pmegp"])["means_of_finance"]
    assert finance["own_contribution"] == 80000 and finance["bank_loan"] == 720000     # 10%
    assert finance["subsidy_estimate"] == 200000                                       # grant_min: general rural 25%


def test_dscr_bands():
    assert project_report.dscr_band(0.99)[0] == "Cannot cover repayments"
    assert project_report.dscr_band(1.0)[0] == "Thin" and project_report.dscr_band(1.49)[0] == "Thin"
    assert project_report.dscr_band(1.5)[0] == "Comfortable"
    weak = {**PROJECT, "monthly_sales_year1_inr": 60000}       # sales too low to cover the loan
    assert project_report.projection(weak, 760000, 0.12, 60)["band"] == "Cannot cover repayments"


def test_missing_inputs_and_cost_mismatch(personas, schemes):
    partial = Profile(**{**personas["lakshmi"], "project": {"machinery_inr": 500000}}).model_dump()
    out = project_report.build(partial, schemes["pmegp"])
    assert out["complete"] is False and "working_capital_inr" in out["missing"]
    assert project_report.build(Profile(**personas["lakshmi"]).model_dump(), schemes["pmegp"])["complete"] is False
    bigger = Profile(**{**personas["lakshmi"], "project": {**PROJECT, "machinery_inr": 600000}}).model_dump()
    assert project_report.build(bigger, schemes["pmegp"])["cost_mismatch"] == {"from_details": 900000, "from_profile": 800000}


def test_affordability_uses_the_project_report(lakshmi, schemes):
    evals = evaluate_all(lakshmi, schemes)
    a = evals["pmegp"]["affordability"]
    assert a["basis"] == "project_report" and a["dscr"] == 2.07 and a["band"] == "Comfortable"
    assert a["emi"] == 16906 and a["ratio"] is None
    vish = evals["pm_vishwakarma"]["affordability"]            # same project, that scheme's own loan and rate
    assert vish["basis"] == "project_report" and vish["annual_rate"] == 0.05 and vish["dscr"] > a["dscr"]


def test_template_narrative_passes_the_guard(lakshmi, report):
    out = provider.draft_project_narrative(lakshmi, report)
    facts = templates.narrative_facts(lakshmi, report)
    assert set(out["sections"]) == {"about", "market", "viability"} and out["used_template"]
    for text in out["sections"].values():
        assert guard.check_text(text, facts) == []
    assert "school uniforms" in out["sections"]["about"] and "[fill in]" in out["sections"]["market"]
    assert "before tax" in out["sections"]["viability"]


def test_guard_rejects_a_narrative_with_an_invented_number(monkeypatch, lakshmi, report):
    class Inventive(provider.MockProvider):
        name = "inventive"

        def project_narrative(self, profile, report):
            return {"about": "The unit will make a profit of ₹9,99,999 a year and employ 40 people.",
                    "market": "Sales are projected at ₹14,40,000 in year 1.",
                    "viability": "Repayment is guaranteed."}

    monkeypatch.setattr(provider, "get_provider", lambda: Inventive())
    out = provider.draft_project_narrative(lakshmi, report)
    template = templates.project_narrative(lakshmi, report)
    assert out["sections"]["about"] == template["about"]                 # 999999 and 40 are not in the figures
    assert out["sections"]["viability"] == template["viability"]         # banned wording
    assert out["sections"]["market"] == "Sales are projected at ₹14,40,000 in year 1."   # every number checks out
    assert out["replaced_sections"] == ["about", "viability"]


def test_id_numbers_in_the_description_are_redacted(personas, schemes):
    project = {**PROJECT, "business_description": "Garment unit. My PAN is ABCDE1234F."}
    profile = Profile(**{**personas["lakshmi"], "project": project}).model_dump(exclude={"consent"})
    out = provider.draft_project_narrative(profile, project_report.build(profile, schemes["pmegp"]))
    assert "ABCDE1234F" not in out["sections"]["about"]


@pytest.mark.parametrize("pid", ["lakshmi", "ravi", "shabana"])
def test_regression_expected_json_still_matches(pid, personas, schemes, conflicts, expected):
    evals = evaluate_all(Profile(**{**personas[pid], "project": PROJECT}).model_dump(exclude={"consent"}), schemes)
    got = {sid: {"status": e["status"], "met": e["met"], "total": e["total"], "unknown": e["unknown"],
                 "fails": e["fails"], "grant_min": e["estimate"]["grant_min"],
                 "grant_max": e["estimate"]["grant_max"], "credit": e["estimate"]["credit"]}
           for sid, e in evals.items()}
    assert got == expected[pid]["schemes"]
    paths = [{k: p[k] for k in ("schemes", "grant_min", "grant_max")} for p in best_paths(evals, schemes, conflicts)]
    assert paths == expected[pid]["best_paths"]


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_api_json_and_pdf(client, personas):
    profile = {**personas["lakshmi"], "project": PROJECT, "consent": {"given": True}}
    pid = client.post("/api/profiles", json={"profile": profile}).json()["profile_id"]
    body = client.post("/api/project-report", json={"profile_id": pid}).json()
    assert body["complete"] and body["average_dscr"] == 2.44 and body["loan"]["emi"] == 16906
    assert set(body["narrative"]["sections"]) == {"about", "market", "viability"}
    assert client.get(f"/api/profiles/{pid}").json()["project"]["machinery_inr"] == 500000

    pdf = client.get(f"/api/project-report/{pid}/pdf")
    assert pdf.status_code == 200 and pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF") and len(pdf.content) > 4000

    assert client.post("/api/project-report", json={"profile_id": "ravi"}).json()["complete"] is False
    assert client.get("/api/project-report/ravi/pdf").status_code == 400
    assert client.get("/api/project-report/nobody/pdf").status_code == 404
    assert client.post("/api/profiles", json={"profile": {**profile, "project": {"annual_sales_growth": 99}}}).status_code == 422
