"""Path planner, fix plan and watch diff."""
from app.engine import watch
from app.engine.fixes import fix_plan
from app.engine.paths import best_paths, forbidden_pairs
from app.engine.run import evaluate_all, opportunity_map
from app.models import Profile


def run(persona, schemes, **changes):
    return evaluate_all(Profile(**{**persona, **changes}).model_dump(), schemes)


def test_forbidden_pairs(conflicts):
    pairs = forbidden_pairs(conflicts)
    assert ("pm_vishwakarma", "pmegp") in pairs and ("mudra", "pm_vishwakarma") in pairs
    assert ("ka_udyogini", "pmegp") in pairs
    assert ("mudra", "pmegp") not in pairs       # anchor_excludes: only anchor vs others


def test_lakshmi_two_best_paths(personas, schemes, conflicts):
    paths = best_paths(run(personas["lakshmi"], schemes), schemes, conflicts)
    assert [p["schemes"] for p in paths] == [["pmegp"], ["pm_vishwakarma", "ka_udyogini"]]
    assert (paths[0]["grant_min"], paths[0]["grant_max"]) == (280000, 280000)
    assert (paths[1]["grant_min"], paths[1]["grant_max"]) == (105000, 165000)
    assert len(paths[0]["conflicts"]) == 2      # the messages that separate A from B


def test_ravi_has_no_grant_path_but_three_credit_options(personas, schemes, conflicts):
    evals = run(personas["ravi"], schemes)
    omap = opportunity_map(evals, schemes, conflicts)
    assert omap["best_paths"] == [] and omap["buckets"]["grants"] == []
    assert omap["headline"]["grant_max"] == 0
    credit = {c["scheme_id"]: c for c in omap["buckets"]["credit"]}
    assert set(credit) == {"mudra", "cgtmse", "me_card"}
    assert credit["mudra"]["tier_name"] == "Kishore" and credit["me_card"]["scheme_status"] == "verify"


def test_grants_and_credit_never_added(personas, schemes, conflicts):
    omap = opportunity_map(run(personas["lakshmi"], schemes), schemes, conflicts)
    assert omap["headline"]["grant_max"] == 280000          # best path only, no credit mixed in
    assert all("credit" not in g for g in omap["buckets"]["grants"])
    # Not-eligible schemes never reach the buckets, even though estimators return numbers for them.
    assert "pm_svanidhi" not in {c["scheme_id"] for c in omap["buckets"]["credit"]}


def test_lakshmi_fix_plan(personas, schemes):
    plan = fix_plan(run(personas["lakshmi"], schemes), schemes)
    assert len(plan) == 1
    assert plan[0]["action_id"] == "register_udyam"
    assert plan[0]["unlocks"] == ["cgtmse", "zed", "me_card"]
    assert plan[0]["credit_unlocked_max"] == 720000 and plan[0]["grant_unlocked"] == 0


def test_shabana_fix_plan(personas, schemes):
    plan = {s["action_id"]: s["unlocks"] for s in fix_plan(run(personas["shabana"], schemes), schemes)}
    assert plan == {"register_udyam": ["cgtmse", "me_card"], "get_pan": ["udyam_registration"]}


def test_watch_diff_after_udyam_registration(personas, schemes):
    before = watch.snapshot(run(personas["lakshmi"], schemes), schemes)
    after = watch.snapshot(run(personas["lakshmi"], schemes, udyam_registered=True), schemes)
    notes = watch.diff(before, after)
    assert {(n["scheme_id"], n["kind"], n["new"]) for n in notes} == {
        ("cgtmse", "improved", "ELIGIBLE"), ("zed", "improved", "ELIGIBLE"), ("me_card", "improved", "ELIGIBLE")}
    assert watch.diff(after, after) == []


def test_watch_other_triggers():
    old = {"a": {"status": "WATCHLIST", "scheme_status": "announced"},
           "b": {"status": "ELIGIBLE", "scheme_status": "active"},
           "c": {"status": "ELIGIBLE", "scheme_status": "active"}}
    new = {"a": {"status": "LIKELY", "scheme_status": "active"},
           "b": {"status": "ELIGIBLE", "scheme_status": "verify"},
           "c": {"status": "NOT_ELIGIBLE", "scheme_status": "active"}}
    assert [(n["scheme_id"], n["kind"]) for n in watch.diff(old, new)] == [("a", "now_active"), ("b", "verify_badge")]
