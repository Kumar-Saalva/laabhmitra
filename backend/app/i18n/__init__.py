"""Backend text: explanation templates and translated scheme text (en, kn, hi)."""
import json
from functools import lru_cache
from pathlib import Path

LANGS = ("en", "kn", "hi")
LANGUAGE_NAMES = {"en": "English", "kn": "Kannada", "hi": "Hindi"}


@lru_cache
def texts(lang: str) -> dict:
    lang = lang if lang in LANGS else "en"
    with open(Path(__file__).parent / f"{lang}.json", encoding="utf-8") as f:
        return json.load(f)


def criterion_label(lang: str, scheme_id: str, criterion: dict) -> str:
    return texts(lang)["criteria"].get(f"{scheme_id}.{criterion['id']}", criterion["label"])


def fix_label(lang: str, fix: dict) -> str:
    return texts(lang)["fixes"].get(fix["action_id"], fix["label"])


def summary(lang: str, scheme: dict) -> str:
    return texts(lang)["summaries"].get(scheme["id"], scheme.get("summary_plain", ""))


def conflict_message(lang: str, conflict: dict) -> str:
    return texts(lang)["conflicts"].get(conflict["id"], conflict["message"])
