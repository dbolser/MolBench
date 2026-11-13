"""The manifest runner on a small mock panel: plan, archive, resume, budget abort,
retries, grading, the json-repair counterfactual, scorecards and the dry run.

No test calls a real model; `MockModel` and small stubs stand in for every provider.
"""

import importlib.util
import json
import os
import pathlib

import pytest

from molbench import manifest as mf
from molbench import runner
from molbench.models import Completion, MockModel, Model, build_model, perturb_reference

REPO = pathlib.Path(__file__).resolve().parent.parent

MANIFEST = """
[run]
name = "t"
samples = 2
max_tokens = 4000
concurrency = 4
per_model_concurrency = 2
validate = "off"

[run.retry]
max_attempts = 3
backoff_seconds = 0.5

[budget]
cap_usd = 1000.0

[corpus]
version = "v-test"

[[conditions]]
name = "spec"

[[conditions]]
name = "spec_structured"
structured = true
models = "structured"

[[conditions]]
name = "spec_grounded"
grounding = true
tracks = ["mvs"]
where = { tier = ["resolve", "clinical"] }

[[conditions]]
name = "bare"
prompt = "bare"
tracks = ["mvs"]
models = ["plain"]

[[models]]
id = "plain"
route = "mock:plain"
price = { input = 1.0, output = 2.0 }

[[models]]
id = "json/mode"
route = "mock:json-mode"
structured = "json_object"
price = { input = 3.0, output = 4.0 }
"""

CALIB = mf.Calibration({"models": {}, "default": {"chars_per_input_token": 4.0,
                                                  "output_tokens_per_ref_char": 0.5}})


def _manifest(text: str = MANIFEST, **swap: str) -> mf.Manifest:
    for old, new in swap.items():
        assert old in text
        text = text.replace(old, new)
    return mf.parse_manifest(text, "test.toml")


@pytest.fixture(scope="module")
def corpus():
    """A slice of the real corpus: a few tasks of each kind the conditions select on."""
    tasks = runner.load_tasks(list(mf.TRACKS))
    pick = ([t for t in tasks if t["category"] == "api_calling"][:3]
            + [t for t in tasks if t.get("source") == "resolve"][:2]
            + [t for t in tasks if t.get("source") == "generated"][:3])
    assert len(pick) == 8
    return pick


def _mocks(m: mf.Manifest) -> dict:
    return {x.id: MockModel(x.id) for x in m.models}


def _run(tmp_path, corpus, m=None, models=None, **kw):
    m = m or _manifest()
    cells = runner.build_plan(m, corpus, m.panel())
    archive = runner.RunArchive(tmp_path / "arch")
    archive.open(m, "corpus-sha", mock=True)
    kw.setdefault("log", lambda s: None)
    kw.setdefault("sleep", lambda s: None)
    stats = runner.generate(m, cells, models or _mocks(m), archive, CALIB, **kw)
    return m, cells, archive, stats


# --- plan --------------------------------------------------------------------------

def test_plan_covers_every_model_condition_task_and_sample(corpus):
    m = _manifest()
    cells = runner.build_plan(m, corpus, m.panel())
    per = {}
    for c in cells:
        per[(c.condition.name, c.model.id)] = per.get((c.condition.name, c.model.id), 0) + 1
    assert per == {("spec", "plain"): 16, ("spec", "json/mode"): 16,
                   ("spec_structured", "json/mode"): 16,     # only the model with JSON mode
                   ("spec_grounded", "plain"): 4, ("spec_grounded", "json/mode"): 4,
                   ("bare", "plain"): 10}                    # MVS only, one model
    assert len({c.key for c in cells}) == len(cells)
    assert cells[0].condition.name == "spec"                 # headline condition first


def test_conditions_change_the_prompt_and_its_hash(corpus):
    m = _manifest()
    cells = runner.build_plan(m, corpus, m.panel())
    by = {(c.condition.name, c.task["id"], c.model.id, c.sample): c for c in cells}
    mvs = next(t["id"] for t in corpus if t.get("source") == "resolve")
    api = next(t["id"] for t in corpus if t["category"] == "api_calling")
    spec, bare, grounded = (by[(c, mvs, "plain", 0)] for c in ("spec", "bare", "spec_grounded"))
    assert "MVS reference" in spec.system and "MVS reference" not in bare.system
    assert spec.user in grounded.user and "Facts about the structures" in grounded.user
    assert len({spec.prompt_sha256, bare.prompt_sha256, grounded.prompt_sha256}) == 3
    assert by[("spec", mvs, "plain", 0)].prompt_sha256 == by[("spec", mvs, "plain", 1)].prompt_sha256
    plain_api, json_api = by[("spec", api, "json/mode", 0)], by[("spec_structured", api, "json/mode", 0)]
    assert json_api.system == plain_api.system + runner.API_STRUCTURED_SUFFIX
    assert (plain_api.structured, json_api.structured) == (None, "json_object")


def test_bare_is_refused_on_the_api_track(corpus):
    m = _manifest(**{'prompt = "bare"\ntracks = ["mvs"]': 'prompt = "bare"'})
    with pytest.raises(mf.ManifestError, match="MVS track only"):
        runner.build_plan(m, corpus, m.panel())


# --- archive -----------------------------------------------------------------------

def test_every_call_is_archived_with_what_a_rerun_or_audit_needs(tmp_path, corpus):
    m, cells, archive, stats = _run(tmp_path, corpus)
    records = archive.load()
    assert stats["called"] == len(cells) == len(records)
    for c in cells:
        r = records[c.key]
        assert isinstance(r["raw"], str)
        assert r["prompt_sha256"] == c.prompt_sha256 and len(r["task_sha256"]) == 64
        assert r["usage"]["input_tokens"] > 0 and r["usage"]["output_tokens"] >= 0
        assert r["finish_reason"] in ("stop", "length") and r["latency_s"] is not None
        assert r["request"] == {"max_tokens": 4000, "structured": c.structured,
                                "temperature": "provider-default"}  # none is ever sent
        assert r["provider"] == "mock" and r["v"] == runner.ARCHIVE_VERSION
        assert r["cost_usd"] == pytest.approx(c.model.price.cost(
            r["usage"]["input_tokens"], r["usage"]["output_tokens"]))
        assert r["attempts"] == 1 and r["mock"] is True and r["route"] == c.model.route
    files = sorted(p.relative_to(tmp_path / "arch").as_posix()
                   for p in (tmp_path / "arch" / "cells").rglob("*.jsonl"))
    assert "cells/mock_plain/bare.jsonl" in files and "cells/mock_json-mode/spec.jsonl" in files
    lock = json.loads((tmp_path / "arch" / "run.json").read_text())
    assert lock["run"] == "t" and lock["corpus_sha256"] == "corpus-sha" and lock["mock"] is True


def test_no_archive_cannot_be_switched_off():
    with pytest.raises(SystemExit) as e:
        runner.main(["--models", "baseline", "--no-archive"])
    assert e.value.code == 2


def test_an_archive_is_never_mixed_with_another_corpus_or_run(tmp_path):
    m = _manifest()
    archive = runner.RunArchive(tmp_path / "arch")
    archive.open(m, "sha-1", mock=True)
    archive.open(m, "sha-1", mock=True)  # same run again: fine, a new session is logged
    assert len(json.loads((tmp_path / "arch" / "run.json").read_text())["sessions"]) == 2
    with pytest.raises(mf.ManifestError, match="corpus_sha256"):
        archive.open(m, "sha-2", mock=True)
    with pytest.raises(mf.ManifestError, match="mock"):
        archive.open(m, "sha-1", mock=False)  # real calls never land in a mock archive


def test_a_torn_last_line_is_ignored_and_a_duplicate_is_an_error(tmp_path, corpus):
    m, cells, archive, _ = _run(tmp_path, corpus)
    f = tmp_path / "arch" / "cells" / "mock_plain" / "bare.jsonl"
    whole = f.read_text()
    f.write_text(whole + '{"model": "plain", "cond')          # crash mid-write
    assert len(archive.load()) == len(cells)
    # the next record starts on its own line instead of being glued to the torn one
    extra = {**json.loads(whole.splitlines()[0]), "sample": 99}
    archive.append("mock_plain", extra)
    assert len(archive.load()) == len(cells) + 1
    f.write_text(whole + whole.splitlines()[0] + "\n")
    with pytest.raises(mf.ManifestError, match="archived twice"):
        archive.load()


# --- resume ------------------------------------------------------------------------

class Counting(MockModel):
    def __init__(self, name):
        super().__init__(name)
        self.seen = []

    def complete(self, system, user, **kw):
        self.seen.append((kw["context"]["condition"], kw["context"]["task_id"],
                          kw["context"]["sample"]))
        return super().complete(system, user, **kw)


def test_resume_skips_archived_cells_and_changes_nothing(tmp_path, corpus):
    m = _manifest(**{"concurrency = 4": "concurrency = 1"})
    models = {x.id: Counting(x.id) for x in m.models}
    _, cells, archive, first = _run(tmp_path, corpus, m, models, stop_after=20)
    assert first["stopped_early"] and first["called"] == 20
    after_first = {k: json.dumps(v, sort_keys=True) for k, v in archive.load().items()}
    assert len(after_first) == 20

    _, _, _, second = _run(tmp_path, corpus, m, models)
    assert second["already_archived"] == 20 and second["called"] == len(cells) - 20
    records = archive.load()
    assert set(records) == {c.key for c in cells}
    assert all(json.dumps(records[k], sort_keys=True) == v for k, v in after_first.items())
    calls = [s for mod in models.values() for s in mod.seen]
    assert len(calls) == len(cells)                 # no cell was ever called twice

    _, _, _, third = _run(tmp_path, corpus, m, models)
    assert third["called"] == 0 and third["already_archived"] == len(cells)


def test_resumed_run_equals_an_uninterrupted_one(tmp_path, corpus):
    m = _manifest()
    _, _, a, _ = _run(tmp_path / "a", corpus, m, stop_after=7)
    _run(tmp_path / "a", corpus, m)
    _, _, b, _ = _run(tmp_path / "b", corpus, m)
    raw = lambda arch: {k: (r["raw"], r["finish_reason"]) for k, r in arch.load().items()}
    assert raw(a) == raw(b)


def test_resume_refuses_an_archive_made_with_other_prompts(tmp_path, corpus):
    m, cells, archive, _ = _run(tmp_path, corpus, stop_after=5)
    changed = [dict(t, prompt=t["prompt"] + " Please.") for t in corpus]
    with pytest.raises(mf.ManifestError, match="different prompt"):
        runner.generate(m, runner.build_plan(m, changed, m.panel()), _mocks(m), archive, CALIB,
                        log=lambda s: None)


# --- budget ------------------------------------------------------------------------

def test_budget_aborts_before_the_first_call(tmp_path, corpus):
    m = _manifest(**{"cap_usd = 1000.0": "cap_usd = 0.01"})
    models = {x.id: Counting(x.id) for x in m.models}
    with pytest.raises(mf.BudgetExceeded, match="above the \\$0.01 cap"):
        _run(tmp_path, corpus, m, models)
    assert not any(mod.seen for mod in models.values())
    assert not (tmp_path / "arch" / "cells").exists()


class Pricey(MockModel):
    """Bills a flat $1 per call, whatever the manifest's price list says."""

    def complete(self, system, user, **kw):
        done = super().complete(system, user, **kw)
        done.cost_usd = 1.0
        return done


def test_budget_aborts_mid_run_and_keeps_the_archive(tmp_path, corpus):
    m = _manifest(**{"cap_usd = 1000.0": "cap_usd = 5.0", "concurrency = 4": "concurrency = 1"})
    models = {x.id: Pricey(x.id) for x in m.models}
    with pytest.raises(mf.BudgetExceeded, match="can be resumed"):
        _run(tmp_path, corpus, m, models)
    records = runner.RunArchive(tmp_path / "arch").load()
    # The estimate said cents; the provider billed $1 a call. It stops as soon as the
    # projection passes $5 - at the fifth call - not after the money is gone.
    assert len(records) == 5
    assert all(r["cost_usd"] == 1.0 and r["cost_source"] == "provider" for r in records.values())
    with pytest.raises(mf.BudgetExceeded):  # and a restart will not spend more
        _run(tmp_path, corpus, m, models)
    assert len(runner.RunArchive(tmp_path / "arch").load()) == 5


def test_dry_run_style_generation_ignores_the_cap(tmp_path, corpus):
    m = _manifest(**{"cap_usd = 1000.0": "cap_usd = 0.01"})
    _, cells, _, stats = _run(tmp_path, corpus, m, enforce_budget=False)
    assert stats["called"] == len(cells)


# --- retries -----------------------------------------------------------------------

class ApiError(Exception):
    def __init__(self, status_code):
        super().__init__(f"HTTP {status_code}")
        self.status_code = status_code


class Flaky(MockModel):
    """Fails each cell's first ``fails`` attempts with the given HTTP status."""

    def __init__(self, name, status, fails=2):
        super().__init__(name)
        self.status, self.fails, self.attempts = status, fails, {}

    def complete(self, system, user, **kw):
        key = tuple(kw["context"][k] for k in ("condition", "task_id", "sample"))
        self.attempts[key] = self.attempts.get(key, 0) + 1
        if self.attempts[key] <= self.fails:
            raise ApiError(self.status)
        return super().complete(system, user, **kw)


def test_transient_errors_are_retried_with_backoff(tmp_path, corpus):
    m = _manifest()
    waits = []
    models = {x.id: Flaky(x.id, status=429) for x in m.models}
    _, cells, archive, stats = _run(tmp_path, corpus, m, models, sleep=waits.append)
    assert stats["called"] == len(cells) and stats["failed"] == 0
    assert all(r["attempts"] == 3 for r in archive.load().values())
    assert sorted(set(waits)) == [0.5, 1.0]


def test_a_cell_that_keeps_failing_is_logged_not_archived_and_retried_next_start(tmp_path, corpus):
    m = _manifest()
    models = {"plain": MockModel("plain"), "json/mode": Flaky("json/mode", status=503, fails=3)}
    _, cells, archive, stats = _run(tmp_path, corpus, m, models)
    mine = [c for c in cells if c.model.id == "json/mode"]
    # ... until the model is dropped from a condition for this start, after 10 failures
    # in a row there (plus at most the one other call that was already in flight).
    # spec_grounded has only 4 cells, so it never reaches the limit.
    per_cond = {c: sum(x.condition.name == c for x in mine)
                for c in ("spec", "spec_structured", "spec_grounded")}
    assert per_cond["spec_grounded"] < runner.MAX_CONSECUTIVE_FAILURES < per_cond["spec"]
    floor = 2 * runner.MAX_CONSECUTIVE_FAILURES + per_cond["spec_grounded"]
    assert 0 <= stats["failed"] - floor < 2 * m.per_model_concurrency
    assert stats["dropped_models"] == ["json/mode"]
    assert stats["dropped"] == [("json/mode", "spec"), ("json/mode", "spec_structured")]
    assert stats["failed"] + stats["skipped"] == len(mine)
    assert not any(k[0] == "json/mode" for k in archive.load())
    errors = [json.loads(x) for x in (tmp_path / "arch" / "errors.jsonl").read_text().splitlines()]
    assert len(errors) == stats["failed"] and errors[0]["attempts"] == 3
    assert "HTTP 503" in errors[0]["error"]
    models["json/mode"].fails = 0  # the provider recovers
    _, _, _, again = _run(tmp_path, corpus, m, models)
    assert again["called"] == len(mine) and len(archive.load()) == len(cells)


def test_a_bad_key_is_not_retried(tmp_path, corpus):
    m = _manifest()
    bad = Flaky("plain", status=401, fails=99)
    _, _, _, stats = _run(tmp_path, corpus, m, {"plain": bad, "json/mode": MockModel("json/mode")})
    assert stats["failed"] and stats["dropped_models"] == ["plain"]
    assert set(bad.attempts.values()) == {1}


class RejectsJsonMode(MockModel):
    def complete(self, system, user, **kw):
        if kw.get("structured"):
            raise ApiError(404)   # "no endpoints found that support response_format"
        return super().complete(system, user, **kw)


def test_a_model_that_rejects_json_mode_still_runs_its_other_conditions(tmp_path, corpus):
    m = _manifest()
    models = {"plain": MockModel("plain"), "json/mode": RejectsJsonMode("json/mode")}
    _, cells, archive, stats = _run(tmp_path, corpus, m, models)
    assert stats["dropped"] == [("json/mode", "spec_structured")]
    done = archive.load()
    for cond in ("spec", "spec_grounded"):
        want = [c.key for c in cells if c.model.id == "json/mode" and c.condition.name == cond]
        assert want and all(k in done for k in want), cond
    assert not any(k[:2] == ("json/mode", "spec_structured") for k in done)


# --- provider adapters (no network: a fake client) -----------------------------------

class _Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def _openai_model(response):
    from molbench.models import OpenAIModel
    model = OpenAIModel("vendor/x", report_cost=True)
    calls = []

    def create(**kw):
        calls.append(kw)
        return response

    model._client = lambda timeout: _Obj(chat=_Obj(completions=_Obj(create=create)))
    return model, calls


def test_openai_adapter_reports_text_usage_cost_and_finish_reason():
    usage = _Obj(prompt_tokens=11, completion_tokens=7, cost=0.0123,
                 completion_tokens_details=_Obj(reasoning_tokens=3))
    resp = _Obj(id="r1", model="vendor/x-0801", usage=usage, choices=[
        _Obj(finish_reason="length", message=_Obj(content='{"root": '))])
    model, calls = _openai_model(resp)
    got = model.complete("sys", "user", max_tokens=99, structured="json_object", timeout=5)
    assert (got.text, got.finish_reason) == ('{"root": ', "length")
    assert (got.input_tokens, got.output_tokens, got.reasoning_tokens) == (11, 7, 3)
    assert got.cost_usd == 0.0123 and got.response_model == "vendor/x-0801"
    sent = calls[0]
    assert sent["response_format"] == {"type": "json_object"} and sent["max_tokens"] == 99
    assert "temperature" not in sent           # plan decision 12: provider default
    assert sent["extra_body"] == {"usage": {"include": True}}


@pytest.mark.parametrize("resp", [
    _Obj(id="r", model="m", usage=None, choices=None,
         error={"code": 429, "message": "upstream rate limit"}),
    _Obj(id="r", model="m", usage=None, choices=[]),
    _Obj(id="r", model="m", usage=None,
         choices=[_Obj(finish_reason="error", message=_Obj(content=""))]),
])
def test_a_provider_error_in_a_200_body_is_raised_not_archived_as_an_answer(resp, tmp_path, corpus):
    from molbench.models import ProviderError
    model, _ = _openai_model(resp)
    with pytest.raises(ProviderError):
        model.complete("sys", "user")
    # ... and the runner retries it, then logs it; nothing is archived for scoring.
    m = _manifest(**{'route = "mock:plain"': 'route = "openrouter:vendor/x"'})
    _, _, archive, stats = _run(tmp_path, corpus[:1], m,
                                {"plain": model, "json/mode": MockModel("json/mode")})
    assert stats["failed"] and not any(k[0] == "plain" for k in archive.load())
    errors = (tmp_path / "arch" / "errors.jsonl").read_text()
    assert "ProviderError" in errors and '"attempts": 3' in errors


# --- a grader that cannot cope --------------------------------------------------------

@pytest.mark.parametrize("raw", ['[{"action": ["x"]}]', '[{"action": {"a": 1}}]'])
def test_an_action_name_that_is_not_a_string_is_invalid_api_not_a_crash(raw, corpus):
    """The schema check reports these as unknown actions (it used to raise TypeError;
    the runner still guards that): outcome invalid_api, and the state grader still
    scores the answer."""
    api = next(t for t in corpus if t["category"] == "api_calling")
    s = runner.grade_output(api, raw)
    assert s["f1"] == 0.0 and s["outcome"] == "invalid_api" and "grader_crash" not in s
    assert s["schema_errors"] == [f"action[0]: unknown action {json.loads(raw)[0]['action']!r}"]
    assert s["grader"] == "state" and not runner.is_success(s)


def test_output_that_crashes_the_grader_scores_zero_and_is_marked(corpus, monkeypatch):
    api = next(t for t in corpus if t["category"] == "api_calling")
    mvs = next(t for t in corpus if t["category"] == "mvs")

    def boom(*a, **k):
        raise TypeError("unhashable")

    monkeypatch.setattr(runner.grader_mod, "grade_task", boom)
    s = runner.grade_output(api, '[{"action": "load", "molecule_id": "1cbs"}]')
    assert s["f1"] == 0.0 and s["outcome"] == "invalid_api" and "unhashable" in s["grader_crash"]
    assert not runner.is_success(s)
    assert runner._track_stats([{**s, "finish_reason": "stop"}], "api_calling",
                               False)["n_grader_crashes"] == 1
    monkeypatch.setattr(runner.mvs_mod, "grade_mvs", boom)
    monkeypatch.setattr(runner.grader_mod, "GRADES_MVS", False, raising=False)
    s = runner.grade_output(mvs, '{"root": {}}')
    assert s["f1"] == 0.0 and s["outcome"] == "not_mvs" and s["grader_crash"]


# --- the grader entry point --------------------------------------------------------

def test_api_answers_go_through_grade_task_so_accepted_alternatives_count():
    tasks = [t for t in runner.load_tasks(["api_calling"]) if t["accepted"]]
    assert tasks
    for t in tasks:
        for alt in t["accepted"]:
            s = runner.grade_output(t, json.dumps(alt))
            assert s["f1"] == 1.0 and runner.is_success(s) and s["grader"] == "state", t["id"]


def test_an_api_answer_not_graded_by_the_state_grader_stops_the_grading(corpus, monkeypatch):
    """No silent fallback to the old sequence grader: it is a different kind of score."""
    api = next(t for t in corpus if t["category"] == "api_calling")
    monkeypatch.setattr(runner.grader_mod, "grade_task",
                        lambda task, pred: {"f1": 1.0, "success": True, "grader": "sequence"})
    with pytest.raises(runner.GradingError, match="not by the final-state grader"):
        runner.grade_output(api, json.dumps(api["reference"]))


def test_a_task_without_an_atom_table_is_refused_before_the_run(corpus):
    m = _manifest()
    ghost = {**corpus[0], "id": "ghost", "structures": ["9zzz"]}
    with pytest.raises(runner.GradingError, match="no atom table for \\['9zzz'\\]"):
        runner.build_plan(m, corpus + [ghost], m.panel())


def test_a_reference_that_does_not_grade_itself_stops_the_grading(tmp_path, corpus, monkeypatch):
    m, cells, archive, _ = _run(tmp_path, corpus[:1])
    monkeypatch.setattr(runner.grader_mod, "grade_task",
                        lambda task, pred: {"f1": 0.5, "success": False, "grader": "state"})
    with pytest.raises(runner.GradingError, match="own reference does not grade"):
        runner.grade_archive(cells, archive.load(), "off", log=lambda s: None)


def test_grader_extras_are_carried_and_a_target_score_reaches_the_scorecard(tmp_path, corpus,
                                                                             monkeypatch):
    """The grader may return more than f1: success, target_f1, outcome, grader. An
    unparseable answer gets target 0 when the grader reports targets for the task."""
    api = [t for t in corpus if t["category"] == "api_calling"][:1]
    m, cells, archive, _ = _run(tmp_path, api)
    real = runner.grader_mod.grade_task

    def with_target(task, pred):
        res = real(task, pred)
        return {**res, "target_f1": 1.0 if res["success"] else 0.25, "extra_key": "ignored"}

    monkeypatch.setattr(runner.grader_mod, "grade_task", with_target)
    graded, _ = runner.grade_archive(cells, archive.load(), "off", log=lambda s: None)
    samples = [s for per in graded.values() for got in per.values() for s in got]
    assert all(runner.target_score(s) is not None for s in samples)
    assert all(s["target_f1"] == 0.0 for s in samples if s["outcome"] == "invalid_json")
    cards = runner.write_scorecards(m, cells, graded, False, tmp_path / "cards", {})
    rec = json.loads(cards[0].read_text())["models"]
    rec = next(iter(rec.values()))
    assert rec["target_f1"] is not None and rec["by_category"]["api_calling"]["target_f1"] is not None
    assert rec["tasks"][0]["target_f1"] is not None


def test_the_grader_is_handed_the_target_in_its_own_form(fixtures, monkeypatch):
    """TASK_FORMAT.md writes a target as a list of parts; the grader reads one object.
    A list handed over as it is would be ignored without a word."""
    seen = []

    def fake(task, pred):
        seen.append(task)
        return {"f1": 1.0, "success": True, "target_f1": 1.0, "grader": "state"}

    monkeypatch.setattr(runner.grader_mod, "grade_task", fake)
    monkeypatch.setattr(runner.grader_mod, "GRADES_MVS", True, raising=False)
    for t in fixtures:
        if t["target"] and not t.get("accepted_targets"):
            runner.grade_parsed(t, t["reference"])
            got = seen[-1]
            assert got["target"] == {"selector": t["target"][0]["selector"]}, t["id"]
            assert got["accepted"] == t["accepted"] and "accepted_targets" not in got
            assert isinstance(t["target"], list)  # the loaded task itself is not changed
    one = fixtures[0]
    parts = [{"selector": {"label_asym_id": "A"}}, {"selector": [{"label_asym_id": "B"}]}]
    assert runner.grader_target(one, parts) == {
        "selector": [{"label_asym_id": "A"}, {"label_asym_id": "B"}]}
    assert runner.grader_target(one, None) is None
    assert runner.grader_target(one, {"selector": "polymer"}) == {"selector": "polymer"}
    two = {**one, "structures": ["1cbs", "1stp"]}
    assert runner.grader_target(two, [{"selector": "ligand", "structure": "1stp"}]) == {
        "selector": "ligand", "entry": "1stp"}
    for bad in ([{"selector": "polymer"}, {"selector": {"label_asym_id": "A"}}],
                [{"selector": "ligand", "structure": "1cbs"},
                 {"selector": "ligand", "structure": "1stp"}]):
        with pytest.raises(runner.GradingError, match="cannot be handed to the grader"):
            runner.grader_target(two, bad)


def test_each_accepted_alternative_is_graded_with_its_own_target(fixtures, monkeypatch):
    """"Either copy will do": the second copy is right on its own target, not scored 0
    on the first copy's."""
    task = next(t for t in fixtures if t.get("accepted_targets"))

    def fake(t, pred):  # right only against the reference it is handed, like a grader
        assert t["accepted"] == [] and isinstance(t["target"], dict)
        hit = t["reference"] == pred
        return {"f1": float(hit), "success": hit, "grader": "state",
                "target_f1": float(hit), "seen_target": t["target"]}

    monkeypatch.setattr(runner.grader_mod, "grade_task", fake)
    monkeypatch.setattr(runner.grader_mod, "GRADES_MVS", True, raising=False)
    for i, state in enumerate([task["reference"]] + task["accepted"]):
        res = runner.grade_parsed(task, state)
        want = (task["target"] if i == 0 else task["accepted_targets"][i - 1])[0]["selector"]
        assert res["success"] and res["target_f1"] == 1.0 and res["matched_reference"] == i
        assert res["seen_target"] == {"selector": want}


def test_task_success_is_reported_as_the_mean_and_as_all_samples_right():
    def sample(f1, success, finish="stop", outcome="valid"):
        return {"f1": f1, "success": success, "finish_reason": finish, "outcome": outcome}
    mixed = runner._aggregate([sample(1.0, True), sample(1.0, True), sample(0.4, False)])
    assert mixed["success"] == round(2 / 3, 4) and mixed["success_all"] is False
    assert mixed["target_f1"] is None                       # the grader reported none
    clean = runner._aggregate([{**sample(1.0, True), "target_f1": 1.0}] * 3)
    assert clean["success"] == 1.0 and clean["success_all"] is True and clean["target_f1"] == 1.0


def test_truncation_is_counted_apart_from_malformed_output():
    cut = {"f1": 0.0, "outcome": "invalid_json", "finish_reason": "length"}
    cut_anthropic = {"f1": 0.0, "outcome": "invalid_json", "finish_reason": "max_tokens"}
    garbled = {"f1": 0.0, "outcome": "invalid_json", "finish_reason": "stop"}
    wrong = {"f1": 0.0, "outcome": "invalid_api", "finish_reason": "stop"}
    fine = {"f1": 1.0, "outcome": "valid", "finish_reason": "stop"}
    stats = runner._track_stats([cut, cut_anthropic, garbled, wrong, fine], "api_calling", False)
    assert stats["n_truncated"] == 2
    assert stats["not_valid"] == {"truncated": 2, "malformed": 2}
    assert stats["valid_rate"] == 0.2                       # the API valid-output rate


# --- follow-up turns, accept sets, twins, paraphrases, the held-back split ----------

@pytest.fixture(scope="module")
def fixtures():
    return runner.tasks_mod.load_corpus(runner.FIXTURE_TASKS)


def test_fixture_tasks_cover_every_special_kind_on_both_tracks(fixtures):
    kinds = runner.kinds_present(fixtures)
    assert set(kinds) == {"follow-up", "follow-up with no change", "accept-set", "twin",
                          "paraphrase", "held-back"}
    assert all(n >= 1 for per in kinds.values() for n in per.values()), kinds
    tasks, added = runner.with_fixtures(runner.load_tasks(list(mf.TRACKS)))
    assert added in (0, len(fixtures))    # added only while the corpus lacks a kind


def test_a_follow_up_shows_the_start_state_then_the_request(fixtures):
    for t in (x for x in fixtures if x["context"]):
        user = runner.user_message(t)
        head, _, request = user.partition("\n\nRequest: ")
        assert request == t["prompt"]
        label, _, state = head.partition("\n")
        if t["category"] == "mvs":
            assert label == "Current scene (MolViewSpec JSON):"
            assert set(json.loads(state)) == {"root"}       # the form the answer must take
            assert runner.grade_parsed({**t, "reference": t["context"]["scene"]},
                                       json.loads(state))["f1"] == 1.0
        else:
            assert label == "Calls made so far (JSON array):"
            assert json.loads(state) == t["context"]["calls"]
    single = next(x for x in fixtures if not x["context"])
    assert runner.user_message(single) == single["prompt"]


def test_no_change_is_the_right_answer_to_a_no_op_follow_up(fixtures):
    for t in (x for x in fixtures if x["context"]):
        start = runner.start_state(t)
        unchanged = runner.grade_output(t, json.dumps(start))
        assert runner.is_success(unchanged) == t["context"]["noop"], t["id"]
        assert runner.is_success(runner.grade_output(t, json.dumps(t["reference"])))


def test_every_accepted_alternative_is_exactly_right(fixtures):
    for t in (x for x in fixtures if x["accepted"]):
        for alt in t["accepted"]:
            s = runner.grade_output(t, json.dumps(alt))
            assert s["f1"] == 1.0 and runner.is_success(s) and s["matched_reference"] == 1


def test_system_prompts_frame_follow_ups_and_keep_the_worked_example_out_of_the_tasks():
    prompts = runner.build_system_prompts("spec")
    bare = runner.build_system_prompts("bare")
    for text in (prompts["api_calling"], prompts["mvs"], bare["mvs"]):
        assert "## Follow-up requests" in text and "{{" not in text.split("## MVS reference")[0]
    api = prompts["api_calling"]
    assert runner.schema.schema_text() in api               # the compact action list
    assert '"$schema"' not in api                           # not the long JSON Schema
    assert "pdbe-molstar 3.3.2" in api and "1HSG" in api
    used = {s for t in runner.load_tasks(list(mf.TRACKS)) for s in t["structures"]}
    assert "1hsg" not in used


def test_the_keyword_baseline_answers_both_tracks_and_echoes_a_follow_up(fixtures):
    baseline, prompts = build_model("baseline"), runner.build_system_prompts("spec")
    for t in fixtures:
        raw = baseline.generate(prompts[t["category"]], runner.user_message(t))
        s = runner.grade_output(t, raw)
        assert s["outcome"] in ("valid", "unchecked"), (t["id"], raw)
        if t["context"]:                                    # doing nothing, scored as such
            assert json.loads(raw) == runner.start_state(t)
            assert runner.is_success(s) == t["context"]["noop"]


# --- the archive lock and the per-sample records ------------------------------------

def test_two_runs_cannot_write_one_archive(tmp_path, corpus):
    m = _manifest()
    cells = runner.build_plan(m, corpus[:1], m.panel())
    first, second = runner.RunArchive(tmp_path / "arch"), runner.RunArchive(tmp_path / "arch")
    first.open(m, "corpus-sha", mock=True)
    with first.exclusive():
        with first.exclusive():                             # re-entrant for its holder
            pass
        with pytest.raises(mf.ManifestError, match="being written by another run"):
            runner.generate(m, cells, _mocks(m), second, CALIB, log=lambda s: None)
        assert second.load() == {}                          # nothing was archived
    stats = runner.generate(m, cells, _mocks(m), second, CALIB, log=lambda s: None)
    assert stats["called"] == len(cells)                    # free again once released


def test_a_record_per_sample_with_call_and_grade_together(tmp_path, corpus):
    m, cells, archive, _ = _run(tmp_path, corpus)
    graded, _ = runner.grade_archive(cells, archive.load(), "off", log=lambda s: None)
    files = runner.write_sample_records(cells, graded, tmp_path / "out")
    rows = [json.loads(line) for f in files for line in f.read_text().splitlines()]
    assert len(rows) == len(cells)
    assert sorted(f.relative_to(tmp_path / "out").as_posix() for f in files)[0] == \
        "samples/bare/mock_plain.jsonl"
    records = archive.load()
    for row in rows:
        assert tuple(row) == runner.SAMPLE_RECORD_FIELDS
        raw = records[(row["model"], row["condition"], row["task_id"], row["sample"])]
        assert row["raw"] == raw["raw"] and row["prompt_sha256"] == raw["prompt_sha256"]
        assert row["temperature"] == "provider-default" and row["max_tokens"] == 4000
        assert row["provider"] == "mock" and row["finish_reason"] in ("stop", "length")
        assert row["truncated"] == (row["finish_reason"] == "length")
        assert isinstance(row["success"], bool) and row["input_tokens"] > 0
        assert row["cost_usd"] is not None and row["latency_s"] is not None
        assert (row["predicted"] is None) == (row["outcome"] == "invalid_json")
        assert row["tier"] and row["split"] == "public"


def test_invalidating_a_scene_clears_a_grader_supplied_success():
    s = {"f1": 1.0, "success": True, "outcome": "unchecked"}
    runner._invalidate(s, "invalid_mvs", ["bad node"])
    assert s["f1"] == 0.0 and not runner.is_success(s)


# --- the mock model ----------------------------------------------------------------

def test_mock_model_is_deterministic_and_costs_nothing(corpus):
    task = corpus[0]
    ctx = {"task": task, "task_id": task["id"], "sample": 1, "condition": "spec"}
    a = MockModel("m", seed=3).complete("sys", "user", context=ctx)
    b = MockModel("m", seed=3).complete("sys", "user", context=ctx)
    assert (a.text, a.finish_reason, a.input_tokens) == (b.text, b.finish_reason, b.input_tokens)
    assert a.cost_usd is None and a.latency_s == 0.0
    assert isinstance(build_model("mock:anything"), MockModel)


def test_mock_model_produces_every_kind_of_reply(corpus):
    mvs = next(t for t in corpus if t["category"] == "mvs")
    model = MockModel("m")
    kinds = {model.reply(mvs, f"spec|{mvs['id']}|{i}")[0] for i in range(400)}
    assert kinds == {"reference", "fenced", "perturbed", "truncated", "malformed", "prose",
                     "wrong_shape", "empty"}


def test_perturbed_reference_is_a_near_miss_not_a_copy(corpus):
    for task in corpus:
        ref = task.get("reference_mvs", task.get("reference"))
        near = perturb_reference(ref)
        assert near != ref and type(near) is type(ref)
        assert task.get("reference_mvs", task.get("reference")) == ref  # input untouched


# --- grading -----------------------------------------------------------------------

def test_outcomes_on_both_tracks(corpus):
    api = next(t for t in corpus if t["category"] == "api_calling")
    mvs = next(t for t in corpus if t["category"] == "mvs")
    good = runner.grade_output(api, json.dumps(api["reference"]))
    assert good["outcome"] == "valid" and good["f1"] == 1.0 and runner.is_success(good)
    wrapped = runner.grade_output(api, json.dumps({"actions": api["reference"]}))
    assert wrapped["outcome"] == "valid" and wrapped["f1"] == 1.0    # JSON-mode shape
    assert runner.grade_output(api, "Sorry, I cannot.")["outcome"] == "invalid_json"
    assert runner.grade_output(api, '[{"action": "no_such_action"}]')["outcome"] == "invalid_api"
    assert runner.grade_output(mvs, json.dumps(mvs["reference_mvs"]))["outcome"] == "unchecked"
    assert runner.grade_output(mvs, '{"answer": 1}')["outcome"] == "not_mvs"
    assert runner.grade_output(mvs, "")["outcome"] == "invalid_json"


def test_a_near_miss_is_never_a_success_and_usually_earns_partial_credit():
    """The state grader scores the *changes* an answer makes to a bare load. A near miss
    that keeps some of them earns partial credit; one that drops the only change the
    task asks for (api-001: load, hide water -> load) has no fact left and scores 0."""
    partial = 0
    tasks = runner.load_tasks(["api_calling"])
    for t in tasks:
        near = runner.grade_output(t, json.dumps(perturb_reference(t["reference"])))
        assert near["outcome"] == "valid" and near["f1"] < 1 and not runner.is_success(near), t["id"]
        partial += 0 < near["f1"]
    assert partial >= len(tasks) - 2
    lost = next(t for t in tasks if len(t["reference"]) == 2
                and t["reference"][1].get("name") == "hide_water")
    assert runner.grade_output(lost, json.dumps(lost["reference"][:1]))["f1"] == 0.0


def test_api_tasks_report_their_skills():
    """API tasks call the field 'skills', MVS tasks 'categories'; both reach the scorecard."""
    report, _ = runner.run(["baseline"], ["api_calling"])
    m = report["models"]["baseline-rules"]
    tasks = {t["id"]: t for t in runner.load_tasks(["api_calling"])}
    for t in m["tasks"]:
        assert t["categories"] == tasks[t["id"]]["skills"] != []
    assert m["by_skill"] and "load" in m["by_skill"]


def test_json_repair_counterfactual_is_recorded_but_never_scored(corpus):
    pytest.importorskip("json_repair")
    for task in (next(t for t in corpus if t["category"] == "mvs"),
                 next(t for t in corpus if t["category"] == "api_calling")):
        whole = json.dumps(task.get("reference_mvs", task.get("reference")))
        cut = runner.grade_output(task, whole.rstrip("]}"))  # closing brackets lost
        assert cut["outcome"] == "invalid_json" and cut["f1"] == 0.0
        fixed = runner.repair_counterfactual(task, cut)
        assert fixed["f1"] == 1.0 and fixed["outcome"] in ("valid", "unchecked")
        assert cut["f1"] == 0.0                              # the strict score is untouched
        assert runner.repair_counterfactual(task, runner.grade_output(task, whole)) is None
        assert runner.repair_counterfactual(task, runner.grade_output(task, "no json here")) is None


def test_grading_reads_only_the_archive(tmp_path, corpus):
    m, cells, archive, _ = _run(tmp_path, corpus)
    graded, validated = runner.grade_archive(cells, archive.load(), "off", log=lambda s: None)
    assert not validated
    assert sum(len(got) for per in graded.values() for got in per.values()) == len(cells)
    samples = [s for per in graded.values() for got in per.values() for s in got]
    assert {s["outcome"] for s in samples} >= {"unchecked", "invalid_json", "valid"}
    assert any("repair" in s for s in samples)
    assert all(s["finish_reason"] and "input_tokens" in s["usage"] for s in samples)
    again, _ = runner.grade_archive(cells, archive.load(), "off", log=lambda s: None)
    assert again == graded


def test_validation_required_fails_loudly_without_molstar(monkeypatch, corpus):
    from molbench import render

    def missing(scenes):
        raise RuntimeError("Mol* bundle missing")
    monkeypatch.setattr(render, "molstar_issues", missing)
    mvs = next(t for t in corpus if t["category"] == "mvs")
    sample = lambda: [runner.grade_output(mvs, json.dumps(mvs["reference_mvs"]))]
    with pytest.raises(mf.ManifestError, match="Mol\\* validation is required"):
        runner.validate_all(sample(), "required")
    got = sample()
    assert runner.validate_all(got, "auto", log=lambda s: None) is False
    assert got[0]["outcome"] == "unchecked"   # no validity is claimed

    # Playwright installed without its browser raises its own error class.
    NoBrowser = type("Error", (Exception,), {"__module__": "playwright._impl._errors"})

    def no_browser(scenes):
        raise NoBrowser("BrowserType.launch: Executable doesn't exist")
    monkeypatch.setattr(render, "molstar_issues", no_browser)
    with pytest.raises(mf.ManifestError, match="Mol\\* validation is required"):
        runner.validate_all(sample(), "required")
    assert runner.validate_all(sample(), "auto", log=lambda s: None) is False

    def bug(scenes):  # anything else is a real failure and is not swallowed
        raise KeyError("x")
    monkeypatch.setattr(render, "molstar_issues", bug)
    with pytest.raises(KeyError):
        runner.validate_all(sample(), "auto", log=lambda s: None)


def test_validated_scenes_and_repairs_get_molstar_outcomes(monkeypatch, tmp_path, corpus):
    from molbench import render
    monkeypatch.setattr(render, "molstar_issues", lambda scenes: [[] for _ in scenes])
    m, cells, archive, _ = _run(tmp_path, corpus)
    graded, validated = runner.grade_archive(cells, archive.load(), "required", log=lambda s: None)
    samples = [s for per in graded.values() for got in per.values() for s in got]
    assert validated and not any(s["outcome"] == "unchecked" for s in samples)
    assert not any(s["repair"]["outcome"] == "unchecked" for s in samples if "repair" in s)


# --- scorecards --------------------------------------------------------------------

def test_scorecards_report_strict_success_validity_and_repair(monkeypatch, tmp_path, corpus):
    from molbench import render
    monkeypatch.setattr(render, "molstar_issues", lambda scenes: [[] for _ in scenes])
    m, cells, archive, _ = _run(tmp_path, corpus)
    graded, validated = runner.grade_archive(cells, archive.load(), "required", log=lambda s: None)
    out = tmp_path / "cards"
    written = runner.write_scorecards(m, cells, graded, validated, out, {"run_name": "t"})
    assert sorted(p.relative_to(out).as_posix() for p in written) == [
        "bare/mock_plain.json", "spec/mock_json-mode.json", "spec/mock_plain.json",
        "spec_grounded/mock_json-mode.json", "spec_grounded/mock_plain.json",
        "spec_structured/mock_json-mode.json"]
    card = json.loads((out / "spec" / "mock_plain.json").read_text())
    assert card["n_tasks"] == 8 and card["samples"] == 2
    assert card["meta"]["complete"] and card["meta"]["cells_archived"] == 16
    rec = card["models"]["plain"]
    assert rec["spec"] == "mock:plain" and rec["usage"]["calls"] == 16 and rec["cost_usd"] > 0
    for track, n in (("mvs", 5), ("api_calling", 3)):
        d = rec["by_category"][track]
        assert d["n"] == n and d["n_samples"] == 2 * n
        assert sum(d["outcomes"].values()) == 2 * n
        assert d["strict_f1"] <= d["repair_f1"] <= 1.0   # repair can only add points
        assert 0.0 <= d["success"] <= d["strict_f1"] <= 1.0  # exactly right <= partly right
        assert "valid_rate" in d and sum(d["finish_reasons"].values()) == 2 * n
        assert 0.0 <= d["success_all"] <= d["success_tasks"] <= 1.0   # all samples <= mean
        assert sum(d["not_valid"].values()) == 2 * n - d["outcomes"]["valid"]
        assert sum(g["n_tasks"] for g in d["by_tier"].values()) == n
        assert d["by_split"]["public"]["n_tasks"] == n
    assert set(rec["outcomes"]) == set(runner.OUTCOMES)   # the scene stats stay MVS-only
    assert sum(rec["outcomes"].values()) == 10
    task = rec["tasks"][0]
    assert len(task["samples"]) == 2 and {"f1", "outcome", "success", "target_f1", "finish_reason",
                                          "truncated"} <= set(task["samples"][0])
    assert {"tier", "family", "structures", "split", "cluster", "success_all"} <= set(task)
    assert 0.0 <= rec["success_all"] <= rec["success"] <= 1.0
    assert task["categories"]                              # skills, on either track


def test_partial_archive_gives_an_incomplete_scorecard(tmp_path, corpus):
    m, cells, archive, _ = _run(tmp_path, corpus, stop_after=10)
    graded, validated = runner.grade_archive(cells, archive.load(), "off", log=lambda s: None)
    written = runner.write_scorecards(m, cells, graded, validated, tmp_path / "cards", {})
    cards = [json.loads(p.read_text()) for p in written]
    assert cards and not any(c["meta"]["complete"] for c in cards)


# --- cost projection ---------------------------------------------------------------

def _estimate_cost():
    spec = importlib.util.spec_from_file_location("estimate_cost", REPO / "scripts" / "estimate_cost.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_projection_uses_real_prompt_lengths_and_manifest_prices(corpus):
    m = _manifest()
    cells = runner.build_plan(m, corpus, m.panel())
    rows = {(r["model"], r["condition"]): r for r in runner.project_costs(m, cells, CALIB)}
    r = rows[("plain", "bare")]
    mine = [c for c in cells if c.key[:2] == ("plain", "bare")]
    assert r["calls"] == len(mine)
    assert r["input_tokens"] == sum(round((len(c.system) + len(c.user)) / 4.0) for c in mine)
    assert r["cost_usd"] == pytest.approx((r["input_tokens"] * 1.0 + r["output_tokens"] * 2.0) / 1e6)
    assert r["worst_cost_usd"] > r["cost_usd"]            # every call at its token limit
    assert rows[("plain", "spec")]["input_tokens"] / 16 > r["input_tokens"] / 10  # spec is longer


def test_cost_scales_with_a_planned_corpus_size():
    ec = _estimate_cost()
    m = mf.load_manifest(REPO / "run" / "final_run.toml")
    calib = mf.Calibration.load()
    tasks = runner.load_tasks(list(mf.TRACKS))
    now, info = ec.estimate(m, calib, tasks, include_optional=False)
    n = info["tasks_now"]
    double, info2 = ec.estimate(m, calib, tasks, False,
                                {"mvs": 2 * n["mvs"], "api_calling": 2 * n["api_calling"]})
    total = lambda rows: sum(r["cost_usd"] for r in rows)
    assert total(double) == pytest.approx(2 * total(now), rel=1e-6)
    assert info2["cells"] == 2 * info["cells"]
    more_api, _ = ec.estimate(m, calib, tasks, False, {"api_calling": 3 * n["api_calling"]})
    assert total(now) < total(more_api) < total(double) * 1.5


# --- the command -------------------------------------------------------------------

def _write_manifest(tmp_path, text=MANIFEST):
    path = tmp_path / "run.toml"
    path.write_text(text)
    return path


def _argv(tmp_path, *extra):
    return ["--manifest", str(_write_manifest(tmp_path)), "--runs-dir", str(tmp_path / "runs"),
            "--results-dir", str(tmp_path / "results"), *extra]


def test_dry_run_exercises_the_whole_pipeline_for_nothing(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(runner, "build_model",
                        lambda spec: pytest.fail("a dry run must not build a real model"))
    with pytest.raises(SystemExit) as e:
        runner.main(_argv(tmp_path, "--dry-run"))
    out = capsys.readouterr().out
    assert e.value.code == 0, out
    assert "DRY RUN PASSED" in out and "[FAIL]" not in out
    assert "Projected cost of the real run" in out
    assert "fixture tasks" in out and "follow-up: " in out   # every task kind is rehearsed
    arch, res = tmp_path / "runs" / "t.dryrun", tmp_path / "results" / "t.dryrun"
    assert (arch / "DRYRUN").exists() and json.loads((arch / "run.json").read_text())["mock"]
    n_cells = sum(len(p.read_text().splitlines()) for p in (arch / "cells").rglob("*.jsonl"))
    assert n_cells > 500   # the whole corpus x both models x every condition
    assert (res / "spec" / "mock_plain.json").exists()
    assert (res / "samples" / "spec" / "mock_plain.jsonl").exists()
    site = res / "site"
    for name in ("scorecard.json", "conditions_data.json", "failures_data.json",
                 "index.html", "failures.html"):
        assert (site / name).stat().st_size > 0, name
    card = json.loads((site / "scorecard.json").read_text())
    assert card["meta"]["run"]["mock"] is True and set(card["models"]) == {"plain", "json/mode"}
    assert card["meta"]["api_track"]["same_run"] and card["meta"]["api_track"]["n_tasks"] > 0
    page = (site / "index.html").read_text()
    assert "DRY RUN" in page                               # the page says it is mock data
    # Task success (both ways), the target score and the API valid-output rate reach the
    # site data, and the leaderboard shows success under the F1.
    for rec in card["models"].values():
        assert {"success", "success_all", "target_f1"} <= set(rec)
        assert rec["by_category"]["api_calling"]["valid_rate"] is not None
        assert "followup" in rec["by_category"]["mvs"]["by_tier"]      # fixtures were run
        assert "heldback" in rec["by_category"]["api_calling"]["by_split"]
    assert "% right</span>" in page and "truncated at the token limit" in page
    fails = json.loads((site / "failures_data.json").read_text())
    assert '"truncated": true' in json.dumps(fails)
    # Run it again: a dry run starts from empty and never touches a real archive.
    with pytest.raises(SystemExit) as e:
        runner.main(_argv(tmp_path, "--dry-run", "--no-site"))
    assert e.value.code == 0


def test_dry_run_will_not_delete_a_directory_it_did_not_make(tmp_path):
    (tmp_path / "runs" / "t.dryrun").mkdir(parents=True)
    (tmp_path / "runs" / "t.dryrun" / "precious.txt").write_text("keep")
    with pytest.raises(SystemExit) as e:
        runner.main(_argv(tmp_path, "--dry-run"))
    assert "not a dry-run directory" in str(e.value.code)
    assert (tmp_path / "runs" / "t.dryrun" / "precious.txt").exists()


def test_without_go_nothing_is_called(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(runner, "build_model", lambda spec: pytest.fail("no model without --go"))
    with pytest.raises(SystemExit) as e:
        runner.main(_argv(tmp_path))
    out = capsys.readouterr().out
    assert e.value.code == 0 and "No model was called" in out
    assert not (tmp_path / "runs").exists()


def test_go_refuses_an_unpinned_corpus_before_building_any_model(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "build_model", lambda spec: pytest.fail("refuse first"))
    monkeypatch.setattr(runner, "load_dotenv", lambda *a: pytest.fail("no keys are read"))
    with pytest.raises(SystemExit) as e:
        runner.main(_argv(tmp_path, "--go"))
    assert "corpus.sha256 is empty" in str(e.value.code)
    assert not (tmp_path / "runs").exists()


def test_go_refuses_a_corpus_with_a_problem_before_any_call(tmp_path, monkeypatch):
    """A task that cannot be graded as right stops the paid run before its first call,
    not when the archive is graded."""
    monkeypatch.setattr(runner, "build_model", lambda spec: pytest.fail("refuse first"))
    monkeypatch.setattr(runner, "load_dotenv", lambda *a: pytest.fail("no keys are read"))
    monkeypatch.setattr(runner, "corpus_problems",
                        lambda tasks: ["api-001: its own reference does not grade as exactly right"])
    sha = mf.corpus_hash(runner.TASKS_DIR)
    path = _write_manifest(tmp_path, MANIFEST.replace(
        'version = "v-test"', f'version = "v-test"\nsha256 = "{sha}"'))
    with pytest.raises(SystemExit) as e:
        runner.main(["--manifest", str(path), "--runs-dir", str(tmp_path / "runs"),
                     "--results-dir", str(tmp_path / "results"), "--go",
                     "--allow-unverified-prices"])
    assert "the corpus has 1 problem(s)" in str(e.value.code) and "api-001" in str(e.value.code)
    assert not (tmp_path / "runs").exists()


def test_corpus_problems_finds_a_reference_that_is_not_right(corpus):
    assert runner.corpus_problems(corpus) == []
    broken = [dict(t) for t in corpus]
    api = next(t for t in broken if t["category"] == "api_calling" and t.get("accepted"))
    api["twin_of"] = "no-such-task"
    assert any("twin_of 'no-such-task' is not a task" in p for p in runner.corpus_problems(broken))


def test_go_refuses_unverified_prices(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "build_model", lambda spec: pytest.fail("refuse first"))
    monkeypatch.setattr(runner, "load_dotenv", lambda *a: None)
    sha = mf.corpus_hash(runner.TASKS_DIR)
    path = _write_manifest(tmp_path, MANIFEST.replace(
        'version = "v-test"', f'version = "v-test"\nsha256 = "{sha}"'))
    with pytest.raises(SystemExit) as e:
        runner.main(["--manifest", str(path), "--runs-dir", str(tmp_path / "runs"),
                     "--results-dir", str(tmp_path / "results"), "--go"])
    assert "unverified price" in str(e.value.code)
    assert not (tmp_path / "runs").exists()


def test_go_then_grade_only_with_mock_routes(tmp_path, monkeypatch, capsys):
    """The paid path end to end - with routes that resolve to the mock model."""
    monkeypatch.setattr(runner, "load_dotenv", lambda *a: None)
    sha = mf.corpus_hash(runner.TASKS_DIR)
    path = _write_manifest(tmp_path, MANIFEST.replace(
        'version = "v-test"', f'version = "v-test"\nsha256 = "{sha}"'))
    argv = ["--manifest", str(path), "--runs-dir", str(tmp_path / "runs"),
            "--results-dir", str(tmp_path / "results"), "--no-site",
            "--allow-unverified-prices"]
    with pytest.raises(SystemExit) as e:
        runner.main(argv + ["--go"])
    assert e.value.code == 0
    assert not (tmp_path / "runs" / "t" / "errors.jsonl").exists()
    card = tmp_path / "results" / "t" / "spec" / "mock_plain.json"
    first = json.loads(card.read_text())
    card.unlink()
    with pytest.raises(SystemExit) as e:
        runner.main(argv + ["--grade-only"])
    assert e.value.code == 0
    again = json.loads(card.read_text())
    assert again["models"]["plain"]["tasks"] == first["models"]["plain"]["tasks"]
    with pytest.raises(SystemExit) as e:   # a second --go finds everything archived
        runner.main(argv + ["--go"])
    assert e.value.code == 0 and "0 to run" in capsys.readouterr().out


def test_preflight_names_missing_keys_and_missing_molstar(monkeypatch):
    for env in set(runner.KEY_ENV.values()):
        monkeypatch.delenv(env, raising=False)
    m = mf.load_manifest(REPO / "run" / "final_run.toml")
    problems = runner.preflight(m, m.panel())
    assert "ANTHROPIC_API_KEY is not set" in problems and "OPENROUTER_API_KEY is not set" in problems
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setenv("OPENROUTER_API_KEY", "x")
    monkeypatch.setattr(runner.importlib.util, "find_spec", lambda name: None)
    assert any("playwright" in p for p in runner.preflight(m, m.panel()))
    mock_only = _manifest()   # mock routes, validate = "off": nothing to check
    assert runner.preflight(mock_only, mock_only.panel()) == []


# --- October data (only where the raw archives are) ---------------------------------

OCTOBER = pathlib.Path(os.environ.get("MOLBENCH_DATA", REPO))


@pytest.mark.skipif(not (OCTOBER / "results" / "r2x2" / "spec").exists(),
                    reason="needs the git-ignored October scorecards and run archives "
                           "(set MOLBENCH_DATA to the checkout that has results/ and runs/)")
def test_october_site_data_still_reproduces(tmp_path):
    """De-hard-coding must not change the published data files (except the two keys
    the failures page now reads instead of hard-coding)."""
    import shutil
    spec = importlib.util.spec_from_file_location("bsd", REPO / "scripts" / "build_site_data.py")
    sd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sd)
    docs = tmp_path / "docs"
    docs.mkdir()
    shutil.copyfile(REPO / "docs" / "scorecard.json", docs / "scorecard.json")
    sd.main(["--results", str(OCTOBER / "results" / "r2x2"), "--runs", str(OCTOBER / "runs"),
             "--docs", str(docs)])
    for name in ("scorecard.json", "escalation_data.json", "gallery_data.json",
                 "conditions_data.json"):
        assert (docs / name).read_bytes() == (REPO / "docs" / name).read_bytes(), name
    new = json.loads((docs / "failures_data.json").read_text())
    assert (new.pop("samples"), new.pop("n_tasks")) == (1, 70)
    assert new == json.loads((REPO / "docs" / "failures_data.json").read_text())
