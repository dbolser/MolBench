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


def test_every_wording_keeps_what_the_request_needs_and_terse_is_shorter():
    for t in TASKS:
        src = SOURCES[t["paraphrase_of"]]
        assert para.lost(src["prompt"], t["prompt"]) == [], t["id"]
        if t["style"] == "terse":
            assert len(t["prompt"]) < len(src["prompt"]), t["id"]
        else:                      # an indirect request is a full sentence
            assert t["prompt"][0].isupper() and t["prompt"].rstrip()[-1] in ".?", t["id"]


def test_no_accept_set_task_is_paraphrased_and_only_public_ones_are():
    """Rulings of 2026-11-15: a paraphrase is never of an accept-set task."""
    assert "accept_set" in para.NEVER
    for t in TASKS:
        assert t["tier"] != "accept_set" and t["split"] == "public", t["id"]
    task = next(x for x in SOURCES.values() if x["tier"] == "accept_set")
    words, why = para.phrasings(task, para.request_of(task)[0])
    assert words is None and "never paraphrased" in why


def test_selection_is_seeded_spread_and_keeps_twins_together():
    ids = para.select_seeded(SOURCES, 30, False, None, public_only=True)
    assert ids == para.select_seeded(SOURCES, 30, False, None, public_only=True)
    assert len(ids) == 30 and set(ids) == set(para.WORDINGS)
    recorded = [x for x in (OUT / para.SELECTION).read_text().splitlines()
                if x.strip() and not x.startswith("#")]
    assert recorded == ids
    tiers = {SOURCES[i]["tier"] for i in ids}
    assert tiers == set(T.TIERS) - {"accept_set"} - {"unclassified"} if hasattr(T, "TIERS") else len(tiers) >= 7
    assert all(SOURCES[i]["split"] == "public" for i in ids)
    # a twin pair is one request: both tracks are paraphrased, with the same words
    originals = {t["paraphrase_of"] for t in TASKS}
    for i in ids:
        twin = SOURCES[i]["twin_of"]
        assert i in originals and (twin is None or twin in originals)
    assert len(TASKS) == 2 * len(originals)


@pytest.mark.parametrize("original, wording, gone", [
    # an id, in either case
    ("Load 1TRN as a grey cartoon.", "1trn grey cartoon", []),
    ("Load 1TRN as a grey cartoon.", "grey cartoon", ["1TRN"]),
    # a residue, a number of a range, a variant name
    ("Colour residues 14-23 of 1CRN brown.", "1crn residues 14 to 23 brown", []),
    ("Colour residues 14-23 of 1CRN brown.", "1crn residues 14 onwards brown", ["23"]),
    ("Show the residue replaced by HBB p.Val68Met in 2HHB as red spheres.",
     "2hhb HBB Val68Met red spheres", ["p.Val68Met"]),
    # a chain letter, a code in capitals, a quoted text
    ("Show 1TRN as a cartoon: chain B in orange.", "1trn cartoon, one chain orange", ["chain B"]),
    ("Now bring in the ligand HEM in plum ball-and-stick.", "add the ligand, plum ball-and-stick", ["HEM"]),
    ('Label the benzamidine (BEN) with the text "ligand".', "label the benzamidine (BEN)", ['"ligand"']),
    # a colour (grey and gray are one word) and a representation
    ("Add chain B too, as a cartoon in grey.", "chain B too, gray cartoon", []),
    ("Add chain B too, as a cartoon in grey.", "chain B too, cartoon", ["grey"]),
    ("Show the ion as a red spacefill sphere in 1TUP.", "1tup ion red", ["spacefill", "sphere"]),
    ("Show the ion as red space-filling spheres in 1TUP.", "1tup ion red spacefill", []),
    # "PDB" and an article "A" carry no value
    ("A PDB entry of human SERPINA1 as a brown cartoon.", "human SERPINA1, brown cartoon", []),
])
def test_lost_names_what_a_wording_drops(original, wording, gone):
    assert para.lost(original, wording) == sorted(gone)


def test_a_request_without_a_wording_stops_the_build(monkeypatch):
    key = next(iter(para.WORDINGS))
    monkeypatch.delitem(para.WORDINGS, key)
    built, skipped = para.build(SOURCES, [key], False)
    assert not built and skipped and "no wording written" in skipped[0]
    monkeypatch.setitem(para.WORDINGS, key, {"terse": "x", "indirect": "Could you do it?"})
    built, skipped = para.build(SOURCES, [key], False)
    assert not built and "drops" in skipped[0]
