"""Loads the seed data from /data. This is the only source of scheme facts at runtime:
the app never calls or scrapes a government portal."""
import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _load(name: str):
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


@lru_cache
def seed() -> dict:
    return _load("schemes.seed.json")


@lru_cache
def schemes() -> dict:
    """{scheme_id: scheme dict}, in seed order."""
    return {s["id"]: s for s in seed()["schemes"]}


def conflicts() -> list:
    return seed()["conflicts"]


@lru_cache
def personas() -> dict:
    return _load("personas.json")
