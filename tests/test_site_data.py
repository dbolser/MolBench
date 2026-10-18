"""The leaderboard's data builder (scripts/build_site_data.py) on tiny fixtures."""

import importlib.util
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent


def _load(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sd = _load("build_site_data")
lb = _load("build_leaderboard")


def _t(i, f1, outcome="valid", decision=None, tier=None):
    t = {"id": i, "category": "mvs", "f1": f1, "outcome": outcome}
    if decision:
        t["escalation"] = {"decision": decision, "tier": tier}
    return t


TASKS = [
    _t("a", 1.0, decision="correct", tier="tree"),
    _t("b", 0.5, decision="rendering-equivalent", tier="visual"),
    _t("c", 0.4, decision="vlm:same", tier="vlm"),
    _t("d", 0.6, decision="vlm:different", tier="vlm"),
    _t("e", 0.0, outcome="invalid_json"),
    # Rescued before validation, then rejected by Mol*: stays 0.
    _t("f", 0.0, outcome="invalid_mvs", decision="rendering-equivalent", tier="visual"),
]


def test_validated_f1_rescues_only_valid_scenes():
    assert [sd.validated_f1(t) for t in TASKS] == [1.0, 1.0, 1.0, 0.6, 0.0, 0.0]


def test_escalation_summary():
    s = sd.escalation_summary(TASKS)
    assert (s["perfect"], s["escalated"], s["failed"]) == (1, 3, 2)
    assert (s["rescued_visual"], s["rescued_vlm"], s["confirmed_different"]) == (1, 1, 1)
    assert s["tree_f1"] == round(2.5 / 6, 3)
    assert s["validated_f1"] == round(3.6 / 6, 3)


def test_paired_delta_separates_validity_from_quality():
    spec = [_t("a", 0.8), _t("b", 0.0, "invalid_json"), _t("c", 0.6)]
    grd = [_t("a", 0.9), _t("b", 0.7), _t("c", 0.0, "invalid_json")]
    d = sd.paired_delta(spec, grd)
    assert d["n_both_valid"] == 1 and d["delta_both_valid"] == 0.1
    assert d["delta"] == round((1.6 - 1.4) / 3, 4)
    assert sd.paired_delta(spec, grd, {"b"})["n"] == 1


def test_mol_star_issues_group_by_message():
    lines = ['Invalid parameters for node of kind "download":', '  Missing required parameter "url".',
             'Node of kind "focus" cannot appear as a child of "structure". Allowed parents '
             'for "focus" are: "root", "component"']
    issues = sd.split_issues(lines)
    assert len(issues) == 2 and issues[0][1] == 'Missing required parameter "url".'
    assert sd.normalise_issue(issues[0]) == \
        'Invalid parameters for node of kind "…": Missing required parameter "…".'
    assert sd.normalise_issue(issues[1]) == \
        'Node of kind "…" cannot appear as a child of "…". Allowed parents: …'


def test_json_error_positions_dropped():
    assert sd.normalise_json_error(
        "JSON parse error: Expecting ',' delimiter: line 1 column 461 (char 460)") == \
        "JSON parse error: Expecting ',' delimiter"


def test_gallery_pick_is_deterministic_and_distinct():
    rows = [{"id": i, "model": m, "mvs_score": f, "decision": d}
            for i, m, f, d in [("x", "m1", 0.5, "rendering-equivalent"),
                               ("x", "m2", 0.4, "vlm:same"),
                               ("y", "m1", 0.3, "vlm:same"),
                               ("z", "m1", 0.9, "vlm:different"),
                               ("w", "m2", 0.7, "vlm:different")]]
    picks = sd.pick_gallery(rows, per_class=1)
    assert [(r["id"], r["decision"]) for r in picks] == [
        ("x", "rendering-equivalent"), ("y", "vlm:same"), ("z", "vlm:different")]


def test_merge_keeps_old_api_track():
    new = {"spec": "openrouter:x", "by_category": {"mvs": {"mean_f1": 0.5}},
           "tasks": [_t("a", 0.5)], "valid_scene": 1.0, "outcomes": {"valid": 1}}
    old = {"spec": "x", "sec_per_call": 2.0,
           "by_category": {"mvs": {"mean_f1": 0.9}, "api_calling": {"mean_f1": 0.7}},
           "tasks": [_t("old", 0.9), {"id": "api", "category": "api_calling", "f1": 0.7}]}
    m = sd.merge_model(new, old)
    assert m["by_category"] == {"mvs": {"mean_f1": 0.5}, "api_calling": {"mean_f1": 0.7}}
    assert [t["id"] for t in m["tasks"]] == ["a", "api"]
    assert m["spec"] == "openrouter:x" and m["sec_per_call"] == 2.0
    gone = sd.merge_model(None, old)  # model not re-run: API only, no MVS
    assert "mvs" not in gone["by_category"] and not lb.has_mvs(gone)


def test_rank_puts_unrun_models_last():
    models = {"a": {"mean_f1": 0.9, "by_category": {"api_calling": {"mean_f1": 0.9}}},
              "b": {"mean_f1": 0.1, "by_category": {"mvs": {"mean_f1": 0.0}}},
              "c": {"mean_f1": 0.5, "by_category": {"mvs": {"mean_f1": 0.4}}}}
    assert [n for n, _ in lb.rank_models(models)] == ["c", "b", "a"]
