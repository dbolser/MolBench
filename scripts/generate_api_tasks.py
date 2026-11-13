#!/usr/bin/env python3
"""
Generate the API-track tasks: ``tasks/api_calling/`` (the 20 curated tasks, rebuilt in
the task format) and ``tasks/api_generated/`` (the generated ones). $0, no network.

    uv run python scripts/generate_api_tasks.py            # rewrite both directories
    uv run python scripts/generate_api_tasks.py --check    # fail if a file would change
    uv run python scripts/generate_api_tasks.py --report   # counts and the coverage table

Everything is read from the frozen panel (``data/panel/facts``, ``molbench/atom_tables``,
``molbench/sifts_tables``). A reference is assembled from those facts by a template and
is then checked, before the file is written, against a second statement of the atoms it
is meant to select (author chain, author number *and residue name*, resolved by the MVS
atom resolver): see ``verify``. Nothing is hand-guessed; a template that cannot make an
exactly checkable task on a structure skips that structure.

Determinism: the only sources of variation are ``SEED`` and the panel. Structures,
residues, colours and wordings are chosen by SHA-256 of ``SEED`` and a key, so a re-run
reproduces every file byte for byte (``--check``).

Held-back split: a seeded fifth of the panel entries that no earlier task used (see
``heldback_structures``). Every task on such a structure is ``split: heldback``; no
public task of this script uses one. ``data/panel/heldback.json`` (a JSON list of ids),
if the lead adds it, overrides the rule so that every generator shares one list.

``tasks/api_generated/README.md`` (written by this script) lists the templates, the
counts and how each reference is derived.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import pathlib
import re
import sys
from collections import Counter
from typing import Any, Callable

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import grounding, runner, sifts  # noqa: E402
from molbench import pdbe_state as ps  # noqa: E402
from molbench import tasks as T  # noqa: E402
from molbench.drawn import TASK_PALETTE  # noqa: E402
from molbench.models import perturb_reference  # noqa: E402

_spec = importlib.util.spec_from_file_location("check_api_refs", REPO / "scripts" / "check_api_refs.py")
check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check)

SCRIPT = "scripts/generate_api_tasks.py"
SEED = 20261113
DATE = "2026-11-12"            # the panel's retrieval date: fixed, so a rebuild is byte-identical
OUT_GENERATED = REPO / "tasks" / "api_generated"
OUT_CURATED = REPO / "tasks" / "api_calling"
HELDBACK_FILE = REPO / "data" / "panel" / "heldback.json"
HELDBACK_SHARE = 0.20
#: Held back whatever the rule says: the structure the fixture tasks hold back
#: (tests/fixtures/tasks, added to a dry run while the corpus lacks some kind of task),
#: so that no structure is in both splits.
ALSO_HELDBACK = ("8ce0",)
MAX_PER_STRUCTURE = 4          # generated tasks per structure and tier (the brief's cap is ~6)

AA = ("ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL").split()
ONE = dict(zip(AA, "ARNDCQEGHILKMFPSTWYV"))
# crystallisation additives: real components, but not what a request would be about
ADDITIVES = {"SO4", "PO4", "GOL", "EDO", "PEG", "DMS", "MPD", "TRS", "ACT", "BME", "P33", "SCN",
             "GLY", "TLA", "BNG", "C8E", "LI1", "SQU", "STE", "DGA", "F09"}
COLOUR_WORDS = {"steelblue": "steel blue", "limegreen": "lime green", "hotpink": "hot pink",
                "gray": "grey"}
BRIGHT = [c for c in TASK_PALETTE if c not in ("white", "black", "gray")]
STYLE_WORDS = {"spacefill": "spacefill", "ball-and-stick": "ball-and-stick",
               "molecular-surface": "a molecular surface", "gaussian-surface": "a Gaussian surface",
               "putty": "putty", "cartoon": "a cartoon"}
OLIGOMER = {"dimeric": "dimer", "trimeric": "trimer", "tetrameric": "tetramer",
            "hexameric": "hexamer", "dodecameric": "dodecamer", "24-meric": "24-mer"}


# --------------------------------------------------------------------------- #
# Seeded choices
# --------------------------------------------------------------------------- #
def h(*key: Any) -> int:
    return int(hashlib.sha256("|".join(map(str, (SEED,) + key)).encode()).hexdigest(), 16)


def pick(seq: list, *key: Any) -> Any:
    return seq[h(*key) % len(seq)]


def shuffled(seq: list, *key: Any) -> list:
    def ident(x: Any) -> Any:
        if isinstance(x, dict):      # a residue, or an entity of the facts
            return x.get("id") or (x["ac"], x["an"], x["ins"])
        return x
    return sorted(seq, key=lambda x: h(*key, ident(x)))


def colours(n: int, *key: Any) -> list[str]:
    return shuffled(BRIGHT, "colour", *key)[:n]


def cw(c: str) -> str:
    return COLOUR_WORDS.get(c, c)


def listing(words: list[str]) -> str:
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


# --------------------------------------------------------------------------- #
# A panel structure, as the templates see it
# --------------------------------------------------------------------------- #
class S:
    """One panel entry: facts, atom table, SIFTS table, and its residues."""

    def __init__(self, entry: dict):
        self.entry = entry
        self.id: str = entry["id"]
        self.kind: str = entry["kind"]
        self.facts: dict = grounding.facts(self.id)
        self.table = T.table_for(self.id)
        self.sifts = sifts.load(self.id)
        self.poly: int = self.table.static.get("polymer", 0)
        self.chains: list[dict] = self.facts["chains"]
        c = self.table.columns
        by_res: dict[int, dict] = {}
        for i, ri in enumerate(c["residue_index"]):
            r = by_res.get(ri)
            if r is None:
                r = by_res[ri] = {"ac": c["auth_asym_id"][i], "an": c["auth_seq_id"][i],
                                  "ins": c["pdbx_PDB_ins_code"][i], "lc": c["label_asym_id"][i],
                                  "ls": c["label_seq_id"][i], "comp": c["label_comp_id"][i],
                                  "mask": 0}
            r["mask"] |= 1 << i
        self.residues: list[dict] = list(by_res.values())
        for r in self.residues:
            r["poly"] = bool(r["mask"] & self.poly)
        self.state = ps.replay([self.load()])
        self.components: dict[str, int] = self.state.components()

    # -- loading -----------------------------------------------------------------
    @property
    def name(self) -> str:
        """How a request names the entry."""
        return self.id.upper()

    @property
    def canonical(self) -> str:
        return ps.canonical_entry(self.load().get("molecule_id"), self.load().get("custom_data"))

    def load(self, **more: Any) -> dict:
        if self.kind == "pdb":
            return {"action": "load", "molecule_id": self.id, **more}
        acc, frag, version = re.fullmatch(r"af-([a-z0-9]+)-f(\d+)-model_v(\d+)", self.id).groups()
        return {"action": "load", "custom_data": {
            "url": f"https://alphafold.ebi.ac.uk/files/AF-{acc.upper()}-F{frag}-model_v{version}.cif",
            "format": "cif", "binary": False}, **more}

    @property
    def inputs(self) -> list[str]:
        out = [f"data/panel/facts/{self.id}.json", f"molbench/atom_tables/{self.id}.json.gz"]
        if self.sifts is not None:
            out.append(f"molbench/sifts_tables/{self.id}.json.gz")
        return out

    # -- atoms -------------------------------------------------------------------
    def mask(self, **cols: Any) -> int:
        m = (1 << self.table.n) - 1
        for col, val in cols.items():
            m &= self.table.index(col).get(val, 0)
        return m

    def addressable(self, r: dict) -> bool:
        """The residue is the only thing with its author chain and number, so the
        author keys name it exactly (pdbe-molstar 3.3.2 ignores insertion codes, and
        waters or ligands can share a number with a residue)."""
        return not r["ins"] and self.mask(auth_asym_id=r["ac"], auth_seq_id=r["an"]) == r["mask"]

    def amino_acids(self, chain: str | None = None, offset: bool = False) -> list[dict]:
        return [r for r in self.residues
                if r["poly"] and r["comp"] in AA and (chain is None or r["ac"] == chain)
                and self.addressable(r) and (not offset or r["an"] != r["ls"])]

    @property
    def multi_chain(self) -> bool:
        return len(self.chains) > 1

    def of_chain(self, chain: str) -> str:
        return f" of chain {chain}" if self.multi_chain else ""

    def label_chains_of(self, auth_chain: str) -> list[str]:
        """Every label chain with atoms on the author chain (read off the atom table)."""
        c = self.table.columns
        return sorted({lc for lc, ac in zip(c["label_asym_id"], c["auth_asym_id"]) if ac == auth_chain})


def res_word(r: dict) -> str:
    return f"{r['comp'].capitalize()}{r['an']}"


def res_words(s: S, rs: list[dict]) -> str:
    """'His57, Asp102 and Ser195 of chain A' (the chain only where there are several)."""
    chains = sorted({r["ac"] for r in rs})
    if not s.multi_chain:
        return listing([res_word(r) for r in rs])
    if len(chains) == 1:
        return listing([res_word(r) for r in rs]) + f" of chain {chains[0]}"
    return listing([f"{res_word(r)} of chain {r['ac']}" for r in rs])


def lig_words(lig: dict) -> str:
    if lig["heme"]:
        return f"heme ({lig['comp_id']})"
    name = lig["name"].lower()
    if len(name) <= 30 and re.fullmatch(r"[a-z0-9 ,'()+-]+", name):
        return f"{name} ({lig['comp_id']})"
    return f"ligand {lig['comp_id']}"


def lig_phrase(lig: dict, chain: str | None = None) -> tuple[str, str]:
    """('the heme (HEM) bound to chain B' | 'both copies of the ...' | 'the ...', 'it' | 'them')."""
    n = len(lig["copies"])
    if chain:
        return f"the {lig_words(lig)} bound to chain {chain}", "it"
    if n == 1:
        return f"the {lig_words(lig)}", "it"
    return f"{'both' if n == 2 else f'all {n}'} copies of the {lig_words(lig)}", "them"


# --------------------------------------------------------------------------- #
# Selections: the API param, and the same atoms stated a second time
# --------------------------------------------------------------------------- #
def sel(param: dict, what: str, atoms: Any, **attrs: Any) -> dict:
    """An API selection with its intended atoms attached (``_t``; stripped on writing).
    ``atoms`` is an MVS selector that names the same atoms another way."""
    return {**param, **attrs, "_t": {"what": what, "atoms": atoms}}


def residue_atoms(r: dict) -> dict:
    return {"auth_asym_id": r["ac"], "auth_seq_id": r["an"], "auth_comp_id": r["comp"]}


def by_author(r: dict, **attrs: Any) -> dict:
    return sel({"auth_asym_id": r["ac"], "auth_seq_id": r["an"]}, res_word(r), [residue_atoms(r)], **attrs)


def by_label(r: dict, **attrs: Any) -> dict:
    return {"struct_asym_id": r["lc"], "residue_number": r["ls"], **attrs}


def ligand_sel(lig: dict, chain: str | None = None, **attrs: Any) -> dict:
    copies = [c for c in lig["copies"] if chain is None or c["auth_asym_id"] == chain]
    atoms = [{"auth_asym_id": c["auth_asym_id"], "auth_seq_id": c["auth_seq_id"],
              "auth_comp_id": lig["comp_id"]} for c in copies]
    param = {"label_comp_id": lig["comp_id"], **({"auth_asym_id": chain} if chain else {})}
    return sel(param, lig["comp_id"] + (f" on chain {chain}" if chain else ""), atoms, **attrs)


def strip(actions: list[dict]) -> tuple[list[dict], list[dict]]:
    """The reference without the ``_t`` notes, and the provenance targets they give."""
    out, targets = [], []
    for ai, act in enumerate(actions):
        act = copy.deepcopy(act)
        for pi, p in enumerate(act.get("data") or []):
            note = p.pop("_t", None)
            if note is not None:
                targets.append({"what": note["what"], "action": ai, "param": pi, "atoms": note["atoms"]})
        out.append(act)
    return out, targets


def color_call(data: list[dict], **more: Any) -> dict:
    return {"action": "color", "data": data, **more}


def prop(name: str, value: Any) -> dict:
    return {"action": "set_property", "name": name, "value": value}


def style(name: str) -> dict:
    return {"action": "set_visual_style", "style": name}


# --------------------------------------------------------------------------- #
# Held-back split
# --------------------------------------------------------------------------- #
def heldback_structures() -> list[str]:
    """Panel entries whose tasks are held back. Rule: of the entries no task used before
    this corpus (``used_by_tasks`` empty in ``panel.json``; never 1HSG), ranked by
    SHA-256 of "molbench-heldback-v1|<id>", the first ``HELDBACK_SHARE`` of the panel
    (``ALSO_HELDBACK`` first).
    The rule has no generator-specific input, so any generator can apply it and get the
    same list; ``data/panel/heldback.json`` overrides it."""
    if HELDBACK_FILE.exists():
        return sorted(json.loads(HELDBACK_FILE.read_text()))
    entries = [e for e in grounding.panel()["entries"] if e["id"] != T.WORKED_EXAMPLE]
    free = [e["id"] for e in entries if not e["used_by_tasks"]]
    free.sort(key=lambda i: hashlib.sha256(f"molbench-heldback-v1|{i}".encode()).hexdigest())
    forced = [i for i in ALSO_HELDBACK if any(e["id"] == i for e in entries)]
    free = [i for i in free if i not in forced]
    return sorted(forced + free[:round(HELDBACK_SHARE * len(entries)) - len(forced)])


# --------------------------------------------------------------------------- #
# Templates. Each returns a dict (prompts, reference, ...) or None if the structure
# cannot carry an exactly checkable task of that kind.
# --------------------------------------------------------------------------- #
def offset_chain(s: S, key: str) -> dict | None:
    """A protein chain whose author numbers differ from the label numbers."""
    chains = [c for c in s.chains if c["polymer_type"] == "protein"
              and any(int(k) != 0 for k in c["auth_minus_label"])
              and len(s.amino_acids(c["auth_asym_id"], offset=True)) >= 3]
    return pick(chains, key, s.id) if chains else None


def chosen_residues(s: S, key: str, n: int) -> list[dict] | None:
    chain = offset_chain(s, key)
    if chain is None:
        return None
    pool = shuffled(s.amino_acids(chain["auth_asym_id"], offset=True), key, s.id)
    picked, names = [], set()
    for r in pool:                          # different residue types read better
        if r["comp"] not in names:
            picked.append(r)
            names.add(r["comp"])
        if len(picked) == n:
            break
    return sorted(picked, key=lambda r: r["an"]) if len(picked) == n else None


def numbering_facts(s: S, rs: list[dict]) -> dict:
    return {"numbering_offset": any(r["an"] != r["ls"] for r in rs),
            "author_minus_label": sorted({r["an"] - r["ls"] for r in rs if r["poly"]}),
            "auth_label_chain": any(r["ac"] != r["lc"] for r in rs),
            "insertion_codes_in_structure": s.facts["numbering"]["insertion_codes"]}


def label_trap(rs: list[dict], **attrs: Any) -> list[dict]:
    """The author number written into the label-number key: the commonest mistake."""
    return [{"auth_asym_id": r["ac"], "residue_number": r["an"], **attrs} for r in rs]


def t_residue_colour(s: S) -> dict | None:
    n = 1 + h("n", "residue-colour", s.id) % 3
    rs = chosen_residues(s, "residue-colour", n)
    if rs is None:
        return None
    (c,) = colours(1, "residue-colour", s.id)
    words = res_words(s, rs)
    L = s.load()
    return {
        "prompts": [f"Load {s.name} and colour {words} {cw(c)}.",
                    f"In {s.name}, colour {words} {cw(c)}; leave everything else as it is.",
                    f"Open {s.name}. On the default view, pick out {words} in {cw(c)}."],
        "reference": [L, color_call([by_author(r, color=c) for r in rs])],
        "target": [{"selector": [residue_atoms(r) for r in rs], "representation": None, "color": c}],
        "skills": ["load", "selection", "author-numbering", "color"],
        "difficulty": numbering_facts(s, rs),
        "derived": "Residues drawn by seed from a protein chain whose author numbers differ from "
                   "its label numbers; each is the only thing with its author chain and number. "
                   "The request names them as papers do (residue name + author number).",
        "alts": [("label chain and label number", [L, color_call([by_label(r, color=c) for r in rs])])],
        "traps": [("the author number in residue_number (label numbering)",
                   [L, color_call(label_trap(rs, color=c))])],
    }


def t_residue_sticks(s: S) -> dict | None:
    n = 1 + h("n", "residue-sticks", s.id) % 3
    rs = chosen_residues(s, "residue-sticks", n)
    if rs is None:
        return None
    (c,) = colours(1, "residue-sticks", s.id)
    rep = pick(["ball-and-stick", "ball-and-stick", "spacefill"], "rep", "residue-sticks", s.id)
    words = res_words(s, rs)
    it = "it" if n == 1 else "them"
    L = s.load()
    full = dict(color=c, representation=rep, representationColor=c)
    return {
        "prompts": [f"Load {s.name}, colour {words} {cw(c)} and also show {it} as {cw(c)} {rep}.",
                    f"In {s.name}, colour {words} {cw(c)} on the cartoon and add a {cw(c)} {rep} "
                    f"representation for {it}.",
                    f"Open {s.name}. Make {words} {cw(c)}, and draw {it} as {cw(c)} {rep} as well."],
        "reference": [L, color_call([by_author(r, **full) for r in rs])],
        "target": [{"selector": [residue_atoms(r) for r in rs], "representation": rep, "color": c}],
        "skills": ["load", "selection", "author-numbering", "color", "per-selection-representation"],
        "difficulty": {**numbering_facts(s, rs), "hinges_on": ["added_representation_colour"]},
        "derived": "As api-residue-colour, plus an added representation in the same colour. In "
                   "pdbe-molstar 3.3.2 `color` paints only the representations the structure "
                   "already has; the added one takes its colour from `representationColor`.",
        "alts": [("label chain and label number", [L, color_call([by_label(r, **full) for r in rs])])],
        "traps": [("no representationColor (the added representation stays element-coloured)",
                   [L, color_call([{**by_label(r), "color": c, "representation": rep} for r in rs])]),
                  ("the author number in residue_number", [L, color_call(label_trap(rs, **full))])],
    }


def t_sticks_plain(s: S) -> dict | None:
    n = 1 + h("n", "sticks-plain", s.id) % 2
    rs = chosen_residues(s, "sticks-plain", n)
    if rs is None:
        return None
    words = res_words(s, rs)
    L = s.load()
    attrs = dict(color=None, representation="ball-and-stick")
    return {
        "prompts": [f"Load {s.name} and add a ball-and-stick representation for {words}, in the "
                    "usual element colours. Do not recolour anything.",
                    f"In {s.name}, also show {words} as ball-and-stick (element colours), leaving "
                    "the colours of the cartoon exactly as they are.",
                    f"Open {s.name} and draw {words} as ball-and-stick on top of the default view; "
                    "keep every colour at its default."],
        "reference": [L, color_call([by_author(r, **attrs) for r in rs])],
        "target": [{"selector": [residue_atoms(r) for r in rs], "representation": "ball-and-stick",
                    "color": None}],
        "skills": ["load", "selection", "author-numbering", "per-selection-representation"],
        "difficulty": {**numbering_facts(s, rs), "hinges_on": ["default_select_colour"]},
        "derived": "An added representation with no recolouring. A selection with no `color` key "
                   "is painted the viewer's default orange, so the reference gives `color: null`.",
        "alts": [("label chain and label number", [L, color_call([by_label(r, **attrs) for r in rs])])],
        "traps": [("no color key (the residues turn the default orange)",
                   [L, color_call([{**by_label(r), "representation": "ball-and-stick"} for r in rs])])],
    }


def a_range(s: S, key: str, need_offset: bool = True, max_len: int = 20) -> dict | None:
    """An author-numbered residue range inside one chain that selects exactly those
    polymer residues (no water, ligand or insertion-coded residue shares the numbers)."""
    options = []
    for c in s.chains:
        for a, b, la, lb in c["runs_auth_label"]:
            if not (re.fullmatch(r"-?\d+", str(a)) and re.fullmatch(r"-?\d+", str(b))):
                continue
            a, b = int(a), int(b)
            if b - a + 1 >= 8 and (a - la != 0 or not need_offset):
                options.append((c, a, b, la))
    for c, a, b, la in sorted(options, key=lambda o: h(key, s.id, o[0]["auth_asym_id"], o[1])):
        for attempt in range(8):
            length = 5 + h(key, s.id, "len", attempt) % (min(max_len, b - a + 1) - 4)
            start = a + h(key, s.id, "start", attempt) % (b - a + 2 - length)
            end = start + length - 1
            got = 0
            for v, m in s.table.index("auth_seq_id").items():
                if start <= v <= end:
                    got |= m
            got &= s.mask(auth_asym_id=c["auth_asym_id"])
            ls, le = la + (start - a), la + (end - a)
            want = s.table.selector({"label_asym_id": c["label_asym_id"], "beg_label_seq_id": ls,
                                     "end_label_seq_id": le})
            if got and got == want:
                return {"chain": c, "start": start, "end": end, "label_start": ls, "label_end": le,
                        "atoms": {"label_asym_id": c["label_asym_id"], "beg_label_seq_id": ls,
                                  "end_label_seq_id": le}}
    return None


def range_sel(rg: dict, **attrs: Any) -> dict:
    c = rg["chain"]
    return sel({"auth_asym_id": c["auth_asym_id"], "start_auth_residue_number": rg["start"],
                "end_auth_residue_number": rg["end"]},
               f"residues {rg['start']}-{rg['end']} of chain {c['auth_asym_id']}", rg["atoms"], **attrs)


def range_label(rg: dict, **attrs: Any) -> dict:
    return {"struct_asym_id": rg["chain"]["label_asym_id"], "start_residue_number": rg["label_start"],
            "end_residue_number": rg["label_end"], **attrs}


def range_trap(rg: dict, **attrs: Any) -> dict:
    return {"auth_asym_id": rg["chain"]["auth_asym_id"], "start_residue_number": rg["start"],
            "end_residue_number": rg["end"], **attrs}


def range_facts(s: S, rg: dict) -> dict:
    c = rg["chain"]
    return {"numbering_offset": rg["start"] != rg["label_start"],
            "author_minus_label": [rg["start"] - rg["label_start"]],
            "auth_label_chain": c["auth_asym_id"] != c["label_asym_id"],
            "insertion_codes_in_structure": s.facts["numbering"]["insertion_codes"]}


def range_words(s: S, rg: dict, i: int = 0) -> str:
    a, b = rg["start"], rg["end"]
    return [f"residues {a} to {b}", f"residues {a}-{b}", f"the stretch from residue {a} to residue {b}"][i % 3] \
        + s.of_chain(rg["chain"]["auth_asym_id"])


def t_range_colour(s: S) -> dict | None:
    rg = a_range(s, "range-colour")
    if rg is None:
        return None
    (c,) = colours(1, "range-colour", s.id)
    rest = pick([None, "white", "gray"], "rest", "range-colour", s.id)
    L = s.load()
    more = {"non_selected_color": rest} if rest else {}
    tail = f" and everything else {cw(rest)}" if rest else ""
    w = range_words
    return {
        "prompts": [f"Load {s.name} and colour {w(s, rg, 0)} {cw(c)}{tail}.",
                    f"In {s.name}, colour {w(s, rg, 1)} {cw(c)}{tail}.",
                    f"Open {s.name}; I want {w(s, rg, 2)} in {cw(c)}{tail}."],
        "reference": [L, color_call([range_sel(rg, color=c)], **more)],
        "target": [{"selector": rg["atoms"], "representation": None, "color": c}],
        "skills": ["load", "selection", "residue-range", "author-numbering", "color"]
                  + (["non-selected-color"] if rest else []),
        "difficulty": range_facts(s, rg),
        "derived": "A seeded author-numbered range inside one run of a chain whose author and "
                   "label numbers differ; kept only if the author range selects exactly the "
                   "polymer residues of the matching label range (no water, ligand or "
                   "insertion-coded residue shares the numbers).",
        "alts": [("label chain and label range", [L, color_call([range_label(rg, color=c)], **more)])],
        "traps": [("the author numbers in start/end_residue_number (label numbering)",
                   [L, color_call([range_trap(rg, color=c)], **more)])],
    }


def t_chain_colour(s: S) -> dict | None:
    differing = [c for c in s.chains if c["auth_asym_id"] != c["label_asym_id"]]
    if not differing:
        return None
    first = pick(differing, "chain-colour", s.id)
    others = [c for c in s.chains if c is not first]
    picked = [first] + ([pick(others, "chain-colour-2", s.id)] if others else [])
    picked.sort(key=lambda c: c["auth_asym_id"])
    cols = colours(len(picked), "chain-colour", s.id)
    # "chain B" means the polymer; ligands and waters often carry the same author chain
    # id. Under the cartoon style only polymer is drawn, so every reading of "chain B"
    # gives the same picture; without it the task is kept only if the author chain is
    # the polymer chain and nothing else.
    exact = all(s.mask(auth_asym_id=c["auth_asym_id"]) == s.mask(label_asym_id=c["label_asym_id"])
                for c in picked)
    pre = [] if exact else [style("cartoon")]
    L = s.load()

    def call(key: str, field: str) -> dict:
        return color_call([{key: c[field], "color": col} for c, col in zip(picked, cols)])

    data = [sel({"auth_asym_id": c["auth_asym_id"]}, f"chain {c['auth_asym_id']}",
                [{"label_asym_id": lc} for lc in s.label_chains_of(c["auth_asym_id"])], color=col)
            for c, col in zip(picked, cols)]
    words = listing([f"chain {c['auth_asym_id']} {cw(col)}" for c, col in zip(picked, cols)])
    if exact:
        prompts = [f"Load {s.name} and colour {words}.", f"In {s.name}, colour {words}.",
                   f"Open {s.name}; make {words}."]
    else:
        prompts = [f"Show {s.name} as a cartoon and colour {words}.",
                   f"Load {s.name}, switch the whole structure to the cartoon style, and colour {words}.",
                   f"Open {s.name} in the cartoon style, with {words}."]
    return {
        "prompts": prompts,
        "reference": [L, *pre, color_call(data)],
        "target": [{"selector": [{"label_asym_id": c["label_asym_id"]} for c in picked],
                    "representation": None, "color": None}],
        "skills": ["load", "selection", "select-by-chain", "color"] + (["global-style"] if pre else []),
        "difficulty": {"numbering_offset": False, "auth_label_chain": True,
                       "chain_ids": {c["auth_asym_id"]: c["label_asym_id"] for c in picked},
                       "cartoon_style_removes_chain_ambiguity": not exact},
        "derived": "Chains of an entry whose author chain ids differ from the label chain ids. "
                   "The request uses the author ids (the letters in the paper). "
                   + ("The author chain is exactly the polymer chain here." if exact else
                      "The cartoon style is asked for, so ligands and waters that share the "
                      "author chain id are not drawn and every reading of 'chain X' agrees."),
        "alts": [("label chain ids", [L, *pre, call("struct_asym_id", "label_asym_id")])],
        "traps": [("the author letters in struct_asym_id (the label chain key)",
                   [L, *pre, call("struct_asym_id", "auth_asym_id")])],
    }


def unp_positions(s: S, key: str) -> tuple[str, list] | None:
    """An accession of the entry and its positions whose residue is observed, is the
    UniProt residue, and has an author number different from the UniProt number."""
    if s.sifts is None:
        return None
    by_acc: dict[str, dict[int, list]] = {}
    for r in s.sifts.rows:
        if r.observed and "-" not in r.accession:
            by_acc.setdefault(r.accession, {}).setdefault(r.unp_num, []).append(r)
    good = {}
    for acc, pos in by_acc.items():
        ok = {n: rows for n, rows in pos.items()
              if all(x.comp_id in AA and ONE[x.comp_id] == x.unp_res and x.auth_seq_id != n
                     for x in rows)}
        if len(ok) >= 12:
            good[acc] = ok
    if not good:
        return None
    acc = pick(sorted(good), key, s.id)
    return acc, sorted(good[acc].items())


def unp_atoms(rows: list) -> list[dict]:
    return [{"auth_asym_id": r.auth_asym_id, "auth_seq_id": r.auth_seq_id,
             "pdbx_PDB_ins_code": r.pdbx_PDB_ins_code, "auth_comp_id": r.comp_id} for r in rows]


def copies_words(n: int, k: int = 1) -> str:
    it = "it" if k == 1 else "them"
    return "" if n == 1 else f" in both chains that have {it}" if n == 2 else f" in all {n} chains that have {it}"


def t_uniprot_residue(s: S) -> dict | None:
    got = unp_positions(s, "uniprot-residue")
    if got is None:
        return None
    acc, positions = got
    n_copies = Counter(len(rows) for _, rows in positions).most_common(1)[0][0]
    positions = [(n, rows) for n, rows in positions if len(rows) == n_copies]
    k = 1 + h("n", "uniprot-residue", s.id) % 2
    chosen = sorted(shuffled([n for n, _ in positions], "uniprot-residue", s.id)[:k])
    rows_of = dict(positions)
    (c,) = colours(1, "uniprot-residue", s.id)
    L = s.load()
    names = [f"{rows_of[n][0].comp_id.capitalize()}{n}" for n in chosen]
    data = [sel({"uniprot_accession": acc, "uniprot_residue_number": n}, f"UniProt {acc} {n}",
                unp_atoms(rows_of[n]), color=c) for n in chosen]
    rows = [r for n in chosen for r in rows_of[n]]
    by_auth = [{"auth_asym_id": r.auth_asym_id, "auth_seq_id": r.auth_seq_id, "color": c} for r in rows]
    alts = []
    if all(not r.pdbx_PDB_ins_code and s.mask(auth_asym_id=r.auth_asym_id, auth_seq_id=r.auth_seq_id)
           == s.table.selector(unp_atoms([r])) for r in rows):
        alts.append(("author chain and author number, mapped by hand", [L, color_call(by_auth)]))
    where = copies_words(n_copies, k)
    return {
        "prompts": [f"Load {s.name} and colour {listing(names)}{where} {cw(c)}. The "
                    f"{'number is' if k == 1 else 'numbers are'} in UniProt numbering ({acc}).",
                    f"In {s.name}, colour UniProt {acc} residue{'s' if k > 1 else ''} "
                    f"{listing(names)}{where} {cw(c)}.",
                    f"Open {s.name}. Using the UniProt numbering of {acc}, colour "
                    f"{listing(names)}{where} {cw(c)}."],
        "reference": [L, color_call(data)],
        "target": [{"selector": unp_atoms(rows), "representation": None, "color": c}],
        "skills": ["load", "selection", "uniprot-numbering", "color"],
        "difficulty": {"uniprot_mapping": True, "numbering_offset": True,
                       "author_minus_uniprot": sorted({r.auth_seq_id - r.unp_num for r in rows}),
                       "label_equals_uniprot": all(r.label_seq_id == r.unp_num for r in rows),
                       "auth_label_chain": any(r.auth_asym_id != r.label_asym_id for r in rows),
                       "chains_mapped": n_copies},
        "derived": "Positions drawn by seed from the frozen SIFTS table: observed, the residue "
                   "is the UniProt residue, and its author number differs from the UniProt "
                   "number. The viewer maps UniProt numbers itself (uniprot_accession + "
                   "uniprot_residue_number); the intended atoms are the SIFTS rows written in "
                   "author numbering with the residue name.",
        "alts": alts,
        "traps": [("the UniProt number used as the author number",
                   [L, color_call([{"auth_seq_id": n, "color": c} for n in chosen])])],
    }


def t_uniprot_range(s: S) -> dict | None:
    got = unp_positions(s, "uniprot-range")
    if got is None:
        return None
    acc, positions = got
    nums = [n for n, _ in positions]
    rows_of = dict(positions)
    runs, run = [], [nums[0]]
    for n in nums[1:]:
        if n == run[-1] + 1 and len(rows_of[n]) == len(rows_of[run[0]]):
            run.append(n)
        else:
            runs.append(run)
            run = [n]
    runs.append(run)
    runs = [r for r in runs if len(r) >= 8]
    if not runs:
        return None
    run = pick(runs, "uniprot-range", s.id)
    length = 5 + h("len", "uniprot-range", s.id) % (min(18, len(run)) - 4)
    start = run[h("start", "uniprot-range", s.id) % (len(run) - length + 1)]
    end = start + length - 1
    rows = [r for n in range(start, end + 1) for r in rows_of[n]]
    (c,) = colours(1, "uniprot-range", s.id)
    L = s.load()
    where = copies_words(len(rows_of[start]), 2)
    data = [sel({"uniprot_accession": acc, "start_uniprot_residue_number": start,
                 "end_uniprot_residue_number": end}, f"UniProt {acc} {start}-{end}", unp_atoms(rows), color=c)]
    return {
        "prompts": [f"Load {s.name} and colour residues {start} to {end} of UniProt {acc}{where} {cw(c)}.",
                    f"In {s.name}, colour the segment {start}-{end} (UniProt numbering, {acc}){where} {cw(c)}.",
                    f"Open {s.name}. In UniProt {acc} numbering, residues {start}-{end}{where} should be {cw(c)}."],
        "reference": [L, color_call(data)],
        "target": [{"selector": unp_atoms(rows), "representation": None, "color": c}],
        "skills": ["load", "selection", "uniprot-numbering", "residue-range", "color"],
        "difficulty": {"uniprot_mapping": True, "numbering_offset": True,
                       "author_minus_uniprot": sorted({r.auth_seq_id - r.unp_num for r in rows}),
                       "label_equals_uniprot": all(r.label_seq_id == r.unp_num for r in rows),
                       "auth_label_chain": any(r.auth_asym_id != r.label_asym_id for r in rows),
                       "chains_mapped": len(rows_of[start])},
        "derived": "A seeded run of consecutive UniProt positions from the frozen SIFTS table, "
                   "all observed and all with an author number different from the UniProt "
                   "number; selected with the viewer's own UniProt range keys.",
        "alts": [],
        "traps": [("the UniProt numbers used as an author range",
                   [L, color_call([{"start_auth_residue_number": start, "end_auth_residue_number": end,
                                    "color": c}])])],
    }


def real_ligands(s: S) -> list[dict]:
    return [g for g in s.facts["ligands"] if g["kind"] == "ligand" and g["comp_id"] not in ADDITIVES
            and g["n_heavy_atoms"] >= 6]


def t_ligand(s: S) -> dict | None:
    ligs = real_ligands(s)
    if not ligs:
        return None
    lig = pick(ligs, "ligand", s.id)
    (c,) = colours(1, "ligand", s.id)
    chains = sorted({x["auth_asym_id"] for x in lig["copies"]})
    one_copy = len(chains) == len(lig["copies"]) > 1 and h("copy", "ligand", s.id) % 2 == 0
    chain = pick(chains, "ligand-chain", s.id) if one_copy else None
    what, it = lig_phrase(lig, chain)
    L = s.load()
    lig_only = {k: v for k, v in ligand_sel(lig, chain).items() if k != "_t"}
    return {
        "prompts": [f"Load {s.name}, colour {what} {cw(c)} and centre the view on {it}.",
                    f"In {s.name}, make {what} {cw(c)} and zoom in on {it}.",
                    f"Open {s.name}; colour {what} {cw(c)}, then focus the camera on {it}."],
        "reference": [L, color_call([ligand_sel(lig, chain, color=c)]),
                      {"action": "focus", "data": [ligand_sel(lig, chain)]}],
        "target": [{"selector": ligand_sel(lig, chain)["_t"]["atoms"], "representation": None, "color": c}],
        "skills": ["load", "selection", "select-by-ligand", "color", "focus"],
        "difficulty": {"ligand_identity_needed": False, "ligand_code_in_prompt": True,
                       "ligand_copies": len(lig["copies"]), "one_copy_by_chain": bool(chain)},
        "derived": "A ligand of the entry (more than five heavy atoms, not a crystallisation "
                   "additive) drawn by seed from the frozen facts. The request names its "
                   "component code, so nothing has to be recalled; the copies are those the "
                   "facts list.",
        "alts": [("colour and focus in one call",
                  [L, color_call([{**lig_only, "color": c, "focus": True}])])],
        "traps": [],
    }


def t_entity(s: S) -> dict | None:
    ents = [e for e in s.facts["entities"] if e["type"] == "polymer"]
    if len(ents) < 2:
        return None
    picked = sorted(shuffled(ents, "entity", s.id)[:2], key=lambda e: int(e["id"]))
    cols = colours(2, "entity", s.id)
    kind = {"protein": "protein", "DNA": "DNA", "RNA": "RNA"}

    def words(e: dict) -> str:
        return f"entity {e['id']} ({kind.get(e['polymer_type'], 'polymer')})"

    L = s.load()
    data = [sel({"entity_id": e["id"]}, f"entity {e['id']}",
                [{"label_asym_id": lc} for lc in e["label_asym_ids"]], color=c)
            for e, c in zip(picked, cols)]
    both = listing([f"{words(e)} {cw(c)}" for e, c in zip(picked, cols)])
    by_chain = [{"struct_asym_id": lc, "color": c} for e, c in zip(picked, cols) for lc in e["label_asym_ids"]]
    return {
        "prompts": [f"Load {s.name} and colour {both}.",
                    f"In {s.name}, colour by molecule: {both}. Leave the other entities alone.",
                    f"Open {s.name}; make {both}."],
        "reference": [L, color_call(data)],
        "target": [{"selector": [{"label_asym_id": lc} for e in picked for lc in e["label_asym_ids"]],
                    "representation": None, "color": None}],
        "skills": ["load", "selection", "select-by-entity", "color"],
        "difficulty": {"entity_ids": [e["id"] for e in picked],
                       "auth_label_chain": s.facts["numbering"]["auth_chain_differs_from_label_chain"]},
        "derived": "Two polymer entities drawn by seed from the frozen facts; the intended atoms "
                   "are the entity's label chains as the facts list them.",
        "alts": [("the entity's label chains, one by one", [L, color_call(by_chain)])],
        "traps": [("entity ids as numbers (the viewer compares with ===, so 2 never equals \"2\")",
                   [L, color_call([{"entity_id": int(e["id"]), "color": c} for e, c in zip(picked, cols)])])],
    }


def t_atoms(s: S) -> dict | None:
    (c,) = colours(1, "atoms", s.id)
    L = s.load()
    ligs = [g for g in real_ligands(s) if len(g["copies"]) == 1]
    if ligs and h("kind", "atoms", s.id) % 5 < 3:
        lig = pick(ligs, "atoms", s.id)
        names = [lig["metals"][0]] if lig["metals"] and lig["metals"][0] in lig["atoms"] else \
            sorted(shuffled([a for a in lig["atoms"] if not a.startswith("C")] or lig["atoms"],
                            "atoms", s.id)[:2])
        cp = lig["copies"][0]
        atoms = [{"auth_asym_id": cp["auth_asym_id"], "auth_seq_id": cp["auth_seq_id"],
                  "auth_comp_id": lig["comp_id"], "label_atom_id": a} for a in names]
        what = (f"atom {names[0]}" if len(names) == 1 else f"atoms {listing(names)}") \
            + f" of the {lig_words(lig)}"
        data = [sel({"label_comp_id": lig["comp_id"], "atoms": names}, what, atoms, color=c)]
        return {
            "prompts": [f"Load {s.name} and colour {what} {cw(c)}.",
                        f"In {s.name}, colour just {what} {cw(c)}, not the rest of the ligand.",
                        f"Open {s.name}; pick out {what} in {cw(c)}."],
            "reference": [L, color_call(data)],
            "target": [{"selector": atoms, "representation": None, "color": c}],
            "skills": ["load", "selection", "select-by-ligand", "select-atoms", "color"],
            "difficulty": {"ligand_identity_needed": False, "ligand_code_in_prompt": True,
                           "atom_names_in_prompt": True},
            "derived": "Atom names drawn by seed from the heavy atoms the facts list for a "
                       "single-copy ligand (its metal, when it has one).",
            "alts": [("the ligand by author chain and number",
                      [L, color_call([{"auth_asym_id": cp["auth_asym_id"], "auth_seq_id": cp["auth_seq_id"],
                                       "atoms": names, "color": c}])])]
            if s.mask(auth_asym_id=cp["auth_asym_id"], auth_seq_id=cp["auth_seq_id"])
            == s.table.selector({"auth_asym_id": cp["auth_asym_id"], "auth_seq_id": cp["auth_seq_id"],
                                 "auth_comp_id": lig["comp_id"]}) else [],
            "traps": [("the whole ligand", [L, color_call([{"label_comp_id": lig["comp_id"], "color": c}])])],
        }
    rs = chosen_residues(s, "atoms", 1)
    if rs is None:
        return None
    r = rs[0]
    side = sorted(a for a in {s.table.columns["label_atom_id"][i] for i in check.rows(r["mask"])}
                  if a not in ("N", "CA", "C", "O", "OXT") and not a.startswith("H"))
    if len(side) < 2:
        return None
    names = sorted(shuffled(side, "atoms", s.id)[:2])
    atoms = [{**residue_atoms(r), "label_atom_id": a} for a in names]
    what = f"atoms {listing(names)} of {res_words(s, [r])}"
    data = [sel({"auth_asym_id": r["ac"], "auth_seq_id": r["an"], "atoms": names}, what, atoms, color=c)]
    return {
        "prompts": [f"Show {s.name} as ball-and-stick and colour {what} {cw(c)}.",
                    f"Load {s.name}, switch the whole structure to ball-and-stick, and colour "
                    f"only {what} {cw(c)}.",
                    f"Open {s.name} in the ball-and-stick style; {what} should be {cw(c)}."],
        "reference": [L, style("ball-and-stick"), color_call(data)],
        "target": [{"selector": atoms, "representation": None, "color": c}],
        "skills": ["load", "global-style", "selection", "author-numbering", "select-atoms", "color"],
        "difficulty": {**numbering_facts(s, rs), "atom_names_in_prompt": True, "order_matters": True},
        "derived": "Two side-chain atom names drawn by seed from the atoms the table holds for a "
                   "seeded residue; the ball-and-stick style is asked for so that single atoms "
                   "are drawn.",
        "alts": [("label chain and label number",
                  [L, style("ball-and-stick"), color_call([by_label(r, atoms=names, color=c)])])],
        "traps": [("the whole residue",
                   [L, style("ball-and-stick"), color_call([by_label(r, color=c)])]),
                  ("the style set after the colouring (a style change reloads and wipes it)",
                   [L, color_call([by_label(r, atoms=names, color=c)]), style("ball-and-stick")])],
    }


def built_assembly(s: S) -> dict | None:
    """Assembly 1, when it is built by symmetry from every deposited polymer chain."""
    for a in s.facts["assemblies"]:
        chains = {c["auth_asym_id"] for c in s.chains} | {c["label_asym_id"] for c in s.chains}
        if a["id"] == "1" and a["relation_to_deposited"] == "built by symmetry" \
                and len(a["polymer_chain_copies"]) == len(s.chains) \
                and set(a["polymer_chain_copies"]) <= chains:
            return a
    return None


def t_assembly(s: S) -> dict | None:
    asm = built_assembly(s)
    if asm is None:
        return None
    (c,) = colours(1, "assembly", s.id)
    ligs = real_ligands(s)
    rg = a_range(s, "assembly", need_offset=False)
    if ligs and (rg is None or h("what", "assembly", s.id) % 2 == 0):
        lig = pick(ligs, "assembly", s.id)
        data, what = [ligand_sel(lig, color=c)], f"the {lig_words(lig)}"
        target = ligand_sel(lig)["_t"]["atoms"]
        alt_data = None
    elif rg is not None:
        data, what, target = [range_sel(rg, color=c)], range_words(s, rg, h("w", "assembly", s.id)), rg["atoms"]
        alt_data = [range_label(rg, color=c)]
    else:
        return None
    oligo = OLIGOMER.get(asm["oligomeric_details"], f"{asm['oligomeric_count']}-mer")
    L, bare = s.load(assembly_id="1"), s.load()
    plain = [{k: v for k, v in p.items() if k != "_t"} for p in data]
    return {
        "prompts": [f"Load the biological assembly of {s.name} (assembly 1, the {oligo}) and colour {what} {cw(c)}.",
                    f"Open {s.name} as its biological assembly 1, the {oligo}, not the deposited "
                    f"asymmetric unit, and colour {what} {cw(c)}.",
                    f"I need the {oligo} of {s.name} (assembly 1). Load it and colour {what} {cw(c)}."],
        "reference": [L, color_call(data)],
        "target": [{"selector": target, "representation": None, "color": c}],
        "skills": ["load", "assembly", "selection", "color"],
        "difficulty": {"assembly_differs_from_deposited": True, "oligomer": oligo,
                       **(range_facts(s, rg) if alt_data else {"ligand_code_in_prompt": True})},
        "derived": f"Assembly 1 is built by symmetry from every deposited polymer chain (frozen "
                   f"facts: {asm['oligomeric_details']}, {asm['oligomeric_count']} chains), so it "
                   "differs from the deposited model. Atoms are compared on the deposited unit; "
                   "the assembly is a fact of the state.",
        "alts": [("assembly_id 'preferred' (the first assembly)",
                  [s.load(assembly_id="preferred"), color_call(plain)])]
                + ([("label chain and label range", [L, color_call(alt_data)])] if alt_data else []),
        "traps": [("no assembly", [bare, color_call(plain)]),
                  ("assembly_id set after the load (it is only read when a structure is loaded)",
                   [bare, prop("assembly_id", "1"), color_call(plain)])],
    }


def t_hide(s: S, want: str) -> dict | None:
    comps = s.components
    (c,) = colours(1, "hide", s.id)
    L = s.load()
    ligs = real_ligands(s)
    sugars_as_ligands = any(g["kind"] == "sugar" for g in s.facts["ligands"])
    options = []
    if "water" in comps and ligs:
        options.append("water+ligand")
    if "branched" in comps and not sugars_as_ligands and "water" in comps:
        options.append("carbs")
    if "non-standard" in comps and "water" in comps:
        options.append("non-standard")
    if ("ligand" in comps or "ion" in comps) and a_range(s, "hide", need_offset=False):
        options.append("het")
    if "water" in comps and ligs and "polymer" in comps:
        options.append("polymer")
    if want not in options:
        return None
    kind = want
    base = {"skills": ["load", "hide"], "alts": [], "traps": [],
            "difficulty": {"components_present": sorted(comps), "hide_kind": kind}}
    if kind == "water+ligand":
        lig = pick(ligs, "hide", s.id)
        what, _ = lig_phrase(lig)
        return {**base,
                "prompts": [f"Load {s.name}, hide the waters and colour {what} {cw(c)}.",
                            f"In {s.name}, switch the water molecules off and make {what} {cw(c)}.",
                            f"Open {s.name} without its waters, with {what} in {cw(c)}."],
                "reference": [L, prop("hide_water", True), color_call([ligand_sel(lig, color=c)])],
                "target": [{"selector": ligand_sel(lig)["_t"]["atoms"], "representation": None, "color": c}],
                "skills": ["load", "hide", "select-by-ligand", "color"],
                "derived": "The entry has waters (default water component) and the named ligand "
                           "(frozen facts); the ligand's code is in the request."}
    if kind == "carbs":
        return {**base,
                "prompts": [f"Load {s.name} and hide the carbohydrates and the waters.",
                            f"In {s.name}, switch off the glycans (carbohydrates) and the water molecules.",
                            f"Open {s.name} with neither the carbohydrates nor the waters shown."],
                "reference": [L, prop("hide_carbs", True), prop("hide_water", True)],
                "target": None,
                "derived": "The entry has branched (oligosaccharide) entities and waters, and no "
                           "sugar that is a single-residue ligand, so 'the carbohydrates' is "
                           "exactly the viewer's carbohydrate component."}
    if kind == "non-standard":
        return {**base,
                "prompts": [f"Load {s.name} and hide the non-standard residues and the waters.",
                            f"In {s.name}, switch off the non-standard (modified) residues and the water molecules.",
                            f"Open {s.name} with the non-standard residues and the waters hidden."],
                "reference": [L, prop("hide_non_standard", True), prop("hide_water", True)],
                "target": None,
                "derived": "The entry has non-standard residues inside a polymer chain (the "
                           "viewer's non-standard component) and waters."}
    if kind == "het":
        rg = a_range(s, "hide", need_offset=False)
        return {**base,
                "prompts": [f"Load {s.name}, hide the ligands and ions, and colour {range_words(s, rg, 0)} {cw(c)}.",
                            f"In {s.name}, switch off all heteroatoms (ligands and ions) but keep the "
                            f"waters, and colour {range_words(s, rg, 1)} {cw(c)}.",
                            f"Open {s.name} with its ligands and ions hidden and {range_words(s, rg, 2)} in {cw(c)}."],
                "reference": [L, prop("hide_heteroatoms", True), color_call([range_sel(rg, color=c)])],
                "target": [{"selector": rg["atoms"], "representation": None, "color": c}],
                "skills": ["load", "hide", "selection", "residue-range", "color"],
                "difficulty": {**base["difficulty"], **range_facts(s, rg)},
                "alts": [("label chain and label range",
                          [L, prop("hide_heteroatoms", True), color_call([range_label(rg, color=c)])])],
                "derived": "The entry has a ligand or ion component; the range is a seeded "
                           "author-numbered range that selects exactly those polymer residues."}
    lig = pick(ligs, "hide", s.id)
    what, _ = lig_phrase(lig)
    return {**base,
            "prompts": [f"Load {s.name}, hide the polymer and the waters, and colour {what} {cw(c)}.",
                        f"In {s.name}, switch off the polymer chains and the water molecules so that only the "
                        f"ligands and ions are left, and make {what} {cw(c)}.",
                        f"Open {s.name} with the polymer and the waters hidden and {what} in {cw(c)}."],
            "reference": [L, prop("hide_polymer", True), prop("hide_water", True),
                          color_call([ligand_sel(lig, color=c)])],
            "target": [{"selector": ligand_sel(lig)["_t"]["atoms"], "representation": None, "color": c}],
            "skills": ["load", "hide", "select-by-ligand", "color"],
            "derived": "The entry has polymer, waters and the named ligand (frozen facts)."}


def t_layered(s: S) -> dict | None:
    rg = a_range(s, "layered", need_offset=True, max_len=30)
    if rg is None:
        return None
    inner_pool = [r for r in s.amino_acids(rg["chain"]["auth_asym_id"])
                  if rg["start"] < r["an"] < rg["end"]]
    if not inner_pool:
        return None
    r = pick(sorted(inner_pool, key=lambda x: x["an"]), "layered", s.id)
    c1, c2 = colours(2, "layered", s.id)
    L = s.load()
    variant = h("variant", "layered", s.id) % 2
    outer, inner = range_sel(rg, color=c1), by_author(r, color=c2)
    plain_outer = {k: v for k, v in outer.items() if k != "_t"}
    plain_inner = {k: v for k, v in inner.items() if k != "_t"}
    w = range_words(s, rg, h("w", "layered", s.id))
    if variant == 0:
        ref = [L, color_call([outer, inner])]
        prompts = [f"Load {s.name} and colour {w} {cw(c1)}, except {res_word(r)}, which should be {cw(c2)}.",
                   f"In {s.name}, colour {w} {cw(c1)} with {res_word(r)} inside it in {cw(c2)}.",
                   f"Open {s.name}; {w} in {cw(c1)}, but {res_word(r)} in {cw(c2)}."]
        alts = [("two calls, the second with keep_colors",
                 [L, color_call([plain_outer]), color_call([plain_inner], keep_colors=True)])]
    else:
        ref = [L, color_call([outer]), color_call([inner], keep_colors=True)]
        prompts = [f"Load {s.name} and colour {w} {cw(c1)}. Then, keeping that colouring, colour {res_word(r)} {cw(c2)}.",
                   f"In {s.name}, first colour {w} {cw(c1)}; next, without losing it, make {res_word(r)} {cw(c2)}.",
                   f"Open {s.name}. Step one: {w} in {cw(c1)}. Step two, on top of step one: {res_word(r)} in {cw(c2)}."]
        alts = [("one call, the residue after the range", [L, color_call([plain_outer, plain_inner])])]
    rest = {"label_asym_id": rg["chain"]["label_asym_id"], "beg_label_seq_id": rg["label_start"],
            "end_label_seq_id": rg["label_end"]}
    return {
        "prompts": prompts,
        "reference": ref,
        "target": [{"selector": rest, "representation": None, "color": None}],
        "skills": ["load", "selection", "residue-range", "author-numbering", "color", "color-order"],
        "difficulty": {**range_facts(s, rg), "order_matters": True,
                       "keep_colors_in_reference": variant == 1},
        "derived": "A seeded author-numbered range and one residue inside it. Later colouring "
                   "lies over earlier colouring, and a second `color` call removes the first "
                   "unless keep_colors is set.",
        "alts": alts,
        "traps": [("the residue first, the range over it", [L, color_call([plain_inner, plain_outer])]),
                  ("two calls without keep_colors (the first colouring is removed)",
                   [L, color_call([plain_outer]), color_call([plain_inner])])],
    }


def t_style_colour(s: S) -> dict | None:
    rg = a_range(s, "style-colour", need_offset=False)
    if rg is None:
        return None
    st = pick(["spacefill", "ball-and-stick", "molecular-surface", "gaussian-surface", "putty"],
              "style-colour", s.id)
    (c,) = colours(1, "style-colour", s.id)
    L = s.load()
    plain = range_label(rg, color=c)
    return {
        "prompts": [f"Show {s.name} as {STYLE_WORDS[st]} and colour {range_words(s, rg, 0)} {cw(c)}.",
                    f"Load {s.name}, switch the whole structure to {STYLE_WORDS[st]}, and colour "
                    f"{range_words(s, rg, 1)} {cw(c)}.",
                    f"Open {s.name} drawn as {STYLE_WORDS[st]} throughout, with {range_words(s, rg, 2)} in {cw(c)}."],
        "reference": [L, style(st), color_call([range_sel(rg, color=c)])],
        "target": [{"selector": rg["atoms"], "representation": None, "color": c}],
        "skills": ["load", "global-style", "selection", "residue-range", "color"],
        "difficulty": {**range_facts(s, rg), "order_matters": True, "style": st},
        "derived": "A global style and a seeded author-numbered range. Setting the style reloads "
                   "the structure, so it has to come before the colouring.",
        "alts": [("label chain and label range", [L, style(st), color_call([plain])])],
        "traps": [("the style set after the colouring (the reload wipes the colour)",
                   [L, color_call([plain]), style(st)]),
                  ("no style", [L, color_call([plain])])],
    }


# --- tool-only templates -----------------------------------------------------------

def xray(s: S) -> bool:
    return s.entry["method"] == "X-ray"


def t_alphafold(s: S) -> dict | None:
    if s.kind == "pdb":
        return None
    acc = re.fullmatch(r"af-([a-z0-9]+)-f\d+-model_v\d+", s.id).group(1).upper()
    protein = re.sub(r"^AlphaFold DB model of ", "", s.entry["title"])
    protein = re.sub(r"\s*\(.*\)$", "", protein)
    rs = [r for r in s.residues if r["poly"] and r["comp"] in AA]
    n = len(rs)
    start = 1 + h("start", "alphafold", s.id) % (n - 30)
    end = start + 9 + h("len", "alphafold", s.id) % 15
    text = f"residues {start}-{end}"
    L = s.load()
    atoms = {"label_asym_id": rs[0]["lc"], "beg_label_seq_id": start, "end_label_seq_id": end}
    tip = sel({"start_auth_residue_number": start, "end_auth_residue_number": end}, text, atoms, tooltip=text)
    return {
        "prompts": [f"Load the AlphaFold DB model of {protein} (UniProt {acc}), colour it by the model's "
                    f"per-residue confidence (pLDDT), and attach the tooltip '{text}' to residues {start} to {end}.",
                    f"Open the AlphaFold prediction for UniProt {acc} ({protein}) coloured by pLDDT, with a "
                    f"tooltip reading '{text}' on residues {start}-{end}.",
                    f"I want the AlphaFold DB model of {protein} ({acc}) in the confidence (pLDDT) colouring; "
                    f"residues {start} to {end} should carry the tooltip '{text}'."],
        "reference": [L, prop("alphafold_view", True), {"action": "tooltips", "data": [tip]}],
        "target": None,
        "skills": ["load", "custom-data", "alphafold", "tooltip"],
        "difficulty": {"needs_alphafold_url": True, "numbering_offset": False},
        "derived": "The panel's frozen AlphaFold DB model. In pdbe-molstar 3.3.2 alphafold_view "
                   "only switches the colouring to pLDDT; the model is loaded with custom_data "
                   "from the AlphaFold DB URL pattern the API reference gives. An AlphaFold "
                   "model is numbered as UniProt, so author and label numbers agree.",
        "alts": [("the binary file of another model version, the flag in the load action, label numbers",
                  [{"action": "load", "alphafold": True, "custom_data": {
                      "url": f"https://alphafold.ebi.ac.uk/files/AF-{acc}-F1-model_v4.bcif",
                      "format": "bcif", "binary": True}},
                   {"action": "tooltips", "data": [{"start_residue_number": start, "end_residue_number": end,
                                                    "tooltip": text}]}])],
        "traps": [("the accession as molecule_id (not a PDB id: nothing loads)",
                   [{"action": "load", "molecule_id": acc, "alphafold": True},
                    {"action": "tooltips", "data": [{"start_residue_number": start,
                                                     "end_residue_number": end, "tooltip": text}]}])],
    }


def t_validation(s: S) -> dict | None:
    if not xray(s) or "water" not in s.components:
        return None
    L = s.load()
    return {
        "prompts": [f"Load {s.name}, hide the waters and overlay the PDBe validation report colouring.",
                    f"In {s.name}, switch off the water molecules and turn on the PDBe geometry-validation annotation.",
                    f"Open {s.name} with the validation annotation on and the waters hidden."],
        "reference": [L, prop("hide_water", True), prop("validation_annotation", True)],
        "target": None,
        "skills": ["load", "hide", "validation-annotation"],
        "difficulty": {"setting_only": ["validation_annotation"]},
        "derived": "An X-ray entry with waters. The annotation is compared as a declared "
                   "setting; what it draws comes from PDBe at run time and is not modelled.",
        "alts": [], "traps": [],
    }


def t_domain(s: S) -> dict | None:
    if s.kind != "pdb" or s.sifts is None:
        return None
    L = s.load()
    return {
        "prompts": [f"Load {s.name}, overlay the domain annotations and open the sequence panel.",
                    f"In {s.name}, turn on the PDBe domain annotation and show the sequence panel.",
                    f"Open {s.name} with the sequence panel visible and the domain annotations switched on."],
        "reference": [L, prop("domain_annotation", True), prop("sequence_panel", True)],
        "target": None,
        "skills": ["load", "domain-annotation", "sequence-panel"],
        "difficulty": {"setting_only": ["domain_annotation", "sequence_panel"]},
        "derived": "A PDB entry with a UniProt mapping. Both options are compared as declared settings.",
        "alts": [], "traps": [],
    }


def t_symmetry(s: S) -> dict | None:
    asm = built_assembly(s)
    if asm is None or asm["oligomeric_count"] < 3 or not xray(s):
        return None
    oligo = OLIGOMER.get(asm["oligomeric_details"], f"{asm['oligomeric_count']}-mer")
    return {
        "prompts": [f"Load the biological assembly of {s.name} (assembly 1, the {oligo}) and switch on the "
                    "assembly-symmetry annotation.",
                    f"Open {s.name} as assembly 1, the {oligo}, with the symmetry annotation turned on.",
                    f"I want the {oligo} of {s.name} (assembly 1) with its symmetry annotation shown."],
        "reference": [s.load(assembly_id="1"), prop("symmetry_annotation", True)],
        "target": None,
        "skills": ["load", "assembly", "symmetry-annotation"],
        "difficulty": {"assembly_differs_from_deposited": True, "setting_only": ["symmetry_annotation"]},
        "derived": "Assembly 1 is built by symmetry from every deposited chain (frozen facts). "
                   "The annotation is compared as a declared setting.",
        "alts": [], "traps": [("no assembly", [s.load(), prop("symmetry_annotation", True)])],
    }


def t_ligand_view(s: S) -> dict | None:
    ligs = [g for g in real_ligands(s) if len(g["copies"]) == 1]
    if not ligs or s.kind != "pdb":
        return None
    lig = pick(ligs, "ligand-view", s.id)
    bg = pick(["black", "white"], "ligand-view", s.id)
    cp = lig["copies"][0]
    return {
        "prompts": [f"Open the PDBe ligand view of the {lig_words(lig)} in {s.name} (only the ligand and its "
                    f"surroundings) on a {bg} background.",
                    f"Load {s.name} in the ligand-page view centred on the {lig_words(lig)}, with a {bg} background.",
                    f"I want the ligand view for the {lig_words(lig)} of {s.name}: just that ligand with its "
                    f"environment, {bg} background."],
        "reference": [s.load(ligand_view={"label_comp_id": lig["comp_id"]}),
                      prop("bg_color", "#000000" if bg == "black" else "#FFFFFF")],
        "target": None,
        "skills": ["load", "ligand-view", "set-background"],
        "difficulty": {"ligand_identity_needed": False, "ligand_code_in_prompt": True,
                       "setting_only": ["ligand_view"]},
        "derived": "A single-copy ligand from the frozen facts, named by its code. The view is "
                   "compared by the ligand it names; the surroundings it draws are not modelled.",
        "alts": [("the ligand by author chain and number, a named background",
                  [s.load(ligand_view={"auth_asym_id": cp["auth_asym_id"], "auth_seq_id": cp["auth_seq_id"]}),
                   prop("bg_color", bg)])],
        "traps": [("ligand_view set after the load (only read when a structure is loaded)",
                   [s.load(), prop("ligand_view", {"label_comp_id": lig["comp_id"]}),
                    prop("bg_color", bg)])],
    }


def t_canvas(s: S) -> dict | None:
    if s.kind != "pdb":
        return None
    bg = pick(["black", "white"], "canvas", s.id)
    light = pick(["flat", "matte", "glossy", "metallic", "plastic"], "canvas", s.id)
    hexbg = "#000000" if bg == "black" else "#FFFFFF"
    return {
        "prompts": [f"Load {s.name} on a {bg} background with {light} lighting and set it spinning.",
                    f"Show {s.name} rotating continuously, {light} lighting, {bg} background.",
                    f"Open {s.name} for a slide: {bg} background, {light} lighting, and let it spin."],
        "reference": [s.load(), prop("bg_color", hexbg), prop("lighting", light), prop("spin", True)],
        "target": None,
        "skills": ["load", "set-background", "lighting", "spin"],
        "difficulty": {"setting_only": ["lighting"]},
        "derived": "Canvas settings only. Background and spin were read back from the viewer; "
                   "lighting is compared as a declared setting.",
        "alts": [("the settings before the load, a named background",
                  [prop("spin", True), prop("lighting", light), prop("bg_color", bg), s.load()])],
        "traps": [],
    }


def t_highlight(s: S) -> dict | None:
    rs = chosen_residues(s, "highlight", 2)
    if rs is None:
        return None
    (c,) = colours(1, "highlight", s.id)
    words = res_words(s, rs)
    L = s.load()
    return {
        "prompts": [f"Load {s.name} and highlight {words} (hover-style highlight) in {cw(c)}, zooming in on them.",
                    f"In {s.name}, put the viewer's highlight on {words}, with {cw(c)} as the highlight "
                    "colour, and focus the camera on them.",
                    f"Open {s.name}; highlight {words} using a {cw(c)} highlight colour and centre the view on them."],
        "reference": [L, {"action": "highlight", "data": [by_author(r) for r in rs], "color": c, "focus": True}],
        "target": [{"selector": [residue_atoms(r) for r in rs], "representation": None, "color": None}],
        "skills": ["load", "selection", "author-numbering", "highlight", "set-highlight-color", "focus"],
        "difficulty": numbering_facts(s, rs),
        "derived": "As api-residue-colour, with the viewer's highlight instead of a colouring. "
                   "The highlight and the focus are compared by the residues the selection "
                   "resolves to; they were not read back from the viewer.",
        "alts": [("label numbering; colour and focus as separate calls",
                  [L, {"action": "set_color", "highlight": c},
                   {"action": "highlight", "data": [by_label(r) for r in rs]},
                   {"action": "focus", "data": [by_label(r) for r in rs]}])],
        "traps": [("the author number in residue_number",
                   [L, {"action": "highlight", "data": label_trap(rs), "color": c, "focus": True}])],
    }


def t_tooltips(s: S) -> dict | None:
    rs = chosen_residues(s, "tooltips", 2)
    if rs is None or "water" not in s.components:
        return None
    L = s.load()
    tips = [by_author(r, tooltip=res_word(r)) for r in rs]
    said = listing([f"'{res_word(r)}' on {res_words(s, [r])}" for r in rs])
    return {
        "prompts": [f"Load {s.name}, hide the waters and attach tooltips: {said}.",
                    f"In {s.name}, switch off the water molecules and add hover tooltips reading {said}.",
                    f"Open {s.name} without waters. When I hover I want to read {said}."],
        "reference": [L, prop("hide_water", True), {"action": "tooltips", "data": tips}],
        "target": [{"selector": [residue_atoms(r) for r in rs], "representation": None, "color": None}],
        "skills": ["load", "hide", "selection", "author-numbering", "tooltip"],
        "difficulty": numbering_facts(s, rs),
        "derived": "Seeded residues as in api-residue-colour; each tooltip text is the residue's "
                   "own name and author number, so the request states it in full.",
        "alts": [("label numbering",
                  [L, prop("hide_water", True),
                   {"action": "tooltips", "data": [by_label(r, tooltip=res_word(r)) for r in rs]}])],
        "traps": [("the author number in residue_number",
                   [L, prop("hide_water", True),
                    {"action": "tooltips", "data": label_trap(rs, tooltip="x")}])],
    }


def t_undo(s: S, variant: str) -> dict | None:
    ligs = real_ligands(s)
    if not ligs or s.kind != "pdb" or "water" not in s.components:
        return None
    lig = pick(ligs, "undo", s.id)
    what, it = lig_phrase(lig)
    (c,) = colours(1, "undo", s.id)
    L = s.load()
    chain = s.chains[0]
    whole = sel({"auth_asym_id": chain["auth_asym_id"]}, f"chain {chain['auth_asym_id']}",
                [{"label_asym_id": lc} for lc in s.label_chains_of(chain["auth_asym_id"])])
    plain_lig = {k: v for k, v in ligand_sel(lig).items() if k != "_t"}
    base = {"target": None, "alts": [], "traps": [],
            "difficulty": {"undo_step": variant, "ligand_code_in_prompt": True}}
    if variant == "camera":
        return {**base,
                "prompts": [f"Load {s.name}, colour {what} {cw(c)} and zoom in on {it}; then reset the camera "
                            "to the whole structure, keeping the colour.",
                            f"In {s.name}, colour {what} {cw(c)}, take a close look at {it}, and then bring the "
                            "camera back out to the default view of everything. The colouring stays.",
                            f"Open {s.name}; {what} in {cw(c)}, zoom to {it}, and afterwards reset the view "
                            "(camera only)."],
                "reference": [L, color_call([ligand_sel(lig, color=c, focus=True)]),
                              {"action": "reset", "camera": True}],
                "target": [{"selector": ligand_sel(lig)["_t"]["atoms"], "representation": None, "color": c}],
                "skills": ["load", "select-by-ligand", "color", "focus", "reset"],
                "derived": "The final state is the colouring with the camera on the whole structure; "
                           "only the final state is graded, so a list that never zooms is right too.",
                "alts": [("never zooming in", [L, color_call([{**plain_lig, "color": c}])])],
                "traps": [("left zoomed in", [L, color_call([{**plain_lig, "color": c, "focus": True}])])]}
    if variant == "selection":
        return {**base,
                "prompts": [f"Load {s.name} and hide the waters. Select chain {chain['auth_asym_id']} (default "
                            f"selection colouring) to see where it is, then clear that selection again and colour "
                            f"only {what} {cw(c)}.",
                            f"In {s.name} with the waters hidden: mark chain {chain['auth_asym_id']} with the "
                            f"default selection colour, clear the selection, and then colour just {what} {cw(c)}.",
                            f"Open {s.name}, waters off. Briefly select chain {chain['auth_asym_id']}, clear it, "
                            f"and finish with {what} in {cw(c)} and nothing else coloured."],
                "reference": [L, prop("hide_water", True), color_call([whole]), {"action": "clear_selection"},
                              color_call([ligand_sel(lig, color=c)])],
                "target": [{"selector": ligand_sel(lig)["_t"]["atoms"], "representation": None, "color": c}],
                "skills": ["load", "hide", "select-by-chain", "clear-selection", "select-by-ligand", "color"],
                "derived": "The chain selection is cleared again, so the final state is the waters "
                           "hidden and the ligand coloured; a list that skips the selection is right too.",
                "alts": [("without the selection that is cleared",
                          [L, prop("hide_water", True), color_call([{**plain_lig, "color": c}])])],
                "traps": [("the chain left selected",
                           [L, prop("hide_water", True), color_call([{"auth_asym_id": chain["auth_asym_id"]}]),
                            color_call([{**plain_lig, "color": c}], keep_colors=True)])]}
    if variant == "highlight":
        return {**base,
                "prompts": [f"Load {s.name} and hide the waters. Highlight chain {chain['auth_asym_id']}, then clear "
                            f"that highlight and highlight {what} instead.",
                            f"In {s.name} with the waters hidden: put the highlight on chain "
                            f"{chain['auth_asym_id']}, remove it again, and leave {what} highlighted.",
                            f"Open {s.name}, waters off. Highlight chain {chain['auth_asym_id']} for a moment, clear "
                            f"the highlight, and end with only {what} highlighted."],
                "reference": [L, prop("hide_water", True), {"action": "highlight", "data": [whole]},
                              {"action": "clear_highlight"}, {"action": "highlight", "data": [ligand_sel(lig)]}],
                "target": [{"selector": ligand_sel(lig)["_t"]["atoms"], "representation": None, "color": None}],
                "skills": ["load", "hide", "highlight", "clear-highlight", "select-by-ligand"],
                "derived": "The first highlight is cleared, so the final state is the waters hidden "
                           "and the ligand highlighted.",
                "alts": [("without the highlight that is cleared",
                          [L, prop("hide_water", True), {"action": "highlight", "data": [plain_lig]}])],
                "traps": [("the highlight left on the chain",
                           [L, prop("hide_water", True),
                            {"action": "highlight", "data": [{"auth_asym_id": chain["auth_asym_id"]}]}])]}
    hi, se = colours(2, "undo-colours", s.id)
    return {**base,
            "prompts": [f"Load {s.name}, set the hover-highlight colour to {cw(hi)} and the selection colour to "
                        f"{cw(se)}; then put the selection colour back to its default.",
                        f"In {s.name}, make the highlight colour {cw(hi)} and the selection colour {cw(se)}. On "
                        "second thoughts, reset the selection colour (only that) to the default.",
                        f"Open {s.name} with a {cw(hi)} highlight colour. Set the selection colour to {cw(se)} "
                        "too, then reset the selection colour."],
            "reference": [s.load(), {"action": "set_color", "highlight": hi, "select": se},
                          {"action": "reset", "selectColor": True}],
            "skills": ["load", "set-highlight-color", "set-select-color", "reset"],
            "difficulty": {"undo_step": variant},
            "derived": "Canvas colours only: the final state has the highlight colour set and the "
                       "selection colour at its default.",
            "alts": [("only the highlight colour set", [s.load(), prop("highlight_color", hi)])],
            "traps": [("the selection colour left set", [s.load(), {"action": "set_color", "highlight": hi, "select": se}])]}


def t_maps(s: S) -> dict | None:
    if not xray(s):
        return None
    which, words = pick([("2fo-fc", "2Fo-Fc"), ("fo-fc(+ve)", "positive Fo-Fc difference"),
                         ("fo-fc(-ve)", "negative Fo-Fc difference")], "maps", s.id)
    opacity = pick([0.3, 0.5, 0.7], "maps-opacity", s.id)
    setting = {which: {"opacity": opacity, "wireframe": True}}
    how = f"a wireframe at opacity {opacity}"
    return {
        "prompts": [f"Load {s.name} with its electron-density maps, drawing the {words} map as {how}.",
                    f"Open {s.name} and switch on the electron density; the {words} map should be {how}.",
                    f"In {s.name}, load the density maps and style the {words} map as {how}."],
        "reference": [s.load(), prop("load_maps", True), prop("map_settings", setting)],
        "target": None,
        "skills": ["load", "maps", "map-settings"],
        "difficulty": {"setting_only": ["load_maps", "map_settings"]},
        "derived": "An X-ray entry. Both options are compared as declared settings (the map "
                   "itself comes from PDBe at run time and is not modelled).",
        "alts": [], "traps": [("the map style without loading the maps", [s.load(), prop("map_settings", setting)])],
    }


def t_preset(s: S, want: str) -> dict | None:
    if want == "nmr" and s.entry["method"] == "NMR" and s.facts["n_models"] > 1:
        preset, words = "all-models", f"all {s.facts['n_models']} models of the NMR ensemble at once"
    elif want == "cell" and xray(s) and "water" in s.components:
        preset, words = pick([("unitcell", "the whole unit cell"), ("supercell", "the supercell")], "preset", s.id)
    else:
        return None
    bg = pick(["black", "white"], "preset", s.id)
    return {
        "prompts": [f"Load {s.name} showing {words}, on a {bg} background.",
                    f"Open {s.name} with the load preset that shows {words}; make the background {bg}.",
                    f"I want to see {words} of {s.name}, {bg} background."],
        "reference": [s.load(preset=preset), prop("bg_color", "#000000" if bg == "black" else "#FFFFFF")],
        "target": None,
        "skills": ["load", "load-preset", "set-background"],
        "difficulty": {"setting_only": ["default_preset"], "preset": preset},
        "derived": "The load preset is a fact of the state; atoms are compared on model 1 of the "
                   "deposited unit. " + ("An NMR entry with several models."
                                         if preset == "all-models" else "An X-ray entry (it has a unit cell)."),
        "alts": [], "traps": [("the default preset", [s.load(), prop("bg_color", bg)])],
    }


def superposition_tasks(n: int, used: set[str]) -> list[dict]:
    """PDBe-KB superposition views, by UniProt accession. They load no structure entry
    (``structures`` is empty) and are compared by their settings."""
    proteins = [p for p in grounding.panel()["disease_proteins"] if p["accession"] not in used]
    out = []
    for p in sorted(proteins, key=lambda p: h("superposition", p["accession"]))[:n]:
        acc, gene = p["accession"], p["gene"]
        bg = pick(["black", "white"], "superposition", acc)
        prompts = [f"Open the PDBe-KB superposition view for human {gene} (UniProt {acc}) on a {bg} background.",
                   f"Show all the superposed PDB structures of UniProt {acc} ({gene}) in the PDBe-KB "
                   f"superposition view, {bg} background.",
                   f"I want the PDBe-KB superposition of the {gene} structures (UniProt {acc}), with a {bg} background."]
        ref = [{"action": "load", "molecule_id": acc}, prop("superposition", True),
               prop("bg_color", "#000000" if bg == "black" else "#FFFFFF")]
        out.append({"family": "api-superposition", "tier": "tool_only", "key": acc.lower(), "structure": None,
                    "prompts": prompts, "reference": ref, "target": None,
                    "skills": ["load", "superposition", "set-background"],
                    "difficulty": {"setting_only": ["superposition"], "needs_uniprot_accession": False},
                    "derived": "A disease protein of the panel (data/panel/panel.json). In pdbe-molstar "
                               "3.3.2 the superposition view takes a UniProt accession as moleculeId; "
                               "it is compared by its settings (its content comes from PDBe-KB at run time).",
                    "alts": [("the settings before the load, a named background",
                              [prop("bg_color", bg), prop("superposition", True),
                               {"action": "load", "molecule_id": acc.lower()}])],
                    "traps": [("a PDB entry of the protein instead of the accession",
                               [{"action": "load", "molecule_id": p["entry"]}, prop("superposition", True),
                                prop("bg_color", bg)])],
                    "inputs": ["data/panel/panel.json"]})
    return out


def only(template: Callable, variant: str) -> Callable:
    return lambda s: template(s, variant)


#: (family, tier, template, how many to generate). A family may have several rows, one
#: per variant, so that every variant gets its share whatever the seed.
FAMILIES: list[tuple[str, str, Callable, int]] = [
    ("api-residue-colour", "translation", t_residue_colour, 9),
    ("api-residue-sticks", "translation", t_residue_sticks, 5),
    ("api-sticks-plain", "translation", t_sticks_plain, 3),
    ("api-range-colour", "translation", t_range_colour, 8),
    ("api-chain-colour", "translation", t_chain_colour, 8),
    ("api-uniprot-residue", "translation", t_uniprot_residue, 9),
    ("api-uniprot-range", "translation", t_uniprot_range, 6),
    ("api-ligand", "translation", t_ligand, 7),
    ("api-entity", "translation", t_entity, 5),
    ("api-atoms", "translation", t_atoms, 5),
    ("api-assembly", "translation", t_assembly, 5),
    ("api-hide", "translation", only(t_hide, "carbs"), 2),
    ("api-hide", "translation", only(t_hide, "non-standard"), 2),
    ("api-hide", "translation", only(t_hide, "polymer"), 2),
    ("api-hide", "translation", only(t_hide, "het"), 1),
    ("api-hide", "translation", only(t_hide, "water+ligand"), 1),
    ("api-layered-colour", "translation", t_layered, 7),
    ("api-style-colour", "translation", t_style_colour, 5),
    ("api-alphafold", "tool_only", t_alphafold, 2),
    ("api-validation-overlay", "tool_only", t_validation, 2),
    ("api-domain-overlay", "tool_only", t_domain, 2),
    ("api-symmetry-overlay", "tool_only", t_symmetry, 1),
    ("api-ligand-view", "tool_only", t_ligand_view, 3),
    ("api-canvas", "tool_only", t_canvas, 2),
    ("api-highlight", "tool_only", t_highlight, 2),
    ("api-tooltips", "tool_only", t_tooltips, 3),
    ("api-undo", "tool_only", only(t_undo, "camera"), 1),
    ("api-undo", "tool_only", only(t_undo, "selection"), 1),
    ("api-undo", "tool_only", only(t_undo, "highlight"), 1),
    ("api-undo", "tool_only", only(t_undo, "colours"), 1),
    ("api-maps", "tool_only", t_maps, 2),
    ("api-preset", "tool_only", only(t_preset, "cell"), 1),
    ("api-preset", "tool_only", only(t_preset, "nmr"), 1),
]
N_SUPERPOSITION = 2


# --------------------------------------------------------------------------- #
# The 20 curated tasks (July 2026, repaired in phase A), rebuilt in the task format
# --------------------------------------------------------------------------- #
def curated(structs: dict[str, S]) -> list[dict]:
    """The curated tasks, each rebuilt from the frozen facts with the same helpers as the
    generated ones. Ids, file names and references are those of phase A (other tests
    and the July results refer to them). Prompts differ from phase A only where a
    ligand was named in words alone: its component code is now given (closed-book
    fairness), which ``prompt_change`` records."""
    def S_(e: str) -> S:
        return structs[e]

    def res(s: S, chain: str, num: int, comp: str) -> dict:
        hits = [r for r in s.residues if r["ac"] == chain and r["an"] == num and not r["ins"] and r["poly"]]
        assert len(hits) == 1 and hits[0]["comp"] == comp, (s.id, chain, num, comp, hits)
        assert s.addressable(hits[0]), (s.id, chain, num)
        return hits[0]

    def lig(s: S, comp: str) -> dict:
        return next(g for g in s.facts["ligands"] if g["comp_id"] == comp)

    def chain_sel(s: S, chain: str, **attrs: Any) -> dict:
        return sel({"auth_asym_id": chain}, f"chain {chain}",
                   [{"label_asym_id": lc} for lc in s.label_chains_of(chain)], **attrs)

    def hexed(alt: list[dict], rgb: dict) -> list[dict]:
        return alt

    out: list[dict] = []

    def add(num: str, stem: str, tier: str, family: str, entry: str | None, title: str, prompt: str,
            reference: list[dict], target: Any, skills: list[str], july: str, derived: str,
            accepted: list[list[dict]] | None = None, notes: str | None = None,
            prompt_change: str | None = None, difficulty: dict | None = None) -> None:
        out.append({"curated": num, "file": f"{num}_{stem}.json", "id": f"api-{num}", "tier": tier,
                    "family": family, "structure": entry, "title": title, "prompts": [prompt],
                    "reference": reference, "target": target, "skills": skills, "july_task": july,
                    "derived": derived, "accepted": accepted or [], "notes": notes,
                    "prompt_change": prompt_change, "difficulty": difficulty or {}, "alts": [], "traps": []})

    code = "the ligand's component code added to the request (it was named in words only)"

    s = S_("1a6m")
    add("001", "load_hide_water", "translation", "api-hide", "1a6m", "Load and hide waters",
        "Load the myoglobin structure 1A6M and hide all the water molecules.",
        [s.load(), prop("hide_water", True)], None, ["load", "hide"], "replaced",
        "1A6M has waters (the July entry, 1MBN, has none, so hiding them changed nothing).")
    s = S_("1cbs")
    add("002", "ligand_only", "translation", "api-hide", "1cbs", "Only the ligand",
        "Load cellular retinoic-acid-binding protein II (1CBS) and hide the protein and the waters so that "
        "only the bound retinoic acid is shown.",
        [s.load(), prop("hide_polymer", True), prop("hide_water", True)], None, ["load", "hide"], "replaced",
        "1CBS has polymer, waters and one ligand; hiding the first two leaves the retinoic acid. "
        "(The July task was the prompt's worked example; that is now 1HSG.)")
    s = S_("1hho")
    hem = lig(s, "HEM")
    assert hem["heme"]
    orange = {"r": 255, "g": 165, "b": 0}
    add("003", "hemoglobin_heme", "translation", "api-ligand-sticks", "1hho",
        "Heme groups as orange ball-and-stick",
        "Open haemoglobin (1HHO) and show the heme groups (HEM) in ball-and-stick coloured orange, with the "
        "rest as cartoon.",
        [s.load(), style("cartoon"),
         color_call([ligand_sel(hem, representation="ball-and-stick", representationColor="orange")])],
        [{"selector": ligand_sel(hem)["_t"]["atoms"], "representation": "ball-and-stick", "color": "orange"}],
        ["load", "global-style", "select-by-ligand", "per-selection-representation", "color"], "unchanged",
        "Under a cartoon style the heme's default representation is not drawn; the added ball-and-stick "
        "takes its colour from representationColor.",
        accepted=[[s.load(), style("cartoon"),
                   color_call([{"label_comp_id": "HEM", "color": orange, "representation": "ball-and-stick",
                                "representationColor": orange}])]],
        notes="An added representation is coloured by representationColor, not color.",
        prompt_change=code, difficulty={"hinges_on": ["added_representation_colour"],
                                        "ligand_code_in_prompt": True})
    s = S_("1lyz")
    e35, d52 = res(s, "A", 35, "GLU"), res(s, "A", 52, "ASP")
    surf = dict(color="red", representation="molecular-surface", representationColor="red")
    add("004", "active_site_surface", "translation", "api-residue-sticks", "1lyz",
        "Catalytic residues as a red surface",
        "Load hen egg-white lysozyme (1LYZ) as a cartoon, colour the two catalytic residues Glu35 and Asp52 "
        "red, and also show them as a red molecular surface.",
        [s.load(), style("cartoon"), color_call([by_author(e35, **surf), by_author(d52, **surf)])],
        [{"selector": [residue_atoms(e35), residue_atoms(d52)], "representation": "molecular-surface",
          "color": "red"}],
        ["load", "global-style", "selection", "author-numbering", "color", "per-selection-representation"],
        "reworded", "The residue names at author numbers 35 and 52 are read from the atom table.",
        accepted=[[s.load(), style("cartoon"), color_call([by_label(e35, **surf), by_label(d52, **surf)])]],
        difficulty={**numbering_facts(s, [e35, d52]), "hinges_on": ["added_representation_colour"]})
    add("005", "superposition_view", "tool_only", "api-superposition", None, "PDBe-KB superposition view",
        "Open the PDBe-KB superposition view for human haemoglobin subunit alpha (UniProt P69905) on a white "
        "background.",
        [{"action": "load", "molecule_id": "P69905"}, prop("superposition", True), prop("bg_color", "#FFFFFF")],
        None, ["load", "superposition", "set-background"], "replaced",
        "In pdbe-molstar 3.3.2 the superposition view takes a UniProt accession as moleculeId and shows the "
        "PDBe-KB superposed entries of that protein. Compared by its settings.",
        notes="Tool-control only: no MVS equivalent.", difficulty={"setting_only": ["superposition"]})
    s = S_("4ins")
    assert "water" in s.components and "ion" in s.components
    add("006", "spin_clean", "tool_only", "api-canvas", "4ins", "Clean spinning view",
        "Show insulin (4INS), hide the waters and the heteroatoms, set glossy lighting, and make it slowly spin.",
        [s.load(), prop("hide_water", True), prop("hide_heteroatoms", True), prop("lighting", "glossy"),
         prop("spin", True)], None, ["load", "hide", "lighting", "spin"], "unchanged",
        "4INS has waters and zinc ions (the heteroatom component).",
        difficulty={"setting_only": ["lighting"]})
    s = S_("1stp")
    btn = lig(s, "BTN")
    add("007", "streptavidin_biotin_focus", "translation", "api-ligand", "1stp", "Centre on the biotin",
        "Load streptavidin (1STP), hide the waters, and centre the view on the bound biotin (BTN).",
        [s.load(), prop("hide_water", True), {"action": "focus", "data": [ligand_sel(btn)]}],
        [{"selector": ligand_sel(btn)["_t"]["atoms"], "representation": None, "color": None}],
        ["load", "hide", "select-by-ligand", "focus"], "reworded",
        "1STP has waters and one biotin (frozen facts).", prompt_change=code,
        difficulty={"ligand_code_in_prompt": True})
    s = S_("3ptb")
    ben, s195 = lig(s, "BEN"), res(s, "A", 195, "SER")
    red = dict(color="red", representation="ball-and-stick", representationColor="red")
    add("008", "trypsin_benzamidine", "translation", "api-ligand-sticks", "3ptb",
        "Benzamidine and Ser195",
        "Load bovine trypsin (3PTB) as a cartoon. Show the benzamidine inhibitor (BEN) as yellow "
        "ball-and-stick, colour the catalytic Ser195 red, and also show Ser195 as red ball-and-stick.",
        [s.load(), style("cartoon"),
         color_call([ligand_sel(ben, representation="ball-and-stick", representationColor="yellow"),
                     by_author(s195, **red)])],
        [{"selector": ligand_sel(ben)["_t"]["atoms"] + [residue_atoms(s195)],
          "representation": "ball-and-stick", "color": None}],
        ["load", "global-style", "select-by-ligand", "selection", "author-numbering", "color",
         "per-selection-representation"], "reworded",
        "Ser195 is the author number (label number 177); the July reference used the label key.",
        accepted=[[s.load(), style("cartoon"),
                   color_call([{"label_comp_id": "BEN", "representation": "ball-and-stick",
                                "representationColor": "yellow"}, by_label(s195, **red)])]],
        prompt_change=code,
        difficulty={**numbering_facts(s, [s195]), "hinges_on": ["added_representation_colour"],
                    "ligand_code_in_prompt": True})
    s = S_("4ins")
    zn = lig(s, "ZN")
    add("009", "insulin_chains_zinc", "translation", "api-chain-colour", "4ins", "Insulin chains and zinc",
        "Load insulin (4INS) as a cartoon. Colour the two A chains (author chains A and C) blue and the two B "
        "chains (author chains B and D) yellow, and show the zinc ions (ZN) as magenta spacefill.",
        [s.load(), style("cartoon"),
         color_call([chain_sel(s, "A", color="blue"), chain_sel(s, "C", color="blue"),
                     chain_sel(s, "B", color="yellow"), chain_sel(s, "D", color="yellow"),
                     ligand_sel(zn, representation="spacefill", representationColor="magenta")])],
        None, ["load", "global-style", "select-by-chain", "color", "select-by-ligand",
               "per-selection-representation"], "reworded",
        "Chain ids and the zinc ions are those of the frozen facts.", prompt_change=code,
        difficulty={"ligand_code_in_prompt": True, "auth_label_chain": False})
    s = S_("1ubq")
    add("010", "ubiquitin_presentation", "tool_only", "api-canvas", "1ubq", "Presentation view",
        "Load ubiquitin (1UBQ) as a cartoon with glossy lighting on a black background, hide the waters, and "
        "set it slowly spinning.",
        [s.load(), style("cartoon"), prop("lighting", "glossy"), prop("bg_color", "#000000"),
         prop("hide_water", True), prop("spin", True)], None,
        ["load", "global-style", "lighting", "set-background", "hide", "spin"], "unchanged",
        "1UBQ has waters. Under the cartoon style they are not drawn anyway, so the hide toggle changes "
        "nothing on screen and an answer without it is graded the same.",
        difficulty={"setting_only": ["lighting"]})
    s = S_("1ema")
    cro = res(s, "A", 66, "CRO")
    add("011", "gfp_chromophore", "translation", "api-ligand-sticks", "1ema", "GFP chromophore",
        "Load green fluorescent protein (1EMA) as a cartoon, colour the chromophore (CRO) orange, and also "
        "show it as orange ball-and-stick.",
        [s.load(), style("cartoon"),
         color_call([sel({"label_comp_id": "CRO"}, "chromophore CRO66", [residue_atoms(cro)], color="orange",
                         representation="ball-and-stick", representationColor="orange")])],
        [{"selector": [residue_atoms(cro)], "representation": "ball-and-stick", "color": "orange"}],
        ["load", "global-style", "select-by-ligand", "color", "per-selection-representation"], "reworded",
        "The chromophore is a modified residue inside the chain (CRO 66, frozen facts), not a ligand.",
        prompt_change=code, difficulty={"hinges_on": ["added_representation_colour"],
                                        "ligand_code_in_prompt": True, "modified_residue": True})
    s = S_("1f88")
    ret = lig(s, "RET")
    assert "branched" in s.components and "water" in s.components
    add("012", "rhodopsin_retinal", "translation", "api-hide", "1f88", "Rhodopsin retinal",
        "Load bovine rhodopsin (1F88), hide the carbohydrates and the waters, and colour the retinal (RET) orange.",
        [s.load(), prop("hide_carbs", True), prop("hide_water", True), color_call([ligand_sel(ret, color="orange")])],
        [{"selector": ligand_sel(ret)["_t"]["atoms"], "representation": None, "color": "orange"}],
        ["load", "hide", "select-by-ligand", "color"], "reworded",
        "1F88 has branched carbohydrates, waters and two retinals (frozen facts).", prompt_change=code,
        difficulty={"ligand_code_in_prompt": True})
    s = S_("1bna")
    add("013", "bdna_by_strand", "translation", "api-chain-colour", "1bna", "B-DNA by strand",
        "Load the Drew-Dickerson B-DNA dodecamer (1BNA) as a cartoon, colour strand A blue and strand B red, "
        "and hide the waters.",
        [s.load(), style("cartoon"), color_call([chain_sel(s, "A", color="blue"), chain_sel(s, "B", color="red")]),
         prop("hide_water", True)], None, ["load", "global-style", "select-by-chain", "color", "hide"],
        "unchanged", "Two DNA chains, A and B (frozen facts).", difficulty={"auth_label_chain": False})
    s = S_("1ubq")
    tail = {"label_asym_id": "A", "beg_label_seq_id": 71, "end_label_seq_id": 76}
    add("014", "ubiquitin_tail_range", "translation", "api-range-colour", "1ubq", "Ubiquitin tail",
        "Load ubiquitin (1UBQ) and colour the C-terminal tail, residues 71 to 76, red and the rest of the "
        "structure white.",
        [s.load(), color_call([sel({"start_residue_number": 71, "end_residue_number": 76}, "residues 71-76",
                                   tail, color="red")], non_selected_color="white")],
        [{"selector": tail, "representation": None, "color": "red"}],
        ["load", "selection", "residue-range", "color", "non-selected-color"], "replaced",
        "In 1UBQ author and label numbers agree, so either range key selects residues 71-76.",
        accepted=[[s.load(), color_call([{"auth_asym_id": "A", "start_auth_residue_number": 71,
                                          "end_auth_residue_number": 76, "color": "red"}],
                                        non_selected_color="white")]],
        difficulty={"numbering_offset": False})
    s = S_("1hho")
    assert built_assembly(s) is not None
    add("015", "hemoglobin_assembly_surface", "translation", "api-assembly", "1hho", "Assembly as a surface",
        "Load oxyhaemoglobin (1HHO) as its biological assembly (the tetramer, assembly 1) and show it as a "
        "molecular surface.",
        [s.load(assembly_id="1"), style("molecular-surface")], None, ["load", "assembly", "global-style"],
        "replaced", "Assembly 1 of 1HHO is built by symmetry (frozen facts): the deposited model is one "
        "alpha-beta pair.", difficulty={"assembly_differs_from_deposited": True})
    s = S_("af-p04637-f1-model_v6")
    add("016", "alphafold_p53", "tool_only", "api-alphafold", s.id, "AlphaFold model with confidence colouring",
        "Load the AlphaFold DB model of human p53 (UniProt P04637) and colour it by the model's per-residue "
        "confidence (pLDDT).",
        [s.load(), prop("alphafold_view", True)], None, ["load", "custom-data", "alphafold"], "reworded",
        "alphafold_view only switches the colouring; the model comes in as custom_data from the AlphaFold DB "
        "file. The entry is compared as AF-P04637-F1 whatever the file version or format.",
        accepted=[[{"action": "load", "alphafold": True, "custom_data": {
            "url": "https://alphafold.ebi.ac.uk/files/AF-P04637-F1-model_v4.bcif", "format": "bcif",
            "binary": True}}]],
        notes="Tool-control: custom data source plus a colouring switch.",
        difficulty={"needs_alphafold_url": True, "setting_only": ["alphafold_view"]})
    s = S_("3eml")
    add("017", "receptor_validation_overlay", "tool_only", "api-validation-overlay", "3eml",
        "Validation overlay",
        "Load the A2A adenosine receptor (3EML) as a cartoon and overlay the PDBe geometry-validation colouring.",
        [s.load(), style("cartoon"), prop("validation_annotation", True)], None,
        ["load", "global-style", "validation-annotation"], "unchanged",
        "The annotation is compared as a declared setting.",
        difficulty={"setting_only": ["validation_annotation"]})
    s = S_("1aki")
    g35 = res(s, "A", 35, "GLU")
    add("018", "lysozyme_domain_tooltip", "tool_only", "api-domain-overlay", "1aki", "Domains and a tooltip",
        "Load hen egg-white lysozyme (1AKI) as a cartoon, overlay the domain annotations, and attach a tooltip "
        "reading 'catalytic glutamate' to Glu35 on chain A.",
        [s.load(), style("cartoon"), prop("domain_annotation", True),
         {"action": "tooltips", "data": [by_author(g35, tooltip="catalytic glutamate")]}],
        [{"selector": [residue_atoms(g35)], "representation": None, "color": None}],
        ["load", "global-style", "domain-annotation", "selection", "author-numbering", "tooltip"], "unchanged",
        "Author residue 35 of chain A is a glutamate (atom table).",
        difficulty={**numbering_facts(s, [g35]), "setting_only": ["domain_annotation"]})
    s = S_("3ptb")
    triad = [res(s, "A", 57, "HIS"), res(s, "A", 102, "ASP"), res(s, "A", 195, "SER")]
    mag = dict(color="magenta", representation="ball-and-stick", representationColor="magenta")
    add("019", "trypsin_triad_focus", "translation", "api-residue-sticks", "3ptb", "Catalytic triad",
        "Load trypsin (3PTB) as a cartoon, colour the catalytic triad (His57, Asp102 and Ser195) magenta, also "
        "show those three residues as magenta ball-and-stick, and centre the camera on them.",
        [s.load(), style("cartoon"), color_call([by_author(r, **mag) for r in triad]),
         {"action": "focus", "data": [by_author(r) for r in triad]}],
        [{"selector": [residue_atoms(r) for r in triad], "representation": "ball-and-stick", "color": "magenta"}],
        ["load", "global-style", "selection", "author-numbering", "color", "per-selection-representation",
         "focus"], "reworded",
        "His57, Asp102 and Ser195 are author numbers (chymotrypsinogen numbering); their label numbers are "
        "40, 84 and 177. The July reference put the author numbers in the label key.",
        accepted=[[s.load(), style("cartoon"), color_call([by_label(r, **mag) for r in triad]),
                   {"action": "focus", "data": [by_label(r) for r in triad]}]],
        difficulty={**numbering_facts(s, triad), "hinges_on": ["added_representation_colour"]})
    s = S_("1hho")
    add("020", "hemoglobin_ui_colors_highlight", "tool_only", "api-highlight", "1hho",
        "Highlight colours and a highlight",
        "Load haemoglobin (1HHO), set the hover-highlight colour to yellow and the selection colour to cyan, "
        "and highlight the heme groups (HEM).",
        [s.load(), {"action": "set_color", "highlight": "yellow", "select": "cyan"},
         {"action": "highlight", "data": [ligand_sel(hem)]}],
        [{"selector": ligand_sel(hem)["_t"]["atoms"], "representation": None, "color": None}],
        ["load", "set-highlight-color", "set-select-color", "select-by-ligand", "highlight"], "reworded",
        "Both heme groups, by component code (frozen facts).",
        accepted=[[s.load(), prop("highlight_color", "#FFFF00"), prop("select_color", "#00FFFF"),
                   {"action": "highlight", "data": [{"label_comp_id": "HEM"}]}]],
        prompt_change=code, difficulty={"ligand_code_in_prompt": True})
    return out


# --------------------------------------------------------------------------- #
# Assembling and checking a task
# --------------------------------------------------------------------------- #
class Unfit(Exception):
    """The template's task on this structure failed one of its own checks."""


def grade(task: dict, answer: list[dict]) -> dict:
    return runner.grade_parsed(task, answer)


def build_task(spec: dict, s: S | None, tid: str, tier: str, family: str, split: str) -> dict:
    wording = h("wording", family, spec.get("key") or (s.id if s else tid)) % len(spec["prompts"])
    reference, targets = strip(spec["reference"])
    accepted = [strip(a)[0] for a in spec.get("accepted", [])]
    table = s.table if s is not None else None
    for t in targets:
        t["n_atoms"] = table.selector(t["atoms"]).bit_count()
    difficulty = {"numbering_offset": False, "auth_label_chain": False, "ligand_identity_needed": False,
                  "uniprot_mapping": False, "hinges_on": [], **spec["difficulty"]}
    prov = {"script": SCRIPT, "inputs": spec.get("inputs") or (s.inputs if s is not None else ["data/panel/panel.json"]), "date": DATE, "checks": [],
            "structure": ps.replay(copy.deepcopy(reference)).entry, "derived": spec["derived"],
            "checked_by": "scripts/check_api_refs.py", "seed": SEED,
            "wording": f"{wording + 1} of {len(spec['prompts'])}", "difficulty": difficulty,
            "targets": targets}
    for key in ("july_task", "prompt_change"):
        if spec.get(key):
            prov[key] = spec[key]
    task = {"id": tid, "track": "api", "tier": tier, "family": family,
            "structures": [s.id] if s is not None else [], "prompt": spec["prompts"][wording],
            "reference": reference, "accepted": accepted, "context": None, "target": spec["target"],
            "twin_of": None, "paraphrase_of": None, "style": "full", "split": split, "grounding": None,
            "provenance": prov, "skills": spec["skills"]}
    if spec.get("title"):
        task["title"] = spec["title"]
    if spec.get("notes"):
        task["notes"] = spec["notes"]
    verify(task, spec)
    return task


def verify(task: dict, spec: dict) -> None:
    """Every check a task passes before it is written; raises `Unfit` otherwise. The
    checks that passed are written, in words, to ``provenance.checks``."""
    done = task["provenance"]["checks"]
    done.append("matches the task format (molbench.tasks.validate_task)")
    errors = T.validate_task(task)
    if errors:
        raise Unfit(f"format: {errors}")
    view = T._with_aliases(dict(task))
    problems = check.check_task(view)
    if problems:
        raise Unfit(f"check_api_refs: {problems}")
    n_sel = len(task["provenance"]["targets"])
    done.append("schema-valid; replays with nothing ignored or unresolved (scripts/check_api_refs.py)")
    if n_sel:
        done.append(f"each of the {n_sel} selection(s) selects exactly the atoms written a second time in "
                    "provenance.targets (author chain, author number and residue name, or label chains / "
                    "label ranges from the frozen facts), resolved by molbench.atoms")
    problems = runner.grader_problems(view)
    if problems:
        raise Unfit(f"grader check: {problems}")
    res = grade(view, task["reference"])
    if not (res["success"] and res["f1"] == 1.0 and res["target_f1"] == 1.0 and res["grader"] == "state"):
        raise Unfit(f"own reference: f1 {res['f1']} success {res['success']} target {res['target_f1']}")
    done.append("the reference grades as exactly right against the task (F1 1, success, target score 1)")
    load = [a for a in task["reference"] if a.get("action") == "load"][:1]
    bare = [{k: v for k, v in load[0].items() if k in ("action", "molecule_id", "custom_data")}]
    if grade(view, bare)["f1"] != 0:
        raise Unfit("a bare load scores above 0")
    done.append("a bare load scores 0")
    near = grade(view, perturb_reference(task["reference"]))
    if near["success"]:
        raise Unfit("the near miss (one colour changed, or the last step dropped) succeeds")
    if near["f1"] > 0:
        done.append("a near miss (first colour changed, or last step dropped) is not a success and earns "
                    f"partial credit (F1 {near['f1']})")
    elif not spec.get("curated"):
        raise Unfit("the near miss earns no partial credit")
    for i, alt in enumerate(task["accepted"]):
        if not grade(view, alt)["success"]:
            raise Unfit(f"accepted[{i}] does not succeed")
    for label, alt in spec.get("alts", []):
        r = grade(view, alt)
        if not r["success"]:
            raise Unfit(f"equivalent answer fails ({label}): f1 {r['f1']}")
        done.append(f"equivalent answer succeeds: {label}")
    for label, trap in spec.get("traps", []):
        r = grade(view, trap)
        if r["success"]:
            raise Unfit(f"wrong answer succeeds ({label})")
        done.append(f"wrong answer fails: {label} (F1 {r['f1']})")
    colours_used = set()

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                if k in ("color", "non_selected_color", "representationColor", "highlight", "select") \
                        and isinstance(v, str) and not v.startswith("#"):
                    colours_used.add(v)
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(task["reference"])
    if not colours_used <= set(TASK_PALETTE):
        raise Unfit(f"colours outside the task palette: {sorted(colours_used - set(TASK_PALETTE))}")
    if T._mentions_worked_example(task):
        raise Unfit("uses 1HSG, the prompt's worked example")


def build_all() -> tuple[list[dict], list[dict], dict]:
    """(curated tasks, generated tasks, bookkeeping)."""
    entries = [e for e in grounding.panel()["entries"] if e["id"] != T.WORKED_EXAMPLE]
    structs = {e["id"]: S(e) for e in entries}
    held = set(heldback_structures())
    cur_specs = curated(structs)
    cur_tasks = []
    usage: Counter = Counter()
    for spec in cur_specs:
        s = structs[spec["structure"]] if spec["structure"] else None
        assert s is None or s.id not in held, f"curated task on a held-back structure: {s.id}"
        task = build_task(spec, s, spec["id"], spec["tier"], spec["family"], "public")
        task["_file"] = spec["file"]
        cur_tasks.append(task)
        if s is not None:
            usage[(spec["tier"], s.id)] += 1
    skipped: dict[str, list[str]] = {}
    gen_tasks: list[dict] = []
    in_family: set[tuple[str, str]] = set()      # one task per structure and family
    for family, tier, template, quota in FAMILIES:
        made = 0
        tried: set[str] = set()
        while made < quota:
            # least-used structure first (so the panel is spread over), then by seed;
            # held-back structures get their share because the order ignores the split
            pool = [s for s in structs.values() if s.id not in tried
                    and usage[(tier, s.id)] < MAX_PER_STRUCTURE
                    and (s.kind == "pdb") == (family != "api-alphafold")
                    and (family, s.id) not in in_family]
            if not pool:
                break
            s = min(pool, key=lambda x: (usage[(tier, x.id)], h("order", family, x.id)))
            tried.add(s.id)
            try:
                spec = template(s)
                if spec is None:
                    continue
                short = s.id if s.kind == "pdb" else s.id.split("-model")[0]
                task = build_task(spec, s, f"{family}-{short}", tier, family,
                                  "heldback" if s.id in held else "public")
            except Unfit as e:
                skipped.setdefault(family, []).append(f"{s.id}: {e}")
                continue
            gen_tasks.append(task)
            usage[(tier, s.id)] += 1
            in_family.add((family, s.id))
            made += 1
        if made < quota:
            skipped.setdefault(family, []).append(f"only {made} of {quota} could be made")
    used_acc = {"P69905"}
    for spec in superposition_tasks(N_SUPERPOSITION, used_acc):
        gen_tasks.append(build_task(spec, None, f"api-superposition-{spec['key']}", "tool_only",
                                    "api-superposition", "public"))
    return cur_tasks, gen_tasks, {"held": sorted(held), "skipped": skipped, "usage": usage}


# --------------------------------------------------------------------------- #
# Reports
# --------------------------------------------------------------------------- #
def coverage(tasks: list[dict]) -> dict[str, Counter]:
    """How many tasks' references use each action, property, selector key, selection
    attribute, load option and visual style."""
    cov = {k: Counter() for k in ("action", "property", "selector key", "selection attribute",
                                  "load option", "visual style", "call option")}
    for t in tasks:
        seen: set[tuple[str, str]] = set()
        for act in t["reference"]:
            name = act["action"]
            seen.add(("action", name))
            if name == "set_property":
                seen.add(("property", act["name"]))
            if name == "set_visual_style":
                seen.add(("visual style", act["style"]))
            if name == "load":
                seen |= {("load option", k) for k in act if k != "action"}
            if name in ("color", "highlight", "reset", "set_color"):
                seen |= {("call option", f"{name}.{k}") for k in act if k not in ("action", "data")}
            for p in act.get("data") or []:
                for k in p:
                    kind = "selector key" if k in ps.LOCATOR_KEYS else "selection attribute"
                    seen.add((kind, k))
                if p.get("representation"):
                    seen.add(("selection attribute", f"representation={p['representation']}"))
        for kind, name in seen:
            cov[kind][name] += 1
    return cov


def coverage_table(tasks: list[dict]) -> str:
    from molbench import schema
    cov = coverage(tasks)
    universe = {
        "action": schema.ACTION_NAMES, "property": list(schema.SETTABLE_PROPERTIES),
        "selector key": schema.SELECTION_LOCATOR_FIELDS, "visual style": schema.REPRESENTATIONS,
        "selection attribute": schema.SELECTION_ATTR_FIELDS
        + [f"representation={r}" for r in schema.REPRESENTATIONS],
        "load option": schema.ACTION_SPECS["load"]["optional"],
        "call option": ["color.non_selected_color", "color.keep_colors", "color.keep_representations",
                        "highlight.color", "highlight.focus", "set_color.highlight", "set_color.select"]
        + [f"reset.{f}" for f in schema.RESET_FLAGS],
    }
    lines = ["| surface | name | tasks |", "|---|---|---:|"]
    for kind, names in universe.items():
        for name in names:
            lines.append(f"| {kind} | `{name}` | {cov[kind].get(name, 0)} |")
    return "\n".join(lines)


DERIVATION = {
    "api-residue-colour": "1-3 seeded residues of a protein chain whose author numbers differ from the label numbers; named as papers do (His57). Checked: author keys select exactly the residue of that name; the label form succeeds; the author number in `residue_number` fails.",
    "api-residue-sticks": "The same, plus an added representation in the same colour (`representationColor`). Hinges on the viewer rule that `color` does not colour an added representation.",
    "api-sticks-plain": "The same, with an added ball-and-stick and no recolouring (`color: null`; without the key the viewer paints its default orange).",
    "api-range-colour": "A seeded author-numbered range inside one run of a chain with a numbering offset; kept only if it selects exactly the polymer residues of the matching label range. A third of the tasks also colour everything else.",
    "api-chain-colour": "One or two chains of an entry whose author chain ids differ from the label chain ids, named by author id. The cartoon style is asked for unless the author chain is exactly the polymer chain, so every reading of 'chain X' gives the same picture.",
    "api-uniprot-residue": "1-2 seeded UniProt positions from the frozen SIFTS table (observed, same residue as UniProt, author number != UniProt number), selected with the viewer's UniProt keys. Checked: the SIFTS rows in author numbering give the same atoms; the UniProt number as an author number fails.",
    "api-uniprot-range": "A seeded run of consecutive UniProt positions, selected with the viewer's UniProt range keys; same checks.",
    "api-ligand": "A ligand from the frozen facts (more than five heavy atoms, not a crystallisation additive), named with its component code; coloured and focused. One copy by chain when each chain has one.",
    "api-ligand-sticks": "(curated only) A ligand or modified residue as an added, coloured representation under the cartoon style.",
    "api-entity": "Two polymer entities by entity id; intended atoms are the entity's label chains from the facts. Entity ids as numbers fail (the viewer compares with ===).",
    "api-atoms": "Named atoms of a single-copy ligand (its metal, when it has one), or two side-chain atoms of a seeded residue under the ball-and-stick style.",
    "api-assembly": "Assembly 1 where the facts say it is built by symmetry from every deposited chain, plus a ligand or range colouring. The assembly is a fact of the state; atoms are compared on the deposited unit.",
    "api-hide": "Hide toggles for components the entry has (waters, heteroatoms, carbohydrates on entries whose sugars are all branched, non-standard residues, polymer), with a colouring or a second toggle.",
    "api-layered-colour": "A seeded author range and one residue inside it in another colour: one call in order, or two calls with keep_colors. The reverse order and two calls without keep_colors fail.",
    "api-style-colour": "A global style and a seeded author range colouring. The style has to be set first (setting it reloads and wipes colouring); the reverse order fails.",
    "api-alphafold": "The panel's AlphaFold DB models, loaded with custom_data from the documented URL pattern, pLDDT colouring switched on, and a tooltip on a seeded range.",
    "api-validation-overlay": "X-ray entries with waters: waters hidden, validation annotation on (a declared setting).",
    "api-domain-overlay": "Entries with a UniProt mapping: domain annotation and sequence panel on (declared settings).",
    "api-symmetry-overlay": "An entry whose assembly 1 is built by symmetry: that assembly with the symmetry annotation on.",
    "api-ligand-view": "The PDBe ligand view of a single-copy ligand named by code, with a background colour. Compared by the ligand it names.",
    "api-superposition": "The PDBe-KB superposition view of a panel disease protein by UniProt accession. No structure entry; compared by settings.",
    "api-canvas": "Background, lighting and spin.",
    "api-highlight": "The viewer's highlight on seeded author-numbered residues, with a highlight colour and focus.",
    "api-tooltips": "Tooltips on seeded author-numbered residues (the text is the residue's own name and number), waters hidden.",
    "api-undo": "A request with a step that is undone again (reset camera, clear selection, clear highlight, reset selection colour). Only the final state is graded.",
    "api-maps": "X-ray entries: electron-density maps on, one map styled (declared settings).",
    "api-preset": "A load preset (unit cell or supercell for an X-ray entry, all models for an NMR ensemble) and a background colour.",
}


def readme(directory: str, tasks: list[dict], info: dict, all_tasks: list[dict]) -> str:
    fam = Counter((t["tier"], t["family"]) for t in tasks)
    tiers = Counter(t["tier"] for t in all_tasks)
    lines = []
    if directory == "api_generated":
        lines += ["# Generated API-track tasks", "",
                  "Written by `scripts/generate_api_tasks.py` (seed "
                  f"{SEED}); do not edit by hand. Re-running the script reproduces every file byte for byte "
                  "(`--check`). The 20 curated tasks are in `tasks/api_calling/`.", ""]
    else:
        lines += ["# Curated API-track tasks", "",
                  "The 20 tasks of July 2026 as repaired in phase A, rebuilt in the task format by "
                  "`scripts/generate_api_tasks.py` (function `curated`); do not edit by hand. Ids, file names "
                  "and references are unchanged. Where a ligand was named in words only, its component code "
                  "was added to the request (`provenance.prompt_change`). The generated tasks are in "
                  "`tasks/api_generated/`.", ""]
    lines += [f"{len(tasks)} tasks on {len({s for t in tasks for s in t['structures']})} structures; "
              f"{sum(t['split'] == 'heldback' for t in tasks)} held back.", "",
              "| tier | template (family) | tasks | share of the tier (both directories) | how the reference is derived |",
              "|---|---|---:|---:|---|"]
    both = Counter((t["tier"], t["family"]) for t in all_tasks)
    for (tier, family), n in sorted(fam.items()):
        lines.append(f"| {tier} | `{family}` | {n} | {both[(tier, family)]} of {tiers[tier]} "
                     f"({100 * both[(tier, family)] / tiers[tier]:.0f}%) | {DERIVATION.get(family, '')} |")
    lines += ["", "## Rules every task obeys", "",
              "- The request names every structure by id, every residue by name and author number, every ligand "
              "by component code and every UniProt position with its accession, so the reference is determined "
              "by the request. No task uses 1HSG (the API prompt's worked example).",
              "- The reference holds only what the request states (a bare load already draws the structure).",
              "- Each selection is checked against a second statement of its atoms (`provenance.targets`), "
              "the reference grades itself as exactly right, a bare load scores 0, and the equivalent and "
              "wrong answers listed in `provenance.checks` succeed and fail as they should.",
              "- `provenance.difficulty` records what makes the task hard: `numbering_offset` (author number "
              "differs from label number), `auth_label_chain`, `uniprot_mapping`, `ligand_identity_needed` "
              "(always false: codes are in the request), `hinges_on` (a viewer rule the task turns on), "
              "`order_matters`, `setting_only` (options compared as declared settings).",
              "- Colours are from `molbench.drawn.TASK_PALETTE`.", ""]
    if directory == "api_generated":
        hinge = Counter(x for t in all_tasks for x in t["provenance"]["difficulty"].get("hinges_on", []))
        lines += ["## Held-back split", "",
                  f"Held-back structures ({len(info['held'])}): {' '.join(info['held'])}. Rule: of the panel "
                  "entries that no task used before this corpus, ranked by SHA-256 of "
                  "`molbench-heldback-v1|<id>`, the first fifth of the panel, 8CE0 (held back by the fixture "
                  "tasks) always among them; `data/panel/heldback.json` "
                  "overrides it. No public task of this script uses one of them.", "",
                  "| tier | structures | held-back structures | tasks | held-back tasks |", "|---|---:|---:|---:|---:|"]
        for tier in sorted(tiers):
            mine = [t for t in all_tasks if t["tier"] == tier]
            st = {s for t in mine for s in t["structures"]}
            hs = {s for t in mine if t["split"] == "heldback" for s in t["structures"]}
            lines.append(f"| {tier} | {len(st)} | {len(hs)} ({100 * len(hs) / len(st):.0f}%) | {len(mine)} | "
                         f"{sum(t['split'] == 'heldback' for t in mine)} |")
        lines += ["", "## Viewer rules that tasks turn on", "",
                  f"Of the {len(all_tasks)} API tasks in both directories: "
                  + "; ".join(f"`{k}` {n} ({100 * n / len(all_tasks):.0f}%)" for k, n in sorted(hinge.items()))
                  + ".", "",
                  "## Viewer surface exercised (references of both directories)", "",
                  coverage_table(all_tasks), ""]
        if info["skipped"]:
            lines += ["## Structures a template skipped", ""]
            for family, why in sorted(info["skipped"].items()):
                lines.append(f"- `{family}`: {len(why)} skipped (a check failed, e.g. a water shares the "
                             "author numbers of the range)")
            lines.append("")
    return "\n".join(lines)


def files(cur: list[dict], gen: list[dict], info: dict) -> dict[pathlib.Path, str]:
    out: dict[pathlib.Path, str] = {}
    for t in cur:
        name = t.pop("_file")
        out[OUT_CURATED / name] = json.dumps(t, indent=2, ensure_ascii=False) + "\n"
    for t in gen:
        out[OUT_GENERATED / f"{t['id']}.json"] = json.dumps(t, indent=2, ensure_ascii=False) + "\n"
    out[OUT_GENERATED / "README.md"] = readme("api_generated", gen, info, cur + gen)
    out[OUT_CURATED / "README.md"] = readme("api_calling", cur, info, cur + gen)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="write nothing; fail if a file would change")
    ap.add_argument("--report", action="store_true", help="print counts, skips and the coverage table")
    a = ap.parse_args(argv)
    cur, gen, info = build_all()
    ids = [t["id"] for t in cur + gen]
    assert len(ids) == len(set(ids)), [i for i, n in Counter(ids).items() if n > 1]
    if a.report:
        for (tier, family), n in sorted(Counter((t["tier"], t["family"]) for t in cur + gen).items()):
            print(f"{tier:12} {family:26} {n}")
        for family, why in sorted(info["skipped"].items()):
            print(f"skipped {family}: " + " | ".join(why)[:600])
        print(coverage_table(cur + gen))
    wanted = files(cur, gen, info)
    existing = {p for d in (OUT_CURATED, OUT_GENERATED) if d.is_dir() for p in d.iterdir()
                if p.suffix in (".json", ".md")}
    changed = [p for p, text in wanted.items() if not p.exists() or p.read_text() != text]
    stale = sorted(existing - set(wanted))
    if a.check:
        for p in changed + stale:
            print(f"would change: {p.relative_to(REPO)}")
        print(f"{len(wanted)} files, {len(changed)} would change, {len(stale)} stale")
        return 1 if changed or stale else 0
    for d in (OUT_CURATED, OUT_GENERATED):
        d.mkdir(parents=True, exist_ok=True)
    for p in stale:
        p.unlink()
    for p, text in wanted.items():
        p.write_text(text)
    print(f"wrote {len(cur)} curated and {len(gen)} generated tasks "
          f"({len(changed)} files changed, {len(stale)} removed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
