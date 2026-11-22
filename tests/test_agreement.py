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


def test_unknown_labels_are_rejected():
    with pytest.raises(ValueError, match="label must be"):
        analyse(KEY, [_r("a-aaaaaaa", "v1", "Same")])
    with pytest.raises(ValueError, match="label must be"):
        analyse(KEY, [_r("a-aaaaaaa", "v1", None)])


def test_tables_survive_a_group_with_no_raters_when_weighted():
    # Nobody passes the checks (none answered), so that group is empty; with a
    # population the weighted block must still exist for the tables.
    pop = {"cells": [["t1", S, 3], ["t3", D, 5]]}
    res = analyse(KEY, [_r("a-aaaaaaa", "v1", S), _r("a-aaaaaaa", "v3", D)], population=pop)
    assert res["cohorts"]["passed_checks"]["weighted"]["ratings"] == 0
    assert res["cohorts"]["all"]["weighted"]["table"]["human same / judge same"] == 3
    assert "weighted" in ag.markdown(res)


def test_a_zero_width_interval_is_not_printed_as_certainty():
    assert ag._ci({"est": 1.0, "lo": 1.0, "hi": 1.0}) == "1.00 (no interval)"
    assert ag._ci({"est": 0.5, "lo": 0.25, "hi": 0.75}) == "0.50 (0.25 to 0.75)"


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
    # Without a `tier` in the key, the tier is the one the task file states (the corpus
    # no longer holds an old-format task, whose tier was the regime of its source).
    import json
    task = next(t for t in (json.loads(p.read_text()) for p in sorted((REPO / "tasks").rglob("*.json")))
                if t.get("tier"))
    tiers = ag.task_tiers({"a": {"kind": "vlm", "task": task["id"]}, "b": {"kind": "vlm", "task": "x", "tier": "T"}})
    assert tiers["x"] == "T"
    assert tiers[task["id"]] == task["tier"]


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


# --------------------------------------------------------------------------- #
# The power simulation (paper/a4/power.py)
# --------------------------------------------------------------------------- #
def _power():
    spec = importlib.util.spec_from_file_location("a4_power", REPO / "paper" / "a4" / "power.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_power_model_pieces():
    pw = _power()
    e = pw.flip_rate(0.18)  # two raters split on 18% of pairs <-> each is off 10% of the time
    assert abs(e - 0.1) < 1e-9
    # 74% of answers say same with 10% error -> 80% of pairs truly same.
    assert abs(pw.latent(0.74, 0.1) - 0.8) < 1e-9
    assert pw.latent(0.05, 0.1) == 0.0
    assert pw.cohen(5, 0, 0, 5) == 1.0 and pw.cohen(5, 5, 5, 5) == 0.0


def test_power_more_pairs_means_a_tighter_interval():
    import random
    pw = _power()

    def hw(n):
        rng = random.Random(1)
        return pw.half_width([pw.simulate(rng, n, 2, 0.5, 0.8, 0.15, 0.1)[0] for _ in range(300)])

    assert hw(400) < hw(100) * 0.65  # about half, as 1 / sqrt(4)
    # No rater error and a judge that is always right: perfect agreement on both measures.
    kappa, fleiss, precision = pw.simulate(random.Random(1), 50, 2, 0.5, 1.0, 0.0, 0.0)
    assert (kappa, fleiss, precision) == (1.0, 1.0, 1.0)


# --------------------------------------------------------------------------- #
# Design v2: the grader against people
# --------------------------------------------------------------------------- #
def _pair(task, cls, tier="clinical", model="lab/m1", target=True, **kw):
    return {"kind": "pair", "task": task, "base_task": task, "tier": tier, "model": model, "sample": 0,
            "success": cls == "right", "target_f1": (1.0 if cls != "wrong" else 0.2) if target else None,
            "grader_class": cls, "has_target": target, **kw}


def _check(kind, task="t-check"):
    return {"kind": kind, "task": task, "tier": "clinical", "has_target": True,
            "expected": "same" if kind == "check-same" else "different"}


def _v2_key(items, **kw):
    return {"set": "a4-v2", "design": "v2", "items": items, **kw}


def _v2(rows, raters=None, repeats=(), set_id="a4-v2"):
    raters = raters or {r["rater"]: {"role": "rater"} for r in rows}
    return {"set": set_id, "exported_at": "2026-12-01T00:00:00+00:00", "raters": raters,
            "rows": [{"created_at": f"2026-12-01T00:{n:02d}:00+00:00", **r} for n, r in enumerate(rows)],
            "repeats": list(repeats)}


def _a(rater, item, label, target=None, **kw):
    return {"rater": rater, "item": item, "label": label, "target_label": target, **kw}


CHECK_ITEMS = {"cs1": _check("check-same"), "cs2": _check("check-same"), "cd1": _check("check-different"),
               "cd2": _check("check-different"), "cc1": _check("check-calibrated")}


def _passing(rater):
    """Five checks answered right: enough to pass the rule."""
    return [_a(rater, "cs1", S, S), _a(rater, "cs2", S, S), _a(rater, "cd1", D, D), _a(rater, "cd2", D, D),
            _a(rater, "cc1", S, D)]   # a calibrated change seen only in the zoomed view still counts


def test_v1_and_v2_are_never_mixed():
    v2 = _v2_key({"p1": _pair("t1", "right")})
    v1 = {"set": "a4-v1", "items": {"a": {"kind": "vlm", "task": "t", "model": "m", "vlm_label": S, "tier": "x"}}}
    assert ag.design_of(v2) == "v2" and ag.design_of(v1) == "v1"
    # a key holding items of both designs
    with pytest.raises(ValueError, match="never analysed together"):
        ag.design_of(_v2_key({**v2["items"], **v1["items"]}))
    with pytest.raises(ValueError, match="never analysed together"):
        ag.design_of({"set": "a4-v1", "items": {**v1["items"], **v2["items"]}})
    # a v2 key with ratings of the pilot set, or with an old bare export
    with pytest.raises(ValueError, match="never analysed together"):
        analyse(v2, _v2([_a("R1", "p1", S, S)], set_id="a4-v1"))
    with pytest.raises(ValueError, match="never analysed together"):
        analyse(v2, [{"evaluator_token": "x" * 12, "item": "p1", "label": S}])
    # a v1 key with ratings of the v2 set
    with pytest.raises(ValueError, match="never analysed together"):
        analyse(v1, _v2([_a("R1", "a", S)]))
    # a v2 rating on an item the key does not hold
    with pytest.raises(ValueError, match="not in the key"):
        analyse(v2, _v2([_a("R1", "zzz", S, S)]))
    with pytest.raises(ValueError, match="labels must be"):
        analyse(v2, _v2([_a("R1", "p1", S, "maybe")]))


def test_v2_grader_against_people_by_hand():
    items = {**CHECK_ITEMS,
             "a": _pair("t1", "right"), "b": _pair("t2", "right"), "c": _pair("t3", "close"),
             "d": _pair("t4", "wrong"), "e": _pair("t5", "wrong", target=False)}
    rows = _passing("R1") + _passing("R2")
    # whole scene: people call a same (2), b split, c different (2), d different (2), e same/can't tell
    # zoomed:      a same (2), b same (2), c same (2), d: one same one different; e has no zoomed view
    rows += [_a("R1", "a", S, S), _a("R2", "a", S, S), _a("R1", "b", S, S), _a("R2", "b", D, S),
             _a("R1", "c", D, S), _a("R2", "c", D, S), _a("R1", "d", D, S), _a("R2", "d", D, D),
             _a("R1", "e", S), _a("R2", "e", "unsure")]
    res = analyse(_v2_key(items), _v2(rows))
    assert res["design"] == "v2" and res["rating_set"]["by_class"] == {"right": 2, "close": 1, "wrong": 2}
    assert res["rating_set"]["with_target_view"] == 4
    assert all(v["passed_checks"] for v in res["raters"].values())
    w = res["cohorts"]["primary"]["whole"]
    # 9 labelled whole answers; the grader (success) agrees on a,a,b(S),c,c,d,d = 7; b(D) and e(S) disagree
    assert w["ratings"] == 9 and w["cant_tell"] == 1 and w["pairs"] == 5 and w["pairs_tied"] == 1
    assert w["unweighted"]["per_rating"]["agreement"]["est"] == 7 / 9
    assert w["unweighted"]["table"] == {"human same / judge same": 3, "human same / judge different": 1,
                                        "human different / judge same": 1, "human different / judge different": 4}
    # per pair (b is tied and left out): people same = a, e; the grader passes a only
    pp = w["unweighted"]["per_pair"]
    assert pp["sensitivity"]["est"] == 0.5 and pp["specificity"]["est"] == 1.0
    assert pp["rescue_precision"]["est"] == 1.0 and pp["npv"]["est"] == 2 / 3
    assert w["human_vs_human"]["pairs"] == 4 and w["human_vs_human"]["pairs_split"] == 1
    # zoomed view against target score = 1 (a, b, c): 7 of 8 answers agree; d(S) does not
    t = res["cohorts"]["primary"]["target"]
    assert t["ratings"] == 8 and t["pairs"] == 4
    assert t["unweighted"]["per_rating"]["agreement"]["est"] == 7 / 8
    # what people said by the grader's verdict: "close" is different on the whole scene, same zoomed
    assert w["by_class"]["close"]["same_share"]["est"] == 0.0 and t["by_class"]["close"]["same_share"]["est"] == 1.0
    assert w["by_class"]["right"]["same_share"]["est"] == 0.75
    assert list(w["by_class"]) == ["right", "close", "wrong"]
    assert res["cohorts"]["all"]["judge"] is None   # the judge was not run


def test_v2_check_rule_and_cohorts():
    items = {**CHECK_ITEMS, "a": _pair("t1", "right")}
    rows = _passing("R1") + [_a("R1", "a", S, S)]                                  # passes
    rows += [r for r in _passing("R2") if r["item"] != "cd1"] + [_a("R2", "cd1", S, S), _a("R2", "a", D, D)]  # easy miss
    rows += _passing("R3")[:3] + [_a("R3", "a", S, S)]                             # 3 checks: too few
    rows += [r for r in _passing("R4") if r["item"] != "cs1"] + [_a("R4", "cs1", "unsure", "unsure"), _a("R4", "a", S, S)]
    rows += _passing("R5") + [_a("R5", "a", D, D)]                                 # the author
    raters = {f"R{n}": {"role": "rater"} for n in range(1, 5)} | {"R5": {"role": "author"}}
    res = analyse(_v2_key(items), _v2(rows, raters))
    passed = {p: v["passed_checks"] for p, v in res["raters"].items()}
    # R4: one miss ("can't tell" on a known-same) is allowed; R2 missed an easy known-different; R3 answered 3
    assert passed == {"R1": True, "R2": False, "R3": False, "R4": True, "R5": True}
    assert res["raters"]["R1"]["check_kinds_in_first_8"] == 3
    c = res["cohorts"]
    assert c["primary"]["raters"] == ["R1", "R4"] and c["no_author"]["raters"] == ["R1", "R2", "R3", "R4"]
    assert c["all"]["raters"] == ["R1", "R2", "R3", "R4", "R5"]
    assert c["primary"]["whole"]["ratings"] == 2 and c["all"]["whole"]["ratings"] == 5
    assert c["all"]["whole"]["unweighted"]["per_rating"]["agreement"]["est"] == 3 / 5


def test_v2_weights_stand_for_the_run():
    items = {"a": _pair("t1", "right"), "b": _pair("t2", "wrong"), "c": _pair("t3", "wrong", tier="grounded")}
    # the run: 90 right, 10 wrong (8 clinical, 2 grounded). People confirm a and b, not c.
    pop = {"cells": [["clinical", "right", 90], ["clinical", "wrong", 8], ["grounded", "wrong", 2]]}
    rows = [_a("R1", "a", S, S), _a("R1", "b", D, D), _a("R1", "c", S, S)]
    w = analyse(_v2_key(items), _v2(rows), population=pop)["cohorts"]["all"]["whole"]
    assert w["unweighted"]["per_rating"]["agreement"]["est"] == 2 / 3
    assert w["weighted"]["per_rating"]["agreement"]["est"] == 98 / 100
    assert ag.weights_v2({k: items[k] for k in "ab"}, pop) == {"a": 90.0, "b": 10.0}   # c's cell is covered by scaling


def test_v2_weights_undo_the_preference_for_passes_that_look_different():
    """The set keeps 3 passes whose pictures differ and 1 identical one, but of the 20
    passes drawn only 4 differed: the three stand for 20% of the run's passes, the one for 80%."""
    items = {k: {**_pair(f"t{n}", "right"), "pictures_differ": k != "d"} for n, k in enumerate("abcd")}
    pop = {"cells": [["clinical", "right", 100]], "right_pictures": {"drawn": 20, "differ": 4}}
    w = ag.weights_v2(items, pop)
    assert w["d"] == pytest.approx(80.0) and sum(w[k] for k in "abc") == pytest.approx(20.0)
    # people reject one of the passes that differ: 1 in 3 of 20%, not 1 in 4 of everything
    rows = [_a("R1", "a", D, D), _a("R1", "b", S, S), _a("R1", "c", S, S), _a("R1", "d", S, S)]
    res = analyse(_v2_key(items), _v2(rows), population=pop)["cohorts"]["all"]["whole"]
    assert res["unweighted"]["per_rating"]["agreement"]["est"] == 0.75
    assert res["weighted"]["per_rating"]["agreement"]["est"] == pytest.approx(1 - 0.2 / 3)
    assert {g: v["pairs"] for g, v in res["right_by_pictures"].items()} == {"differ": 3, "identical": 1}
    # a key from before the preference (no flag, no counts) is weighted as before
    plain = {k: _pair(f"t{n}", "right") for n, k in enumerate("ab")}
    assert ag.weights_v2(plain, {"cells": [["clinical", "right", 100]]}) == {"a": 50.0, "b": 50.0}


def test_v2_retest_judge_and_markdown():
    items = {**CHECK_ITEMS, "aaaaaaaaaaaa": _pair("t1", "right", judge_label=S),
             "bbbbbbbbbbbb": _pair("t2", "wrong", judge_label=S), "cccccccccccc": _pair("t3", "wrong")}
    rows = _passing("R1") + _passing("R2") + [
        _a("R1", "aaaaaaaaaaaa", S, S), _a("R2", "aaaaaaaaaaaa", S, S), _a("R1", "bbbbbbbbbbbb", D, D),
        _a("R2", "bbbbbbbbbbbb", D, D), _a("R1", "cccccccccccc", D, D, note="colour differs | here", ref_wrong=True)]
    repeats = [{"rater": "R1", "item": "aaaaaaaaaaaa", "label": S, "target_label": D},
               {"rater": "R1", "item": "bbbbbbbbbbbb", "label": D, "target_label": D}]
    res = analyse(_v2_key(items), _v2(rows, repeats=repeats))
    assert res["raters"]["R1"]["retest"] == {"whole": {"n": 2, "same_answer": 2}, "target": {"n": 2, "same_answer": 1}}
    assert res["retest_no_author"]["target"] == {"n": 2, "same_answer": 1}
    j = res["cohorts"]["all"]["judge"]
    # the judge said same on a and b; people: a same, b different -> 2 of 4 answers agree; c has no verdict
    assert j["pairs"] == 2 and j["unweighted"]["per_rating"]["agreement"]["est"] == 0.5
    md = ag.markdown_v2(res)
    for heading in ("Primary: task success against people", "Primary: target score against people",
                    "People against people", "Secondary: the image-pair judge", "by the grader's verdict"):
        assert heading in md
    assert "aaaaaaaaaaaa" not in md and "colour differs \\| here" in md   # no item ids; notes escaped
    import json as _json
    assert "aaaaaaaaaaaa" not in _json.dumps(res)


def test_v2_two_way_bootstrap_is_no_narrower_when_raters_differ():
    # R1 always agrees with the grader, R2 never does: resampling raters must widen the interval.
    recs = [(f"t{n}", p, S if (p == "R1") == (n % 2 == 0) else D, S if n % 2 == 0 else D)
            for n in range(40) for p in ("R1", "R2")]
    two = ag.bootstrap_tasks_and_raters(recs, reps=400, seed=1)["agreement"]
    clusters = collections.defaultdict(list)
    for t, _, h, j in recs:
        clusters[t].append((h, j, 1.0))
    one = ag.bootstrap(clusters, ag.judge_measures, reps=400, seed=1)["agreement"]
    assert one["lo"] == one["hi"] == 0.5          # every task holds one agreeing and one disagreeing answer
    assert two["lo"] == 0.0 and two["hi"] == 1.0  # the panel of raters is the uncertainty


def test_export_repeats_use_the_same_pseudonyms(monkeypatch):
    rows = [{"evaluator_token": "tokA", "name": "Al", "item": "i1", "label": S, "target_label": D}]
    out, names = ex.pseudonymise(rows, {})
    assert out[0]["target_label"] == D
    rep = ex.pseudonymise_repeats([{"evaluator_token": "tokA", "item": "i1", "label": S, "target_label": S,
                                    "ms": 5, "created_at": "x"}], names)
    assert rep == [{"rater": "R1", "item": "i1", "label": S, "target_label": S, "ms": 5, "created_at": "x"}]
    sent = []
    monkeypatch.setattr(ex, "select", lambda q, project=ex.PROJECT: sent.append(q) or [{"ok": False}])
    assert ex.fetch_repeats("a4-v2") == [] and len(sent) == 1     # no table: nothing more is asked
    with pytest.raises(ValueError):
        ex._safe("a4'; drop table x; --")
    monkeypatch.undo()
    for bad in ("delete from ratings", "select 1; drop table ratings"):
        with pytest.raises(ValueError, match="only a single SELECT"):
            ex.select(bad)      # refused before anything is sent
