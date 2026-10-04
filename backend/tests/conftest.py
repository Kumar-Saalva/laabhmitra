import json
import os

import pytest

os.environ["LLM_PROVIDER"] = "mock"
os.environ["LAABHMITRA_DB"] = ":memory:"

from app import data  # noqa: E402


@pytest.fixture(scope="session")
def schemes():
    return data.schemes()


@pytest.fixture(scope="session")
def conflicts():
    return data.conflicts()


@pytest.fixture(scope="session")
def personas():
    return data.personas()


@pytest.fixture(scope="session")
def expected():
    with open(data.DATA_DIR / "expected.json", encoding="utf-8") as f:
        return json.load(f)
