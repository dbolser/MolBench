"""The paper pipeline: scripts/paper_tables.py and paper/build.py.

Three layers:

* a tiny synthetic run (built in a temp dir) exercises the whole of paper_tables.py, so the
  test runs anywhere, with no archives;
* the October archives, if this machine has them (results/ and runs/ are git-ignored), are
  run through the same code and compared with the committed paper/generated/values.json;
* paper/build.py must resolve every value key and citation in the committed paper.
"""

import importlib.util
import json
import pathlib
import re
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


pt = _load("paper_tables", REPO / "scripts" / "paper_tables.py")
pb = _load("paper_build", REPO / "paper" / "build.py")


# --------------------------------------------------------------------------- #
# A synthetic run
# --------------------------------------------------------------------------- #
def _scene(entry, selector="polymer", colour=None):
    rep = {"kind": "representation", "params": {"type": "cartoon"}}
    if colour:
        rep["children"] = [{"kind": "color", "params": {"color": colour}}]
    return {"root": {"kind": "root", "children": [
        {"kind": "download", "params": {"url": f"https://files.rcsb.org/download/{entry}.cif"},
         "children": [{"kind": "parse", "params": {"format": "mmcif"}, "children": [
             {"kind": "structure", "params": {"type": "model"}, "children": [
                 {"kind": "component", "params": {"selector": selector}, "children": [rep]}]}]}]}]}}


TASKS = {  # id -> (source, entry)
    "t-a1": ("generated", "1abc"), "t-a2": ("generated", "1abc"),
    "t-b1": ("generated", "2xyz"), "t-c1": ("clinvar-variant", "3pqr"),
    "t-d1": ("resolve", "4stu"), "t-e1": ("brand-new-tier", "5vwx"),
}


def _row(tid, f1s, outcomes, predicted=None, error=None):
    return {"id": tid, "category": "mvs", "f1": sum(f1s) / len(f1s), "samples_f1": f1s,
            "outcomes": outcomes, "outcome": outcomes[0], "n_samples": len(f1s),
            "predicted": predicted, "error": error}


def _card(model, condition, grounding, rows, run_id, cost=None):
    return {"n_tasks": len(rows), "samples": 2,
            "meta": {"condition": condition, "grounding": grounding, "run_id": run_id},
            "models": {model: {"spec": f"mock:{model}", "tasks": rows, "cost_usd": cost,
                               "usage": {"input_tokens": 1000, "output_tokens": 200, "calls": 12}}}}


@pytest.fixture()
def synthetic(tmp_path):
    tdir = tmp_path / "tasks" / "mvs"
    tdir.mkdir(parents=True)
    for tid, (source, entry) in TASKS.items():
        (tdir / f"{tid}.json").write_text(json.dumps({
            "id": tid, "category": "mvs", "source": source, "prompt": "show it",
            "reference_mvs": _scene(entry)}))
    broken = json.dumps(_scene("1abc"))[:-1]          # one closing brace short
    for model, good in (("vendor/model-good", True), ("model-weak", False)):
        for cond, grounding in (("spec", False), ("spec", True), ("bare", False)):
            rows, raws = [], {}
            for tid, (_, entry) in TASKS.items():
                if cond == "bare":
                    rows.append(_row(tid, [0.0, 0.0], ["invalid_mvs", "invalid_mvs"]))
                elif not good and tid == "t-a1":
                    rows.append(_row(tid, [0.0, 0.0], ["invalid_json", "invalid_json"],
                                     error="JSON parse error: Expecting ',' delimiter: "
                                           "line 1 column 9 (char 8)"))
                    raws[tid] = [{"raw": broken}, {"raw": ""}]
                elif tid == "t-c1":
                    rows.append(_row(tid, [0.5, 1.0], ["valid", "valid"], _scene(entry, "protein")))
                else:
                    rows.append(_row(tid, [1.0, 1.0], ["valid", "valid"], _scene(entry)))
                    raws[tid] = [{"raw": "{}"}, {"raw": "{}"}]
            run_id = f"{model}-{cond}-{grounding}"
            card = _card(model, cond, grounding, rows, run_id, cost=0.5 if good else None)
            d = tmp_path / "results" / (cond + ("_grounded" if grounding else ""))
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{model.replace('/', '_')}.json").write_text(json.dumps(card))
            arch = dict(card, raw_samples={model: raws})
            (tmp_path / "runs").mkdir(exist_ok=True)
            (tmp_path / "runs" / f"run_{run_id.replace('/', '_')}.json").write_text(json.dumps(arch))
    manifest = {"label": "synthetic", "status": "final", "tasks_dir": "tasks",
                "scorecards": ["results/*/*.json"], "archives": ["runs/run_*.json"],
                "model_info": {"vendor/model-good": {"weights": "open"},
                               "model-weak": {"weights": "closed"}}}
    return manifest, tmp_path


def _build(manifest, root, n_boot=200):
    p = pt.Paper(manifest, [root], n_boot, seed=1)
    p.run()
    return p


def test_synthetic_run_end_to_end(synthetic, tmp_path):
    manifest, root = synthetic
    p = _build(manifest, root)
    v = p.values
    assert v["mvs.n_tasks"] == 6 and v["mvs.n_structures"] == 5
    assert v["mvs.spec.n_models"] == 2 and v["mvs.spec.samples_per_task"] == 2
    # Good model: 5 tasks at 1.0 and one at 0.75 -> strict F1 = 5.75 / 6; all valid.
    assert v["mvs.spec.model.model-good.f1"] == pytest.approx(5.75 / 6, abs=1e-4)
    assert v["mvs.spec.model.model-good.valid"] == 1.0
    # Weak model: one task (two samples) is invalid JSON.
    assert v["mvs.spec.model.model-weak.valid"] == pytest.approx(5 / 6, abs=1e-4)
    assert v["mvs.spec.model.model-weak.f1"] == pytest.approx(4.75 / 6, abs=1e-4)
    assert v["mvs.spec.model.model-weak.f1_valid"] == pytest.approx(9.5 / 10, abs=1e-4)
    # Success = valid and exactly 1: the clinical task succeeds on one sample of two.
    assert v["mvs.spec.model.model-good.success"] == pytest.approx(5.5 / 6, abs=1e-4)
    assert v["mvs.spec.outcome.invalid_json"] == 2
    lo, hi = v["mvs.spec.model.model-weak.f1_lo"], v["mvs.spec.model.model-weak.f1_hi"]
    assert 0 <= lo <= v["mvs.spec.model.model-weak.f1"] <= hi <= 1
    # Conditions are read from the scorecards' own metadata.
    assert v["mvs.bare.n_models"] == 2 and v["mvs.bare.n_valid"] == 0
    assert v["mvs.grounding.n_models"] == 2 and v["mvs.grounding.all.delta"] == 0.0
    assert v["mvs.grounding.n_lookup_tasks"] == 2          # the clinical and the resolve task
    # A task source nobody mapped becomes its own regime instead of joining another.
    assert v["mvs.regime.brand-new-tier.n_tasks"] == 1
    # One structure in a regime -> no interval is invented.
    assert "n/a" in p.tables["table_mvs_regimes"]
    assert v["mvs.spec.cost.n_priced"] == 1 and v["mvs.spec.cost.n_unpriced"] == 1
    pt.write_outputs(p, tmp_path / "out", None)
    assert json.loads((tmp_path / "out" / "values.json").read_text())["run.label"] == "synthetic"
    assert (tmp_path / "out" / "table_mvs_leaderboard.md").exists()


def test_bracket_shapes_from_archived_raw_text(synthetic):
    p = _build(*synthetic)
    v = p.values
    assert v["mvs.spec.json_shape.n_raw"] == 2
    assert v["mvs.spec.json_shape.too_few"] == 1 and v["mvs.spec.json_shape.empty"] == 1


def test_repair_counterfactual(synthetic):
    pytest.importorskip("json_repair")   # `uv run --with json-repair pytest` to include this
    v = _build(*synthetic).values
    assert v["mvs.spec.repair.computed"] is True
    assert v["mvs.spec.repair.n_raw"] == 2 and v["mvs.spec.repair.n_scene"] == 1
    # The truncated scene repairs to the reference: +1.0 on one sample of two, on one of six tasks.
    assert v["mvs.spec.repair.model.model-weak.repaired"] == pytest.approx(
        v["mvs.spec.repair.model.model-weak.strict"] + 0.5 / 6, abs=1e-4)


def test_duplicate_scorecard_is_an_error(synthetic):
    manifest, root = synthetic
    src = root / "results" / "spec" / "model-weak.json"
    (root / "results" / "spec" / "copy.json").write_text(src.read_text())
    with pytest.raises(SystemExit):
        _build(manifest, root)


def test_bootstrap_resamples_structures():
    tasks = {f"t{i}": {"structure": "s1" if i < 5 else f"s{i}"} for i in range(8)}
    boot = pt.Bootstrap(tasks, sorted(tasks), 500, seed=3)
    assert boot.n_clusters == 4
    lo, hi = boot.ci({i: (1.0 if tasks[i]["structure"] == "s1" else 0.0) for i in tasks})
    assert lo < 5 / 8 < hi                      # the big structure drives the spread
    assert boot.ci({i: 1.0 for i in tasks}) == (1.0, 1.0)
    one = pt.Bootstrap({"a": {"structure": "s"}, "b": {"structure": "s"}}, ["a", "b"], 100, 1)
    assert one.ci({"a": 1.0, "b": 0.0}) is None   # a single structure: no interval


def test_structure_of():
    assert pt.structure_of({"id": "x", "pdb": "1TUP"}) == "1tup"
    assert pt.structure_of({"id": "x", "reference_mvs": _scene("1cbs")}) == "1cbs"
    assert pt.structure_of({"id": "x"}) == "task:x"


def test_scene_differences():
    ref = _scene("1abc")
    assert pt.scene_differences(ref, _scene("1abc", colour="red")) == ["unrequested colour"]
    assert pt.scene_differences(_scene("1abc", colour="red"), ref) == ["missing colour"]
    assert "structure" in pt.scene_differences(ref, _scene("9zzz"))


# --------------------------------------------------------------------------- #
# The October archives (only on a machine that has them)
# --------------------------------------------------------------------------- #
def _october():
    manifest = json.loads((REPO / "paper" / "inputs.json").read_text())
    root = pt.default_data_root()
    if not pt.expand(manifest["scorecards"], [REPO, root]):
        pytest.skip("October scorecards (results/r2x2) are not on this machine")
    return manifest, root


def test_october_data_reproduces_committed_values():
    manifest, root = _october()
    p = pt.build(manifest, root, n_boot=300)
    v = p.values
    assert v["mvs.spec.n_models"] == 15 and v["mvs.n_tasks"] == 70
    assert v["mvs.spec.n_samples"] == 1050 and v["mvs.spec.n_valid"] == 784
    assert v["mvs.spec.best.name"] == "deepseek-v3.2"
    # The three grounding numbers, each on its own denominator.
    assert v["mvs.grounding.both_valid.n"] == 647
    assert (v["mvs.grounding.both_valid.better"], v["mvs.grounding.both_valid.worse"],
            v["mvs.grounding.both_valid.same"]) == (69, 92, 486)
    assert v["mvs.bare.n_models"] == 3 and v["mvs.bare.n_samples"] == 420
    assert v["mvs.bare.n_valid"] == 0
    assert len([t for t in p.tables if t.startswith("table_mvs_")]) >= 10
    # Everything that does not depend on the bootstrap size or on json-repair must equal
    # the committed values exactly: the committed paper is what the archives give.
    committed = json.loads((REPO / "paper" / "generated" / "values.json").read_text())
    skip = re.compile(r"(_lo|_hi|\.lo|\.hi|n_overlap_best|bootstrap_replicates|\.repair\.)")
    diff = {k: (committed.get(k), v[k]) for k in v
            if not skip.search(k) and committed.get(k) != v[k]}
    assert not diff, f"committed paper/generated/values.json is stale: {list(diff.items())[:5]}"


# --------------------------------------------------------------------------- #
# paper/build.py
# --------------------------------------------------------------------------- #
def test_paper_builds_with_no_unresolved_keys():
    md, pending, problems = pb.build()
    assert problems == []
    assert "{{" not in md and "}}" not in md
    assert not re.search(r"\[@[A-Za-z]", md), "an unresolved citation is left in the text"
    assert "## References" in md
    # PENDING tags are allowed; each one is listed in PENDING.md.
    values = json.loads(pb.VALUES.read_text())
    report = pb.pending_report(pending, values)
    assert len(pending) == md.count("⟦PENDING:")
    for p in pending:
        assert p["what"].replace("|", "/") in report
    # The authorship and acknowledgement lines are left for Dan.
    assert any(p["what"].startswith("Dan") for p in pending)


def test_committed_build_outputs_are_current():
    md, pending, _ = pb.build()
    values = json.loads(pb.VALUES.read_text())
    assert pb.OUT_MD.read_text() == md, "run `python paper/build.py` and commit molbench.md"
    assert pb.OUT_PENDING.read_text() == pb.pending_report(pending, values), \
        "run `python paper/build.py` and commit PENDING.md"


def test_build_reports_unknown_key_and_citation(monkeypatch, tmp_path):
    sec = tmp_path / "sections"
    sec.mkdir()
    (sec / "01.md").write_text("A {{no.such.key}} and {{maybe|PENDING: later}} [@nobody2026] "
                               "{{x:.1%}} {{include:generated/none.md|PENDING: a table}}")
    monkeypatch.setattr(pb, "SECTIONS", sec)
    md, pending, problems = pb.build({"x": 0.5})
    assert any("no.such.key" in p for p in problems)
    assert any("nobody2026" in p for p in problems)
    assert "50.0%" in md and "⟦PENDING: later⟧" in md and "⟦PENDING: a table⟧" in md
    assert [p["what"] for p in pending] == ["later", "a table"]


def test_every_reference_has_a_locator():
    bib = pb.parse_bib(pb.BIB.read_text())
    assert len(bib) >= 25
    for key, e in bib.items():
        assert e.get("title") and e.get("year"), key
        assert e.get("url") or e.get("doi"), f"{key} has no URL or DOI"
