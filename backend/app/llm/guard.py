"""Guardrails for LLM text. The rule: the LLM may only repeat facts, never add them.

- numbers check: every number in the text must already be in the input facts;
- wording check: no "guaranteed" / "will get";
- explanations must end with the source title.
If any check fails, the caller uses the template text instead.
"""
import json
import re

from app.models import PROFILE_FIELDS, Profile

NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
BANNED = ("guaranteed", "guarantee you", "will get", "will receive")

# Things that look like identity numbers. They are removed before any text reaches an LLM
# or the database: we only ever keep booleans such as pan_available.
PAN_NUMBER = re.compile(r"\b[A-Za-z]{5}\d{4}[A-Za-z]\b")
AADHAAR_NUMBER = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")


def redact_ids(text: str) -> str:
    text = PAN_NUMBER.sub("[PAN removed]", text)
    return AADHAAR_NUMBER.sub("[number removed]", text)


def _canonical(token: str):
    """'2,80,000' -> 280000.0 ; '7.2' -> 7.2 ; '10.' -> 10.0"""
    try:
        return float(token.replace(",", "").rstrip("."))
    except ValueError:
        return None


def numbers_in(text: str) -> set:
    found = {_canonical(m) for m in NUMBER.findall(text)}
    found.discard(None)
    return found


def allowed_numbers(facts) -> set:
    """Numbers in the facts, plus the same amounts written the way people say them:
    800000 may be written as 8 (lakh), 0.35 as 35 (%), 20000000 as 2 (crore)."""
    raw = facts if isinstance(facts, str) else json.dumps(facts, ensure_ascii=False)
    base = numbers_in(raw)
    allowed = set(base)
    for n in base:
        if 0 < n < 1:
            allowed.add(round(n * 100, 4))               # rate -> percent
        if n >= 1000:
            for unit in (1_000, 100_000, 10_000_000):    # thousand, lakh, crore
                allowed.add(round(n / unit, 4))
    return allowed


def unsupported_numbers(text: str, facts) -> list:
    allowed = allowed_numbers(facts)
    return sorted(n for n in numbers_in(text) if round(n, 4) not in allowed)


def check_text(text: str, facts, source_title: str | None = None) -> list:
    """Return a list of problems. An empty list means the text is safe to show."""
    problems = []
    if not text or not text.strip():
        return ["empty"]
    bad = unsupported_numbers(text, facts)
    if bad:
        problems.append(f"numbers not in facts: {bad}")
    lowered = text.lower()
    problems += [f"banned wording: {w}" for w in BANNED if w in lowered]
    if source_title and not text.rstrip().rstrip(".").endswith(source_title.rstrip(".")):
        problems.append("does not end with the source title")
    return problems


def guarded(text: str, facts, template_text: str, source_title: str | None = None) -> tuple:
    """Return (text to show, used_fallback, problems)."""
    problems = check_text(text, facts, source_title)
    if problems:
        return template_text, True, problems
    return text, False, []


def clean_profile(raw) -> dict:
    """Schema validation for extract_profile: keep only allowed keys with valid values.

    Each field is validated on its own, so one bad value never throws away the rest.
    """
    if not isinstance(raw, dict):
        return {}
    clean = {}
    for key in PROFILE_FIELDS:
        if raw.get(key) is None:
            continue
        try:
            value = getattr(Profile(**{key: raw[key]}), key)
        except Exception:
            continue
        if key == "existing_govt_loans":
            value = [loan.model_dump() for loan in value]
            if not value:
                continue
        clean[key] = value
    return clean
