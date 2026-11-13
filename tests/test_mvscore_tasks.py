"""
The four generated MVS tiers (translation, grounded, interactions, resolve): the files
on disk are what the generators build, and the rules the generators promise hold.

No network. The frozen inputs are data/panel, the atom tables and data/mvscore.
"""

from __future__ import annotations

import json
import pathlib
import sys
from collections import Counter

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import mvscore_common as C  # noqa: E402
import author_interaction_tasks as interactions  # noqa: E402
import generate_grounded_tasks as grounded  # noqa: E402
import generate_mvs_tasks as translation  # noqa: E402
import generate_resolve_tasks as resolve  # noqa: E402
from molbench import runner, tasks as T  # noqa: E402

GENERATORS = {"translation": translation, "grounded": grounded,
              "interactions": interactions, "resolve": resolve}
# The largest share one template may have. The resolve tier has five templates (there
# are few distinct ways to name a protein); the others keep to about 12%.
MAX_SHARE = {"translation": 0.13, "grounded": 0.13, "interactions": 0.13, "resolve": 0.32}
MIN_TASKS = {"translation": 60, "grounded": 60, "interactions": 40, "resolve": 38}
DIFFICULTY_KEYS = {"author_number_differs_from_label", "author_chain_differs_from_label",
                   "insertion_code", "needs_ligand_identity", "needs_uniprot_mapping",
                   "needs_structure_lookup"}


def on_disk(tier: str) -> list[dict]:
    out = GENERATORS[tier].OUT
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(out.glob("*.json"))]


@pytest.fixture(scope="module")
def corpus() -> dict[str, list[dict]]:
    return {tier: on_disk(tier) for tier in GENERATORS}


@pytest.fixture(scope="module")
def loaded() -> dict[str, dict]:
    return {t["id"]: t for t in runner.load_tasks(["mvs"])}


# --------------------------------------------------------------------------- #
# The files are what the generators build
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("tier", list(GENERATORS))
def test_a_rebuild_reproduces_the_files_byte_for_byte(tier):
    mod = GENERATORS[tier]
    built = C.verify(mod.build(), mod.OUT)       # grades every reference with the grader
    if tier == "resolve":
        mod.check_answers(built)
    assert C.write_all(built, mod.OUT, True, mod.readme(built)) == 0
    assert mod.build() == mod.build(), "two builds in one process differ"


def test_no_old_format_task_and_no_hand_written_directory_is_left(corpus):
    for tier, tasks in corpus.items():
        assert len(tasks) >= MIN_TASKS[tier], (tier, len(tasks))
        for t in tasks:
            assert t["tier"] == tier and t["track"] == "mvs" and "category" not in t
            assert (REPO / t["provenance"]["script"]).samefile(GENERATORS[tier].__file__)
    assert not (REPO / "tasks" / "mvs").exists()
    assert not (REPO / "tasks" / "visual_rubric").exists()
    assert (REPO / "tasks_future" / "README.md").exists()
    assert len(list((REPO / "tasks_future" / "visual_rubric").glob("*.json"))) == 2
    assert not any(t["id"].startswith("vis-") for t in runner.load_tasks(None))


# --------------------------------------------------------------------------- #
# Shared rules
# --------------------------------------------------------------------------- #
def test_the_heldback_seed_is_the_smallest_that_covers_the_panel():
    assert C.first_covering_seed() == C.HELDBACK_SEED
    chosen = C._heldback_for(C.HELDBACK_SEED)
    assert len(chosen) == C.HELDBACK_N and C.heldback_covers(chosen)
    assert set(C.ALSO_HELDBACK) <= {e["id"] for e in chosen}
    assert all(not e["used_by_tasks"] for e in chosen), "held back but published before"


def test_heldback_structures_are_in_no_public_task_and_get_about_a_fifth(corpus):
    held = C.heldback_structures()
    for tier, tasks in corpus.items():
        for t in tasks:
            assert t["split"] == ("heldback" if t["structures"][0] in held else "public"), t["id"]
        share = sum(t["split"] == "heldback" for t in tasks) / len(tasks)
        assert 0.15 <= share <= 0.27, (tier, share)
    public = {s for tasks in corpus.values() for t in tasks if t["split"] == "public"
              for s in t["structures"]}
    assert not public & held


def test_reuse_is_capped_per_structure_and_per_template(corpus):
    for tier, tasks in corpus.items():
        per_structure = Counter(t["structures"][0] for t in tasks)
        assert max(per_structure.values()) <= C.MAX_PER_STRUCTURE, tier
        per_family = Counter(t["family"] for t in tasks)
        assert max(per_family.values()) / len(tasks) <= MAX_SHARE[tier], (tier, per_family)
        assert len(per_structure) >= 35, (tier, len(per_structure))


def test_no_task_touches_the_worked_example(corpus):
    for tasks in corpus.values():
        for t in tasks:
            text = json.dumps({k: t[k] for k in ("prompt", "structures", "reference", "accepted",
                                                 "grounding")}).lower()
            assert T.WORKED_EXAMPLE not in text, t["id"]
            assert T.WORKED_EXAMPLE not in t.get("accepted_structures", []), t["id"]


def test_prompts_are_plain_requests_and_differ(corpus):
    prompts = Counter()
    for tasks in corpus.values():
        for t in tasks:
            assert not C.prompt_problems(t["prompt"]), (t["id"], C.prompt_problems(t["prompt"]))
            prompts[t["prompt"]] += 1
    assert max(prompts.values()) == 1, [p for p, n in prompts.items() if n > 1]


def test_every_template_is_worded_several_ways(corpus):
    for tier, tasks in corpus.items():
        by_family: dict[str, set] = {}
        for t in tasks:
            # the opening words differ between the wordings of a template
            by_family.setdefault(t["family"], set()).add(" ".join(t["prompt"].split()[:2]))
        one_way = [f for f, starts in by_family.items()
                   if len(starts) < 2 and sum(t["family"] == f for t in tasks) >= 4]
        assert not one_way, (tier, one_way)


def test_provenance_carries_the_difficulty_facts(corpus):
    for tasks in corpus.values():
        for t in tasks:
            prov = t["provenance"]
            assert DIFFICULTY_KEYS <= set(prov["difficulty"]), t["id"]
            assert all(isinstance(prov["difficulty"][k], bool) for k in DIFFICULTY_KEYS), t["id"]
            assert prov["derivation"] and len(prov["checks"]) >= 2 and prov["date"] == C.DATE
            assert all((REPO / f).exists() for f in prov["inputs"]), (t["id"], prov["inputs"])


def test_references_draw_only_palette_colours_and_every_representation_is_coloured(corpus):
    def walk(node, found):
        if isinstance(node, dict):
            if node.get("kind") == "representation":
                kinds = [c.get("kind") for c in node.get("children", [])]
                found.append("color" in kinds)
            for v in node.values():
                walk(v, found)
        elif isinstance(node, list):
            for v in node:
                walk(v, found)

    for tasks in corpus.values():
        for t in tasks:
            found: list[bool] = []
            walk(t["reference"], found)
            assert found and all(found), f"{t['id']}: a representation without a colour"
            assert C._colours_used(t["reference"]) <= set(C.PALETTE), t["id"]


# --------------------------------------------------------------------------- #
# Translation
# --------------------------------------------------------------------------- #
def test_ions_are_asked_for_only_where_the_ion_selection_is_single_atom_ions(corpus):
    ions = [t for t in corpus["translation"] if t["family"] == "tr-ions"]
    assert ions and all(t["structures"][0] != "1hho" for t in ions)   # its "ion" is a phosphate
    for t in ions:
        entry = t["structures"][0]
        table = C.table(entry)
        rows = C.residue_rows(entry, "ion")
        assert rows, t["id"]
        per_residue = Counter(table.columns["residue_index"][i]
                              for i in range(len(table.columns["residue_index"]))
                              if table.static["ion"] >> i & 1)
        assert set(per_residue.values()) == {1}, f"{t['id']}: an 'ion' of several atoms"


def test_colour_by_chain_is_on_complexes_of_three_or_more_chains(corpus):
    tasks = [t for t in corpus["translation"] if t["family"] == "tr-colour-by-chain"]
    assert len(tasks) >= 4
    for t in tasks:
        chains = [c for c in C.facts(t["structures"][0])["chains"]]
        assert len(chains) >= 3, t["id"]


# --------------------------------------------------------------------------- #
# Interactions
# --------------------------------------------------------------------------- #
def _lines(tree) -> list[tuple[dict, dict]]:
    out = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("kind") == "primitive":
                out.append((node["params"]["start"], node["params"]["end"]))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(tree)
    return out


def _gemmi_atom(entry: str, sel: dict):
    """The one atom a line end names, found in the frozen mmCIF without the atom table."""
    hits = []
    for chain in C.cif_structure(entry)[0]:
        if "auth_asym_id" in sel and chain.name != sel["auth_asym_id"]:
            continue
        for res in chain:
            if "auth_seq_id" in sel and (res.seqid.num != sel["auth_seq_id"]
                                         or res.seqid.icode.strip()
                                         != sel.get("pdbx_PDB_ins_code", "")):
                continue
            if "label_comp_id" in sel and res.name != sel["label_comp_id"]:
                continue
            hits += [a for a in res if a.name == sel["label_atom_id"]]
    assert len(hits) == 1, (entry, sel, len(hits))
    return hits[0]


def test_every_measured_line_joins_two_single_atoms_at_the_recorded_distance(corpus):
    n = 0
    for t in corpus["interactions"]:
        entry = t["structures"][0]
        measured = t["provenance"]["measured"]
        lines = _lines(t["reference"])
        assert [(m["start"], m["end"]) for m in measured] == lines, t["id"]
        for m in measured:
            for end in (m["start"], m["end"]):
                assert C.n_atoms(C.mask_of(entry, end)) == 1, (t["id"], end)
            a, b = _gemmi_atom(entry, m["start"]), _gemmi_atom(entry, m["end"])
            assert abs(a.pos.dist(b.pos) - m["distance_A"]) < 0.006, (t["id"], m)
            n += 1
    assert n >= 30


def test_contact_distances_fit_the_kind_of_contact(corpus):
    limits = {"in-hbond": (2.5, 3.0), "in-salt-bridge": (2.5, 3.2), "in-disulfide": (1.9, 2.3),
              "in-metal-contact": (1.8, 3.0), "in-ligand-contact": (2.5, 3.2),
              "in-ca-distance": (6.0, 30.0)}
    for t in corpus["interactions"]:
        if t["family"] in limits:
            lo, hi = limits[t["family"]]
            for m in t["provenance"]["measured"]:
                assert lo <= m["distance_A"] <= hi, (t["id"], m)


def test_contact_tasks_ask_for_the_view_and_have_a_focus(corpus):
    words = ("zoom", "centre", "centred", "focus", "camera")
    for t in corpus["interactions"]:
        has_focus = '"kind": "focus"' in json.dumps(t["reference"])
        asks = any(w in t["prompt"].lower() for w in words)
        assert has_focus == asks, f"{t['id']}: focus in the reference but not in the prompt, or the reverse"
        if t["family"] not in ("in-ca-distance", "in-transparent"):
            assert has_focus, t["id"]


def test_a_wrong_atom_or_a_missing_line_is_not_exactly_right(corpus, loaded):
    for t in corpus["interactions"]:
        if not t["provenance"]["measured"]:
            continue
        task = loaded[t["id"]]
        text = json.dumps(t["reference"])
        end = t["provenance"]["measured"][0]["end"]
        other = "CB" if end["label_atom_id"] != "CB" else "CA"
        swapped = json.loads(text.replace(json.dumps(end), json.dumps({**end, "label_atom_id": other})))
        assert swapped != t["reference"]
        assert not runner.grade_parsed(task, swapped)["success"], t["id"]
        no_line = json.loads(text)
        kids = no_line["root"]["children"][0]["children"][0]["children"][0]["children"]
        kids[:] = [k for k in kids if k["kind"] != "primitives"]
        assert not runner.grade_parsed(task, no_line)["success"], t["id"]


# --------------------------------------------------------------------------- #
# Resolve
# --------------------------------------------------------------------------- #
def test_accepted_lists_are_the_frozen_lists(corpus):
    ids, date = resolve.pdb_ids()
    assert len(ids) > 200_000 and date == resolve.frozen()["retrieved"]
    for t in corpus["resolve"]:
        prov = t["provenance"]
        entry = t["structures"][0]
        accepted = set(t["accepted_structures"]) | {entry}
        assert len(accepted) == prov["n_accepted"] >= 3, t["id"]
        assert accepted <= ids, t["id"]
        assert prov["accepted_retrieved"] == resolve.frozen()["retrieved"]
        for acc in prov["accessions"]:
            rows = resolve.protein(acc)["entries"]
            assert all(rows[e][0] >= resolve.threshold(acc) for e in accepted), (t["id"], acc)
            resolve.protein_phrase(acc)          # raises if the wording is not UniProt's
            assert resolve.sifts_residues(entry, acc) > 0, (t["id"], acc)


def test_no_protein_is_in_both_splits_of_the_resolve_tier(corpus):
    split: dict[str, str] = {}
    for t in corpus["resolve"]:
        for acc in t["provenance"]["accessions"]:
            assert split.setdefault(acc, t["split"]) == t["split"], (acc, t["id"])


def test_resolve_prompts_name_no_entry(corpus):
    import re
    ids = resolve.pdb_ids()[0]
    for t in corpus["resolve"]:
        words = {w.lower() for w in re.findall(r"\b[0-9][A-Za-z0-9]{3}\b", t["prompt"])}
        assert not words & ids, (t["id"], words & ids)


def test_an_answer_is_sorted_into_accepted_wrong_entry_or_no_such_entry(corpus, loaded):
    t = next(t for t in corpus["resolve"] if "O76074" in t["provenance"]["accessions"])
    # The case that started this tier: "a structure of PDE5A" answered with 1UJ7.
    assert not resolve.pdb_id_exists("1uj7")
    assert resolve.answer_outcome(t, "1UJ7") == "no_such_entry"
    assert resolve.answer_outcome(t, "1udt") == "accepted"
    assert resolve.answer_outcome(t, "1crn") == "wrong_entry"
    task = loaded[t["id"]]
    for bad in ("1uj7", "1crn"):
        res = runner.grade_parsed(task, resolve.repoint(t["reference"], "1udt", bad))
        assert not res["success"] and res["f1"] < 1.0, bad
    other = t["accepted_structures"][0]
    res = runner.grade_parsed(task, resolve.repoint(t["reference"], "1udt", other))
    assert res["success"] and res["accepted_structure"] == other


def test_harmless_namings_pass_on_an_entry_without_an_atom_table(corpus, loaded):
    t = next(t for t in corpus["resolve"] if t["family"] == "res-name")
    entry = t["structures"][0]
    other = next(e for e in t["accepted_structures"] if T.table_for(e) is None)
    colour = t["target"][0]["color"]
    for naming in resolve.cartoon_namings(entry):
        answer = C.scene(other, [C.drawn_comp(naming, "cartoon", colour)])
        assert runner.grade_parsed(loaded[t["id"]], answer)["success"], naming
    wrong_colour = C.scene(other, [C.drawn_comp("polymer", "cartoon",
                                                "red" if colour != "red" else "blue")])
    assert not runner.grade_parsed(loaded[t["id"]], wrong_colour)["success"]


def test_resolve_packs_state_facts_only(corpus):
    import re
    styling = re.compile(r"\b(cartoon|ball[-_]and[-_]stick|spacefill|surface|representation|"
                         r"component|primitives?|focus|colou?r|red|grey|gray|blue|orange|"
                         r"draw|show|highlight)\b", re.I)
    for t in corpus["resolve"]:
        pack = t["grounding"]
        assert pack["rule"] == resolve.PACK_RULE and len(pack["text"]) < 6000
        assert not styling.search(pack["text"]), (t["id"], styling.search(pack["text"]).group())
        assert all(acc in pack["text"] for acc in t["provenance"]["accessions"])
    for tier in ("translation", "grounded", "interactions"):
        assert all(t["grounding"] is None for t in corpus[tier])
