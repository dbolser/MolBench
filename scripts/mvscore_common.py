"""
Shared code of the four MVS task generators (translation, grounded, interactions,
resolve): scene building, the held-back split, seeded choices, and the build / verify /
write loop. No network; everything is read from the frozen panel (``data/panel``), the
atom tables and ``data/mvscore``.

The generators that use it:

    scripts/generate_mvs_tasks.py          tasks/mvs_generated/      translation
    scripts/generate_grounded_tasks.py     tasks/mvs_grounded/       grounded
    scripts/author_interaction_tasks.py    tasks/mvs_interactions/   interactions
    scripts/generate_resolve_tasks.py      tasks/mvs_resolve/        resolve

Rules they share (FINAL_PLAN decisions 17, 18, 21):

* a reference holds only what the prompt states, and every representation has a colour
  the prompt states (an uncoloured representation is white in Mol*, which no prompt
  asks for), from ``molbench.drawn.TASK_PALETTE``;
* every reference is checked before it is written: the task schema, the corpus checks
  (``molbench.tasks.check_corpus`` with the benchmark's grader: success, F1 = 1,
  target score 1, no empty selection), and the generator's own check against the
  frozen mmCIF or atom table, recorded in ``provenance.checks``;
* a re-run reproduces the files byte for byte (``--check`` fails if it would not);
* no structure serves more than ``MAX_PER_STRUCTURE`` tasks of one tier, and no task
  uses 1HSG (the API prompt's worked example);
* held-back structures are one fixed set for the whole corpus (below).
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import pathlib
import random
import sys
from collections import Counter
from typing import Any, Callable, Iterable

REPO = pathlib.Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from molbench import drawn, grounding, mvs, runner, tasks as T  # noqa: E402
from molbench.atoms import AtomTable  # noqa: E402

DATA = REPO / "data" / "mvscore"
DATE = "2026-11-13"          # fixed, so a rebuild is byte-identical
SEED = 20261113
MAX_PER_STRUCTURE = 6        # tasks of one tier on one structure
HELDBACK_SHARE = 0.2
PALETTE = drawn.TASK_PALETTE

# --------------------------------------------------------------------------- #
# The held-back split (decision 21)
# --------------------------------------------------------------------------- #
HELDBACK_SEED = 2            # the smallest covering seed; a test re-derives it
HELDBACK_N = 15              # 20% of the 75 usable panel entries when the list was frozen
# The corpus-wide list, when the lead has frozen one: a JSON list of panel ids. It
# replaces the rule below (the API and accept-set generators read the same file).
HELDBACK_FILE = REPO / "data" / "panel" / "heldback.json"
# Held back whatever the hash says: the structure the fixture tasks
# (tests/fixtures/tasks) hold back, which the dry run mixes with the corpus.
ALSO_HELDBACK = ("8ce0",)
# What the held-back set must contain, so that every tier has held-back tasks of most
# of its templates: feature (as in panel.json) -> at least this many entries.
HELDBACK_NEEDS = {"ligand": 5, "heme": 1, "disulfide": 2, "metal": 4, "nucleic": 2,
                  "protein-dna": 1, "glycan": 2, "modified-residue": 1, "multi-chain": 4,
                  "clinical": 4, "uniprot-offset": 5, "auth-label-chain": 2,
                  "insertion-codes": 1}


def _has(entry: dict, feature: str) -> bool:
    if feature == "multi-chain":
        return len(grounding.facts(entry["id"])["chains"]) > 1
    return feature in entry["features"] or feature in entry["families"]


def heldback_candidates() -> list[dict]:
    """Panel entries that may be held back: never used by a task published before the
    final corpus (``used_by_tasks`` empty in panel.json), and not the worked example."""
    return [e for e in grounding.panel()["entries"]
            if not e["used_by_tasks"] and e["id"] != T.WORKED_EXAMPLE
            and not e.get("public_only")]      # joined the panel after the list was frozen


def _heldback_for(seed: int) -> list[dict]:
    def key(e: dict) -> str:
        return hashlib.sha256(f"molbench-heldback-{seed}:{e['id']}".encode()).hexdigest()
    forced = [e for e in heldback_candidates() if e["id"] in ALSO_HELDBACK]
    assert len(forced) == len(ALSO_HELDBACK), "a forced held-back entry is not a candidate"
    rest = sorted((e for e in heldback_candidates() if e["id"] not in ALSO_HELDBACK), key=key)
    return forced + rest[:HELDBACK_N - len(forced)]


def heldback_covers(chosen: list[dict]) -> bool:
    if not all(sum(_has(e, f) for e in chosen) >= n for f, n in HELDBACK_NEEDS.items()):
        return False
    return sum("clinical" in e["features"] and bool(e["offset"]) for e in chosen) >= 2


@functools.lru_cache(maxsize=None)
def heldback_structures() -> frozenset[str]:
    """The held-back structures of the whole corpus: one fixed set, the same in every
    tier, so no structure can be public in one tier and held back in another.

    If ``data/panel/heldback.json`` exists, it is the set. Otherwise the rule: 8CE0
    (held back by the fixture tasks), then the candidates (`heldback_candidates`) in
    order of SHA-256 of ``"molbench-heldback-<seed>:<id>"``, 15 in all (20% of the 75
    usable entries). The seed is the smallest non-negative integer whose set covers
    every feature in ``HELDBACK_NEEDS`` and has two disease proteins with a numbering
    offset; a test re-derives it."""
    if HELDBACK_FILE.exists():
        ids = json.loads(HELDBACK_FILE.read_text(encoding="utf-8"))
        known = {e["id"] for e in grounding.panel()["entries"]}
        assert set(ids) <= known and T.WORKED_EXAMPLE not in ids, "heldback.json: unknown ids"
        return frozenset(ids)
    chosen = _heldback_for(HELDBACK_SEED)
    assert heldback_covers(chosen), "the held-back seed no longer covers the panel"
    return frozenset(e["id"] for e in chosen)


def first_covering_seed(limit: int = 1000) -> int | None:
    return next((s for s in range(limit) if heldback_covers(_heldback_for(s))), None)


def split_of(entry: str) -> str:
    return "heldback" if entry in heldback_structures() else "public"


# --------------------------------------------------------------------------- #
# Seeded choices
# --------------------------------------------------------------------------- #
def rng(*key: Any) -> random.Random:
    """A random generator that depends only on the key (and the corpus seed)."""
    text = "|".join(str(k) for k in (SEED, *key))
    return random.Random(int(hashlib.sha256(text.encode()).hexdigest()[:16], 16))


def pick(options: list, *key: Any):
    return rng(*key).choice(options)


def shuffled(items: Iterable, *key: Any) -> list:
    out = sorted(items, key=lambda x: json.dumps(x, sort_keys=True, default=str))
    rng(*key).shuffle(out)
    return out


def colours(n: int, *key: Any, avoid: Iterable[str] = ("white", "black", "gray")) -> list[str]:
    """``n`` different palette colours, chosen by seed. White, black and grey are left
    out by default (grey is the usual context colour; white is the uncoloured default)."""
    pool = [c for c in PALETTE if c not in set(avoid)]
    return rng("colours", *key).sample(pool, n)


def say_colour(c: str) -> str:
    """A palette colour as written in a prompt."""
    return {"gray": "grey", "steelblue": "steel blue", "limegreen": "lime green",
            "hotpink": "hot pink"}.get(c, c)


# --------------------------------------------------------------------------- #
# Panel access
# --------------------------------------------------------------------------- #
def usable_entries() -> list[dict]:
    """Panel entries a task may use: all but the worked example."""
    return [e for e in grounding.panel()["entries"] if e["id"] != T.WORKED_EXAMPLE]


def pdb_entries() -> list[dict]:
    return [e for e in usable_entries() if e["kind"] == "pdb"]


def facts(entry: str) -> dict:
    return grounding.facts(entry)


def table(entry: str) -> AtomTable:
    t = T.table_for(entry)
    assert t is not None, f"no atom table for {entry}"
    return t


def n_atoms(mask: int) -> int:
    return bin(mask).count("1")


def url(entry: str) -> str:
    if entry.startswith("af-"):
        acc = entry.split("-")[1].upper()
        version = entry.rsplit("_", 1)[-1]
        return f"https://alphafold.ebi.ac.uk/files/AF-{acc}-F1-model_{version}.cif"
    return f"https://files.rcsb.org/download/{entry}.cif"


def inputs(entry: str, *more: str) -> list[str]:
    return [f"data/panel/facts/{entry}.json", f"molbench/atom_tables/{entry}.json.gz", *more]


def cif_input(entry: str) -> str:
    return f"data/panel/cif/{entry}.cif.gz"


# --------------------------------------------------------------------------- #
# Numbering facts for the paper's difficulty analysis
# --------------------------------------------------------------------------- #
def residue_rows(entry: str, selector: Any) -> list[int]:
    """One atom-table row per residue the selector touches."""
    t = table(entry)
    mask = t.selector(selector) or 0
    seen, rows = set(), []
    col = t.columns["residue_index"]
    i = 0
    while mask:
        if mask & 1 and col[i] not in seen:
            seen.add(col[i])
            rows.append(i)
        mask >>= 1
        i += 1
    return rows


def numbering_facts(entry: str, selector: Any) -> dict:
    """Whether naming these residues takes more than copying numbers: does the author
    residue number differ from the label (SEQRES) number, the author chain id from the
    label chain id, and is there an insertion code, on any residue of the selection."""
    t = table(entry)
    c = t.columns
    rows = residue_rows(entry, selector)
    polymer = t.static.get("polymer", 0)
    poly_rows = [r for r in rows if polymer >> r & 1]
    return {
        "author_number_differs_from_label": any(c["auth_seq_id"][r] != c["label_seq_id"][r]
                                                for r in poly_rows),
        "author_chain_differs_from_label": any(c["auth_asym_id"][r] != c["label_asym_id"][r]
                                               for r in rows),
        "insertion_code": any(bool(c["pdbx_PDB_ins_code"][r]) for r in rows),
    }


def difficulty(entry: str, selector: Any = None, *, ligand_identity: bool = False,
               uniprot_mapping: bool = False, structure_lookup: bool = False,
               **more: Any) -> dict:
    """The difficulty-relevant facts of a task, for ``provenance.difficulty``.

    ``needs_ligand_identity``: the prompt names a compound in words and the answer needs
    its component id. ``needs_uniprot_mapping``: the answer needs a UniProt -> structure
    residue mapping. ``needs_structure_lookup``: the atoms asked for are not named in the
    prompt and must be found in the entry (which cysteines are bonded, which residues
    hold the metal). The three numbering flags are about the residues the answer
    selects (`numbering_facts`); they are false when it selects none by number."""
    num = (numbering_facts(entry, selector) if selector is not None else
           {"author_number_differs_from_label": False, "author_chain_differs_from_label": False,
            "insertion_code": False})
    return {**num, "needs_ligand_identity": ligand_identity,
            "needs_uniprot_mapping": uniprot_mapping,
            "needs_structure_lookup": structure_lookup, **more}


# --------------------------------------------------------------------------- #
# Scene building (plain dicts, in the shape the molviewspec builder writes)
# --------------------------------------------------------------------------- #
def colour(name: str, selector: Any = None) -> dict:
    assert name in PALETTE, f"{name!r} is not a task palette colour"
    params: dict = {"color": name}
    if selector is not None:
        params["selector"] = selector
    return {"kind": "color", "params": params}


def theme(name: str) -> dict:
    """A Mol* colour theme (``chain-id``, ``entity-id``); the placeholder colour is what
    the MVS schema requires and Mol* ignores."""
    return {"kind": "color", "params": {"color": "white"},
            "custom": {"molstar_color_theme_name": name}}


def rep(rtype: str, *children: dict, opacity: float | None = None) -> dict:
    kids = list(children)
    if opacity is not None:
        kids.append({"kind": "opacity", "params": {"opacity": opacity}})
    node: dict = {"kind": "representation", "params": {"type": rtype}}
    if kids:
        node["children"] = kids
    return node


def comp(selector: Any, *children: dict, custom: dict | None = None) -> dict:
    node: dict = {"kind": "component", "params": {"selector": selector}}
    if children:
        node["children"] = list(children)
    if custom:
        node["custom"] = custom
    return node


def drawn_comp(selector: Any, rtype: str, colour_name: str, opacity: float | None = None) -> dict:
    return comp(selector, rep(rtype, colour(colour_name), opacity=opacity))


FOCUS = {"kind": "focus", "params": {}}


def distance(start: dict, end: dict) -> dict:
    """A dashed line between two atoms, labelled with its length."""
    return {"kind": "primitive",
            "params": {"kind": "distance_measurement", "start": start, "end": end,
                       "dash_length": 0.15, "label_template": "{{distance}}"}}


def primitives(*items: dict) -> dict:
    return {"kind": "primitives", "params": {}, "children": list(items)}


def scene(entry: str, children: list[dict]) -> dict:
    return {"root": {"kind": "root", "children": [
        {"kind": "download", "params": {"url": url(entry)}, "children": [
            {"kind": "parse", "params": {"format": "mmcif"}, "children": [
                {"kind": "structure", "params": {"type": "model"},
                 "children": children}]}]}]}}


def part(selector: Any, representation: str | None = None, colour_name: str | None = None) -> dict:
    """One part of a task ``target``."""
    return {"selector": selector, "representation": representation, "color": colour_name}


def residue(r: dict) -> dict:
    """The author-numbered selector of one residue record of the facts (chain, number,
    insertion code when there is one)."""
    out = {"auth_asym_id": r["auth_asym_id"], "auth_seq_id": r["auth_seq_id"]}
    if r.get("pdbx_PDB_ins_code"):
        out["pdbx_PDB_ins_code"] = r["pdbx_PDB_ins_code"]
    return out


def atom(r: dict, name: str | None = None) -> dict:
    return {**residue(r), "label_atom_id": name or r["atom"]}


def unique(records: Iterable[dict]) -> list[dict]:
    """Residue records without repeats, in order of first appearance."""
    seen, out = set(), []
    for r in records:
        key = (r["auth_asym_id"], r["auth_seq_id"], r.get("pdbx_PDB_ins_code") or "")
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def mask_of(entry: str, selector: Any) -> int:
    m = table(entry).selector(selector)
    assert m is not None, f"{entry}: selector cannot be resolved: {selector}"
    return m


# --------------------------------------------------------------------------- #
# The frozen mmCIF, read afresh with gemmi (the independent check on the facts)
# --------------------------------------------------------------------------- #
def rkey(r: dict) -> tuple:
    return (r["auth_asym_id"], r["auth_seq_id"], r.get("pdbx_PDB_ins_code") or "")


@functools.lru_cache(maxsize=4)
def cif_structure(entry: str):
    import gemmi
    st = gemmi.read_structure(str(grounding.structure_file(entry)))
    st.setup_entities()
    return st


def cif_atoms(entry: str, r: dict, name: str) -> list:
    """The atoms (one per alternate conformer) with this name in the residue a facts
    record names, in model 1 of the frozen mmCIF."""
    out = []
    for chain in cif_structure(entry)[0]:
        if chain.name != r["auth_asym_id"]:
            continue
        for res in chain:
            if res.seqid.num == r["auth_seq_id"] \
                    and res.seqid.icode.strip() == (r.get("pdbx_PDB_ins_code") or "") \
                    and r.get("comp_id") in (None, res.name):
                out += [a for a in res if a.name == name]
    return out


def cif_distance(entry: str, a: dict, a_name: str, b: dict, b_name: str) -> float:
    """Distance in A between two named atoms (first conformer of each) in the frozen mmCIF."""
    x, y = cif_atoms(entry, a, a_name), cif_atoms(entry, b, b_name)
    assert x and y, f"{entry}: atom not found: {a} {a_name} / {b} {b_name}"
    return x[0].pos.dist(y[0].pos)


def _search(entry: str):
    import gemmi
    st = cif_structure(entry)
    return gemmi.NeighborSearch(st[0], st.cell, 6).populate(include_h=False)


def cif_neighbours(entry: str, records: list[dict], atom_name: str, radius: float,
                   elements: tuple = ("N", "O", "S")) -> set[tuple]:
    """Polymer residues with an N, O or S atom within ``radius`` of the named atom of
    any of the records, crystal-symmetry copies included."""
    import gemmi
    st = cif_structure(entry)
    ns = _search(entry)
    out = set()
    for r in records:
        for atom in cif_atoms(entry, r, atom_name):
            for mark in ns.find_atoms(atom.pos, "\0", radius=radius):
                cra = mark.to_cra(st[0])
                if cra.residue.entity_type == gemmi.EntityType.Polymer \
                        and cra.atom.element.name in elements:
                    out.add((cra.chain.name, cra.residue.seqid.num, cra.residue.seqid.icode.strip()))
    return out


def cif_close_pairs(entry: str, comp: str, atom_name: str, radius: float) -> set[frozenset]:
    """Pairs of residues of one kind whose named atoms are within ``radius`` of each
    other in the deposited model (no symmetry copies)."""
    st = cif_structure(entry)
    atoms = [((chain.name, res.seqid.num, res.seqid.icode.strip()), a)
             for chain in st[0] for res in chain if res.name == comp
             for a in res if a.name == atom_name]
    out = set()
    for i, (ka, a) in enumerate(atoms):
        for kb, b in atoms[i + 1:]:
            if ka != kb and a.pos.dist(b.pos) <= radius:
                out.add(frozenset((ka, kb)))
    return out


def cif_secondary(entry: str) -> tuple[list[tuple], list[tuple]]:
    """Helix and strand ranges (author chain, first and last author number) as the
    frozen mmCIF records them; a strand in two sheets is listed once."""
    st = cif_structure(entry)
    helices = sorted((h.start.chain_name, h.start.res_id.seqid.num, h.end.res_id.seqid.num)
                     for h in st.helices)
    strands = sorted({(s.start.chain_name, s.start.res_id.seqid.num, s.end.res_id.seqid.num)
                      for sheet in st.sheets for s in sheet.strands})
    return helices, strands


# --------------------------------------------------------------------------- #
# Words
# --------------------------------------------------------------------------- #
_ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
         "ten", "eleven", "twelve"]


def number(n: int) -> str:
    return _ONES[n] if 0 <= n < len(_ONES) else str(n)


def article(word: str) -> str:
    return "an " if word[:1].lower() in "aeiou" else "a "


def join(words: list[str], last: str = "and") -> str:
    words = list(words)
    if len(words) <= 1:
        return "".join(words)
    if len(words) == 2:
        return f"{words[0]} {last} {words[1]}"
    return ", ".join(words[:-1]) + f" {last} {words[-1]}"


REP_WORDS = {"cartoon": "cartoon", "ball_and_stick": "ball-and-stick", "spacefill": "spheres",
             "surface": "surface", "line": "lines", "backbone": "backbone trace"}

# Words that belong to the file format or the selector syntax, not to a request. A
# prompt may not contain them (checked for every task).
FORBIDDEN_WORDS = ("label_", "auth_", "asym", "seq_id", "comp_id", "atom_id", "selector",
                   "component", "molviewspec", " mvs", "struct_conn", "sifts", "mmcif",
                   "ball_and_stick", "entity id", "label chain", "author chain", "{", "}")


def prompt_problems(prompt: str) -> list[str]:
    low = prompt.lower()
    out = [f"prompt contains {w!r}" for w in FORBIDDEN_WORDS if w in low]
    if "  " in prompt or prompt != prompt.strip():
        out.append("prompt has stray spaces")
    if T.WORKED_EXAMPLE in low:
        out.append("prompt names the worked example")
    return out


# --------------------------------------------------------------------------- #
# Tasks
# --------------------------------------------------------------------------- #
def make_task(tid: str, tier: str, family: str, entry: str, prompt: str, reference: dict,
              target: list[dict] | None, *, script: str, input_files: list[str],
              derivation: str, difficulty: dict, checks: list[str] | None = None,
              accepted: list[dict] | None = None, extra_skills: Iterable[str] = (),
              provenance: dict | None = None, **more: Any) -> dict:
    """One task in the final format. ``derivation`` says in words how the reference
    was derived; ``checks`` are the generator's own checks (the common ones are added
    by `verify`)."""
    skills = list(mvs.categorize(reference["root"]))
    for s in extra_skills:
        if s not in skills:
            skills.append(s)
    return {
        "id": tid, "track": "mvs", "tier": tier, "family": family, "structures": [entry],
        "prompt": prompt, "reference": reference, "accepted": accepted or [],
        "context": None, "target": target, "twin_of": None, "paraphrase_of": None,
        "style": "full", "split": split_of(entry), "grounding": None,
        "provenance": {"script": script, "inputs": input_files, "date": DATE,
                       "checks": list(checks or []), "derivation": derivation,
                       "difficulty": difficulty, **(provenance or {})},
        "skills": skills, **more}


class Picker:
    """Chooses the structures of one tier: seeded, least-used structure first, never
    more than ``MAX_PER_STRUCTURE`` tasks on one structure, and a held-back share."""

    def __init__(self, tier: str):
        self.tier = tier
        self.used: Counter = Counter()

    def choose(self, family: str, candidates: list, n: int, entry_of: Callable = lambda c: c,
               per_structure: int = 1) -> list:
        """Up to ``n`` candidates of a template: about ``HELDBACK_SHARE`` of them on
        held-back structures, the rest public; within each split in a seeded order,
        structures with fewer tasks of this tier first, at most ``per_structure`` per
        structure for this template."""
        order = shuffled(candidates, self.tier, family)
        held = [c for c in order if split_of(entry_of(c)) == "heldback"]
        public = [c for c in order if split_of(entry_of(c)) == "public"]
        n_held = min(len({entry_of(c) for c in held}) * per_structure,
                     max(1, round(n * HELDBACK_SHARE)) if held else 0)
        out: list = []
        for pool, quota in ((held, n_held), (public, n - n_held)):
            mine: Counter = Counter()
            for _ in range(quota):
                best = None
                for c in pool:
                    e = entry_of(c)
                    if c in out or mine[e] >= per_structure \
                            or self.used[e] >= MAX_PER_STRUCTURE:
                        continue
                    if best is None or self.used[e] < self.used[entry_of(best)]:
                        best = c
                if best is None:
                    break
                out.append(best)
                mine[entry_of(best)] += 1
                self.used[entry_of(best)] += 1
        return out


def enough(family: str, chosen: list, n: int) -> None:
    """A template must yield its full count under the built-in held-back rule. Under a
    held-back list given as a file, the structures on each side of the split are not
    ours to choose, so a shortfall is reported, not refused."""
    if len(chosen) == n:
        return
    message = f"{family}: only {len(chosen)} of {n} tasks could be built"
    assert HELDBACK_FILE.exists(), message
    print(f"note: {message} with the held-back list of {HELDBACK_FILE.name}", file=sys.stderr)


def verify(built: list[dict], out_dir: pathlib.Path) -> list[dict]:
    """Run the format and corpus checks on the built tasks (the benchmark's own grader
    grades every reference) and record what each task passed."""
    ids = Counter(t["id"] for t in built)
    assert not [i for i, n in ids.items() if n > 1], [i for i, n in ids.items() if n > 1]
    loaded = []
    for t in built:
        own = t["provenance"]["checks"]
        t["provenance"]["checks"] = own or ["(filled in below)"]
        problems = T.validate_task(t) + prompt_problems(t["prompt"])
        if problems:
            raise SystemExit(f"{t['id']}: " + "; ".join(problems))
        t["provenance"]["checks"] = own
        rel = (out_dir / f"{t['id']}.json").relative_to(REPO)
        full = T._with_aliases({**json.loads(json.dumps(t)), "_path": str(rel)})
        full["provenance"]["checks"] = own or ["x"]
        loaded.append(full)
    errors, _ = T.check_corpus(loaded, grade=runner.grade_parsed, final=True,
                               check=runner.grader_problems)
    if errors:
        raise SystemExit("tasks fail the corpus checks:\n  " + "\n  ".join(errors))
    for t, full in zip(built, loaded):
        used = _colours_used(t["reference"]) | {c for a in t["accepted"] for c in _colours_used(a)}
        assert used <= set(PALETTE), f"{t['id']}: colours outside the palette: {used}"
        common = ["reference grades as exactly right against the task with the benchmark's "
                  "grader (success, F1 = 1, target score 1); no selection is empty"]
        if t["target"]:
            atoms = sum(n_atoms(m) for m in T.target_atoms(full).values())
            common.append(f"target selects {atoms} atoms on the frozen atom table")
        if t["accepted"]:
            common.append("every accepted alternative grades as itself and is accepted by "
                          "the task")
        t["provenance"]["checks"] = t["provenance"]["checks"] + common
    return built


def _colours_used(tree: Any) -> set[str]:
    out: set[str] = set()

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            if x.get("kind") == "color" and not (x.get("custom") or {}).get(
                    "molstar_color_theme_name"):
                out.add((x.get("params") or {}).get("color"))
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(tree)
    return out


def dump(task: dict) -> str:
    return json.dumps(task, indent=1, ensure_ascii=False) + "\n"


def write_all(built: list[dict], out_dir: pathlib.Path, check: bool, readme: str | None = None,
              keep: Iterable[str] = ()) -> int:
    """Write one file per task (and the README); remove task files that are no longer
    built. With ``check``, write nothing and return 1 if anything would change."""
    # A link to an API twin is written into the task file afterwards, by
    # scripts/translate_mvs_to_api.py; a rebuild keeps the link the file already has.
    for t in built:
        path = out_dir / f"{t['id']}.json"
        if t.get("twin_of") is None and path.exists():
            t["twin_of"] = json.loads(path.read_text(encoding="utf-8")).get("twin_of")
    files = {out_dir / f"{t['id']}.json": dump(t) for t in built}
    if readme is not None:
        files[out_dir / "README.md"] = readme
    stale = sorted(p for p in out_dir.glob("*.json") if p not in files and p.name not in keep)
    changed = [p for p, text in files.items()
               if not p.exists() or p.read_text(encoding="utf-8") != text]
    rel = out_dir.relative_to(REPO)
    if check:
        if changed or stale:
            print(f"{rel} is out of date:", *[p.name for p in changed + stale][:20])
            return 1
        print(f"{rel}: {len(built)} tasks are up to date")
        return 0
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in stale:
        p.unlink()
    for p, text in files.items():
        p.write_text(text, encoding="utf-8")
    print(f"{rel}: wrote {len(built)} tasks ({len(changed)} files changed, {len(stale)} removed)")
    return 0


def summary_tables(built: list[dict]) -> str:
    """The counts every README carries: tasks per template and split, structures."""
    fams = sorted({t["family"] for t in built})
    lines = ["| template | public | held back | total | share |", "|---|---:|---:|---:|---:|"]
    for f in fams:
        mine = [t for t in built if t["family"] == f]
        held = sum(t["split"] == "heldback" for t in mine)
        lines.append(f"| `{f}` | {len(mine) - held} | {held} | {len(mine)} | "
                     f"{100 * len(mine) / len(built):.0f}% |")
    held = sum(t["split"] == "heldback" for t in built)
    lines.append(f"| **all** | {len(built) - held} | {held} | {len(built)} | 100% |")
    per = Counter(t["structures"][0] for t in built)
    held_s = sorted(s for s in per if s in heldback_structures())
    lines += ["", f"Structures: {len(per)} ({len(held_s)} held back: "
              f"{', '.join(s.upper() for s in held_s)}). Most tasks on one structure: "
              f"{max(per.values())} (cap {MAX_PER_STRUCTURE})."]
    return "\n".join(lines)


INTERACTIONS_FLAG = "molstar_show_non_covalent_interactions"


def viewer_check(built: list[dict], cache: pathlib.Path | None = None) -> int:
    """Load the reference and every accepted alternative of every task in headless Mol*
    (the pinned bundle, the frozen structure file) and compare what the viewer's own
    representation objects draw (type, colour, opacity, atoms) with the grader's
    resolved state of the same scene. Returns the number of scenes that differ or do
    not load. A scene with Mol*'s computed-interactions display switched on is held to
    less: every draw of the grader must be in the viewer's state. Lines, labels and the camera are not read back: for a measured line the
    check is the atom-table one in ``provenance.checks``. Needs the ``execute`` extra
    and Playwright's Chromium; nothing is written to the tasks."""
    import importlib.util
    import tempfile
    spec = importlib.util.spec_from_file_location("grader_controls",
                                                  REPO / "scripts" / "grader_controls.py")
    gc = importlib.util.module_from_spec(spec)
    sys.modules["grader_controls"] = gc
    spec.loader.exec_module(gc)
    cache = cache or pathlib.Path(tempfile.mkdtemp(prefix="mvscore-viewer-"))
    bad = n = 0
    with gc.Molstar(cache) as viewer:
        for t in built:
            for i, tree in enumerate([t["reference"]] + t["accepted"]):
                n += 1
                try:
                    seen = viewer.state(tree)
                except Exception as e:  # noqa: BLE001
                    seen = f"{type(e).__name__}: {str(e).splitlines()[0][:200]}"
                if isinstance(seen, str):
                    ok = False
                elif INTERACTIONS_FLAG in json.dumps(tree):
                    # With the flag Mol* also draws the surroundings of the component
                    # (its own computation, which the grader does not model): every
                    # draw of the grader must be there, on at least its atoms.
                    mine = gc.grader_state(tree)
                    ok = bool(mine) and all(seen.get(d, 0) & m == m for d, m in mine.items())
                else:
                    ok = gc._grader_vs_viewer(tree, seen)
                bad += not ok
                name = "reference" if i == 0 else f"accepted {i}"
                print(f"viewer  {t['id']} [{name}]: {'agrees' if ok else 'DIFFERS'}"
                      + (f" ({seen[:160]})" if isinstance(seen, str) else ""), flush=True)
    version = (REPO / "molbench" / "static" / "molstar" / "VERSION").read_text().strip()
    print(f"viewer: {n} scenes of {len(built)} tasks loaded in Mol* {version}; {bad} differ")
    return bad


def finish(built: list[dict], out_dir: pathlib.Path, args: argparse.Namespace,
           readme: str | None = None) -> int:
    """Write (or, with --check, compare) the task files; with --viewer also run the
    Mol* read-back, which fails the command if any scene differs."""
    status = write_all(built, out_dir, args.check, readme)
    if args.viewer:
        status = status or (1 if viewer_check(built) else 0)
    return status


def cli(doc: str) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=doc.strip().split("\n\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="write nothing; fail if the task files would change")
    ap.add_argument("--viewer", action="store_true",
                    help="also load every reference in headless Mol* and compare what it "
                         "draws with the grader's resolved state")
    ap.add_argument("--refresh", action="store_true",
                    help="re-download the frozen inputs this generator owns (network)")
    return ap.parse_args()
