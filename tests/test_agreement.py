"""A4 agreement maths (scripts/agreement.py) on hand-checkable cases."""

import collections
import importlib.util
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("agreement", REPO / "scripts" / "agreement.py")
ag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ag)

C = collections.Counter


def test_fleiss_perfect_and_chance():
    assert ag.fleiss_kappa([C(same=2), C(different=2)]) == 1.0
    # Every item split 1-1: observed agreement 0, chance 0.5 -> kappa -1.
    assert ag.fleiss_kappa([C(same=1, different=1)] * 4) == -1.0
    assert ag.fleiss_kappa([C(same=1)]) is None  # single ratings don't count


def test_cohen():
    assert ag.cohen_kappa([("same", "same"), ("different", "different")]) == 1.0
    # p_o = 3/4; p_e = 0.5 * 0.25 + 0.5 * 0.75 = 0.5 -> (0.75 - 0.5) / 0.5
    pairs = [("same", "same"), ("same", "different"), ("different", "different"), ("different", "different")]
    assert abs(ag.cohen_kappa(pairs) - 0.5) < 1e-9


def _r(tok, item, label):
    return {"evaluator_token": tok, "item": item, "label": label}


KEY = {"set": "t", "items": {
    "v1": {"kind": "vlm", "vlm_label": "same"},
    "v2": {"kind": "vlm", "vlm_label": "same"},
    "v3": {"kind": "vlm", "vlm_label": "different"},
    "cs": {"kind": "control-same", "expected": "same"},
    "cd": {"kind": "control-different", "expected": "different"},
}}


def test_analyse_drops_raters_who_fail_checks():
    good = [_r("good-aaaa", i, lab) for i, lab in
            (("v1", "same"), ("v2", "different"), ("v3", "different"), ("cs", "same"), ("cd", "different"))]
    good2 = [_r("good-bbbb", i, lab) for i, lab in
             (("v1", "same"), ("v2", "different"), ("v3", "unsure"), ("cs", "same"), ("cd", "different"))]
    lazy = [_r("lazy-cccc", i, "same") for i in KEY["items"]]  # fails the different-check
    out = ag.analyse(KEY, good + good2 + lazy, min_checks=0.8)
    assert out["raters"]["lazy-ccc"]["check_accuracy"] == {"control-same": 1.0, "control-different": 0.0}
    assert out["raters_kept"] == 2
    assert out["items_with_2plus"] == 2  # v3 has one labelled vote; "unsure" carries none
    assert out["human_fleiss_kappa"] == 1.0
    # Judge said same on v1 (both humans agree) and v2 (both disagree); v3 one vote agrees.
    assert out["rescue_precision"] == 0.5
    assert out["human_vs_vlm_agreement"] == 3 / 5


def test_split_pairs_still_count_against_the_judge():
    a = [_r("a-aaaaaaa", i, lab) for i, lab in (("v1", "same"), ("cs", "same"), ("cd", "different"))]
    b = [_r("b-bbbbbbb", i, lab) for i, lab in (("v1", "different"), ("cs", "same"), ("cd", "different"))]
    out = ag.analyse(KEY, a + b, min_checks=0.8)
    assert out["human_vlm_pairs"] == 2
    assert out["rescue_precision"] == 0.5


def test_raters_without_enough_checks_are_dropped():
    unsure = [_r("u-uuuuuuu", "cs", "unsure"), _r("u-uuuuuuu", "cd", "unsure"), _r("u-uuuuuuu", "v1", "same")]
    out = ag.analyse(KEY, unsure, min_checks=0.8)
    assert out["raters_kept"] == 0 and out["human_vlm_pairs"] == 0


def test_checks_of_only_one_kind_are_not_enough():
    key = {"set": "t", "items": {**KEY["items"], "cs2": {"kind": "control-same", "expected": "same"}}}
    always_same = [_r("s-sssssss", i, "same") for i in ("cs", "cs2", "v1")]
    assert ag.analyse(key, always_same, min_checks=0.8)["raters_kept"] == 0


def test_duplicate_ratings_are_rejected():
    import pytest
    with pytest.raises(ValueError):
        ag.analyse(KEY, [_r("a-aaaaaaa", "v1", "same"), _r("a-aaaaaaa", "v1", "different")], min_checks=0.8)


def test_each_kind_of_check_must_pass_on_its_own():
    same = {f"cs{i}": {"kind": "control-same", "expected": "same"} for i in range(5)}
    key = {"set": "t", "items": {**KEY["items"], **same}}
    always_same = [_r("s-sssssss", i, "same") for i in [*same, "cd", "v1"]]  # 5/6 overall
    assert ag.analyse(key, always_same, min_checks=0.8)["raters_kept"] == 0
