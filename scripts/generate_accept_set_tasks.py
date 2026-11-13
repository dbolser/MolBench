#!/usr/bin/env python3
"""
Generate the accept-set tier (FINAL_PLAN decision 7, issue #4): under-specified
requests where several final states are all right, and the set of right states is
ENUMERATED BY SCRIPT from the frozen panel.

    uv run python scripts/generate_accept_set_tasks.py           # rewrite the files
    uv run python scripts/generate_accept_set_tasks.py --check   # fail if they would change
    uv run python scripts/generate_accept_set_tasks.py --heldback-file ids.json

Writes ``tasks/mvs_accept/`` and ``tasks/api_accept/`` (one JSON file per task, plus a
generated ``README.md`` in each). No network; inputs are ``data/panel/facts`` and the
frozen atom tables. Deterministic: every choice (structure, residue, colour, wording)
is a SHA-256 ranking under ``SEED``, so a re-run reproduces the files byte for byte.

What "under-specified" means here. Each template leaves exactly ONE thing open, and
the things it could be are countable in the deposited structure:

* which copy     - "the heme" in an entry with four hemes; "Asp25" in a homodimer
* which one      - "the ligand" in an entry with two different ligands; "the metal ion"
* which is which - "colour the two chains red and blue" (who gets red?)
* which drawing  - "show the retinoic acid in red" (no representation named)

The accept rule is fixed per template (``RULES``) and written into every task's
provenance together with what is NOT accepted and why. Requests that are vague in a
way a script cannot enumerate ("clean up the view", "focus on the important parts")
are out of this tier; the README lists which of the seven issue-#4 seeds were dropped.

Every accepted state is checked twice before a file is written: (1) the atoms it
draws, read back from the grader's own resolver (``mvs.resolve_scene`` /
``pdbe_state.replay``), must equal the atoms computed here straight from the atom
table columns; (2) the corpus checks of ``molbench.tasks.check_corpus`` (the reference
grades itself as exactly right, every alternative is accepted and is a different final
state, targets select atoms, twins select the same atoms).
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import itertools
import json
import pathlib
import re
import sys
from collections import Counter

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import drawn, grounding, mvs, pdbe_state, runner, tasks as T  # noqa: E402
from molbench.atoms import load_table  # noqa: E402

SCRIPT = "scripts/generate_accept_set_tasks.py"
SEED = "molbench-accept-set-v1"
DATE = "2026-11-13"            # fixed, so a rebuild is byte-identical
OUT = {"mvs": REPO / "tasks" / "mvs_accept", "api": REPO / "tasks" / "api_accept"}

# Held-back structures (decision 21). The validator refuses a structure that is public
# in one task and held back in another ANYWHERE in the corpus, so the rule cannot depend
# on the tier: it is a fixed fifth of the panel, by hash of the entry id. Any generator
# can call `heldback_structures()`; `--heldback-file` replaces it with a shared list.
HELDBACK_SEED = "molbench-heldback-v1"
HELDBACK_SHARE = 0.2

MAX_ATOMS = 15000              # the panel's own size rule (two older entries exceed it)
MAX_PER_STRUCTURE = 6          # tasks of this tier on one structure, both tracks counted
MAX_COPIES = 4                 # more copies than this is no longer "which one?"
HIGHLIGHTS = ("red", "orange", "yellow", "green", "blue", "purple", "magenta", "cyan")
OPEN_REPRESENTATIONS = ("ball_and_stick", "spacefill", "line", "surface")
API_REP = {"ball_and_stick": "ball-and-stick", "cartoon": "cartoon"}
NUMBER = {2: "two", 3: "three", 4: "four"}
METAL = {"ZN": "zinc", "MG": "magnesium", "MN": "manganese", "K": "potassium",
         "CA": "calcium", "FE": "iron", "CU": "copper", "NA": "sodium", "HG": "mercury",
         "NI": "nickel", "CO": "cobalt", "CD": "cadmium"}
assert set(HIGHLIGHTS) <= set(drawn.TASK_PALETTE)


# --------------------------------------------------------------------------- #
# Seeded choice
# --------------------------------------------------------------------------- #
def rank(*key) -> str:
    return hashlib.sha256("|".join([SEED, *map(str, key)]).encode()).hexdigest()


def pick(options: list, *key):
    """One of ``options``, chosen by the seed and ``key`` (independent of list order
    only if the options are listed in a fixed order, which they always are here)."""
    return options[int(rank(*key), 16) % len(options)]


def heldback_structures(share: float = HELDBACK_SHARE) -> set[str]:
    """The held-back fifth of the panel: the PDB entries (the API prompt's worked
    example excluded) with the lowest SHA-256 of ``"molbench-heldback-v1:<id>"``."""
    ids = sorted(e["id"] for e in grounding.panel()["entries"]
                 if e["kind"] == "pdb" and e["id"] != T.WORKED_EXAMPLE)
    ids.sort(key=lambda i: hashlib.sha256(f"{HELDBACK_SEED}:{i}".encode()).hexdigest())
    return set(ids[:round(share * len(ids))])


# --------------------------------------------------------------------------- #
# Reading the panel
# --------------------------------------------------------------------------- #
class Entry:
    def __init__(self, record: dict):
        self.id: str = record["id"]
        self.features: list[str] = record["features"]
        self.facts: dict = grounding.facts(self.id)
        self.table = load_table(self.id)
        self.chains: list[dict] = self.facts["chains"]            # polymer chains
        self.ligands: list[dict] = self.facts["ligands"]

    def rows(self, **eq) -> int:
        """Atoms whose columns equal ``eq``, straight from the table columns (the
        column index, not the selector code the grader resolves answers with)."""
        mask = (1 << self.table.n) - 1
        for column, value in eq.items():
            mask &= self.table.index(column).get(value, 0)
        return mask

    def polymer_word(self) -> str:
        kinds = []
        for c in self.chains:
            if c["polymer_type"] not in kinds:
                kinds.append(c["polymer_type"])
        order = [k for k in ("protein", "DNA", "RNA") if k in kinds]
        assert order and len(order) == len(kinds), (self.id, kinds)
        return " and ".join(order)

    def copy_mask(self, copy: dict) -> int:
        return self.rows(label_asym_id=copy["label_asym_id"], auth_seq_id=copy["auth_seq_id"],
                         label_comp_id=copy["comp_id"])

    def difficulty(self, chains: list[dict] = (), residues: list[dict] = (),
                   ligand_identity: bool = False) -> dict:
        """The facts the paper analyses difficulty by, for the atoms asked about."""
        return {
            "needs_numbering_offset": any(r["auth_seq_id"] != r["label_seq_id"] for r in residues),
            "author_chain_differs_from_label_chain":
                any(c["auth_asym_id"] != c["label_asym_id"] for c in chains),
            "needs_ligand_identity": ligand_identity,
            "needs_uniprot_mapping": False,
        }


def entries() -> list[Entry]:
    out = []
    for e in grounding.panel()["entries"]:
        if e["kind"] != "pdb" or e["id"] == T.WORKED_EXAMPLE or e["atoms"] > MAX_ATOMS:
            continue
        if grounding.facts(e["id"])["n_models"] != 1 or load_table(e["id"]) is None:
            continue
        out.append(Entry(e))
    return sorted(out, key=lambda x: x.id)


def ligand_phrase(lig: dict) -> str:
    """How a person would name the component: "heme", "retinal (RET)", "ligand STI"."""
    if lig["heme"]:
        return "heme"
    name = lig["name"].strip()
    if len(name) <= 24 and re.fullmatch(r"[A-Za-z0-9 -]+", name):
        return f"{name.lower()} ({lig['comp_id']})"
    return f"ligand {lig['comp_id']}"


def real_ligands(e: Entry) -> list[dict]:
    return [x for x in e.ligands if x["kind"] == "ligand"]


def metal_ions(e: Entry) -> list[dict]:
    return [x for x in e.ligands if x["kind"] == "ion" and x["metals"]]


def copy_selector(copy: dict) -> dict:
    return {"label_asym_id": copy["label_asym_id"], "auth_seq_id": copy["auth_seq_id"]}


def copy_api(copy: dict) -> dict:
    return {"struct_asym_id": copy["label_asym_id"], "label_comp_id": copy["comp_id"]}


def copy_label(copy: dict) -> str:
    return f"{copy['comp_id']} {copy['auth_asym_id']}:{copy['auth_seq_id']}"


# --------------------------------------------------------------------------- #
# States. A state is a list of parts; a part is some atoms drawn one way.
# --------------------------------------------------------------------------- #
def part(selector, api: list[dict] | None, rep: str, color: str, mask: int) -> dict:
    """``selector``: MVS selector (an expression, a list of them, or a static name).
    ``api``: the same atoms as pdbe-molstar selection params (None: MVS only).
    ``mask``: the atoms, computed from the table columns, for the read-back check."""
    return {"selector": selector, "api": api, "rep": rep, "color": color, "mask": mask}


def one_or_all(labels: list[str]) -> list[tuple[str, list[int]]]:
    """The accept rule "any one copy, or every copy": index lists into the copies."""
    out = [(labels[i], [i]) for i in range(len(labels))]
    out.append(("all " + str(len(labels)) + " copies" if len(labels) > 2 else "both copies",
                list(range(len(labels)))))
    return out


def subsets(labels: list[str]) -> list[tuple[str, list[int]]]:
    """Every non-empty subset (used only for two candidates: either, or both)."""
    out = []
    for n in range(1, len(labels) + 1):
        for combo in itertools.combinations(range(len(labels)), n):
            out.append((" + ".join(labels[i] for i in combo), list(combo)))
    return out


def merged(sels: list[dict]):
    return sels[0] if len(sels) == 1 else sels


def highlight_states(e: Entry, items: list[tuple[str, dict, list[dict] | None, int]],
                     groups, rep: str, color: str) -> list[dict]:
    """One state per group of items; each state draws the group's atoms as one part.
    ``items``: (label, MVS expression, API params, mask)."""
    out = []
    for label, idx in groups:
        api = None if any(items[i][2] is None for i in idx) else \
            [p for i in idx for p in items[i][2]]
        mask = 0
        for i in idx:
            mask |= items[i][3]
        out.append({"label": label,
                    "parts": [part(merged([items[i][1] for i in idx]), api, rep, color, mask)]})
    return out


# --------------------------------------------------------------------------- #
# Templates. Each yields candidate specs: one per structure it applies to.
# --------------------------------------------------------------------------- #
RULES = {
    "acc-chain-colours": (
        "The request gives one colour per chain but not which chain gets which. "
        "Accepted: every one-to-one assignment of the named colours to the polymer chains "
        "(n! states), on a cartoon of the whole polymer.",
        ["a colour used on two chains, or a chain left uncoloured: the request names one "
         "colour per chain",
         "other colours, or a colour-by-chain theme with the viewer's own colours: the "
         "request names the colours",
         "ligands, ions or water drawn or coloured: not requested"]),
    "acc-ligand-which": (
        "The entry has exactly two different ligands, one copy each, and the request says "
        "\"the ligand\". Accepted: either ligand alone, or both. On the MVS track also the "
        "viewer's own built-in 'ligand' selection when it is not the same atoms (Mol* adds "
        "residues covalently bonded to a ligand), because an answer that uses the viewer's "
        "word for exactly what was asked is not wrong.",
        ["ions, water or buffer components shown as the ligand: not ligands of the entry "
         "(data/panel facts: kind 'ion')",
         "part of a ligand, or protein residues around it (other than through the viewer's "
         "built-in selection): not requested",
         "another representation or colour: both are stated"]),
    "acc-ligand-copy": (
        "The request names one ligand; the entry holds several copies of it. Accepted: any "
        "one copy, or every copy. Not an arbitrary several-but-not-all: no reading of the "
        "request picks, say, two of four.",
        ["some but not all copies (when there are more than two): no reading of the request",
         "other components, or the residues bonded to the ligand: not requested",
         "another representation or colour: both are stated"]),
    "acc-metal-copy": (
        "The request asks for \"the <metal> ion\"; the entry holds several ions of that "
        "metal and no other metal. Accepted: any one of them, or all of them.",
        ["some but not all ions (when there are more than two): no reading of the request",
         "the residues that bind the metal: not requested",
         "another representation or colour: both are stated"]),
    "acc-metal-which": (
        "The request asks for \"the metal ion\"; the entry holds exactly two metal ions, of "
        "different elements, and no metal inside a ligand. Accepted: either ion, or both.",
        ["a non-metal ion or a ligand: not a metal ion",
         "the residues that bind the metal: not requested",
         "another representation or colour: both are stated"]),
    "acc-residue-copy": (
        "The request names a residue by type and author number but no chain; the protein "
        "is present as several identical chains, each with that residue. Accepted: the "
        "residue in any one chain, or in every chain.",
        ["some but not all chains (when there are more than two): no reading of the request",
         "a residue with that number in another protein of the entry, or the residue with "
         "that label (sequence) number where it differs: a different residue",
         "another representation or colour: both are stated"]),
    "acc-residue-colour": (
        "The request asks to colour a residue, named by type and author number but with no "
        "chain; the protein is present as several identical chains. Accepted: the residue "
        "coloured in any one chain, or in every chain.",
        ["some but not all chains (when there are more than two): no reading of the request",
         "a residue with that number in another protein of the entry, or the residue with "
         "that label (sequence) number where it differs: a different residue",
         "an added representation (sticks) for the residue: only a colour is requested"]),
    "acc-representation-open": (
        "The request asks to show a ligand in a stated colour and names no representation. "
        "Accepted: each MVS representation type that draws every atom of the ligand "
        "(GRADING.md, 'A representation draws atoms of its component'): ball_and_stick, "
        "spacefill, line, surface. A cartoon, backbone or putty asked for on a ligand is "
        "drawn by the viewer as ball-and-stick and so is graded as that state.",
        ["two representations at once on the ligand: the request asks for one drawing",
         "another colour: it is stated",
         "the residues around the ligand: not requested"]),
    "acc-ligand-colours": (
        "The entry has exactly two different ligands, one copy each; the request gives two "
        "colours, \"one ... and the other ...\". Accepted: both assignments.",
        ["both ligands the same colour, or only one ligand shown: the request asks for both, "
         "in different colours",
         "ions, water or bonded protein residues shown as ligands: not ligands of the entry",
         "another representation: it is stated"]),
}

WORDINGS = {
    "acc-chain-colours": [
        "Load {ID} and show it as a cartoon, with the {n} chains coloured {colours}.",
        "Show {ID} as a cartoon. Colour its {n} chains {colours}.",
        "Open {ID} in cartoon representation and colour the {n} chains {colours}.",
    ],
    "acc-ligand-which": [
        "Load {ID}. Show the {poly} as a cartoon and the ligand as {colour} ball-and-stick.",
        "Open {ID} with the {poly} as a cartoon and the ligand in {colour} ball-and-stick.",
        "Show {ID} with the {poly} as a cartoon and the bound ligand as ball-and-stick, "
        "coloured {colour}.",
    ],
    "acc-ligand-copy": [
        "Load {ID}. Show the {poly} as a cartoon and the {thing} as {colour} ball-and-stick.",
        "Open {ID} with the {poly} as a cartoon and the {thing} in {colour} ball-and-stick.",
        "Show {ID} with the {poly} as a cartoon and the {thing} as ball-and-stick, "
        "coloured {colour}.",
    ],
    "acc-metal-copy": [
        "Load {ID}. Show the {poly} as a cartoon and the {thing} ion as {colour} spacefill.",
        "Open {ID} with the {poly} as a cartoon and the {thing} ion in {colour} spacefill.",
        "Show {ID} with the {poly} as a cartoon and the {thing} ion as a spacefill sphere, "
        "coloured {colour}.",
    ],
    "acc-metal-which": [
        "Load {ID}. Show the {poly} as a cartoon and the metal ion as {colour} spacefill.",
        "Open {ID} with the {poly} as a cartoon and the metal ion in {colour} spacefill.",
        "Show {ID} with the {poly} as a cartoon and the metal ion as a spacefill sphere, "
        "coloured {colour}.",
    ],
    "acc-residue-copy": [
        "Load {ID}. Show the {poly} as a cartoon and {thing} as {colour} ball-and-stick.",
        "Open {ID} with the {poly} as a cartoon and {thing} in {colour} ball-and-stick.",
        "Show {ID} with the {poly} as a cartoon and {thing} as ball-and-stick, "
        "coloured {colour}.",
    ],
    "acc-residue-colour": [
        "Load {ID}, show the {poly} as a cartoon and colour {thing} {colour}.",
        "Show {ID} with the {poly} as a cartoon. Colour {thing} {colour}.",
        "Open {ID} with the {poly} as a cartoon, with {thing} coloured {colour}.",
    ],
    "acc-representation-open": [
        "Load {ID}. Draw the {poly} as a cartoon and show the {thing} in {colour}.",
        "Open {ID} with the {poly} as a cartoon, and show the {thing} in {colour}.",
        "Show {ID} with the {poly} as a cartoon and the {thing} shown in {colour}.",
    ],
    "acc-ligand-colours": [
        "Load {ID}. Show the {poly} as a cartoon and the two ligands as ball-and-stick, one "
        "{colour} and the other {colour2}.",
        "Open {ID} with the {poly} as a cartoon and its two ligands in ball-and-stick, one "
        "{colour} and the other {colour2}.",
        "Show {ID} with the {poly} as a cartoon and the two ligands as ball-and-stick: one "
        "{colour}, the other {colour2}.",
    ],
}

# What each template leaves open (README, provenance) and which issue-#4 seed it answers.
OPEN = {
    "acc-chain-colours": "which chain gets which colour",
    "acc-ligand-which": "which of two different ligands (or both)",
    "acc-ligand-copy": "which copy of the named ligand (or all)",
    "acc-metal-copy": "which of several ions of the named metal (or all)",
    "acc-metal-which": "which of two different metal ions (or both)",
    "acc-residue-copy": "which chain's copy of the named residue (or all)",
    "acc-residue-colour": "which chain's copy of the named residue (or all)",
    "acc-representation-open": "which representation",
    "acc-ligand-colours": "which ligand gets which colour",
}
SKILLS = {
    "acc-chain-colours": ["load", "representation", "selection", "color"],
    "acc-residue-colour": ["load", "representation", "selection", "color"],
}
DEFAULT_SKILLS = ["load", "representation", "selection", "color"]

# (template, MVS tasks, also an API twin?)  Order is the order structures are handed out.
PLAN = [
    ("acc-ligand-which", 3, True),
    ("acc-ligand-colours", 2, True),
    ("acc-metal-which", 2, False),
    ("acc-chain-colours", 4, True),
    ("acc-ligand-copy", 4, True),
    ("acc-metal-copy", 3, False),
    ("acc-residue-copy", 3, False),
    ("acc-residue-colour", 3, True),
    ("acc-representation-open", 3, False),
]


def colours(n: int, *key) -> list[str]:
    order = sorted(HIGHLIGHTS, key=lambda c: rank("colour", *key, c))
    return order[:n]


def two_ligands(e: Entry) -> list[dict] | None:
    """The two ligands of an entry that has exactly two, one copy each. Membrane-protein
    entries are left out: their non-polymer components are lipids and detergents, which
    nobody calls "the ligand"."""
    ligs = real_ligands(e)
    if "membrane" in e.features:
        return None
    if len(ligs) != 2 or any(len(x["copies"]) != 1 or x["n_heavy_atoms"] < 8 for x in ligs):
        return None
    return ligs


def spec_chain_colours(e: Entry) -> dict | None:
    chains = e.chains
    if len(chains) not in (2, 3):
        return None
    cols = colours(len(chains), "acc-chain-colours", e.id)
    masks = [e.rows(label_asym_id=c["label_asym_id"]) & e.table.static["polymer"] for c in chains]
    states = []
    for perm in itertools.permutations(range(len(chains))):
        parts = [part({"label_asym_id": c["label_asym_id"]},
                      [{"struct_asym_id": c["label_asym_id"]}], "cartoon", cols[perm[i]],
                      masks[i]) for i, c in enumerate(chains)]
        states.append({"label": ", ".join(f"chain {c['auth_asym_id']} {cols[perm[i]]}"
                                          for i, c in enumerate(chains)), "parts": parts})
    return {"states": states, "candidates": [f"chain {c['auth_asym_id']}" for c in chains],
            "slots": {"n": NUMBER[len(chains)],
                      "colours": ", ".join(cols[:-1]) + " and " + cols[-1]},
            "facts": e.difficulty(chains=chains)}


def spec_ligand_which(e: Entry) -> dict | None:
    ligs = two_ligands(e)
    if ligs is None:
        return None
    colour = colours(1, "acc-ligand-which", e.id)[0]
    items = [(x["comp_id"], copy_selector(x["copies"][0]), [copy_api(x["copies"][0])],
              e.copy_mask(x["copies"][0])) for x in ligs]
    states = highlight_states(e, items, subsets([x["comp_id"] for x in ligs]),
                              "ball_and_stick", colour)
    both = items[0][3] | items[1][3]
    viewer = e.table.static["ligand"]
    extra = []
    if viewer != both and viewer & both == both:
        # MVS only: the viewer's own "ligand" (the two ligands plus what Mol* adds).
        extra.append({"label": "the viewer's built-in 'ligand' selection", "mvs_only": True,
                      "parts": [part("ligand", None, "ball_and_stick", colour, viewer)]})
    return {"states": states + extra, "candidates": [x["comp_id"] for x in ligs],
            "slots": {"colour": colour},
            "facts": e.difficulty(ligand_identity=True)}


def spec_ligand_colours(e: Entry) -> dict | None:
    ligs = two_ligands(e)
    if ligs is None:
        return None
    cols = colours(2, "acc-ligand-colours", e.id)
    states = []
    for a, b in ((0, 1), (1, 0)):
        parts = [part(copy_selector(x["copies"][0]), [copy_api(x["copies"][0])],
                      "ball_and_stick", cols[i], e.copy_mask(x["copies"][0]))
                 for x, i in zip(ligs, (a, b))]
        states.append({"label": ", ".join(f"{x['comp_id']} {cols[i]}"
                                          for x, i in zip(ligs, (a, b))), "parts": parts})
    return {"states": states, "candidates": [x["comp_id"] for x in ligs],
            "slots": {"colour": cols[0], "colour2": cols[1]},
            "facts": e.difficulty(ligand_identity=True)}


def spec_ligand_copy(e: Entry) -> dict | None:
    options = [x for x in real_ligands(e)
               if 2 <= len(x["copies"]) <= MAX_COPIES and x["n_heavy_atoms"] >= 8]
    if not options:
        return None
    lig = pick(options, "acc-ligand-copy", e.id, "ligand")
    colour = colours(1, "acc-ligand-copy", e.id)[0]
    items = [(copy_label(c), copy_selector(c), [copy_api(c)], e.copy_mask(c))
             for c in lig["copies"]]
    return {"states": highlight_states(e, items, one_or_all([i[0] for i in items]),
                                       "ball_and_stick", colour),
            "candidates": [i[0] for i in items],
            "slots": {"thing": ligand_phrase(lig), "colour": colour},
            "facts": e.difficulty(ligand_identity=lig["comp_id"] not in ligand_phrase(lig))}


def spec_metal_copy(e: Entry) -> dict | None:
    metals = metal_ions(e)
    if (len(metals) != 1 or not 2 <= len(metals[0]["copies"]) <= MAX_COPIES
            or metals[0]["comp_id"] not in METAL or any(x["metals"] for x in real_ligands(e))):
        return None
    ion = metals[0]
    colour = colours(1, "acc-metal-copy", e.id)[0]
    items = [(copy_label(c), copy_selector(c), None, e.copy_mask(c)) for c in ion["copies"]]
    return {"states": highlight_states(e, items, one_or_all([i[0] for i in items]),
                                       "spacefill", colour),
            "candidates": [i[0] for i in items],
            "slots": {"thing": METAL[ion["comp_id"]], "colour": colour},
            "facts": e.difficulty(ligand_identity=True)}


def spec_metal_which(e: Entry) -> dict | None:
    metals = metal_ions(e)
    if (len(metals) != 2 or any(len(x["copies"]) != 1 for x in metals)
            or any(x["metals"] for x in real_ligands(e))):
        return None
    union = 0
    for x in metals:
        union |= e.copy_mask(x["copies"][0])
    if union != e.table.static["ion"]:       # another (non-metal) ion would blur "the ion"
        return None
    colour = colours(1, "acc-metal-which", e.id)[0]
    items = [(x["comp_id"], copy_selector(x["copies"][0]), None, e.copy_mask(x["copies"][0]))
             for x in metals]
    return {"states": highlight_states(e, items, subsets([x["comp_id"] for x in metals]),
                                       "spacefill", colour),
            "candidates": [x["comp_id"] for x in metals],
            "slots": {"colour": colour},
            "facts": e.difficulty(ligand_identity=True)}


def shared_residues(e: Entry, chains: list[dict]) -> list[tuple[int, str, list[dict]]]:
    """Residues (author number, name) present under the same author number and name in
    every one of ``chains`` and in no other polymer chain, with no insertion code, and
    selected exactly by author chain + author number. Glycine is left out (no side
    chain to show)."""
    cols = e.table.columns
    per_chain: dict[str, dict[int, dict]] = {}
    polymer = e.table.static["polymer"]
    for i in range(e.table.n):
        if not polymer >> i & 1:
            continue
        key = cols["label_asym_id"][i]
        res = per_chain.setdefault(key, {})
        num = cols["auth_seq_id"][i]
        if cols["pdbx_PDB_ins_code"][i]:
            res[num] = None                                   # insertion code: unusable
        elif num not in res:
            res[num] = {"comp": cols["label_comp_id"][i], "label_seq_id": cols["label_seq_id"][i]}
        elif res[num] is not None and res[num]["comp"] != cols["label_comp_id"][i]:
            res[num] = None                                   # microheterogeneity
    mine = [c["label_asym_id"] for c in chains]
    others = [k for k in per_chain if k not in mine]
    out = []
    for num, first in sorted(per_chain.get(mine[0], {}).items()):
        if first is None or first["comp"] == "GLY":
            continue
        found = [per_chain.get(k, {}).get(num) for k in mine]
        if any(f is None or f["comp"] != first["comp"] for f in found):
            continue
        if any((per_chain[k].get(num) or {}).get("comp") == first["comp"] for k in others):
            continue
        residues = []
        for c, f in zip(chains, found):
            mask = e.rows(label_asym_id=c["label_asym_id"], auth_seq_id=num,
                          label_comp_id=first["comp"])
            by_author = e.rows(auth_asym_id=c["auth_asym_id"], auth_seq_id=num)
            if mask != by_author:      # a ligand or water with that number in the author chain
                break
            residues.append({"auth_asym_id": c["auth_asym_id"], "auth_seq_id": num,
                             "label_asym_id": c["label_asym_id"],
                             "label_seq_id": f["label_seq_id"], "comp_id": first["comp"],
                             "mask": mask})
        else:
            out.append((num, first["comp"], residues))
    return out


def residue_spec(e: Entry, template: str, rep: str) -> dict | None:
    groups = []
    for ent in e.facts["entities"]:
        if ent.get("polymer_type") != "protein" or not 2 <= len(ent["label_asym_ids"]) <= 3:
            continue
        chains = [c for c in e.chains if c["label_asym_id"] in ent["label_asym_ids"]]
        shared = shared_residues(e, chains)
        if shared:
            groups.append((chains, shared))
    if not groups:
        return None
    chains, shared = pick(groups, template, e.id, "entity")
    num, comp, residues = pick(shared, template, e.id, "residue")
    colour = colours(1, template, e.id)[0]
    items = [(f"{comp} {r['auth_asym_id']}:{num}",
              {"auth_asym_id": r["auth_asym_id"], "auth_seq_id": num},
              [{"auth_asym_id": r["auth_asym_id"], "auth_residue_number": num}], r["mask"])
             for r in residues]
    return {"states": highlight_states(e, items, one_or_all([i[0] for i in items]), rep, colour),
            "candidates": [i[0] for i in items],
            "slots": {"thing": f"{comp.capitalize()}{num}", "colour": colour},
            "residues": [{k: v for k, v in r.items() if k != "mask"} for r in residues],
            "facts": e.difficulty(chains=chains, residues=residues)}


def spec_residue_copy(e: Entry) -> dict | None:
    return residue_spec(e, "acc-residue-copy", "ball_and_stick")


def spec_residue_colour(e: Entry) -> dict | None:
    return residue_spec(e, "acc-residue-colour", "cartoon")


def spec_representation_open(e: Entry) -> dict | None:
    ligs = real_ligands(e)
    if len(ligs) != 1 or len(ligs[0]["copies"]) != 1 or ligs[0]["n_heavy_atoms"] < 8:
        return None
    lig, copy = ligs[0], ligs[0]["copies"][0]
    colour = colours(1, "acc-representation-open", e.id)[0]
    mask = e.copy_mask(copy)
    states = [{"label": rep, "parts": [part(copy_selector(copy), None, rep, colour, mask)]}
              for rep in OPEN_REPRESENTATIONS]
    return {"states": states, "candidates": list(OPEN_REPRESENTATIONS),
            "slots": {"thing": ligand_phrase(lig), "colour": colour},
            "facts": e.difficulty(ligand_identity=lig["comp_id"] not in ligand_phrase(lig))}


SPEC = {
    "acc-chain-colours": spec_chain_colours, "acc-ligand-which": spec_ligand_which,
    "acc-ligand-colours": spec_ligand_colours, "acc-ligand-copy": spec_ligand_copy,
    "acc-metal-copy": spec_metal_copy, "acc-metal-which": spec_metal_which,
    "acc-residue-copy": spec_residue_copy, "acc-residue-colour": spec_residue_colour,
    "acc-representation-open": spec_representation_open,
}


# --------------------------------------------------------------------------- #
# From a state to a scene, a call list and a target
# --------------------------------------------------------------------------- #
def mvs_scene(entry: str, state: dict) -> dict:
    cartoon = {"kind": "representation", "params": {"type": "cartoon"}}
    paints = [{"kind": "color", "params": {"color": p["color"], "selector": p["selector"]}}
              for p in state["parts"] if p["rep"] == "cartoon"]
    if paints:
        cartoon["children"] = paints
    components = [{"kind": "component", "params": {"selector": "polymer"}, "children": [cartoon]}]
    for p in state["parts"]:
        if p["rep"] != "cartoon":
            components.append({"kind": "component", "params": {"selector": p["selector"]},
                               "children": [{"kind": "representation", "params": {"type": p["rep"]},
                                             "children": [{"kind": "color",
                                                           "params": {"color": p["color"]}}]}]})
    return {"root": {"kind": "root", "children": [
        {"kind": "download", "params": {"url": f"https://files.rcsb.org/download/{entry}.cif"},
         "children": [{"kind": "parse", "params": {"format": "mmcif"}, "children": [
             {"kind": "structure", "params": {"type": "model"}, "children": components}]}]}]}}


def api_calls(entry: str, state: dict) -> list[dict]:
    """A bare load already draws the polymer as a cartoon and ligands as ball-and-stick,
    so the requested state is one ``color`` call."""
    data = [{**loc, "color": p["color"]} for p in state["parts"] for loc in p["api"]]
    return [{"action": "load", "molecule_id": entry}, {"action": "color", "data": data}]


def target(track: str, state: dict) -> list[dict]:
    return [{"selector": p["selector"],
             "representation": p["rep"] if track == "mvs" else API_REP[p["rep"]],
             "color": p["color"]} for p in state["parts"]]


@functools.lru_cache(maxsize=None)
def plain_cartoon(entry: str) -> int:
    """The atoms a cartoon of the whole polymer draws (residues with a trace atom)."""
    out = 0
    scene = mvs.resolve_scene(mvs_scene(entry, {"parts": []}))
    for (rep, _, _), m in scene.structures[entry].draws.items():
        if rep == "cartoon":
            out |= m
    return out


def read_back(track: str, entry: str, state: dict, answer) -> str | None:
    """Compare what the grader's resolver says ``answer`` draws with the atoms computed
    from the table columns. None = they agree."""
    table = load_table(entry)
    for p in state["parts"]:
        rgb = drawn.mvs_color(p["color"]) if track == "mvs" else pdbe_state.normalize_color(p["color"])
        if track == "mvs":
            draws = mvs.resolve_scene(answer).structures[entry].draws
            got = draws.get((p["rep"], rgb, 1.0), draws.get((p["rep"], rgb, 1), 0))
        else:
            got = pdbe_state.changes(pdbe_state.replay(answer)).get((API_REP[p["rep"]], rgb), 0)
        want = p["mask"]
        if p["rep"] == "cartoon":
            # A ribbon is drawn for the residues whose trace atom is in the selection; a
            # whole chain is selected here, or a whole residue, so compare as residues.
            got, want = pdbe_state.residues_of(table, got), pdbe_state.residues_of(table, want)
            want &= pdbe_state.residues_of(table, table.static["polymer"])
            want &= pdbe_state.residues_of(table, plain_cartoon(entry))
        if got != want or not want:
            return (f"{state['label']}: {p['rep']} {p['color']} is drawn on "
                    f"{bin(got).count('1')} atoms, expected {bin(want).count('1')}")
    return None


# --------------------------------------------------------------------------- #
# Choosing structures and building tasks
# --------------------------------------------------------------------------- #
def choose(template: str, cands: list[tuple[Entry, dict]], n: int, twin: bool,
           used: Counter, held: set[str]) -> list[tuple[Entry, dict]]:
    """``n`` candidates: about a fifth from held-back structures, the rest public; the
    least-used structures first, then by seed. A structure at the tier cap is skipped."""
    cost = 2 if twin else 1
    ok = [c for c in cands if used[c[0].id] + cost <= MAX_PER_STRUCTURE]
    ok.sort(key=lambda c: (used[c[0].id], rank("structure", template, c[0].id)))
    back = [c for c in ok if c[0].id in held]
    public = [c for c in ok if c[0].id not in held]
    n_back = min(len(back), round(HELDBACK_SHARE * n + 1e-9))
    chosen = back[:n_back] + public[:n - n_back]
    chosen += back[n_back:n_back + n - len(chosen)]
    for e, _ in chosen:
        used[e.id] += cost
    return sorted(chosen, key=lambda c: c[0].id)


def make_task(track: str, template: str, e: Entry, spec: dict, split: str, prompt: str,
              wording: int) -> dict:
    states = [s for s in spec["states"] if track == "mvs" or not s.get("mvs_only")]
    build = (lambda s: mvs_scene(e.id, s)) if track == "mvs" else (lambda s: api_calls(e.id, s))
    answers = [build(s) for s in states]
    for s, a in zip(states, answers):
        problem = read_back(track, e.id, s, a)
        if problem:
            raise SystemExit(f"{template} {e.id} {track}: {problem}")
    rule, not_accepted = RULES[template]
    # The slots the full wordings of this template use (plus the id in lower case, for
    # terse paraphrases): scripts/generate_paraphrases.py fills its wordings from them.
    wanted = {k for w in WORDINGS[template] for k in re.findall(r"{(\w+)}", w)} | {"id"}
    slots = {k: v for k, v in {"ID": e.id.upper(), "id": e.id, "poly": e.polymer_word(),
                               **spec["slots"]}.items() if k in wanted}
    prov = {
        "script": SCRIPT,
        "inputs": [f"data/panel/facts/{e.id}.json", f"molbench/atom_tables/{e.id}.json.gz"],
        "date": DATE,
        "checks": [],
        "seed": SEED,
        "template": template,
        "wording": wording,
        "slots": slots,
        "open": OPEN[template],
        "rule": rule,
        "candidates": spec["candidates"],
        "accepted_states": [s["label"] for s in states],
        "not_accepted": not_accepted,
        "facts": {**spec["facts"], "n_candidates": len(spec["candidates"]),
                  "n_accepted_states": len(states)},
    }
    if "residues" in spec:
        prov["residues"] = spec["residues"]
    return {
        "id": f"{template}-{e.id}-{track}", "track": track, "tier": "accept_set",
        "family": template, "structures": [e.id], "prompt": prompt,
        "reference": answers[0], "accepted": answers[1:], "context": None,
        "target": target(track, states[0]), "twin_of": None, "paraphrase_of": None,
        "style": "full", "split": split, "grounding": None, "provenance": prov,
        "skills": SKILLS.get(template, DEFAULT_SKILLS),
        "accepted_targets": [target(track, s) for s in states[1:]],
        "notes": f"Left open: {OPEN[template]}. Reference = accepted state 1 of "
                 f"{len(states)} ({states[0]['label']}); the others are in 'accepted', in the "
                 "order of provenance.accepted_states.",
    }


def build(held: set[str]) -> list[dict]:
    pool = entries()
    used: Counter = Counter()
    out: list[dict] = []
    for template, n, twin in PLAN:
        cands = [(e, s) for e in pool for s in [SPEC[template](e)] if s is not None]
        chosen = choose(template, cands, n, twin, used, held)
        if len(chosen) < n:
            raise SystemExit(f"{template}: only {len(chosen)} of {n} structures available")
        for e, spec in chosen:
            split = "heldback" if e.id in held else "public"
            wording = int(rank("wording", template, e.id), 16) % len(WORDINGS[template])
            slots = {"ID": e.id.upper(), "poly": e.polymer_word(), **spec["slots"]}
            prompt = WORDINGS[template][wording].format(**slots)
            a = make_task("mvs", template, e, spec, split, prompt, wording)
            out.append(a)
            if twin:
                b = make_task("api", template, e, spec, split, prompt, wording)
                a["twin_of"], b["twin_of"] = b["id"], a["id"]
                out.append(b)
    return out


def verify(built: list[dict]) -> list[dict]:
    """The corpus checks on the built tasks; record what each passed."""
    loaded = []
    for t in built:
        t["provenance"]["checks"] = ["(filled in below, once passed)"]
        errors = T.validate_task(t)
        if errors:
            raise SystemExit(f"{t['id']}: " + "; ".join(errors))
        loaded.append(T._with_aliases({**t, "_path": f"{OUT[t['track']].name}/{t['id']}.json"}))
    errors, _ = T.check_corpus(loaded, grade=runner.grade_parsed, check=runner.grader_problems)
    if errors:
        raise SystemExit("accept-set tasks fail the corpus checks:\n  " + "\n  ".join(errors))
    for t, full in zip(built, loaded):
        resolver = "mvs.resolve_scene" if t["track"] == "mvs" else "pdbe_state.replay"
        n_atoms = sum(bin(m).count("1") for m in T.target_atoms(full).values())
        res = runner.grade_parsed(full, t["reference"])
        assert res["success"] is True and res["f1"] == 1.0 and res["target_f1"] == 1.0, t["id"]
        checks = [
            f"each of the {1 + len(t['accepted'])} accepted states: the atoms it draws, read "
            f"back from {resolver}, equal the atoms computed from the atom-table columns",
            "reference grades as exactly right against the task (success, F1 1, target score 1; "
            "runner.grade_parsed)",
            "every accepted alternative grades as itself, is accepted by the task with target "
            "score 1, and is a different final state from the reference",
            f"target selects {n_atoms} atoms on the frozen atom table",
            "no accepted state equals another (pairwise, by the grader)",
        ]
        states = [t["reference"]] + t["accepted"]
        for i, j in itertools.combinations(range(len(states)), 2):
            alone = {**full, "reference": states[i], "accepted": [], "target": None,
                     "accepted_targets": None,
                     **({"reference_mvs": states[i]} if t["track"] == "mvs" else {})}
            if runner.grade_parsed(alone, states[j]).get("success"):
                raise SystemExit(f"{t['id']}: accepted states {i} and {j} are the same state")
        if t["twin_of"]:
            checks.append("twin selects the same target atoms")
        t["provenance"]["checks"] = checks
    return built


# --------------------------------------------------------------------------- #
# README (generated, so the counts cannot drift from the files)
# --------------------------------------------------------------------------- #
DERIVED = {
    "acc-chain-colours": "polymer chains from `facts.chains`; exactly 2 or 3; n colours by seed; "
                         "all n! assignments",
    "acc-ligand-which": "`facts.ligands` of kind `ligand`: exactly two components, one copy each, "
                        "≥ 8 heavy atoms, entry not a membrane protein (panel feature); states = A, B, A+B (+ Mol*'s static `ligand` on MVS when "
                        "it differs)",
    "acc-ligand-colours": "same entries as above; two colours by seed; both assignments",
    "acc-ligand-copy": "a `ligand` component with 2–4 copies (≥ 8 heavy atoms); each copy, and all",
    "acc-metal-copy": "the entry's only metal: an `ion` component with 2–4 copies, no metal in "
                      "any ligand; each ion, and all",
    "acc-metal-which": "exactly two metal `ion` components, one copy each, equal to Mol*'s static "
                       "`ion` selection, no metal in any ligand; states = A, B, A+B",
    "acc-residue-copy": "a protein entity with 2–3 chains; a residue (seeded) with the same author "
                        "number and name in every one of them and in no other chain; each chain's "
                        "copy, and all",
    "acc-residue-colour": "as above, coloured on the cartoon instead of added as sticks",
    "acc-representation-open": "the entry's only `ligand` component (one copy, ≥ 8 heavy atoms); "
                               "one state per representation type that draws all its atoms",
}

SEEDS = """\
## The seven seed prompts of issue #4

| seed | prompt | here |
|---|---|---|
| amb-001 | clean up the view | **dropped**: which things are clutter is a judgement, not a count in the structure |
| amb-002 | focus on the important parts | **dropped**: same reason |
| amb-003 | what structures do I have loaded? | **not this tier**: a question, so the right final state is the start state (follow-up tier, `noop`) |
| amb-004 | hide the binding site | **dropped**: needs a distance cut-off nobody stated; and "hide" needs a start scene |
| amb-005 | delete the waters | **not this tier**: one right state (waters not shown); a wording variant, not an ambiguity |
| amb-006 | remove everything except the ligand | covered in part by `acc-ligand-which` (which ligand?); the "remove" needs a start scene (follow-up tier) |
| amb-007 | show me the drug | `acc-ligand-which`, worded "the ligand" ("drug" is not a fact of the frozen panel) |

"Colour the chains differently" with no colours named is not here either: on the MVS
track the grader already accepts any one-colour-per-chain answer against a `chain-id`
theme reference (GRADING.md), so it is an ordinary single-reference task; on the API
track no grading rule for "any distinct colours" exists yet. `acc-chain-colours` is the
enumerable neighbour: the colours are named, the assignment is not.
"""


def readme(track: str, tasks: list[dict], held: set[str]) -> str:
    mine = [t for t in tasks if t["track"] == track]
    name = {"mvs": "MVS", "api": "API (pdbe-molstar 3.3.2 calls)"}[track]
    lines = [
        f"# Accept-set tier, {name} track",
        "",
        "Generated by `scripts/generate_accept_set_tasks.py` (seed `" + SEED + "`); do not edit.",
        "Under-specified requests where several final states are all right. Every accepted",
        "state is enumerated by script from the frozen panel (`data/panel/facts`, the atom",
        "tables) and listed in the task: `reference` is the first, `accepted` the others,",
        "`accepted_targets` their targets. `provenance` holds the rule that generated them",
        "(`rule`), their names in order (`accepted_states`), what is not accepted and why",
        "(`not_accepted`), and the difficulty facts (`facts`).",
        "",
        f"{len(mine)} tasks on {len({t['structures'][0] for t in mine})} structures; "
        f"{sum(t['split'] == 'heldback' for t in mine)} tasks on "
        f"{len({t['structures'][0] for t in mine if t['split'] == 'heldback'})} held-back structures; "
        f"{sum(t['twin_of'] is not None for t in mine)} have a twin on the other track.",
        "",
        "## Templates",
        "",
        "| family | tasks | accepted states per task | left open | example prompt |",
        "|---|---:|---|---|---|",
    ]
    for template, _, _ in PLAN:
        ts = [t for t in mine if t["family"] == template]
        if not ts:
            continue
        n_states = sorted({1 + len(t["accepted"]) for t in ts})
        lines.append(f"| `{template}` | {len(ts)} | {', '.join(map(str, n_states))} | "
                     f"{OPEN[template]} | {ts[0]['prompt']} |")
    lines += ["", "## How each reference is derived", "",
              "| family | from the frozen data | accept rule |", "|---|---|---|"]
    for template, _, _ in PLAN:
        if any(t["family"] == template for t in mine):
            lines.append(f"| `{template}` | {DERIVED[template]} | {RULES[template][0]} |")
    lines += ["", "## Tasks", "",
              "| id | structure | split | states | candidates |", "|---|---|---|---:|---|"]
    for t in sorted(mine, key=lambda t: t["id"]):
        lines.append(f"| `{t['id']}` | {t['structures'][0]} | {t['split']} | "
                     f"{1 + len(t['accepted'])} | {', '.join(t['provenance']['candidates'])} |")
    lines += ["", SEEDS, "## Rules shared by all templates", "",
              "- Structures: PDB entries of the panel with one model and at most "
              f"{MAX_ATOMS:,} atoms; never 1HSG. At most {MAX_PER_STRUCTURE} tasks of the tier "
              "(both tracks) on one structure.",
              "- \"Any one, or all\": with more than two copies, a several-but-not-all answer is "
              "not accepted, because no reading of the request picks it.",
              "- Held-back structures are a fixed fifth of the panel by hash of the entry id "
              "(`heldback_structures()`), not chosen per tier, because the validator refuses a "
              "structure used by both splits anywhere in the corpus. In this tier: "
              + ", ".join(sorted({t["structures"][0] for t in tasks if t["split"] == "heldback"}))
              + ".",
              "- The cartoon is not given a colour by the request, so the reference leaves it "
              "at the viewer's default.",
              ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if the files would change")
    ap.add_argument("--heldback-file", type=pathlib.Path,
                    help="JSON list of held-back structure ids (replaces the hash rule)")
    a = ap.parse_args(argv)
    held = (set(json.loads(a.heldback_file.read_text())) if a.heldback_file
            else heldback_structures())
    tasks = verify(build(held))
    files = {OUT[t["track"]] / f"{t['id']}.json": json.dumps(t, indent=1) + "\n" for t in tasks}
    for track, folder in OUT.items():
        files[folder / "README.md"] = readme(track, tasks, held)
    stale = sorted(p for folder in OUT.values() for p in folder.glob("*") if p not in files)
    changed = [p for p, text in files.items()
               if not p.exists() or p.read_text(encoding="utf-8") != text]
    if a.check:
        if changed or stale:
            print("accept-set tasks are out of date:", *[p.name for p in changed + stale])
            return 1
        print(f"{len(tasks)} accept-set tasks are up to date")
        return 0
    for folder in OUT.values():
        folder.mkdir(parents=True, exist_ok=True)
    for p in stale:
        p.unlink()
    for p, text in files.items():
        p.write_text(text, encoding="utf-8")
    per = Counter(t["track"] for t in tasks)
    print(f"wrote {per['mvs']} MVS and {per['api']} API accept-set tasks "
          f"({len(changed)} files changed, {len(stale)} removed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
