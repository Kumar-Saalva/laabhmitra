"""M8: loan affordability check. Profiles are copies built here; data files are never edited."""
import json

import pytest
from fastapi.testclient import TestClient

from app import data
from app.engine import affordability_config as cfg
from app.engine.affordability import check, emi
from app.engine.paths import best_paths
from app.engine.run import evaluate_all
from app.main import app
from app.models import Profile

RAVI_CASH = {"monthly_sales_inr": 375000, "monthly_costs_inr": 340000, "existing_emis_inr": 0}


def run(persona, schemes, **changes):
    profile = Profile(**{**persona, **changes}).model_dump(exclude={"consent"})
    return profile, evaluate_all(profile, schemes)


def test_emi_formula():
    assert round(emi(100000, 0.12, 12), 2) == 8884.88
    assert round(emi(120000, 0, 12), 2) == 10000.00          # zero interest: plain division
    with pytest.raises(ValueError):
        emi(100000, 0.12, 0)


def test_ravi_mudra_is_comfortable(personas, schemes):
    _, evals = run(personas["ravi"], schemes, **RAVI_CASH)
    a = evals["mudra"]["affordability"]
    assert a["principal"] == 400000 and a["emi"] == 8898
    assert a["annual_rate"] == 0.12 and a["tenure_months"] == 60
    assert a["monthly_surplus"] == 35000
    assert a["ratio"] == pytest.approx(0.254, abs=0.001)
    assert a["band"] == "Comfortable" and a["basis"] == "current_cash"


def test_pm_vishwakarma_uses_the_scheme_rate():
    assert round(emi(300000, 0.05, 60)) == 5661
    a = check({"is_new_project": False, **RAVI_CASH}, "pm_vishwakarma", 300000)
    assert a["annual_rate"] == 0.05 and a["emi"] == 5661


def test_me_card_has_no_fixed_emi(personas, schemes):
    _, evals = run(personas["ravi"], schemes, **RAVI_CASH)
    a = evals["me_card"]["affordability"]
    assert a["band"] == "No fixed EMI" and a["emi"] is None
    assert "no fixed emi" in a["message"].lower() and "interest depends on usage" in a["message"]


def test_missing_monthly_fields_is_unknown(personas, schemes):
    _, evals = run(personas["ravi"], schemes)
    a = evals["mudra"]["affordability"]
    assert a["band"] == "Unknown" and a["emi"] == 8898
    assert a["message"] == "Add monthly sales and costs to check affordability"
    _, evals = run(personas["ravi"], schemes, monthly_sales_inr=375000, monthly_costs_inr=340000)
    assert evals["mudra"]["affordability"]["band"] == "Unknown"      # existing EMIs not given


def test_no_surplus_may_strain(personas, schemes):
    for costs in (375000, 400000):                                   # surplus zero, then negative
        _, evals = run(personas["ravi"], schemes, monthly_sales_inr=375000, monthly_costs_inr=costs, existing_emis_inr=0)
        a = evals["mudra"]["affordability"]
        assert a["band"] == "May strain your cash" and a["ratio"] is None


def test_bands():
    profile = {"is_new_project": False, "monthly_sales_inr": 100000, "monthly_costs_inr": 0, "existing_emis_inr": 0}
    payment = emi(400000, 0.12, 60)                                   # about 8898
    for surplus, band in ((payment / 0.30 + 1, "Comfortable"), (payment / 0.35, "Tight"),
                          (payment / 0.40 + 1, "Tight"), (payment / 0.45, "May strain your cash")):
        a = check({**profile, "monthly_sales_inr": round(surplus)}, "mudra", 400000)
        assert a["band"] == band, (surplus, a)
    assert (cfg.COMFORTABLE_MAX, cfg.TIGHT_MAX) == (0.30, 0.40)


def test_existing_emis_reduce_the_surplus():
    a = check({"is_new_project": False, "monthly_sales_inr": 375000, "monthly_costs_inr": 340000,
               "existing_emis_inr": 15000}, "mudra", 400000)
    assert a["monthly_surplus"] == 20000 and a["band"] == "May strain your cash"


def test_new_project_needs_a_project_report(personas, schemes):
    _, evals = run(personas["lakshmi"], schemes, **RAVI_CASH)
    a = evals["pmegp"]["affordability"]
    assert a["principal"] == 760000                                   # the bank-finance figure
    assert a["band"] == "Unknown" and a["basis"] == "project_report"
    assert a["message"] == "Unknown: needs a project report"
    assert "Conservative" in a["assumptions_note"]


def test_schemes_without_a_loan_have_no_affordability(personas, schemes):
    _, evals = run(personas["ravi"], schemes, **RAVI_CASH)
    assert evals["zed"]["affordability"] is None and evals["udyam_registration"]["affordability"] is None


def test_wording_never_says_guaranteed(personas, schemes):
    _, evals = run(personas["ravi"], schemes, **RAVI_CASH)
    assert "guaranteed" not in json.dumps([e["affordability"] for e in evals.values()]).lower()


@pytest.mark.parametrize("pid", ["lakshmi", "ravi", "shabana"])
def test_regression_expected_json_still_matches(pid, personas, schemes, conflicts, expected):
    """Affordability inputs must never change a status, an amount or a best path."""
    for extra in ({}, RAVI_CASH, {"monthly_sales_inr": 1, "monthly_costs_inr": 999999, "existing_emis_inr": 5}):
        _, evals = run(personas[pid], schemes, **extra)
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


def test_api_evaluate_includes_affordability(client, personas):
    body = client.post("/api/evaluate", json={"profile": {**personas["ravi"], **RAVI_CASH}}).json()
    by_id = {r["scheme_id"]: r for r in body["results"]}
    assert by_id["mudra"]["affordability"]["band"] == "Comfortable"
    assert by_id["mudra"]["status"] == "ELIGIBLE"
    asked = [q["field"] for q in client.post("/api/evaluate", json={"profile": personas["ravi"]}).json()["next_questions"]]
    assert asked[-3:] == ["monthly_sales_inr", "monthly_costs_inr", "existing_emis_inr"]


def test_api_affordability_lets_the_user_change_rate_and_tenure(client, personas):
    profile = {**personas["ravi"], **RAVI_CASH}
    default = client.post("/api/affordability", json={"profile": profile, "scheme_id": "mudra"}).json()
    assert default["emi"] == 8898
    changed = client.post("/api/affordability", json={"profile": profile, "scheme_id": "mudra",
                                                      "annual_rate": 0.10, "tenure_months": 36}).json()
    assert changed["emi"] == round(emi(400000, 0.10, 36)) and changed["principal"] == 400000
    assert changed["band"] == "Tight" and changed["tenure_months"] == 36
    assert client.post("/api/affordability", json={"profile": profile, "scheme_id": "zed"}).status_code == 404
    assert client.post("/api/affordability", json={"profile": profile, "scheme_id": "mudra",
                                                   "annual_rate": 5}).status_code == 422
    assert data.schemes()["mudra"]["status"] == "active"
