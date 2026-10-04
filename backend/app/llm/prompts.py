"""Prompts for the real LLM provider (spec 2.5). The LLM only ever sees structured facts."""
import json

from app.i18n import LANGUAGE_NAMES
from app.models import PROFILE_FIELDS, VISHWAKARMA_TRADES

EXPLAIN_ELIGIBILITY = """You explain government scheme eligibility to a small business owner in {language}.
Use ONLY the facts in the JSON below. Do not add schemes, amounts, dates or conditions.
Say "may be eligible", never "will get". Keep sentences short (max 15 words).
Mention each criterion result once. End with: "Source: {source_title}".
If a criterion is UNKNOWN, say what information is missing.
FACTS: {scheme_json} RESULTS: {criteria_results} PROFILE: {relevant_profile_fields}"""

EXPLAIN_WHY_NOT = """You explain to a small business owner in {language} why a government scheme does not fit yet.
Use ONLY the facts in the JSON below. Do not add schemes, amounts, dates or conditions.
Give one short reason for each FALSE or UNKNOWN criterion. If a criterion has a fix, say the fix.
Never say "guaranteed" or "will get". Keep sentences short (max 15 words).
End with: "Source: {source_title}".
FACTS: {scheme_json} RESULTS: {criteria_results} PROFILE: {relevant_profile_fields}"""

DRAFT_PACK = """Write a one-page cover note in English for an application under the scheme below.
Start with the line "DRAFT: review before use".
Use ONLY the facts in the JSON. Do not invent names, numbers, dates or addresses.
Where a fact is missing write the placeholder [fill in].
Never say "guaranteed". Do not mention any Aadhaar, PAN or bank account number.
SCHEME: {scheme_json} PROFILE: {profile_json} DOCUMENTS: {documents}"""

EXTRACT_PROFILE = """Extract a small business profile from the merchant's message (English, Kannada or Hindi).
Return ONLY a JSON object. Use only these keys: {fields}.
Allowed values:
- area_type: urban | rural
- business_activity: manufacturing | service | trading | street_vending
- trade: {trades} | none
- ownership_type: proprietorship | partnership | llp | shg | company | other_noncorporate
- owner_gender: female | male | transgender | prefer_not
- social_category: general | sc | st | obc | minority | prefer_not
- state: two-letter state code such as KA
- money fields end in _inr and are whole rupees (8 lakh = 800000)
- all other fields are true/false or whole numbers
Leave out anything the merchant did not say. Never guess. Never output ID numbers."""


PROJECT_NARRATIVE = """Write three short sections for a bank project report, in plain English.
Return ONLY a JSON object with the keys "about", "market" and "viability" (3 to 5 sentences each):
about = About the business; market = Market and customers; viability = Why it is viable.
Use ONLY the business description and the computed figures below. Do not invent numbers, names,
customers or dates: every number you write must appear in the figures. Where a fact is missing
write [fill in]. All profits are before tax. Never say "guaranteed".
DESCRIPTION: {description} BUSINESS: {business} FIGURES: {figures}"""


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def explain_prompt(kind: str, facts: dict, lang: str) -> str:
    template = EXPLAIN_ELIGIBILITY if kind == "why" else EXPLAIN_WHY_NOT
    return template.format(
        language=LANGUAGE_NAMES.get(lang, "English"),
        source_title=facts["source_title"],
        scheme_json=_json(facts["scheme"]),
        criteria_results=_json({"results": facts["results"], "estimate": facts["estimate"]}),
        relevant_profile_fields=_json(facts["profile"]),
    )


def draft_prompt(facts: dict) -> str:
    return DRAFT_PACK.format(scheme_json=_json(facts["scheme"]), profile_json=_json(facts["profile"]),
                             documents=_json(facts["documents"]))


def extract_prompt() -> str:
    return EXTRACT_PROFILE.format(fields=", ".join(PROFILE_FIELDS), trades=" | ".join(VISHWAKARMA_TRADES))


def narrative_prompt(facts: dict) -> str:
    return PROJECT_NARRATIVE.format(description=_json(facts["business_description"]),
                                    business=_json(facts["business"]), figures=_json(facts["figures"]))
