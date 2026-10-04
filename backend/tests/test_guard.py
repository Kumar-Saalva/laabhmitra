"""LLM guardrails: numbers check, wording, template fallback, schema validation, mock extractor."""
import pytest

from app.engine.run import evaluate_all
from app.llm import guard, keywords, provider, templates
from app.models import Profile


def setup(pid, sid, personas, schemes):
    profile = Profile(**personas[pid]).model_dump(exclude={"consent"})
    result = evaluate_all(profile, schemes)[sid]
    return profile, schemes[sid], result


def test_number_not_in_facts_is_replaced_by_template(personas, schemes):
    profile, scheme, result = setup("lakshmi", "pmegp", personas, schemes)
    facts = templates.build_facts(profile, scheme, result)
    title = scheme["sources"][0]["title"]
    template = templates.explain("why", profile, scheme, result, "en")
    invented = f"You may be eligible. The subsidy is ₹4,00,000. Source: {title}"
    text, used_fallback, problems = guard.guarded(invented, facts, template, title)
    assert used_fallback and text == template
    assert "400000" in problems[0]


def test_good_text_passes_and_lakh_wording_is_allowed(personas, schemes):
    profile, scheme, result = setup("lakshmi", "pmegp", personas, schemes)
    facts = templates.build_facts(profile, scheme, result)
    title = scheme["sources"][0]["title"]
    good = ("You may be eligible. You are 34 and 18 is needed. Your ₹8 lakh project is within the ₹50 lakh limit. "
            f"As a woman in a rural area the rate is 35%. Estimated subsidy ₹2,80,000. Source: {title}")
    text, used_fallback, problems = guard.guarded(good, facts, "TEMPLATE", title)
    assert not used_fallback and text == good and problems == []


def test_banned_wording_and_missing_source(personas, schemes):
    profile, scheme, result = setup("lakshmi", "pmegp", personas, schemes)
    facts = templates.build_facts(profile, scheme, result)
    title = scheme["sources"][0]["title"]
    assert guard.check_text(f"This is guaranteed. Source: {title}", facts, title)
    assert guard.check_text(f"You will get the subsidy. Source: {title}", facts, title)
    assert "does not end with the source title" in guard.check_text("You may be eligible.", facts, title)
    assert guard.check_text("", facts, title) == ["empty"]


@pytest.mark.parametrize("lang", ["en", "kn", "hi"])
@pytest.mark.parametrize("kind", ["why", "why_not"])
def test_every_template_passes_its_own_guard(lang, kind, personas, schemes):
    for pid in personas:
        for sid in schemes:
            profile, scheme, result = setup(pid, sid, personas, schemes)
            facts = templates.build_facts(profile, scheme, result)
            text = templates.explain(kind, profile, scheme, result, lang)
            assert guard.check_text(text, facts, scheme["sources"][0]["title"]) == [], (pid, sid, text)
            assert "guaranteed" not in text.lower()


def test_templates_use_careful_wording(personas, schemes):
    profile, scheme, result = setup("lakshmi", "pmegp", personas, schemes)
    text = templates.explain("why", profile, scheme, result, "en")
    assert text.startswith("You may be eligible for PMEGP.")
    assert "Estimated subsidy: ₹2,80,000." in text
    assert text.endswith("Source: " + scheme["sources"][0]["title"])
    kn = templates.explain("why", profile, scheme, result, "kn")
    assert "ಅರ್ಹರಾಗಿರಬಹುದು" in kn and "₹2,80,000" in kn


def test_why_not_names_the_rule_the_value_and_the_fix(personas, schemes):
    profile, scheme, result = setup("lakshmi", "stand_up_india", personas, schemes)
    text = templates.explain("why_not", profile, scheme, result, "en")
    assert "✗ Loan of at least ₹10 lakh. Yours: ₹7,20,000." in text
    profile, scheme, result = setup("lakshmi", "cgtmse", personas, schemes)
    text = templates.explain("why_not", profile, scheme, result, "en")
    assert "What you can do: Register on the Udyam portal" in text


def test_draft_is_marked_and_uses_placeholders(personas, schemes):
    profile, scheme, result = setup("ravi", "mudra", personas, schemes)
    draft = provider.draft_pack(profile, scheme, result)["text"]
    assert draft.startswith("DRAFT: review before use")
    assert "[fill in]" in draft and "₹4,00,000" in draft
    assert "Project cost: [fill in]" in draft          # Ravi has no project cost: not invented
    assert guard.unsupported_numbers(draft, templates.draft_facts(profile, scheme, result)) == []


def test_clean_profile_keeps_only_allowed_keys_and_valid_values():
    raw = {"state": "KA", "owner_age": 34, "business_activity": "farming", "pan_number": "ABCDE1234F",
           "owner_gender": "female", "project_cost_inr": "800000", "existing_govt_loans": [], "trade": None}
    assert guard.clean_profile(raw) == {"state": "KA", "owner_age": 34, "owner_gender": "female",
                                        "project_cost_inr": 800000}
    assert guard.clean_profile("not a dict") == {}


def test_id_numbers_are_redacted():
    text = guard.redact_ids("My PAN is ABCDE1234F and Aadhaar 1234 5678 9012, need 25000")
    assert "ABCDE1234F" not in text and "9012" not in text and "25000" in text


def test_mock_extracts_lakshmi_sentence():
    got = keywords.extract("I'm a tailor in Mandya village, want to start a small garment unit costing 8 lakh")
    assert got == {"state": "KA", "district": "Mandya", "area_type": "rural", "trade": "tailor",
                   "self_employed": True, "business_activity": "manufacturing", "is_new_project": True,
                   "project_cost_inr": 800000}


def test_mock_extracts_ravi_sentence():
    got = keywords.extract("I run a kirana shop in Jayanagar Bengaluru for 6 years, turnover 45 lakh, "
                           "Udyam and GST registered, I need 4 lakh working capital")
    assert got["business_activity"] == "trading" and got["area_type"] == "urban" and got["state"] == "KA"
    assert got["years_operating"] == 6 and got["is_new_project"] is False
    assert got["annual_turnover_inr"] == 4500000 and got["loan_amount_needed_inr"] == 400000
    assert got["udyam_registered"] is True and got["gst_registered"] is True


def test_mock_extracts_shabana_sentence():
    got = keywords.extract("I am a street vendor selling fruit in KR Market, I have a vending certificate, "
                           "no PAN, need 25000")
    assert got["business_activity"] == "street_vending" and got["district"] == "Bengaluru Urban"
    assert got["has_vending_proof"] is True and got["pan_available"] is False
    assert got["loan_amount_needed_inr"] == 25000


def test_mock_extracts_kannada():
    got = keywords.extract("ನಾನು ಮಂಡ್ಯ ಹಳ್ಳಿಯ ದರ್ಜಿ, 8 ಲಕ್ಷ ವೆಚ್ಚದ ಹೊಸ ಗಾರ್ಮೆಂಟ್ ಘಟಕ ಶುರು ಮಾಡಬೇಕು")
    assert got["trade"] == "tailor" and got["area_type"] == "rural" and got["district"] == "Mandya"
    assert got["business_activity"] == "manufacturing" and got["project_cost_inr"] == 800000


def test_provider_falls_back_to_mock_on_error(monkeypatch, personas, schemes):
    class Broken(provider.MockProvider):
        name = "broken"

        def extract_profile(self, text):
            raise TimeoutError("no network")

        def explain(self, *args):
            raise TimeoutError("no network")

    monkeypatch.setattr(provider, "get_provider", lambda: Broken())
    assert provider.extract_profile("tailor in Mandya village")["provider"] == "mock"
    profile, scheme, result = setup("lakshmi", "pmegp", personas, schemes)
    out = provider.explain("why", profile, scheme, result, "en")
    assert out["used_template"] and out["text"] == templates.explain("why", profile, scheme, result, "en")


def test_llm_text_cannot_change_status_or_amount(monkeypatch, personas, schemes):
    class Liar(provider.MockProvider):
        name = "liar"

        def explain(self, kind, profile, scheme, result, lang):
            return "You will get ₹9,99,999. Source: " + scheme["sources"][0]["title"]

    monkeypatch.setattr(provider, "get_provider", lambda: Liar())
    profile, scheme, result = setup("ravi", "pmegp", personas, schemes)
    out = provider.explain("why", profile, scheme, result, "en")
    assert out["used_template"] and "9,99,999" not in out["text"]
    assert result["status"] == "NOT_ELIGIBLE"
