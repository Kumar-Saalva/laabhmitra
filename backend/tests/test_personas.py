"""Acceptance tests: the engine must reproduce data/expected.json exactly."""
import pytest

from app.engine.paths import best_paths
from app.engine.run import evaluate_all
from app.models import Profile

PERSONAS = ["lakshmi", "ravi", "shabana"]
SCHEMES = ["udyam_registration", "udyam_assist", "pmegp", "mudra", "cgtmse", "pm_vishwakarma",
           "pm_svanidhi", "stand_up_india", "zed", "me_card", "ka_udyogini", "first_time_women_scst"]


def run(persona, schemes):
    # Go through the Pydantic model, exactly as the API does.
    return evaluate_all(Profile(**persona).model_dump(), schemes)


@pytest.mark.parametrize("pid", PERSONAS)
@pytest.mark.parametrize("sid", SCHEMES)
def test_scheme_result(pid, sid, personas, schemes, expected):
    got = run(personas[pid], schemes)[sid]
    want = expected[pid]["schemes"][sid]
    assert got["status"] == want["status"]
    assert (got["met"], got["total"], got["unknown"]) == (want["met"], want["total"], want["unknown"])
    assert got["fails"] == want["fails"]
    est = got["estimate"]
    assert (est["grant_min"], est["grant_max"], est["credit"]) == (want["grant_min"], want["grant_max"], want["credit"])


@pytest.mark.parametrize("pid", PERSONAS)
def test_best_paths(pid, personas, schemes, conflicts, expected):
    paths = best_paths(run(personas[pid], schemes), schemes, conflicts)
    got = [{k: p[k] for k in ("schemes", "grant_min", "grant_max")} for p in paths]
    assert got == expected[pid]["best_paths"]


def test_all_twelve_schemes_covered(schemes, expected):
    assert list(schemes) == SCHEMES
    assert all(list(expected[p]["schemes"]) == SCHEMES for p in PERSONAS)
