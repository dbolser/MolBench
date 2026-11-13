"""
The API-track generator (``scripts/generate_api_tasks.py``): the files on disk are what
the script writes, and the corpus it writes obeys the generator rules of the brief.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from collections import Counter

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


gen = _load("generate_api_tasks")


@pytest.fixture(scope="module")
def built():
    cur, generated, info = gen.build_all()
    return cur, generated, info


def test_files_on_disk_are_what_the_script_writes(built):
    """Byte for byte: a second build gives the same text, and it is the text on disk."""
    cur, generated, info = built
    import copy
    wanted = gen.files(copy.deepcopy(cur), copy.deepcopy(generated), info)
    again = gen.files(*gen.build_all())
    assert {p: t for p, t in wanted.items()} == again
    for path, text in wanted.items():
        assert path.read_text() == text, path
    on_disk = {p for d in (gen.OUT_CURATED, gen.OUT_GENERATED) for p in d.iterdir()
               if p.suffix in (".json", ".md")}
    assert on_disk == set(wanted)


def test_counts(built):
    cur, generated, _ = built
    assert len(cur) == 20
    assert len(generated) >= 110
    assert sum(t["tier"] == "tool_only" for t in generated) >= 25
    ids = [t["id"] for t in cur + generated]
    assert len(ids) == len(set(ids))


def test_no_task_uses_the_worked_example(built):
    cur, generated, _ = built
    for t in cur + generated:
        assert not gen.T._mentions_worked_example(t), t["id"]


def test_reuse_caps(built):
    """No structure in more than 6 tasks of a tier; no template above ~12% of a tier."""
    cur, generated, _ = built
    tasks = cur + generated
    per = Counter((t["tier"], s) for t in tasks for s in t["structures"])
    assert max(per.values()) <= 6, per.most_common(3)
    tiers = Counter(t["tier"] for t in tasks)
    for (tier, family), n in Counter((t["tier"], t["family"]) for t in tasks).items():
        assert n / tiers[tier] <= 0.125, (tier, family, n, tiers[tier])


def test_heldback_split(built):
    """About a fifth of each tier's structures are held back, and a held-back structure
    is in no public task (of any tier)."""
    cur, generated, info = built
    tasks = cur + generated
    held = set(info["held"])
    public = {s for t in tasks if t["split"] == "public" for s in t["structures"]}
    back = {s for t in tasks if t["split"] == "heldback" for s in t["structures"]}
    assert not public & back
    assert back <= held and not public & held
    for tier in {t["tier"] for t in tasks}:
        mine = [t for t in tasks if t["tier"] == tier]
        st = {s for t in mine for s in t["structures"]}
        hs = {s for t in mine if t["split"] == "heldback" for s in t["structures"]}
        assert 0.12 <= len(hs) / len(st) <= 0.30, (tier, len(hs), len(st))


def test_quirk_share_is_capped(built):
    """At most a tenth of the track hinges on 'color does not colour an added
    representation' (the lead's ruling on open question 1 of phase A)."""
    cur, generated, _ = built
    tasks = cur + generated
    n = sum("added_representation_colour" in t["provenance"]["difficulty"]["hinges_on"] for t in tasks)
    assert n / len(tasks) <= 0.10, n


def test_difficulty_facts_are_recorded(built):
    cur, generated, _ = built
    for t in cur + generated:
        d = t["provenance"]["difficulty"]
        for key in ("numbering_offset", "auth_label_chain", "ligand_identity_needed", "uniprot_mapping",
                    "hinges_on"):
            assert key in d, (t["id"], key)
        assert d["ligand_identity_needed"] is False      # every ligand is named by its code
    assert sum(t["provenance"]["difficulty"]["numbering_offset"] for t in generated) >= 40
    assert sum(t["provenance"]["difficulty"]["uniprot_mapping"] for t in generated) >= 12
    assert sum(t["provenance"]["difficulty"]["auth_label_chain"] for t in generated) >= 10


def test_wordings_vary(built):
    """Each template has several wordings and the seed spreads tasks over them."""
    _, generated, _ = built
    by_family: dict[str, set] = {}
    for t in generated:
        by_family.setdefault(t["family"], set()).add(t["provenance"]["wording"])
    assert sum(len(w) > 1 for w in by_family.values()) >= 0.7 * len(by_family)


def test_prompts_do_not_leak_the_selector_syntax(built):
    """A request is worded as a scientist would word it: no API key names."""
    _, generated, _ = built
    banned = ("auth_", "label_", "residue_number", "struct_asym", "entity_id", "uniprot_accession",
              "representationColor", "keep_colors", "non_selected", "hide_", "custom_data", "molecule_id")
    for t in generated:
        assert not any(b in t["prompt"] for b in banned), (t["id"], t["prompt"])


def test_a_wrong_reference_is_refused(built):
    """`verify` is not vacuous: the July mistake (author number in the label key) is caught."""
    _, generated, _ = built
    import copy
    task = copy.deepcopy(next(t for t in generated if t["family"] == "api-residue-colour"))
    for p in task["reference"][1]["data"]:
        p["residue_number"] = p.pop("auth_seq_id")
    task["provenance"]["checks"] = []
    with pytest.raises(gen.Unfit):
        gen.verify(task, {"alts": [], "traps": []})
