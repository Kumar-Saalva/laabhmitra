"""API tests: every endpoint in spec 2.6, end to end with LLM_PROVIDER=mock and no network."""
import copy

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


CONSENT = {"given": True, "purposes": ["eligibility"]}


def test_health_and_docs(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok" and body["schemes"] == 12 and body["llm_provider"] == "mock"
    assert client.get("/docs").status_code == 200


def test_schemes_and_personas(client):
    schemes = client.get("/api/schemes").json()
    assert len(schemes) == 12 and {"id", "name", "status", "last_verified"} <= set(schemes[0])
    assert set(client.get("/api/personas").json()) == {"lakshmi", "ravi", "shabana"}
    assert client.get("/api/schemes/pmegp").json()["rates"]["special"]["rural"] == 0.35
    assert client.get("/api/schemes/nope").status_code == 404


def test_profile_needs_consent(client, personas):
    assert client.post("/api/profiles", json={"profile": personas["ravi"]}).status_code == 400
    refused = {**personas["ravi"], "consent": {"given": False}}
    assert client.post("/api/profiles", json={"profile": refused}).status_code == 400
    ok = client.post("/api/profiles", json={"profile": {**personas["ravi"], "consent": CONSENT}})
    assert ok.status_code == 200
    saved = client.get(f"/api/profiles/{ok.json()['profile_id']}").json()
    assert saved["consent"]["given"] and saved["consent"]["timestamp"] and saved["owner_age"] == 41


def test_profile_rejects_bad_values_and_drops_id_numbers(client):
    bad = {"state": "KA", "business_activity": "farming", "consent": CONSENT}
    assert client.post("/api/profiles", json={"profile": bad}).status_code == 422
    sneaky = {"state": "KA", "business_activity": "trading", "pan_number": "ABCDE1234F", "consent": CONSENT}
    pid = client.post("/api/profiles", json={"profile": sneaky}).json()["profile_id"]
    assert "pan_number" not in client.get(f"/api/profiles/{pid}").json()


def test_evaluate_with_profile_and_with_id(client, personas, expected):
    by_profile = client.post("/api/evaluate", json={"profile": personas["lakshmi"]}).json()
    by_id = client.post("/api/evaluate", json={"profile_id": "shabana"}).json()   # preloaded in demo mode
    for body, pid in ((by_profile, "lakshmi"), (by_id, "shabana")):
        assert len(body["results"]) == 12
        for r in body["results"]:
            want = expected[pid]["schemes"][r["scheme_id"]]
            assert r["status"] == want["status"] and r["estimate"]["grant_max"] == want["grant_max"]
            assert r["scheme"]["sources"] and r["scheme"]["last_verified"]     # every card has its source
    tiers = [r["tier"] for r in by_profile["results"]]
    assert tiers == sorted(tiers, key=["ready", "likely", "one_step", "not_now", "watchlist", "hidden"].index)
    assert by_profile["results"][0]["scheme_id"] == "pmegp"                  # ready, biggest grant first
    assert client.post("/api/evaluate", json={}).status_code == 422
    assert client.post("/api/evaluate", json={"profile_id": "nobody"}).status_code == 404


def test_evaluate_in_kannada_changes_words_not_results(client, personas):
    en = client.post("/api/evaluate", json={"profile": personas["lakshmi"], "lang": "en"}).json()
    kn = client.post("/api/evaluate", json={"profile": personas["lakshmi"], "lang": "kn"}).json()
    assert [(r["scheme_id"], r["status"], r["estimate"]) for r in en["results"]] == \
           [(r["scheme_id"], r["status"], r["estimate"]) for r in kn["results"]]
    assert en["results"][0]["criteria"][0]["label"] != kn["results"][0]["criteria"][0]["label"]


def test_opportunity_map(client):
    omap = client.get("/api/opportunity-map/lakshmi").json()
    assert set(omap["buckets"]) == {"grants", "credit", "fee_savings", "non_monetary"}
    assert omap["headline"]["grant_max"] == 280000
    assert [p["schemes"] for p in omap["best_paths"]] == [["pmegp"], ["pm_vishwakarma", "ka_udyogini"]]
    assert omap["fix_plan"][0]["unlock_names"] == ["CGTMSE", "ZED Certification", "ME-Card"]
    assert [f["scheme_id"] for f in omap["buckets"]["fee_savings"]] == ["zed"]
    assert client.get("/api/opportunity-map/nobody").status_code == 404


def test_explain_why_and_why_not(client):
    why = client.post("/api/explain", json={"profile_id": "lakshmi", "scheme_id": "pmegp", "lang": "en"}).json()
    assert why["text"].startswith("You may be eligible") and why["source"]["url"].startswith("https://")
    not_ = client.post("/api/explain", json={"profile_id": "lakshmi", "scheme_id": "stand_up_india",
                                             "lang": "kn", "kind": "why_not"}).json()
    assert "₹7,20,000" in not_["text"] and not_["status"] == "NOT_ELIGIBLE"


def test_extract(client):
    body = client.post("/api/extract", json={"text": "I'm a tailor in Mandya village, want to start a "
                                                     "small garment unit costing 8 lakh"}).json()
    assert body["provider"] == "mock" and body["profile"]["project_cost_inr"] == 800000


def test_pack_pdf_preview_and_tracker(client):
    req = {"profile_id": "lakshmi", "scheme_id": "pmegp", "lang": "en"}
    pdf = client.post("/api/pack", json=req)
    assert pdf.status_code == 200 and pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF") and len(pdf.content) > 2000
    preview = client.post("/api/pack/preview", json=req).json()
    states = {i["document"]: i["state"] for i in preview["checklist"]}
    assert states["PAN"] == "have" and states["Bank details"] == "have" and states["Project report"] == "check"
    assert preview["draft"]["text"].startswith("DRAFT") and preview["tracker"]["status"] == "not_started"
    shabana = client.post("/api/pack/preview", json={"profile_id": "shabana", "scheme_id": "udyam_registration"}).json()
    assert {i["document"]: i["state"] for i in shabana["checklist"]}["PAN"] == "need"

    update = {"profile_id": "lakshmi", "scheme_id": "pmegp", "status": "received", "amount_received_inr": 280000}
    assert client.post("/api/pack/status", json=update).json()["status"] == "received"
    assert client.get("/api/pack/status/lakshmi").json()[0]["amount_received_inr"] == 280000
    assert client.post("/api/pack/status", json={**update, "status": "won"}).status_code == 422


def test_watch_feed_after_udyam_registration(client, personas):
    profile = {**personas["lakshmi"], "consent": CONSENT}
    pid = client.post("/api/profiles", json={"profile": profile}).json()["profile_id"]
    assert client.get(f"/api/watch/{pid}").json()["notifications"] == []
    changed = client.post("/api/profiles", json={"profile": {**profile, "udyam_registered": True},
                                                 "profile_id": pid}).json()
    assert {n["scheme_id"] for n in changed["notifications"]} == {"cgtmse", "zed", "me_card"}
    feed = client.get(f"/api/watch/{pid}").json()["notifications"]
    assert len(feed) == 3 and all(n["kind"] == "improved" and n["new"] == "ELIGIBLE" for n in feed)
    assert {n["short_name"] for n in feed} == {"CGTMSE", "ZED Certification", "ME-Card"}


def test_admin_rule_tester(client, schemes):
    ok = client.post("/api/admin/test-scheme", json={"scheme": schemes["pmegp"]}).json()
    assert ok["valid"] and [r["status"] for r in ok["results"]] == ["ELIGIBLE", "NOT_ELIGIBLE", "NOT_ELIGIBLE"]
    assert all(r["matches_expected"] for r in ok["results"])

    edited = copy.deepcopy(schemes["stand_up_india"])
    edited["criteria"][3]["value"] = 500000                      # lower the minimum loan to 5 lakh
    changed = client.post("/api/admin/test-scheme", json={"scheme": edited}).json()
    assert changed["results"][0]["status"] == "ELIGIBLE" and changed["results"][0]["matches_expected"] is False

    new = {"id": "demo_new", "short_name": "Demo", "name": "Demo scheme", "kind": "credit", "status": "active",
           "criteria": [{"id": "ka", "label": "In Karnataka", "field": "state", "op": "eq", "value": "KA",
                         "hard": True, "source_ref": "s1"}],
           "documents": [], "application": {"channel": "x", "url": None, "steps": []},
           "sources": [{"id": "s1", "title": "t", "url": "https://example.org"}], "last_verified": "2026-10-04"}
    added = client.post("/api/admin/test-scheme", json={"scheme": new}).json()
    assert added["valid"] and added["is_new"] and all(r["status"] == "ELIGIBLE" for r in added["results"])

    broken = {**new, "status": "maybe", "criteria": [{**new["criteria"][0], "op": "almost"}]}
    bad = client.post("/api/admin/test-scheme", json={"scheme": broken}).json()
    assert not bad["valid"] and len(bad["errors"]) == 2
    missing_ref = {**new, "criteria": [{**new["criteria"][0], "source_ref": "s9"}]}
    assert "source_ref" in client.post("/api/admin/test-scheme", json={"scheme": missing_ref}).json()["errors"][0]
