"""Paraphrases (scripts/generate_paraphrases.py): the files are what the script writes,
a paraphrase changes only the words, and the wording guards work."""

import importlib.util
import pathlib

import pytest

from molbench import runner, tasks as T

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "tasks" / "paraphrases"

spec = importlib.util.spec_from_file_location(
    "generate_paraphrases", REPO / "scripts" / "generate_paraphrases.py")
para = importlib.util.module_from_spec(spec)
spec.loader.exec_module(para)

SOURCES = para.load_sources(T.TASKS_DIR, OUT)
TASKS = [T.load_task(p) for p in sorted(OUT.glob("*.json"))]


def test_files_are_what_the_script_writes():
    assert para.main(["--check"]) == 0


def test_a_paraphrase_changes_only_the_words():
    assert TASKS
    styles = {}
    for t in TASKS:
        src = SOURCES[t["paraphrase_of"]]
        assert t["style"] in ("terse", "indirect") and src["style"] == "full"
        for key in ("track", "reference", "accepted", "target", "structures", "split", "tier",
                    "family", "context", "skills"):
            assert t[key] == src[key], (t["id"], key)
        assert t.get("accepted_targets") == src.get("accepted_targets")
        assert t["prompt"] != src["prompt"]
        assert runner.grade_parsed(t, t["reference"])["success"]
        styles.setdefault(t["paraphrase_of"], set()).add(t["style"])
        if src["twin_of"]:
            assert t["twin_of"] == f"{src['twin_of']}.{t['style']}"
            twin = next(x for x in TASKS if x["id"] == t["twin_of"])
            assert twin["prompt"] == t["prompt"] and twin["twin_of"] == t["id"]
    assert all(s == {"terse", "indirect"} for s in styles.values())


def test_terse_is_shorter_and_keeps_every_slot():
    for t in TASKS:
        src = SOURCES[t["paraphrase_of"]]
        slots = src["provenance"]["slots"]
        for key, value in slots.items():
            if key.lower() != "id":
                assert str(value).lower() in t["prompt"].lower(), (t["id"], key)
        assert slots["id"] in t["prompt"].lower()
        if t["style"] == "terse":
            assert len(t["prompt"]) < len(src["prompt"])
            assert not t["prompt"].endswith(".") and t["prompt"].startswith(slots["id"])
        else:
            assert "?" in t["prompt"] or "would" in t["prompt"].lower()


def test_every_family_template_fills_and_is_checked():
    for family, table in para.TEMPLATES.items():
        assert len(table["terse"]) >= 2 and len(table["indirect"]) >= 2
    seen = {t["family"] for t in SOURCES.values()}
    assert set(para.TEMPLATES) <= seen          # no template for a family that is gone
    for t in SOURCES.values():
        if t["family"] in para.TEMPLATES:
            words, why = para.phrasings(t, para.request_of(t)[0], False)
            assert words, (t["id"], why)


def test_a_wording_that_drops_a_slot_is_refused(monkeypatch):
    t = next(x for x in SOURCES.values() if x["family"] == "acc-ligand-copy")
    monkeypatch.setitem(para.TEMPLATES, "acc-ligand-copy",
                        {"terse": ["{id} {thing} ball-and-stick"],      # no colour
                         "indirect": para.TEMPLATES["acc-ligand-copy"]["indirect"]})
    words, why = para.phrasings(t, t["id"], False)
    assert words is None and "colour" in why


def test_selection_is_seeded_spread_and_keeps_twins_together():
    a = para.select_seeded(SOURCES, 9, False, ["accept_set"])
    assert a == para.select_seeded(SOURCES, 9, False, ["accept_set"]) and len(a) == 9
    assert len({SOURCES[i]["family"] for i in a}) == 9      # one per family first
    built, skipped = para.build(SOURCES, a, False)
    assert not skipped
    originals = {t["paraphrase_of"] for t in built}
    for i in originals:
        assert SOURCES[i]["twin_of"] in originals | {None}


def test_unknown_family_is_skipped_unless_generic_is_asked_for():
    t = {**next(iter(SOURCES.values())), "family": "no-such-family"}
    assert para.phrasings(t, t["id"], False)[0] is None
    shipped = {**t, "provenance": {**t["provenance"],
                                   "paraphrases": {"terse": "x y", "indirect": "could you x y?"}}}
    assert para.phrasings(shipped, t["id"], False)[0] == {"terse": "x y",
                                                          "indirect": "could you x y?"}


@pytest.mark.parametrize("full, terse", [
    ("Load 1CBS. Show the protein as a cartoon and the retinoic acid (REA) as red ball-and-stick.",
     "1cbs; protein cartoon and retinoic acid (REA) red ball-and-stick"),
    ("In p53 (PDB 1TUP), chain A, highlight the residue affected by the pathogenic ClinVar "
     "variant S241Y as red ball-and-stick.",
     "p53 (PDB 1tup), chain A, highlight residue affected by pathogenic ClinVar variant S241Y "
     "red ball-and-stick"),
    ("Load the myoglobin structure 1A6M and hide all the water molecules.",
     "Load myoglobin structure 1a6m and hide all water molecules"),
])
def test_generic_terse_deletes_only_function_words(full, terse):
    assert para.generic_terse(full) == terse


def test_generic_rewrites_refuse_what_they_cannot_do_safely():
    assert para.generic_terse("Now colour it red.") is None         # nothing to delete
    assert para.generic_indirect("Now colour it red.") is None      # not an imperative
    assert para.generic_indirect("Colour the biotin (BTN) red.") == \
        "Could you colour the biotin (BTN) red?"
    # a chain called A is not the article "a"
    assert "chains A and B" in para.generic_terse(
        "Load 4INS and show the chains A and B as a cartoon.")


def test_generic_fallback_runs_on_a_corpus_without_templates(tmp_path):
    fixtures = REPO / "tests" / "fixtures" / "tasks"
    out = tmp_path / "paraphrases"
    code = para.main(["--tasks-dir", str(fixtures), "--out", str(out), "--generic-fallback",
                      "--select-seeded", "2", "--tiers", "translation"])
    assert code == 0
    written = sorted(p.name for p in out.glob("*.json"))
    assert len(written) == 8                    # 2 requests x 2 twins x 2 styles
    assert para.main(["--tasks-dir", str(fixtures), "--out", str(out), "--check"]) == 0
