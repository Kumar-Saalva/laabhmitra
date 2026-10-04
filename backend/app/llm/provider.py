"""LLM providers. MockProvider is the default and needs no network or key.

The LLM never decides eligibility or amounts. It only (a) reads a profile out of free text,
(b) rewords engine facts, (c) drafts a cover note. Every answer goes through guard.py,
and any error or timeout falls back to the mock output, so the UI never breaks.
"""
import json
import logging
import os
import re

from app.llm import guard, keywords, prompts, templates

log = logging.getLogger("laabhmitra.llm")
TIMEOUT_SECONDS = 20


class MockProvider:
    """Templates + keyword extractor. Deterministic and offline."""
    name = "mock"

    def extract_profile(self, text: str) -> dict:
        return keywords.extract(text)

    def explain(self, kind: str, profile: dict, scheme: dict, result: dict, lang: str) -> str:
        return templates.explain(kind, profile, scheme, result, lang)

    def draft_pack(self, profile: dict, scheme: dict, result: dict) -> str:
        return templates.draft(profile, scheme, result)

    def project_narrative(self, profile: dict, report: dict) -> dict:
        return templates.project_narrative(profile, report)


class AnthropicProvider(MockProvider):
    """Claude through the Messages API. Key comes from LLM_API_KEY only."""
    name = "anthropic"
    url = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str, model: str | None = None):
        self.api_key = api_key
        self.model = model or os.getenv("LLM_MODEL", "claude-sonnet-5-5")

    def _complete(self, system: str, user: str, max_tokens: int = 700) -> str:
        import httpx
        response = httpx.post(
            self.url, timeout=TIMEOUT_SECONDS,
            headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
            json={"model": self.model, "max_tokens": max_tokens, "system": system,
                  "messages": [{"role": "user", "content": user}]},
        )
        response.raise_for_status()
        return "".join(block.get("text", "") for block in response.json()["content"]).strip()

    def extract_profile(self, text: str) -> dict:
        answer = self._complete(prompts.extract_prompt(), text, max_tokens=500)
        match = re.search(r"\{.*\}", answer, re.S)
        return json.loads(match.group(0)) if match else {}

    def explain(self, kind, profile, scheme, result, lang) -> str:
        facts = templates.build_facts(profile, scheme, result)
        return self._complete(prompts.explain_prompt(kind, facts, lang), "Write the explanation now.")

    def draft_pack(self, profile, scheme, result) -> str:
        facts = templates.draft_facts(profile, scheme, result)
        return self._complete(prompts.draft_prompt(facts), "Write the draft now.", max_tokens=900)


    def project_narrative(self, profile, report) -> dict:
        facts = templates.narrative_facts(profile, report)
        answer = self._complete(prompts.narrative_prompt(facts), "Write the three sections now.", max_tokens=900)
        match = re.search(r"\{.*\}", answer, re.S)
        return json.loads(match.group(0)) if match else {}


def get_provider():
    """Chosen by LLM_PROVIDER (mock | anthropic | gemini | openai | sarvam). Default: mock."""
    choice = os.getenv("LLM_PROVIDER", "mock").lower()
    key = os.getenv("LLM_API_KEY")
    if choice == "anthropic" and key:
        return AnthropicProvider(key)
    if choice != "mock":
        log.warning("LLM_PROVIDER=%s is not available (no key or not implemented); using mock.", choice)
    return MockProvider()


MOCK = MockProvider()


def extract_profile(text: str) -> dict:
    """Free text -> partial profile with allowed keys and valid values only."""
    text = guard.redact_ids(text)          # ID numbers never reach an LLM or the database
    provider = get_provider()
    try:
        raw = provider.extract_profile(text)
    except Exception as error:             # timeout, bad key, bad JSON, no network...
        log.warning("extract_profile failed (%s); using mock.", error)
        provider, raw = MOCK, MOCK.extract_profile(text)
    return {"profile": guard.clean_profile(raw), "provider": provider.name}


def explain(kind: str, profile: dict, scheme: dict, result: dict, lang: str) -> dict:
    """Explanation text for 'why' or 'why_not'. Status and amounts come from `result` only."""
    template_text = templates.explain(kind, profile, scheme, result, lang)
    source = scheme["sources"][0]
    provider, problems, fallback = get_provider(), [], False
    text = template_text
    if provider.name != "mock":
        facts = templates.build_facts(profile, scheme, result)
        try:
            answer = provider.explain(kind, profile, scheme, result, lang)
            text, fallback, problems = guard.guarded(answer, facts, template_text, source["title"])
        except Exception as error:
            log.warning("explain failed (%s); using template.", error)
            fallback, problems = True, [str(error)]
    return {"text": text, "source": source, "provider": provider.name,
            "used_template": fallback or provider.name == "mock", "guard_problems": problems}


def draft_pack(profile: dict, scheme: dict, result: dict) -> dict:
    template_text = templates.draft(profile, scheme, result)
    provider, text, fallback = get_provider(), template_text, False
    if provider.name != "mock":
        facts = templates.draft_facts(profile, scheme, result)
        try:
            answer = provider.draft_pack(profile, scheme, result)
            text, fallback, _ = guard.guarded(answer, facts, template_text)
            if not text.lstrip().upper().startswith("DRAFT"):
                text = "DRAFT: review before use\n\n" + text
        except Exception as error:
            log.warning("draft_pack failed (%s); using template.", error)
            fallback = True
    return {"text": text, "provider": provider.name, "used_template": fallback or provider.name == "mock"}


def draft_project_narrative(profile: dict, report: dict) -> dict:
    """Narrative sections for the project report. Numbers are checked section by section:
    a section with a number that is not in the computed figures is replaced by its template."""
    description = (profile.get("project") or {}).get("business_description")
    if description:                         # ID numbers never reach an LLM or the PDF
        profile = {**profile, "project": {**profile["project"], "business_description": guard.redact_ids(description)}}
    template = templates.project_narrative(profile, report)
    provider, sections, replaced = get_provider(), dict(template), []
    if provider.name != "mock":
        facts = templates.narrative_facts(profile, report)
        try:
            answer = provider.project_narrative(profile, report)
        except Exception as error:
            log.warning("project_narrative failed (%s); using template.", error)
            answer = {}
        for key in templates.NARRATIVE_SECTIONS:
            text = answer.get(key) if isinstance(answer, dict) else None
            sections[key], fallback, _ = guard.guarded(text if isinstance(text, str) else "", facts, template[key])
            if fallback:
                replaced.append(key)
    return {"sections": sections, "titles": templates.NARRATIVE_TITLES, "provider": provider.name,
            "used_template": provider.name == "mock" or bool(replaced), "replaced_sections": replaced}
