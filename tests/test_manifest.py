"""The run manifest: parsing, validation, corpus hash, cost arithmetic, budget guard."""

import json
import pathlib

import pytest

from molbench import manifest as mf

REPO = pathlib.Path(__file__).resolve().parent.parent
FINAL = REPO / "run" / "final_run.toml"

MINIMAL = """
[run]
name = "t"
samples = 2
max_tokens = 100

[budget]
cap_usd = 1.0

[corpus]
version = "v-test"

[[conditions]]
name = "spec"

[[models]]
id = "m1"
route = "mock:m1"
price = { input = 1.0, output = 2.0 }
"""


def _with(extra: str = "", **swap: str) -> str:
    text = MINIMAL
    for old, new in swap.items():
        assert old in text
        text = text.replace(old, new)
    return text + extra


# --- the real manifest -------------------------------------------------------------

def test_final_manifest_states_the_planned_run():
    m = mf.load_manifest(FINAL)
    core = m.panel()
    assert len(core) == 16 and not any(x.optional for x in core)
    assert 3 <= len(m.panel(include_optional=True)) - 16 <= 5
    assert m.samples == 3 and m.temperature == "provider-default"
    assert m.budget_usd > 0 and m.validate == "required"
    conds = {c.name: c for c in m.conditions}
    assert m.conditions[0].name == "spec"  # the headline runs first
    assert conds["spec"].models == "all" and set(conds["spec"].tracks) == set(mf.TRACKS)
    assert conds["spec_grounded"].grounding and conds["spec_grounded"].where["source"]
    assert conds["bare"].prompt == "bare" and len(conds["bare"].models) == 3
    assert conds["spec_structured"].structured


def test_every_model_has_a_sourced_price_and_optional_ones_a_reason():
    m = mf.load_manifest(FINAL)
    for x in m.models:
        assert x.price is not None, x.id
        assert x.price.source and x.price.date, x.id
        if x.optional:
            assert x.reason, x.id


def test_panel_matches_the_published_leaderboard():
    card = json.loads((REPO / "docs" / "scorecard.json").read_text())
    published = {m["spec"] for m in card["models"].values() if m["spec"] != "baseline"}
    assert {x.route for x in mf.load_manifest(FINAL).panel()} == published


def test_calibration_covers_the_core_panel_or_falls_back():
    m, calib = mf.load_manifest(FINAL), mf.Calibration.load()
    measured = [x for x in m.panel() if calib.rates(x).calibrated]
    assert len(measured) >= 15
    for x in m.panel(include_optional=True):
        r = calib.rates(x)
        assert 2.0 < r.chars_per_input_token < 6.0 and r.output_tokens_per_ref_char > 0


# --- parsing -----------------------------------------------------------------------

def test_minimal_manifest_parses_with_defaults():
    m = mf.parse_manifest(MINIMAL)
    assert (m.name, m.samples, m.max_tokens, m.reasoning_max_tokens) == ("t", 2, 100, 100)
    assert m.conditions[0].tracks == mf.TRACKS and m.conditions[0].models == "all"
    assert m.retry.max_attempts == 5 and len(m.sha256) == 64


@pytest.mark.parametrize("text, message", [
    ("not = [valid", "not valid TOML"),
    (_with(**{'samples = 2': 'samples = 2\ntypo = 1'}), "unknown key"),
    (_with(**{'samples = 2': 'samples = 0'}), "must be >= 1"),
    (_with(**{'cap_usd = 1.0': 'cap_usd = 0'}), "cap_usd"),
    (_with(**{'max_tokens = 100': 'max_tokens = 100\ntemperature = "0"'}), "temperature"),
    (_with(**{'max_tokens = 100': 'max_tokens = 100\nvalidate = "maybe"'}), "validate"),
    (_with(**{'name = "t"': 'name = "a/b"'}), "directory name"),
    (_with('\n[[models]]\nid = "m1"\nroute = "mock:other"\n'), "duplicate id"),
    (_with('\n[[models]]\nid = "m2"\nroute = "mock:m1"\n'), "duplicate route"),
    (_with('\n[[models]]\nid = "m2"\nroute = "mock:m2"\nstructured = "xml"\n'), "structured"),
    (_with(**{'name = "spec"': 'name = "spec"\nmodels = ["nope"]'}), "unknown model"),
    (_with(**{'name = "spec"': 'name = "spec"\nprompt = "fancy"'}), "prompt must be"),
    (_with(**{'name = "spec"': 'name = "spec"\ntracks = ["visual_rubric"]'}), "tracks"),
    (_with(**{'name = "spec"': 'name = "spec"\nmodels = "structured"'}), "structured = true"),
    (_with(**{'output = 2.0': 'output = 2.0, verified = true'}), "source and a date"),
    (_with(**{'output = 2.0': 'output = -2.0'}), "negative price"),
    (_with(**{'samples = 2': 'samples = 2.5'}), "whole number"),
    (_with(**{'max_tokens = 100': 'max_tokens = "8k"'}), "whole number"),
    (_with(**{'samples = 2\n': ''}), "missing 'samples'"),
    (_with(**{'cap_usd = 1.0': 'cap_usd = "lots"'}), "must be a number"),
    (_with(**{'max_tokens = 100': 'max_tokens = 100\n[run.retry]\nmax_attempts = "five"'}),
     "whole number"),
    (_with(**{'max_tokens = 100': 'max_tokens = 100\n[run.retry]\ntimeout_seconds = 0'}),
     "timeout_seconds"),
    (_with(**{'route = "mock:m1"': 'route = "mock:m1"\nmax_concurrency = 0'}), "must be >= 1"),
    (_with(**{'output = 2.0': 'output = "cheap"'}), "must be a number"),
])
def test_bad_manifests_are_rejected_with_a_reason(text, message):
    with pytest.raises(mf.ManifestError, match=message):
        mf.parse_manifest(text)


def test_panel_selection():
    m = mf.parse_manifest(_with('\n[[models]]\nid = "extra"\nroute = "mock:extra"\noptional = true\n'))
    assert [x.id for x in m.panel()] == ["m1"]
    assert [x.id for x in m.panel(include_optional=True)] == ["m1", "extra"]
    assert [x.id for x in m.panel(only=["extra"])] == ["extra"]
    with pytest.raises(mf.ManifestError, match="not in the manifest"):
        m.panel(only=["ghost"])


def test_conditions_pick_tasks_and_models():
    lookup = mf.Condition("g", grounding=True, tracks=("mvs",), where={"source": ("resolve",)})
    assert lookup.takes_task({"category": "mvs", "source": "resolve", "grounding": {"text": "x"}})
    assert not lookup.takes_task({"category": "mvs", "source": "resolve"})  # no pack to add
    assert not lookup.takes_task({"category": "mvs", "source": "generated", "grounding": {"text": "x"}})
    assert not lookup.takes_task({"category": "api_calling", "source": "resolve", "grounding": {"text": "x"}})
    plain, json_mode = mf.ModelSpec("a", "mock:a"), mf.ModelSpec("b", "mock:b", structured="json_object")
    structured = mf.Condition("s", structured=True, models="structured")
    assert structured.takes_model(json_mode) and not structured.takes_model(plain)
    assert mf.Condition("few", models=("a",)).takes_model(plain)
    assert not mf.Condition("few", models=("a",)).takes_model(json_mode)


def test_reasoning_models_get_the_larger_token_limit():
    m = mf.parse_manifest(_with(**{'max_tokens = 100': 'max_tokens = 100\nreasoning_max_tokens = 900'}))
    assert m.max_tokens_for(mf.ModelSpec("a", "mock:a")) == 100
    assert m.max_tokens_for(mf.ModelSpec("a", "mock:a", reasoning=True)) == 900
    assert m.max_tokens_for(mf.ModelSpec("a", "mock:a", reasoning=True, max_tokens=7)) == 7


def test_retry_backoff_doubles_up_to_the_cap():
    r = mf.Retry(backoff_seconds=2, backoff_max_seconds=10)
    assert [r.delay(i) for i in (1, 2, 3, 4)] == [2, 4, 8, 10]


# --- corpus identity ---------------------------------------------------------------

def test_corpus_hash_tracks_content_and_paths(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "1.json").write_text('{"id": "1"}')
    (tmp_path / "b.json").write_text('{"id": "2"}')
    first = mf.corpus_hash(tmp_path)
    assert first == mf.corpus_hash(tmp_path)
    (tmp_path / "a" / "1.json").write_text('{"id": "1", "prompt": "changed"}')
    changed = mf.corpus_hash(tmp_path)
    assert changed != first
    (tmp_path / "a" / "1.json").rename(tmp_path / "a" / "renamed.json")
    assert mf.corpus_hash(tmp_path) != changed
    (tmp_path / "notes.txt").write_text("not a task")
    (tmp_path / "a" / "renamed.json").rename(tmp_path / "a" / "1.json")
    assert mf.corpus_hash(tmp_path) == changed


def test_a_paid_run_needs_the_pinned_corpus(tmp_path):
    (tmp_path / "t.json").write_text("{}")
    actual = mf.corpus_hash(tmp_path)
    unpinned = mf.parse_manifest(MINIMAL)
    assert mf.check_corpus(unpinned, tmp_path, strict=False) == actual
    with pytest.raises(mf.ManifestError, match="sha256 is empty"):
        mf.check_corpus(unpinned, tmp_path, strict=True)
    wrong = mf.parse_manifest(_with(**{'version = "v-test"': 'version = "v-test"\nsha256 = "abc"'}))
    with pytest.raises(mf.ManifestError, match="not the corpus the manifest pins"):
        mf.check_corpus(wrong, tmp_path, strict=True)
    pinned = mf.parse_manifest(_with(**{'version = "v-test"': f'version = "v-test"\nsha256 = "{actual}"'}))
    assert mf.check_corpus(pinned, tmp_path, strict=True) == actual


# --- cost arithmetic ---------------------------------------------------------------

def test_price_is_per_million_tokens():
    assert mf.Price(1.0, 5.0).cost(2_000_000, 100_000) == pytest.approx(2.5)
    assert mf.estimate_cost(None, 10, 10) is None


def test_token_estimate_caps_output_at_the_limit():
    rates = mf.TokenRates(chars_per_input_token=4.0, output_tokens_per_ref_char=0.5)
    assert mf.estimate_tokens(4000, 1000, rates, max_tokens=8000) == (1000, 500)
    assert mf.estimate_tokens(4000, 1000, rates, max_tokens=100) == (1000, 100)


def test_uncalibrated_models_use_pooled_rates():
    rows = {"a": {"chars_per_input_token": 3.0, "output_tokens_per_ref_char": 0.5},
            "b": {"chars_per_input_token": 4.0, "output_tokens_per_ref_char": 2.0},
            "c": {"chars_per_input_token": 3.5, "output_tokens_per_ref_char": 1.0}}
    calib = mf.Calibration({"models": rows, **mf.pooled_rates(rows)})
    assert calib.rates(mf.ModelSpec("a", "x:a")).calibrated
    plain = calib.rates(mf.ModelSpec("new", "x:new"))
    assert not plain.calibrated and plain.output_tokens_per_ref_char == 1.0  # the median
    # A reasoning model nobody has run: assume the most expensive behaviour seen.
    thinker = calib.rates(mf.ModelSpec("new", "x:new", reasoning=True))
    assert (thinker.chars_per_input_token, thinker.output_tokens_per_ref_char) == (3.0, 2.0)


# --- budget guard ------------------------------------------------------------------

def test_budget_refuses_a_plan_above_the_cap():
    with pytest.raises(mf.BudgetExceeded, match="above the \\$10.00 cap"):
        mf.Budget(10.0, spent=4.0, remaining_estimate=6.5).check()
    mf.Budget(10.0, spent=4.0, remaining_estimate=6.0).check()  # exactly at the cap is fine


def test_budget_aborts_when_real_cost_outruns_the_estimate():
    b = mf.Budget(10.0, remaining_estimate=8.0)   # four calls, estimated $2 each
    b.charge(actual=2.0, estimate=2.0)
    assert b.projected == pytest.approx(8.0)
    b.charge(actual=3.0, estimate=2.0)            # dearer than planned: 5 spent + 4 to go
    assert b.projected == pytest.approx(9.0)
    with pytest.raises(mf.BudgetExceeded):
        b.charge(actual=4.5, estimate=2.0)        # 9.5 spent + 2 to go
    assert b.exceeded and b.spent == pytest.approx(9.5)
