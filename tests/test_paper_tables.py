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


def test_target_check_separates_wrong_atoms_from_missing_context():
    """Reference = grey cartoon of the protein (context) + one red residue (target)."""
    def scene(parts):
        comps = []
        for selector, rep, colour in parts:
            node = {"kind": "representation", "params": {"type": rep}}
            if colour:
                node["children"] = [{"kind": "color", "params": {"color": colour}}]
            comps.append({"kind": "component", "params": {"selector": selector},
                          "children": [node]})
        return {"root": {"kind": "root", "children": [
            {"kind": "download", "params": {"url": "https://files.rcsb.org/download/1tup.cif"},
             "children": [{"kind": "parse", "params": {"format": "mmcif"}, "children": [
                 {"kind": "structure", "params": {"type": "model"}, "children": comps}]}]}]}}

    res = lambda n: {"auth_asym_id": "A", "auth_seq_id": n}  # noqa: E731
    ref = scene([("polymer", "cartoon", "grey"), (res(175), "ball_and_stick", "red")])
    if pt.target_check(ref, ref) is None:
        pytest.skip("no frozen atom table for 1tup in this checkout")
    assert pt.target_check(ref, ref) == {"target_exact": True, "target_atoms": True,
                                         "has_context": True, "context_exact": True}
    no_context = pt.target_check(ref, scene([(res(175), "ball_and_stick", "red")]))
    assert no_context["target_exact"] and not no_context["context_exact"]
    restyled = pt.target_check(ref, scene([("polymer", "cartoon", "grey"),
                                           (res(175), "spacefill", "red")]))
    assert not restyled["target_exact"] and restyled["target_atoms"]
    wrong = pt.target_check(ref, scene([("polymer", "cartoon", "grey"),
                                        (res(176), "ball_and_stick", "red")]))
    assert not wrong["target_exact"] and not wrong["target_atoms"]
    assert pt.target_check(ref, {"nonsense": 1}) is None


# --- tables of a manifest run (molbench/analysis.py) --------------------------------

from molbench import analysis  # noqa: E402

FINAL_TABLES = {
    "table_corpus", "table_corpus_kinds", "table_corpus_difficulty", "table_panel",
    "table_controls", "table_mvs_leaderboard", "table_api_leaderboard", "table_mvs_validity",
    "table_api_validity", "table_mvs_tiers", "table_api_tiers", "table_tier_track",
    "table_mvs_split", "table_api_split", "table_mvs_paraphrase", "table_api_paraphrase",
    "table_paired", "table_followup", "table_followup_edits", "table_accept_readings",
    "table_accept_tasks", "table_clinical_strata", "table_clinical_models",
    "table_clinical_pairs", "table_difficulty", "table_resolve_entries", "table_structured",
    "table_grounding", "table_cost"}
# plus table_tracks and table_bare, which need three models and the bare condition


@pytest.fixture(scope="module")
def mock_run(tmp_path_factory):
    """A dry run of the pilot manifest (mock model, about 110 calls): the scorecards a
    real run writes, small."""
    from molbench import runner
    tmp = tmp_path_factory.mktemp("mockrun")
    with pytest.raises(SystemExit) as e:
        runner.main(["--manifest", str(REPO / "run" / "pilot.toml"), "--dry-run", "--no-site",
                     "--runs-dir", str(tmp / "runs"), "--results-dir", str(tmp / "results")])
    assert e.value.code == 0
    return tmp / "results" / "pilot-v1.dryrun"


def test_every_final_table_is_built_from_a_dry_run_and_says_it_is_mock(mock_run, tmp_path):
    out = tmp_path / "generated_mock"
    t = analysis.build(mock_run, out, replicates=100, require_mock=True, flag="--from-dry-run")
    assert FINAL_TABLES <= set(t.tables), FINAL_TABLES - set(t.tables)
    for name in t.tables:
        text = (out / f"{name}.md").read_text()
        if name in analysis.NOT_RUN_RESULTS:      # counted or measured, not answered
            assert "MOCK" not in text.splitlines()[0], name
        else:
            assert text.startswith(analysis.MOCK_BANNER), name
    values = json.loads((out / "values.json").read_text())
    assert values["status"] == "MOCK" and values["run.name"] == "pilot-v1"
    assert "MOCK" in (out / "README.md").read_text().splitlines()[0]
    # the corpus numbers come from the task files, whatever was run (CORPUS.md)
    from molbench import difficulty, tasks as tasks_mod
    corpus = tasks_mod.load_corpus()
    orig = [t for t in corpus if not t["paraphrase_of"]]
    mvs_o = [t for t in orig if t["track"] == "mvs"]
    twins = [t for t in mvs_o if t["twin_of"]]
    by_id = {t["id"]: t for t in corpus}
    hide = [t for t in twins if difficulty.normalised(by_id[t["twin_of"]])["hide_toggle"]]
    assert (values["corpus.n_original"], values["corpus.n_paraphrases"]) == \
        (len(orig), len(corpus) - len(orig)) == (797, 82)
    assert (values["corpus.mvs.n"], values["corpus.api.n"]) == (len(mvs_o), len(orig) - len(mvs_o))
    assert (values["corpus.n_twin_pairs"], values["corpus.n_twin_pairs_hide_toggle"]) == \
        (len(twins), len(hide))
    assert values["corpus.n_paraphrase_requests"] == 30
    assert (values["corpus.mvs.followup.n_noop"], values["corpus.api.followup.n_noop"]) == (10, 8)
    # twins: all outside the clinical tier, the same without unstated hide toggles, clinical
    # apart; by the target score (the like-for-like measure) and by task success
    plain = [t for t in twins if t["tier"] != "clinical"]
    want = (len(plain), len([t for t in plain if t not in hide]), len(twins) - len(plain))
    for prefix in ("paired", "paired_target"):
        assert (values[f"{prefix}.all.n_pairs"], values[f"{prefix}.no_hide_toggle.n_pairs"],
                values[f"{prefix}.clinical.n_pairs"]) == want
    assert want[2] == 82
    assert values["controls.mvs.false_pass_rate"] == 0 and values["controls.api.n"] > 0
    assert values["clinical.needs_offset.yes.n_proteins"] > 1      # not one protein's story


def test_mock_and_real_tables_are_never_mixed(mock_run, tmp_path):
    with pytest.raises(SystemExit, match="is a dry run"):
        analysis.build(mock_run, tmp_path / "final", replicates=10, require_mock=False)
    assert not (tmp_path / "final").exists()
    real = tmp_path / "real"
    real.mkdir()
    (real / "values.json").write_text('{"status": "final"}')
    with pytest.raises(SystemExit, match="refusing to overwrite"):
        analysis.build(mock_run, real, replicates=10)
    with pytest.raises(SystemExit, match="another kind"):      # the October tables
        analysis.build(mock_run, REPO / "paper" / "generated", replicates=10)
    # a scorecard that does not say mock is a real run: it stays out of the mock directory
    copy = tmp_path / "copy"
    import shutil
    shutil.copytree(mock_run, copy, ignore=shutil.ignore_patterns("paper", "samples", "site"))
    for f in copy.glob("*/*.json"):
        card = json.loads(f.read_text())
        card["meta"]["mock"] = False
        f.write_text(json.dumps(card))
    with pytest.raises(SystemExit, match="is a real run"):
        analysis.build(copy, tmp_path / "mock", replicates=10, require_mock=True)
    one = next(copy.glob("spec/*.json"))
    card = json.loads(one.read_text())
    card["meta"]["mock"] = True
    one.write_text(json.dumps(card))
    with pytest.raises(SystemExit, match="mixes mock and real"):
        analysis.build(copy, tmp_path / "mixed", replicates=10)


# --- the seven tables the paper includes (analysis.Tables.final) ------------------------

#: table_final_<name> takes the place of shape_<name> (paper/sections/07_results.md)
PAPER_SHAPES = {"table_final_leaderboard_scene": "shape_leaderboard",
                "table_final_leaderboard_calls": "shape_leaderboard",
                "table_final_tiers": "shape_tiers", "table_final_paired": "shape_paired",
                "table_final_clinical": "shape_clinical",
                "table_final_followup": "shape_followup",
                "table_final_robustness": "shape_robustness"}


def _header(text: str) -> list[str]:
    row = next(line for line in text.splitlines() if line.startswith("| "))
    return [c.strip() for c in row.strip("|").split("|")]


def test_the_papers_seven_tables_have_the_columns_of_the_shape_tables(mock_run, tmp_path):
    """The mapping from a run's scorecards to the tables the paper includes: seven
    tables, each with exactly the columns of the pending-shape table it replaces, in
    the paper's words (scene track / call-list track, the paper's tier names)."""
    t = analysis.build(mock_run, tmp_path / "generated_mock", replicates=50, require_mock=True)
    assert set(analysis.PAPER_TABLES) == set(PAPER_SHAPES) <= set(t.tables)
    for name, shape in PAPER_SHAPES.items():
        want = _header((REPO / "paper" / "generated" / f"{shape}.md").read_text())
        got = _header(t.tables[name])
        if shape == "shape_leaderboard":      # the pilot manifest takes one sample
            assert got[7] == "Tasks with the one sample right"
            assert want[7] == "Tasks with all 3 samples right"
            got[7] = want[7]
        assert got == want, name
        assert t.tables[name].startswith(analysis.MOCK_BANNER)
    tiers = t.tables["table_final_tiers"]
    assert "Scene track: Clinical variant" in tiers and "Call-list track: Translation" in tiers
    assert "mvs" not in tiers.lower() and "api" not in tiers.lower()
    # every include of a result table in the paper has its table here, and no other
    text = (REPO / "paper" / "sections" / "07_results.md").read_text()
    asked = set(re.findall(r"include:generated/(table_final_\w+)\.md", text))
    assert asked == set(analysis.PAPER_TABLES)


def test_only_the_real_complete_run_is_written_into_the_paper(mock_run, tmp_path):
    t = analysis.build(mock_run, tmp_path / "generated_mock", replicates=50, require_mock=True)
    into = tmp_path / "generated"
    into.mkdir()
    with pytest.raises(SystemExit, match="mock data"):
        analysis.copy_into_paper(t, into)
    with pytest.raises(SystemExit, match="pilot_summary is for a real pilot"):
        analysis.pilot_summary(t.run)
    # a real pilot is refused as well; its own small table is labelled a pilot
    import shutil
    copy = tmp_path / "copy"
    shutil.copytree(mock_run, copy, ignore=shutil.ignore_patterns("paper", "samples", "site"))
    for f in copy.glob("*/*.json"):
        card = json.loads(f.read_text())
        card["meta"]["mock"] = False
        f.write_text(json.dumps(card))
    real = analysis.build(copy, tmp_path / "pilot_tables", replicates=50)
    with pytest.raises(SystemExit, match="pilot is not the benchmark run"):
        analysis.copy_into_paper(real, into)
    assert not list(into.iterdir())
    for name in analysis.PAPER_TABLES:
        assert real.tables[name].startswith(analysis.PILOT_BANNER), name
    text, values = analysis.pilot_summary(real.run)
    assert text.startswith(analysis.PILOT_BANNER) and values["pilot.status"] == "pilot"
    assert values["pilot.n_tasks"] == 39 and values["pilot.samples_per_task"] == 1
    with pytest.raises(SystemExit, match="dry run is mock data"):
        pt.main(["--from-dry-run", str(mock_run), "--into-paper", "--out", str(tmp_path / "x")])


def test_the_committed_pilot_table_is_labelled_and_is_not_a_result_table():
    gen = REPO / "paper" / "generated"
    text = (gen / "pilot_results.md").read_text()
    values = json.loads((gen / "pilot_values.json").read_text())
    assert text.startswith(analysis.PILOT_BANNER)
    assert values["pilot.status"] == "pilot" and values["pilot.model"] == "claude-haiku-4-5"
    assert values["pilot.n_tasks"] == 39 and values["pilot.n_calls"] == 46
    assert values["pilot.samples_per_task"] == 1
    assert not list(gen.glob("table_final_*.md")), "result tables come from the real run only"
    assert not [k for k in json.loads((gen / "values.json").read_text()) if k.startswith("pilot.")]


def test_from_dry_run_flag_writes_the_mock_directory(mock_run, tmp_path, capsys):
    out = tmp_path / "generated_mock"
    assert pt.main(["--from-dry-run", str(mock_run), "--out", str(out),
                              "--bootstrap", "50"]) == 0
    assert "MOCK" in capsys.readouterr().out
    assert json.loads((out / "values.json").read_text())["status"] == "MOCK"
    with pytest.raises(SystemExit):
        pt.main(["--from-run", str(mock_run), "--out", str(tmp_path / "final")])
    assert pt.MOCK_OUT.name == "generated_mock" != pt.DEFAULT_OUT.name


def test_committed_mock_tables_are_flagged_and_october_tables_stay_labelled():
    mock = REPO / "paper" / "generated_mock"
    values = json.loads((mock / "values.json").read_text())
    assert values["status"] == "MOCK"
    tables = sorted(mock.glob("table_*.md"))
    assert FINAL_TABLES | {"table_bare", "table_tracks"} <= {f.stem for f in tables}
    assert -1.0 <= values["tracks.r_success"] <= 1.0
    for f in tables:
        first = f.read_text().splitlines()[0]
        assert first.startswith("> **MOCK DATA.**") or f.stem in analysis.NOT_RUN_RESULTS, f.name
    # corpus numbers in the mock directory are the real ones, and are current
    from molbench import runner
    corpus = runner.load_tasks(["mvs", "api_calling"])
    assert values["corpus.n_task_files"] == len(corpus)
    # the October preliminary tables are still there, labelled, in their own directory
    october = REPO / "paper" / "generated"
    assert "PRELIMINARY" in (october / "table_mvs_leaderboard.md").read_text()
    assert "status" not in json.loads((october / "values.json").read_text())
    assert not list(october.glob("table_paired.md"))


def test_mcnemar_exact():
    assert analysis.mcnemar_exact(0, 0) is None            # no discordant pair, no test
    assert analysis.mcnemar_exact(5, 5) == 1.0
    assert analysis.mcnemar_exact(0, 5) == pytest.approx(2 / 32)
    assert analysis.mcnemar_exact(9, 1) == pytest.approx(2 * 11 / 1024)
    assert analysis.mcnemar_exact(1, 9) == analysis.mcnemar_exact(9, 1)


def test_task_is_solved_when_most_samples_are_right():
    assert analysis.solved({"success": 2 / 3}) and analysis.solved({"success": 1.0})
    assert not analysis.solved({"success": 1 / 3}) and not analysis.solved({"success": 0.5})


def test_run_bootstrap_resamples_structures_not_tasks():
    boot = analysis.Bootstrap(replicates=400, seed=1)
    assert boot.ci([("a", 1.0), ("a", 0.0)]) is None       # one structure: no interval
    # ten tasks on two structures: all of a structure's tasks move together
    clustered = [("a", 1.0)] * 5 + [("b", 0.0)] * 5
    spread = [(f"s{i}", v) for i, (_, v) in enumerate(clustered)]
    lo, hi = boot.ci(clustered, "x")
    lo2, hi2 = boot.ci(spread, "x")
    assert (lo, hi) == (0.0, 1.0) and hi2 - lo2 < 1.0
    assert boot.ci(clustered, "x") == (lo, hi)              # seeded: the same every time
    d = boot.diff_ci([("a", 1.0), ("b", 1.0)], [("c", 0.0), ("d", 0.0)], "y")
    assert d == (1.0, 1.0)
    assert boot.diff_ci([("a", 1.0)], [("c", 0.0), ("d", 0.0)]) is None


def test_accept_set_readings_are_counted_not_call_forms():
    from molbench import runner
    tasks = [t for t in runner.load_tasks(["mvs", "api_calling"])
             if t["tier"] == "accept_set" and not t.get("paraphrase_of")]
    assert len(tasks) == 41
    for t in tasks:
        states = analysis.readings_by_state(t)
        assert len(states) == 1 + len(t["accepted"]), t["id"]   # the reference, then each alternative
        assert analysis.readings(t)[0] == states[0] and len(analysis.readings(t)) >= 2, t["id"]
    api = [t for t in tasks if t["category"] == "api_calling"]
    # on the API track one reading can be written in several call forms
    assert any(len(analysis.readings(t)) < len(analysis.readings_by_state(t)) for t in api)


def test_paraphrase_groups_have_three_phrasings(mock_run):
    run = analysis.Run(mock_run)
    t = analysis.Tables(run, replicates=10)
    groups = {track: t.paraphrase_groups(track) for track in analysis.TRACKS}
    assert (len(groups["mvs"]), len(groups["api_calling"])) == (22, 19)   # tasks/paraphrases
    assert all(set(g) == {"full", "terse", "indirect"} for gs in groups.values() for g in gs.values())
    assert run.mock and run.samples == {"spec": 1, "spec_structured": 1, "spec_grounded": 1}
