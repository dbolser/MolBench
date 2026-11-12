"""A4 agreement maths (scripts/agreement.py, scripts/export_ratings.py) on hand-checkable cases."""

import collections
import importlib.util
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent


def _load(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ag = _load("agreement")
ex = _load("export_ratings")

C = collections.Counter
S, D = "same", "different"


def analyse(key, ratings, **kw):
    return ag.analyse(key, ratings, **{"reps": 50, **kw})


# --------------------------------------------------------------------------- #
# The statistics
# --------------------------------------------------------------------------- #
def test_fleiss_perfect_and_chance():
    assert ag.fleiss_kappa([C(same=2), C(different=2)]) == 1.0
    # Every item split 1-1: observed agreement 0, chance 0.5 -> kappa -1.
    assert ag.fleiss_kappa([C(same=1, different=1)] * 4) == -1.0
    assert ag.fleiss_kappa([C(same=1)]) is None  # single ratings don't count


def test_cohen():
    assert ag.cohen_kappa([(S, S), (D, D)]) == 1.0
    # p_o = 3/4; p_e = 0.5 * 0.25 + 0.5 * 0.75 = 0.5 -> (0.75 - 0.5) / 0.5
    assert abs(ag.cohen_kappa([(S, S), (S, D), (D, D), (D, D)]) - 0.5) < 1e-9
    assert ag.cohen_kappa([]) is None


def test_krippendorff_alpha():
    assert ag.krippendorff_alpha([C(same=2), C(different=2)]) == 1.0
    # Krippendorff's own 2-observer binary example: 10 units, 4 mismatched pairs,
    # values 0 x 10 and 1 x 10 -> alpha = 1 - 19 * 4 / (10 * 10 * 2) ... = 0.095
    units = [C(same=2)] * 3 + [C(different=2)] * 3 + [C(same=1, different=1)] * 4
    # n = 20, n_same = n_diff = 10; D_o = 8 / 20; D_e = 2 * 10 * 10 / (20 * 19)
    assert abs(ag.krippendorff_alpha(units) - (1 - (8 / 20) / (200 / 380))) < 1e-9
    assert ag.krippendorff_alpha([C(same=1)]) is None
    assert ag.krippendorff_alpha([C(same=2), C(same=3)]) is None  # one label only: undefined
    # Three raters on one item, two on another.
    assert ag.krippendorff_alpha([C(same=3), C(different=2)]) == 1.0


def test_pairwise_agreement():
    assert ag.pairwise_agreement([C(same=2), C(same=1, different=1)]) == 0.5
    assert abs(ag.pairwise_agreement([C(same=2, different=1)]) - 1 / 3) < 1e-9


def test_judge_measures_on_a_hand_table():
    # human same/judge same 4, human same/judge different 1, human different/judge same 2, both different 13
    recs = [(S, S, 1)] * 4 + [(S, D, 1)] + [(D, S, 1)] * 2 + [(D, D, 1)] * 13
    m = ag.judge_measures(recs)
    assert m["agreement"] == 17 / 20
    assert m["sensitivity"] == 4 / 5 and m["specificity"] == 13 / 15
    assert m["balanced_accuracy"] == (4 / 5 + 13 / 15) / 2
    assert m["rescue_precision"] == 4 / 6 and m["npv"] == 13 / 14
    p_e = 0.25 * 0.30 + 0.75 * 0.70
    assert abs(m["cohen_kappa"] - (0.85 - p_e) / (1 - p_e)) < 1e-9
    pi = (0.25 + 0.30) / 2
    assert abs(m["gwet_ac1"] - (0.85 - 2 * pi * (1 - pi)) / (1 - 2 * pi * (1 - pi))) < 1e-9


def test_ac1_stays_high_where_kappa_collapses():
    # 18 of 20 agree, but almost everything is "different": kappa's chance term eats the agreement.
    m = ag.judge_measures([(D, D, 1)] * 18 + [(S, D, 1), (D, S, 1)])
    assert m["agreement"] == 0.9 and m["cohen_kappa"] < 0 and m["gwet_ac1"] > 0.85


def test_weights_change_the_table():
    recs = [(S, S, 1), (D, D, 1)]
    assert ag.judge_measures(recs)["agreement"] == 1.0
    assert ag.judge_measures([(S, S, 1), (S, D, 3)])["agreement"] == 0.25
    assert ag.judge_measures([]) == dict.fromkeys(ag.MEASURES)


def test_bootstrap_resamples_whole_tasks():
    # Two tasks that each agree perfectly within themselves: every replicate is 0 or 1 or a mix
    clusters = {"t1": [(S, S, 1.0)] * 5, "t2": [(S, D, 1.0)] * 5}
    b = ag.bootstrap(clusters, ag.judge_measures, reps=200, seed=1)["agreement"]
    assert b["est"] == 0.5 and b["lo"] == 0.0 and b["hi"] == 1.0
    one = ag.bootstrap({"t1": [(S, S, 1.0)] * 5}, ag.judge_measures, reps=50, seed=1)
    assert one["agreement"] == {"est": 1.0, "lo": 1.0, "hi": 1.0, "se": 0.0}
    assert one["specificity"]["est"] is None and one["specificity"]["lo"] is None
    assert ag.bootstrap({}, ag.judge_measures, reps=50, seed=1)["agreement"]["est"] is None


def test_bootstrap_is_reproducible():
    clusters = {f"t{i}": [(S, S if i % 3 else D, 1.0), (D, D, 1.0)] for i in range(12)}
    a = ag.bootstrap(clusters, ag.judge_measures, reps=100, seed=7)
    assert a == ag.bootstrap(clusters, ag.judge_measures, reps=100, seed=7)
    assert a["cohen_kappa"]["lo"] <= a["cohen_kappa"]["est"] <= a["cohen_kappa"]["hi"]


def test_item_weights_scale_to_the_run():
    rated = {"a": {"task": "t1", "vlm_label": S}, "b": {"task": "t1", "vlm_label": D},
             "c": {"task": "t2", "vlm_label": D}}
    # t1 has 2 same and 4 different in the run, t2 has 3 different; t3 (5 different) was never rated.
    pop = {"cells": [["t1", S, 2], ["t1", D, 4], ["t2", D, 3], ["t3", D, 5]]}
    w = ag.item_weights(rated, pop)
    assert w["a"] == 2.0
    # Cell weights 4 and 3, scaled so "different" adds up to all 12 different pairs of the run.
    assert abs(w["b"] - 4 * 12 / 7) < 1e-9 and abs(w["c"] - 3 * 12 / 7) < 1e-9
    assert ag.item_weights(rated, None) is None


# --------------------------------------------------------------------------- #
# The whole analysis
# --------------------------------------------------------------------------- #
def _r(tok, item, label, **extra):
    return {"evaluator_token": tok, "item": item, "label": label, **extra}


KEY = {"set": "t", "items": {
    "v1": {"kind": "vlm", "vlm_label": S, "task": "t1", "model": "x/m1", "tier": "easy"},
    "v2": {"kind": "vlm", "vlm_label": S, "task": "t2", "model": "x/m2", "tier": "easy"},
    "v3": {"kind": "vlm", "vlm_label": D, "task": "t3", "model": "x/m1", "tier": "hard"},
    "cs": {"kind": "control-same", "expected": S, "task": "t4", "model": "x/m3", "tier": "easy"},
    "cd": {"kind": "control-different", "expected": D, "task": "t5", "tier": "easy"},
}}
CHECKS_OK = (("cs", S), ("cd", D))


def test_raters_who_fail_checks_are_left_out_of_the_passed_group_only():
    good = [_r("good-aaaa", i, lab) for i, lab in (("v1", S), ("v2", D), ("v3", D), *CHECKS_OK)]
    good2 = [_r("good-bbbb", i, lab) for i, lab in (("v1", S), ("v2", D), ("v3", "unsure"), *CHECKS_OK)]
    lazy = [_r("lazy-cccc", i, S) for i in KEY["items"]]  # fails the different-check
    out = analyse(KEY, good + good2 + lazy)
    checks = out["raters"]["lazy-ccc"]["checks"]
    assert (checks["control-same"]["accuracy"], checks["control-different"]["accuracy"]) == (1.0, 0.0)
    assert not out["raters"]["lazy-ccc"]["passed_checks"]
    passed = out["cohorts"]["passed_checks"]
    assert passed["raters"] == ["good-aaa", "good-bbb"]
    assert passed["pairs_by_n_raters"] == {1: 1, 2: 2}  # v3 has one labelled vote; "unsure" carries none
    assert passed["cant_tell"] == 1
    assert passed["human_vs_human"]["fleiss_kappa"]["est"] == 1.0
    assert passed["human_vs_human"]["krippendorff_alpha"]["est"] == 1.0
    # Judge said same on v1 (both humans agree) and v2 (both disagree); v3 one vote agrees.
    assert passed["unweighted"]["per_rating"]["rescue_precision"]["est"] == 0.5
    assert passed["unweighted"]["per_rating"]["agreement"]["est"] == 3 / 5
    assert passed["unweighted"]["per_pair"]["rescue_precision"]["est"] == 0.5
    assert passed["unweighted"]["pairs"] == 3
    # Everyone: the lazy rater's three "same" answers are in.
    assert out["cohorts"]["all"]["unweighted"]["ratings"] == 8
    assert out["cohorts"]["all"]["raters"] == ["good-aaa", "good-bbb", "lazy-ccc"]


def test_split_pairs_still_count_against_the_judge_per_rating_but_have_no_majority():
    a = [_r("a-aaaaaaa", i, lab) for i, lab in (("v1", S), *CHECKS_OK)]
    b = [_r("b-bbbbbbb", i, lab) for i, lab in (("v1", D), *CHECKS_OK)]
    out = analyse(KEY, a + b)["cohorts"]["all"]
    assert out["unweighted"]["ratings"] == 2
    assert out["unweighted"]["per_rating"]["rescue_precision"]["est"] == 0.5
    assert out["pairs_tied"] == 1 and out["unweighted"]["pairs"] == 0
    assert out["unweighted"]["per_pair"]["rescue_precision"]["est"] is None
    assert out["human_vs_human"]["pairs"] == 1 and out["human_vs_human"]["pairs_split"] == 1
    assert out["human_vs_human"]["agreement"]["est"] == 0.0


def test_raters_without_enough_checks_do_not_pass():
    unsure = [_r("u-uuuuuuu", "cs", "unsure"), _r("u-uuuuuuu", "cd", "unsure"), _r("u-uuuuuuu", "v1", S)]
    out = analyse(KEY, unsure)
    assert out["cohorts"]["passed_checks"]["raters"] == []
    assert out["cohorts"]["passed_checks"]["unweighted"]["ratings"] == 0
    assert out["raters"]["u-uuuuuu"]["checks"]["control-same"] == {
        "n": 1, "right": 0, "unsure": 1, "wrong": 0, "accuracy": 0.0}


def test_checks_of_only_one_kind_are_not_enough():
    key = {"set": "t", "items": {**KEY["items"], "cs2": {"kind": "control-same", "expected": S, "task": "t6"}}}
    always_same = [_r("s-sssssss", i, S) for i in ("cs", "cs2", "v1")]
    out = analyse(key, always_same)
    assert not out["raters"]["s-ssssss"]["passed_checks"]
    assert out["raters"]["s-ssssss"]["checks"]["control-different"]["accuracy"] is None


def test_duplicate_ratings_are_rejected():
    with pytest.raises(ValueError):
        analyse(KEY, [_r("a-aaaaaaa", "v1", S), _r("a-aaaaaaa", "v1", D)])


def test_flags_must_be_booleans():
    # A CSV export turns false into the string "false", which is truthy.
    with pytest.raises(ValueError):
        analyse(KEY, [_r("a-aaaaaaa", "v1", S, ref_wrong="false")])


def test_each_kind_of_check_must_pass_on_its_own():
    same = {f"cs{i}": {"kind": "control-same", "expected": S, "task": f"s{i}"} for i in range(5)}
    key = {"set": "t", "items": {**KEY["items"], **same}}
    always_same = [_r("s-sssssss", i, S) for i in [*same, "cd", "v1"]]  # 5/6 overall
    assert not analyse(key, always_same)["raters"]["s-ssssss"]["passed_checks"]


def test_cant_tell_on_a_check_counts_as_a_miss():
    key = {"set": "t", "items": {**KEY["items"], "cs2": {"kind": "control-same", "expected": S, "task": "t6"},
                                 "cd2": {"kind": "control-different", "expected": D, "task": "t7"}}}
    dodger = [_r("d-ddddddd", "cs", S), _r("d-ddddddd", "cd", D),
              _r("d-ddddddd", "cs2", "unsure"), _r("d-ddddddd", "cd2", "unsure"), _r("d-ddddddd", "v1", S)]
    r = analyse(key, dodger)["raters"]["d-dddddd"]
    assert [r["checks"][k]["accuracy"] for k in ag.CHECKS] == [0.5, 0.5]
    assert [r["checks"][k]["wrong"] for k in ag.CHECKS] == [0, 0]
    assert not r["passed_checks"]


EXPORT = {"set": "t", "exported_at": "2026-01-01T00:00:00+00:00",
          "raters": {"R1": {"role": "author"}, "R2": {"role": "rater"}, "R3": {"role": "test"}},
          "rows": []}


def _x(rater, item, label, **extra):
    return {"rater": rater, "item": item, "label": label, **extra}


def test_test_tokens_and_removed_items_are_dropped_and_counted():
    rows = [_x("R1", "v1", S), _x("R1", "gone", S), _x("R2", "v1", S), _x("R2", "cs", S), _x("R2", "cd", D),
            _x("R3", "v1", D), _x("R3", "v2", D)]
    out = analyse(KEY, {**EXPORT, "rows": rows})
    assert out["ratings"] == {"exported": 7, "from_test_tokens": 2, "on_items_not_in_set": {"R1": 1}, "analysed": 4}
    assert set(out["raters"]) == {"R1", "R2"}
    assert out["cohorts"]["all"]["unweighted"]["ratings"] == 2  # the test token's "different" is not in


def test_results_come_with_and_without_the_author():
    rows = [_x("R1", "v1", S), _x("R1", "v2", S), _x("R1", "v3", D),
            _x("R2", "v1", D), _x("R2", "v3", D), _x("R2", "cs", S), _x("R2", "cd", D)]
    c = analyse(KEY, {**EXPORT, "rows": rows})["cohorts"]
    assert c["all"]["raters"] == ["R1", "R2"] and c["no_author"]["raters"] == ["R2"]
    assert c["passed_checks"]["raters"] == ["R2"]  # the author saw no checks
    assert c["all"]["unweighted"]["per_rating"]["agreement"]["est"] == 4 / 5
    assert c["no_author"]["unweighted"]["per_rating"]["agreement"]["est"] == 1 / 2
    assert c["all"]["by_rater"]["R1"]["agreement"]["est"] == 1.0
    assert c["all"]["by_rater"]["R1"]["judge_same_ratings"] == 2


def test_breakdowns_by_tier_and_model():
    rows = [_x("R2", "v1", S), _x("R2", "v2", D), _x("R2", "v3", D)]
    c = analyse(KEY, {**EXPORT, "rows": rows})["cohorts"]["all"]
    assert set(c["by_tier"]) == {"easy", "hard"}
    assert c["by_tier"]["easy"]["ratings"] == 2 and c["by_tier"]["easy"]["agreement"]["est"] == 0.5
    assert c["by_tier"]["hard"]["agreement"]["est"] == 1.0
    assert c["by_model"]["m1"]["pairs"] == 2 and c["by_model"]["m2"]["judge_same_ratings"] == 1


def test_weighted_results_stand_for_the_run():
    # The judge's "same" calls are over-sampled: 2 of 2 in the set, but 2 of 12 in the run.
    pop = {"frame": "test", "cells": [["t1", S, 1], ["t2", S, 1], ["t3", D, 10]]}
    rows = [_x("R2", "v1", S), _x("R2", "v2", D), _x("R2", "v3", D)]
    out = analyse(KEY, {**EXPORT, "rows": rows}, population=pop)
    c = out["cohorts"]["all"]
    assert out["population"] == {"frame": "test", "same": 2, "different": 10, "tasks": 3}
    assert c["unweighted"]["per_rating"]["agreement"]["est"] == 2 / 3
    assert c["weighted"]["per_rating"]["agreement"]["est"] == 11 / 12
    assert c["weighted"]["per_pair"]["specificity"]["est"] == 10 / 11
    assert c["weighted"]["per_pair"]["rescue_precision"]["est"] == 0.5  # within one label, weights cancel
    assert analyse(KEY, {**EXPORT, "rows": rows})["cohorts"]["all"]["weighted"] is None


def test_weighted_pair_counts_once_however_many_raters():
    pop = {"cells": [["t1", S, 1], ["t3", D, 1]]}
    rows = [_x("R1", "v1", S), _x("R2", "v1", D), _x("R2", "v3", D)]
    c = analyse(KEY, {**EXPORT, "rows": rows}, population=pop)["cohorts"]["all"]
    assert c["unweighted"]["per_rating"]["agreement"]["est"] == 2 / 3   # three ratings
    assert c["weighted"]["per_rating"]["agreement"]["est"] == 0.75      # two pairs, v1 half right


def test_flags_point_at_references_to_fix():
    rs = [_r("a-aaaaaaa", "cs", S), _r("a-aaaaaaa", "cd", D),
          _r("a-aaaaaaa", "v1", D, ref_wrong=True, model_better=True, note="  ref lacks\nthe ligand "),
          _r("a-aaaaaaa", "v2", S, ref_wrong=False, model_better=False),
          _r("z-zzzzzzz", "v2", S, model_better=True)]
    f = analyse(KEY, rs)["flags"]
    assert f["ref_wrong_ratings"] == 1 and f["model_better_ratings"] == 2
    assert f["model_better_by_answer"] == {"human different / judge same": 1, "human same / judge same": 1}
    assert f["tasks"]["t1"]["ref_wrong"] == ["a-aaaaaa"]
    assert f["tasks"]["t1"]["model_better"] == {"m1": ["a-aaaaaa"]}
    assert f["tasks"]["t1"]["notes"] == [{"rater": "a-aaaaaa", "answer": D, "kind": "vlm", "model": "m1",
                                          "note": "ref lacks the ligand"}]
    assert f["tasks"]["t2"]["model_better"] == {"m2": ["z-zzzzzz"]}
    assert "t3" not in f["tasks"]


def test_a_rater_flags_a_reference_once_however_many_models_they_see():
    key = {"set": "t", "items": {**KEY["items"], "v2": {**KEY["items"]["v2"], "task": "t1"}}}
    rs = [_r("a-aaaaaaa", "v1", D, ref_wrong=True), _r("a-aaaaaaa", "v2", D, ref_wrong=True)]
    assert analyse(key, rs)["flags"]["tasks"]["t1"]["ref_wrong"] == ["a-aaaaaa"]


def test_markdown_has_no_item_ids_and_names_every_group():
    rows = [_x("R1", "v1", S), _x("R2", "v1", D), _x("R2", "v3", D), _x("R2", "cs", S), _x("R2", "cd", D)]
    out = analyse(KEY, {**EXPORT, "rows": rows}, population={"cells": [["t1", S, 1], ["t3", D, 4]]})
    md = ag.markdown(out)
    for word in ("all raters", "without the author", "passed-checks only", "Krippendorff", "Gwet", "weighted"):
        assert word in md
    import json
    dumped = json.dumps(out)
    assert not any(f'"{i}"' in dumped for i in KEY["items"])  # the key's item ids never leave


def test_tiers_fall_back_to_the_task_files():
    # Without a `tier` in the key, the tier is the regime of the task's source.
    import json
    task = next(t for t in (json.loads(p.read_text()) for p in sorted((REPO / "tasks").rglob("*.json")))
                if t.get("source"))
    tiers = ag.task_tiers({"a": {"kind": "vlm", "task": task["id"]}, "b": {"kind": "vlm", "task": "x", "tier": "T"}})
    assert tiers["x"] == "T"
    assert tiers[task["id"]] == _load("build_leaderboard")._regime_of(task["source"])


# --------------------------------------------------------------------------- #
# The export
# --------------------------------------------------------------------------- #
def _row(tok, name, item, label="same"):
    return {"evaluator_token": tok, "name": name, "item": item, "label": label, "ref_wrong": False,
            "model_better": False, "note": None, "ms": 5000, "client": "c", "created_at": "2026-01-01"}


def test_export_pseudonyms_are_stable_and_carry_no_names():
    rows = [_row("tok-b", "Bea", "i1"), _row("tok-a", "Al", "i1"), _row("tok-b", "Bea", "i2")]
    out, names = ex.pseudonymise(rows, {}, author={"Al"})
    assert [r["rater"] for r in out] == ["R1", "R2", "R1"]  # numbered by first rating
    assert names["R2"] == {"token": "tok-a", "name": "Al", "role": "author"}
    assert all("evaluator_token" not in r and "name" not in r for r in out)
    # Next export: a new rater rates first, yet the old pseudonyms and roles hold.
    later = [_row("tok-c", "Cy", "i1"), *rows]
    out2, names2 = ex.pseudonymise(later, names, test={"Cy"})
    assert [r["rater"] for r in out2] == ["R3", "R1", "R2", "R1"]
    assert names2["R2"]["role"] == "author" and names2["R3"]["role"] == "test"


def test_export_only_ever_sends_one_select(monkeypatch):
    sent = {}

    class Reply:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b"[]"

    def fake_urlopen(req, timeout):
        sent["url"], sent["body"], sent["auth"] = req.full_url, req.data, req.get_header("Authorization")
        return Reply()

    monkeypatch.setenv("SUPABASE_ACCESS_TOKEN", "not-a-real-token")
    monkeypatch.setattr(ex.urllib.request, "urlopen", fake_urlopen)
    assert ex.fetch("a4-v1") == []
    import json
    query = json.loads(sent["body"])["query"].strip().lower()
    assert query.startswith("select") and ";" not in query
    assert not any(w in query.split() for w in ("insert", "update", "delete", "drop", "alter", "truncate"))
    assert sent["auth"] == "Bearer not-a-real-token" and sent["url"].endswith("/database/query")
    with pytest.raises(ValueError):
        ex.fetch("a4-v1'; drop table ratings; --")
