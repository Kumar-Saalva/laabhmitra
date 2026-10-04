"""Unit tests: operators, 'when', unknown_values, derived fields, staleness, display rules."""
from datetime import date

import pytest

from app.engine import derive as dv
from app.engine.estimate import estimate, mudra_tier
from app.engine.evaluate import (apply_op, evaluate_condition, evaluate_criterion, evaluate_scheme,
                                 is_stale, is_visible)
from app.engine.run import evaluate_all, next_questions
from app.models import Profile
from app.money import format_inr

T, F, U, NA = "TRUE", "FALSE", "UNKNOWN", "N/A"


@pytest.mark.parametrize("value,op,target,want", [
    (5, "eq", 5, T), (5, "eq", 6, F),
    (5, "neq", 6, T), (5, "neq", 5, F),
    ("a", "in", ["a", "b"], T), ("c", "in", ["a", "b"], F),
    ("c", "not_in", ["a", "b"], T), ("a", "not_in", ["a", "b"], F),
    (6, "gt", 5, T), (5, "gt", 5, F),
    (5, "gte", 5, T), (4, "gte", 5, F),
    (4, "lt", 5, T), (5, "lt", 5, F),
    (5, "lte", 5, T), (6, "lte", 5, F),
    (18, "between", [18, 55], T), (55, "between", [18, 55], T), (56, "between", [18, 55], F),
    (True, "is_true", None, T), (False, "is_true", None, F),
    (False, "is_false", None, T), (True, "is_false", None, F),
])
def test_operators(value, op, target, want):
    assert apply_op(value, op, target) == want


def test_missing_value_is_unknown_for_every_operator():
    for op in ["eq", "neq", "in", "not_in", "gt", "gte", "lt", "lte", "between", "is_true", "is_false"]:
        assert apply_op(None, op, [1, 2]) == U


def test_bad_operator_raises():
    with pytest.raises(ValueError):
        apply_op(1, "almost", 1)


CRIT = {"id": "c", "label": "c", "field": "x", "op": "lte", "value": 10, "hard": True,
        "when": {"field": "kind", "op": "eq", "value": "a"}}


def test_when_false_gives_na():
    assert evaluate_criterion(CRIT, {"x": 5, "kind": "b"}) == NA


def test_when_unknown_gives_unknown():
    assert evaluate_criterion(CRIT, {"x": 5}) == U


def test_when_true_applies_operator():
    assert evaluate_criterion(CRIT, {"x": 5, "kind": "a"}) == T
    assert evaluate_criterion(CRIT, {"x": 50, "kind": "a"}) == F


def test_when_all():
    cond = {"all": [{"field": "a", "op": "eq", "value": 1}, {"field": "b", "op": "gt", "value": 1}]}
    assert evaluate_condition(cond, {"a": 1, "b": 2}) == T
    assert evaluate_condition(cond, {"a": 2}) == F          # one FALSE wins over UNKNOWN
    assert evaluate_condition(cond, {"a": 1}) == U


def test_unknown_values():
    crit = {"id": "c", "label": "c", "field": "act", "op": "in", "value": ["m"], "hard": True,
            "unknown_values": ["trading"]}
    assert evaluate_criterion(crit, {"act": "trading"}) == U
    assert evaluate_criterion(crit, {"act": "m"}) == T
    assert evaluate_criterion(crit, {"act": "other"}) == F


def scheme(criteria, status="active", kind="credit"):
    return {"id": "s", "status": status, "kind": kind, "criteria": criteria}


def crit(cid, field, fix=False):
    c = {"id": cid, "label": cid, "field": field, "op": "is_true", "value": None, "hard": True}
    if fix:
        c["fix"] = {"action_id": "do_" + cid, "label": "do it"}
    return c


def test_status_order():
    a, b, c = crit("a", "a"), crit("b", "b", fix=True), crit("c", "c", fix=True)
    assert evaluate_scheme(scheme([a]), {"a": True})["status"] == "ELIGIBLE"
    assert evaluate_scheme(scheme([a]), {})["status"] == "LIKELY"
    assert evaluate_scheme(scheme([a, b]), {"a": True, "b": False})["status"] == "NEAR_MISS"
    assert evaluate_scheme(scheme([a, b]), {"a": False, "b": False})["status"] == "NOT_ELIGIBLE"
    three = [b, c, crit("d", "d", fix=True)]
    assert evaluate_scheme(scheme(three), {"b": False, "c": False, "d": False})["status"] == "NOT_ELIGIBLE"
    assert evaluate_scheme(scheme([a], status="announced"), {"a": False})["status"] == "WATCHLIST"


def test_registration_already_done_is_not_applicable():
    not_yet = {"id": "not_yet", "label": "x", "field": "udyam_registered", "op": "is_false", "value": None, "hard": True}
    result = evaluate_scheme(scheme([not_yet], kind="registration"), {"udyam_registered": True})
    assert result["status"] == "NOT_APPLICABLE"


def test_counts_skip_na():
    r = evaluate_scheme(scheme([CRIT, crit("a", "a"), crit("b", "b")]), {"kind": "b", "a": True})
    assert (r["met"], r["total"], r["unknown"]) == (1, 2, 1)


def test_enterprise_size():
    assert dv.enterprise_size(None, 1) is None
    assert dv.enterprise_size(2.5e7, 1e8) == "micro"
    assert dv.enterprise_size(2.5e7 + 1, 1e8) == "small"
    assert dv.enterprise_size(1.25e9, 5e9) == "medium"
    assert dv.enterprise_size(1.25e9 + 1, 1) == "large"


def test_female_or_scst_and_pmegp_special():
    assert dv.female_or_scst("female", "prefer_not") is True
    assert dv.female_or_scst("male", "st") is True
    assert dv.female_or_scst("male", "prefer_not") is None
    assert dv.female_or_scst("male", "obc") is False
    assert dv.pmegp_special({"owner_gender": "male", "social_category": "obc"}) is True
    assert dv.pmegp_special({"owner_gender": "male", "social_category": "general", "is_ex_serviceman": True}) is True
    assert dv.pmegp_special({"owner_gender": "male", "social_category": "prefer_not"}) is None
    assert dv.pmegp_special({"owner_gender": "male", "social_category": "general"}) is False


def test_similar_loan_last_5y():
    assert dv.similar_loan_last_5y([], 2026) is False
    assert dv.similar_loan_last_5y([{"scheme": "mudra", "year": 2019, "repaid": False}], 2026) is False
    assert dv.similar_loan_last_5y([{"scheme": "other", "year": 2025, "repaid": False}], 2026) is False
    assert dv.similar_loan_last_5y([{"scheme": "mudra", "year": 2024, "repaid": True}], 2026) is None
    assert dv.similar_loan_last_5y([{"scheme": "mudra", "year": 2024, "repaid": False}], 2026) is True


def test_udyogini_income_ok():
    ok = dv.udyogini_income_ok
    assert ok({"is_widow": True, "family_annual_income_inr": 900000}) is True
    assert ok({"social_category": "sc"}) is None
    assert ok({"social_category": "sc", "family_annual_income_inr": 199999}) is True
    assert ok({"social_category": "general", "family_annual_income_inr": 150000}) is False
    assert ok({"social_category": "prefer_not", "family_annual_income_inr": 140000}) is True
    assert ok({"social_category": "prefer_not", "family_annual_income_inr": 170000}) is None
    assert ok({"social_category": "prefer_not", "family_annual_income_inr": 200000}) is False


def test_staleness():
    assert is_stale("2026-10-04", date(2026, 10, 4)) is False
    assert is_stale("2026-10-04", date(2027, 1, 2)) is False     # exactly 90 days
    assert is_stale("2026-10-04", date(2027, 1, 3)) is True      # 91 days


def test_display_rules(personas, schemes):
    def visible(pid):
        evals = evaluate_all(Profile(**personas[pid]).model_dump(), schemes)
        return {sid for sid, e in evals.items() if e["visible"]}
    lakshmi, ravi, shabana = visible("lakshmi"), visible("ravi"), visible("shabana")
    assert "udyam_assist" not in lakshmi and "udyam_registration" in lakshmi   # she has a PAN
    assert "udyam_assist" in shabana                                            # no PAN
    assert "udyam_registration" not in ravi and "udyam_assist" not in ravi      # NOT_APPLICABLE hidden
    assert "first_time_women_scst" in lakshmi                                   # watchlist, no hard FALSE
    assert "first_time_women_scst" not in ravi and "first_time_women_scst" not in shabana
    assert is_visible({"id": "x"}, {"status": "ELIGIBLE", "fails": []}, {}) is True


def test_estimates(schemes):
    assert [mudra_tier(a) for a in (25000, 400000, 1000000, 1500000)] == ["Shishu", "Kishore", "Tarun", "Tarun Plus"]
    d = dv.derive({"project_cost_inr": 9000000, "business_activity": "service", "area_type": "urban",
                   "owner_gender": "male", "social_category": "general"})
    e = estimate(schemes["pmegp"], d)
    assert (e["grant_min"], e["grant_max"], e["credit"]) == (300000, 300000, 1800000)   # capped at 20 lakh
    d = dv.derive({"project_cost_inr": 1000000, "business_activity": "manufacturing", "area_type": "rural",
                   "owner_gender": "male", "social_category": "prefer_not"})
    e = estimate(schemes["pmegp"], d)
    assert (e["grant_min"], e["grant_max"]) == (250000, 350000)                         # range when unknown
    assert estimate(schemes["mudra"], {"loan_amount_needed_inr": 400000})["tier_name"] == "Kishore"


def test_next_questions_rank_missing_fields(schemes):
    profile = Profile(state="KA", business_activity="manufacturing").model_dump()
    asked = [q["field"] for q in next_questions(profile, schemes, evaluate_all(profile, schemes))]
    assert asked and "state" not in asked and "udyam_registered" in asked
    empty = Profile().model_dump()
    first_two = [q["field"] for q in next_questions(empty, schemes, evaluate_all(empty, schemes))[:2]]
    assert set(first_two) == {"state", "business_activity"}      # the two required fields come first


def test_profile_drops_unknown_keys_and_numbers():
    p = Profile(state="KA", pan_number="ABCDE1234F", aadhaar="123412341234")
    assert "pan_number" not in p.model_dump() and "aadhaar" not in p.model_dump()


def test_format_inr():
    assert format_inr(280000) == "₹2,80,000"
    assert format_inr(7500) == "₹7,500"
    assert format_inr(100000000) == "₹10,00,00,000"
    assert format_inr(0) == "₹0"
