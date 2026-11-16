#!/usr/bin/env python3
"""
Translation-tier MVS tasks (``tasks/mvs_generated/``): everything the answer needs is
in the request, so the task measures turning words into a scene.

Every prompt names the entry, the chains and residue numbers (author numbering, as in
the paper of the structure), the representation and the colour. The reference is built
from those same values, which the script takes from the frozen facts and atom table of
the entry; nothing is typed in by hand. Templates, counts and how each reference is
derived: ``tasks/mvs_generated/README.md`` (written by this script).

    uv run python scripts/generate_mvs_tasks.py           # rewrite tasks/mvs_generated/
    uv run python scripts/generate_mvs_tasks.py --check   # fail if the files would change

No network. Deterministic: the choice of structures, colours and wordings depends only
on the seed in ``scripts/mvscore_common.py``.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import mvscore_common as C  # noqa: E402
import generate_grounded_tasks as grounded  # noqa: E402

OUT = C.REPO / "tasks" / "mvs_generated"
SCRIPT = "scripts/generate_mvs_tasks.py"
TIER = "translation"
GREY = "gray"


# --------------------------------------------------------------------------- #
# What an entry offers
# --------------------------------------------------------------------------- #
def polymer_chains(entry: str, kind: str | None = None) -> list[dict]:
    return [c for c in C.facts(entry)["chains"]
            if kind is None or (c["polymer_type"] == "protein") == (kind == "protein")]


def protein_only(entry: str) -> bool:
    t = C.table(entry)
    return bool(t.static.get("polymer")) and t.static["polymer"] == t.static.get("protein")


def what(entry: str) -> str:
    """The word for the entry's polymer in a prompt."""
    t = C.table(entry)
    if protein_only(entry):
        return "protein"
    if not t.static.get("protein"):
        kinds = {c["polymer_type"] for c in C.facts(entry)["chains"]}
        return "RNA" if kinds == {"RNA"} else "DNA" if kinds == {"DNA"} else "nucleic acid"
    return "complex"


def chain_selector(chain: dict) -> dict:
    return {"auth_asym_id": chain["auth_asym_id"]}


def plain_ranges(entry: str, chain: dict, length: int) -> list[tuple[int, int]]:
    """Author-number ranges of ``length`` observed residues of a chain that a request
    can name without doubt: consecutive numbers, no insertion code, and the range
    selects polymer atoms only (no water or ligand shares the chain id and numbers)."""
    t = C.table(entry)
    c = t.columns
    rows = C.residue_rows(entry, {"auth_asym_id": chain["auth_asym_id"]})
    polymer = t.static["polymer"]
    nums = [c["auth_seq_id"][r] for r in rows if polymer >> r & 1]
    coded = {c["auth_seq_id"][r] for r in rows if c["pdbx_PDB_ins_code"][r]}
    out = []
    for i in range(len(nums) - length + 1):
        a, b = nums[i], nums[i + length - 1]
        if b - a != length - 1 or coded & set(range(a, b + 1)):
            continue
        mask = t.selector({"auth_asym_id": chain["auth_asym_id"], "beg_auth_seq_id": a,
                           "end_auth_seq_id": b})
        if mask and not mask & ~polymer:
            out.append((a, b))
    return out


def range_selector(chain: dict, a: int, b: int) -> dict:
    return {"auth_asym_id": chain["auth_asym_id"], "beg_auth_seq_id": a, "end_auth_seq_id": b}


def single_atom_ions(entry: str) -> list[dict]:
    return [g for g in C.facts(entry)["ligands"] if g["n_heavy_atoms"] == 1 and g["comp_id"] != "OH"
            and g["kind"] == "ion"]


def ions_unambiguous(entry: str) -> bool:
    """Mol*'s ``ion`` selection is exactly the entry's single-atom ions, so "the ions"
    means one thing (in 1HHO it would be a phosphate, which is why this is checked)."""
    t = C.table(entry)
    groups = single_atom_ions(entry)
    mine = 0
    for g in groups:
        mine |= t.selector({"label_comp_id": g["comp_id"]}) or 0
    return bool(mine) and mine == t.static.get("ion", 0)


def ligands_unambiguous(entry: str) -> bool:
    """Mol*'s ``ligand`` selection is exactly the entry's non-polymer, non-water,
    non-sugar groups: there are no ions, and no polymer residue is pulled in by a bond."""
    t = C.table(entry)
    s = t.static
    rest = s["all"] & ~s.get("polymer", 0) & ~s.get("water", 0) & ~s.get("branched", 0)
    groups = C.facts(entry)["ligands"]
    return (bool(s.get("ligand")) and s["ligand"] == rest and not s.get("ion")
            and all(g["kind"] == "ligand" for g in groups))


# Crystallisation and buffer additives. An entry whose only non-polymer groups are
# these has no "ligand" in a structural biologist's sense, so its prompt says "small
# molecule" (same atoms: Mol*'s `ligand` selection).
ADDITIVES = frozenset({"GOL", "EDO", "DMS", "GLY", "TLA", "C8E", "PEG", "PGE", "PG4", "MPD",
                       "ACT", "FMT", "IPA", "EOH", "BME", "TRS", "MES", "EPE", "CIT"})


def sugar_chains(entry: str) -> list[str]:
    """Label chain ids whose atoms are all sugar (glycan chains and single sugars)."""
    t = C.table(entry)
    sugar = t.static.get("branched", 0) & ~t.static.get("polymer", 0)
    return sorted((a for a, m in t.index("label_asym_id").items() if m and not m & ~sugar),
                  key=lambda a: (len(a), a))


# --------------------------------------------------------------------------- #
# Templates. Each returns a list of candidate tasks as dicts with the keys
# entry, prompt wordings, reference children, target, derivation, selector for the
# numbering facts, and optional accepted alternatives.
# --------------------------------------------------------------------------- #
def cand(entry, wordings, children, target, derivation, numbering=None, accepted=None,
         extra_inputs=(), **words):
    return {"entry": entry, "wordings": wordings, "children": children, "target": target,
            "derivation": derivation, "numbering": numbering, "accepted": accepted or [],
            "words": words, "extra_inputs": list(extra_inputs)}


def t_cartoon():
    out = []
    for e in C.usable_entries():
        entry = e["id"]
        if entry.startswith("af-"):
            continue
        col = C.colours(1, "cartoon", entry)[0]
        out.append(cand(
            entry,
            ["Load {ID} and show the {what} as a {c} cartoon.",
             "Show me {ID} as a {c} cartoon.",
             "Open PDB entry {ID}; draw the whole {what} as a cartoon, coloured {c}."],
            [C.drawn_comp("polymer", "cartoon", col)],
            [C.part("polymer", "cartoon", col)],
            "the whole polymer (Mol*'s `polymer` selection) as one cartoon",
            what=what(entry), c=C.say_colour(col)))
    return out


def t_surface():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        if not protein_only(entry) or e["atoms"] > 8000:
            continue
        col = C.colours(1, "surface", entry)[0]
        out.append(cand(
            entry,
            ["Load {ID} and show the protein as a {c} molecular surface.",
             "Show the protein of {ID} as a surface, coloured {c}.",
             "{ID}: I want the protein as a {c} surface."],
            [C.drawn_comp("polymer", "surface", col)],
            [C.part("polymer", "surface", col)],
            "the whole polymer as a surface; the entry's only polymer is protein, so "
            "`polymer` and `protein` are the same atoms",
            c=C.say_colour(col)))
    return out


def t_chain_colour():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        chains = polymer_chains(entry)
        if not 2 <= len(chains) <= 12:
            continue
        chain = C.pick(chains, "chain-colour", entry)
        col = C.colours(1, "chain-colour", entry)[0]
        sel = chain_selector(chain)
        out.append(cand(
            entry,
            ["Load {ID} as a grey cartoon and colour chain {X} {c}.",
             "Show {ID} as a cartoon: chain {X} in {c}, everything else grey.",
             "Open {ID}, cartoon, all grey except chain {X}, which should be {c}."],
            [C.comp("polymer", C.rep("cartoon", C.colour(GREY), C.colour(col, sel)))],
            [C.part(sel, "cartoon", col)],
            "one cartoon of the polymer, grey, recoloured on the named chain (author "
            "chain id from the facts)", numbering=sel,
            X=chain["auth_asym_id"], c=C.say_colour(col)))
    return out


def t_chain_only():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        chains = polymer_chains(entry)
        if not 2 <= len(chains) <= 12:
            continue
        chain = C.pick(chains, "chain-only", entry)
        col = C.colours(1, "chain-only", entry)[0]
        sel = chain_selector(chain)
        out.append(cand(
            entry,
            ["Load {ID} and show only chain {X}, as a {c} cartoon.",
             "From {ID} I want just chain {X}: a {c} cartoon and nothing else.",
             "Show chain {X} of {ID} on its own as a {c} cartoon; leave everything else out."],
            [C.drawn_comp(sel, "cartoon", col)],
            [C.part(sel, "cartoon", col)],
            "a cartoon of the named chain only (author chain id from the facts); the "
            "other chains are not drawn", numbering=sel,
            X=chain["auth_asym_id"], c=C.say_colour(col)))
    return out


def t_range_sticks():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        chains = [c for c in polymer_chains(entry, "protein") if c["n_observed"] >= 40]
        if not chains:
            continue
        chain = C.pick(chains, "range-sticks", entry)
        length = C.pick([5, 6, 8, 10, 12], "range-sticks-len", entry)
        ranges = plain_ranges(entry, chain, length)
        if not ranges:
            continue
        a, b = C.pick(ranges, "range-sticks-range", entry)
        col = C.colours(1, "range-sticks", entry)[0]
        sel = range_selector(chain, a, b)
        many = len(polymer_chains(entry)) > 1
        out.append(cand(
            entry,
            ["Load {ID} as a grey cartoon and show residues {a}-{b}{of} as {c} ball-and-stick.",
             "Show {ID} as a grey cartoon, with residues {a} to {b}{of} added as {c} "
             "ball-and-stick.",
             "{ID}: grey cartoon for the whole {what}; residues {a}-{b}{of} in {c} "
             "ball-and-stick on top."],
            [C.drawn_comp("polymer", "cartoon", GREY), C.drawn_comp(sel, "ball_and_stick", col)],
            [C.part(sel, "ball_and_stick", col)],
            "a grey cartoon of the polymer, plus the named residue range (author "
            "numbering, read from the atom table; consecutive, no insertion codes, "
            "polymer atoms only) as ball-and-stick", numbering=sel,
            a=a, b=b, c=C.say_colour(col), what=what(entry),
            of=f" of chain {chain['auth_asym_id']}" if many else ""))
    return out


def t_range_rows():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        chains = [c for c in polymer_chains(entry, "protein") if c["n_observed"] >= 40]
        if not chains:
            continue
        n = C.pick([2, 3], "range-rows-n", entry)
        cols = C.colours(n, "range-rows", entry)
        rows, taken = [], []
        r = C.rng("range-rows", entry)
        for i in range(n):
            chain = r.choice(chains)
            ranges = [(a, b) for a, b in plain_ranges(entry, chain, r.choice([6, 8, 10, 12, 15]))
                      if not any(ch is chain and a <= y + 3 and x - 3 <= b for ch, x, y in taken)]
            if not ranges:
                break
            a, b = r.choice(ranges)
            taken.append((chain, a, b))
            rows.append((chain, a, b, cols[i]))
        if len(rows) != n:
            continue
        rows.sort(key=lambda x: (x[0]["auth_asym_id"], x[1]))
        sels = [range_selector(ch, a, b) for ch, a, b, _ in rows]
        spec = "; ".join(f"chain {ch['auth_asym_id']} {a}-{b} {C.say_colour(col)}"
                         for ch, a, b, col in rows)
        out.append(cand(
            entry,
            ["Load {ID} as a grey cartoon and colour these segments: {spec}.",
             "{ID}, cartoon, grey, except: {spec}.",
             "Show {ID} as a cartoon in grey with the following residue ranges recoloured: "
             "{spec}."],
            [C.comp("polymer", C.rep("cartoon", C.colour(GREY),
                                     *[C.colour(col, s) for (_, _, _, col), s in zip(rows, sels)]))],
            [C.part(s, "cartoon", col) for (_, _, _, col), s in zip(rows, sels)],
            "one grey cartoon of the polymer, recoloured on each listed range (author "
            "chain and numbering from the atom table; ranges do not overlap)",
            numbering=sels, spec=spec))
    return out


LABEL_TEXTS = ["region 1", "region 2", "region 3", "site A", "site B", "segment 1",
               "segment 2", "patch A", "patch B"]


def t_range_labels():
    """The most common request of the chat site's users: rows of chain, residue range,
    colour and a text label (LEDGER U6 and U17). The label texts are neutral names from
    a fixed list, so the prompt claims nothing about the structure."""
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        chains = [c for c in polymer_chains(entry, "protein") if c["n_observed"] >= 40]
        if not chains:
            continue
        r = C.rng("range-labels", entry)
        cols = C.colours(2, "range-labels", entry)
        texts = r.sample(LABEL_TEXTS, 2)
        rows, taken = [], []
        for i in range(2):
            chain = r.choice(chains)
            ranges = [(a, b) for a, b in plain_ranges(entry, chain, r.choice([5, 6, 8, 10, 12]))
                      if not any(ch is chain and a <= y + 3 and x - 3 <= b for ch, x, y in taken)]
            if not ranges:
                break
            a, b = r.choice(ranges)
            taken.append((chain, a, b))
            rows.append((chain, a, b, cols[i], texts[i]))
        if len(rows) != 2:
            continue
        rows.sort(key=lambda x: (x[0]["auth_asym_id"], x[1]))
        sels = [range_selector(ch, a, b) for ch, a, b, _, _ in rows]
        spec = "; ".join(f"chain {ch['auth_asym_id']}, residues {a}-{b}, {C.say_colour(col)}, "
                         f"label \"{text}\"" for ch, a, b, col, text in rows)
        long = " and ".join(f"colour residues {a}-{b} of chain {ch['auth_asym_id']} "
                            f"{C.say_colour(col)} with the text label \"{text}\""
                            for ch, a, b, col, text in rows)
        out.append(cand(
            entry,
            ["{ID}, grey cartoon. {spec}.",
             "Load {ID} as a grey cartoon, then {long}.",
             "Show {ID} as a cartoon in grey and mark these segments, each recoloured and "
             "with its own text label: {spec}."],
            [C.comp("polymer", C.rep("cartoon", C.colour(GREY),
                                     *[C.colour(row[3], s) for row, s in zip(rows, sels)])),
             *[C.comp(s, {"kind": "label", "params": {"text": row[4]}})
               for row, s in zip(rows, sels)]],
            [C.part(s, "cartoon", row[3]) for row, s in zip(rows, sels)],
            "one grey cartoon of the polymer, recoloured on each listed range (author "
            "chain and numbering from the atom table; ranges do not overlap), and one "
            "text label on each range with the text the prompt gives",
            numbering=sels, spec=spec, long=long))
    return out


def t_ligands():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        if not ligands_unambiguous(entry):
            continue
        comps = {g["comp_id"] for g in C.facts(entry)["ligands"]}
        if comps & ADDITIVES and comps - ADDITIVES:
            continue                     # a ligand plus additives: "the ligand" would be one of them
        word = "small molecule" if comps <= ADDITIVES else "ligand"
        col = C.colours(1, "ligands", entry)[0]
        one = C.n_atoms(C.table(entry).static["ligand"]) and sum(
            len(g["copies"]) for g in C.facts(entry)["ligands"]) == 1
        out.append(cand(
            entry,
            ["Load {ID}; show the {what} as a grey cartoon and the {lig} as {c} ball-and-stick.",
             "Show {ID} with the {what} as a grey cartoon and the bound {lig} in {c} "
             "ball-and-stick.",
             "{ID}: grey cartoon for the {what}, {c} ball-and-stick for the {lig}."],
            [C.drawn_comp("polymer", "cartoon", GREY), C.drawn_comp("ligand", "ball_and_stick", col)],
            [C.part("ligand", "ball_and_stick", col)],
            "a grey cartoon of the polymer plus Mol*'s `ligand` selection as "
            "ball-and-stick; used only where that selection is exactly the entry's "
            "non-polymer, non-water, non-sugar groups (no ions, no bonded residue)"
            + ("; they are crystallisation additives (" + ", ".join(sorted(comps))
               + "), so the prompt says \"small molecule\", not \"ligand\""
               if word != "ligand" else ""),
            what=what(entry), lig=word if one else word + "s", c=C.say_colour(col)))
    return out


def t_ions():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        if not ions_unambiguous(entry):
            continue
        groups = single_atom_ions(entry)
        metals = all(g["metals"] for g in groups)
        n = sum(len(g["copies"]) for g in groups)
        col = C.colours(1, "ions", entry)[0]
        out.append(cand(
            entry,
            ["Load {ID}; show the {what} as a grey cartoon and the {ions} as {a_}{c} {spheres}.",
             "Show {ID} as a grey cartoon with the {ions} drawn as {a_}{c} {spheres}.",
             "{ID}: grey cartoon, plus the {ions} as {a_}{c} space-filling {spheres}."],
            [C.drawn_comp("polymer", "cartoon", GREY), C.drawn_comp("ion", "spacefill", col)],
            [C.part("ion", "spacefill", col)],
            "a grey cartoon of the polymer plus Mol*'s `ion` selection as spheres; used "
            "only where that selection is exactly the entry's single-atom ions ("
            + ", ".join(f"{len(g['copies'])} {g['comp_id']}" for g in groups) + ")",
            what=what(entry), c=C.say_colour(col),
            spheres="spheres" if n > 1 else "sphere", a_="" if n > 1 else "a ",
            ions=("metal ion" if metals else "ion") + ("s" if n > 1 else "")))
    return out


def t_water():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        waters = C.table(entry).static.get("water", 0)
        if not 20 <= C.n_atoms(waters) <= 400 or not protein_only(entry) \
                or C.facts(entry)["n_models"] != 1:
            continue
        c1, c2 = C.colours(2, "water", entry)
        out.append(cand(
            entry,
            ["Load {ID}; show the protein as a {c1} cartoon and the water molecules as {c2} "
             "spheres.",
             "Show {ID} as a {c1} cartoon together with its waters as {c2} spheres.",
             "{ID}: protein as a {c1} cartoon, crystallographic waters as {c2} spheres."],
            [C.drawn_comp("polymer", "cartoon", c1), C.drawn_comp("water", "spacefill", c2)],
            [C.part("water", "spacefill", c2)],
            "a cartoon of the polymer plus Mol*'s `water` selection as spheres",
            c1=C.say_colour(c1), c2=C.say_colour(c2)))
    return out


def t_strands():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        nucleic = [c for c in C.facts(entry)["chains"] if c["polymer_type"] != "protein"]
        if len(nucleic) != 2 or {c["polymer_type"] for c in nucleic} != {"DNA"}:
            continue
        c1, c2 = C.colours(2, "strands", entry)
        s1, s2 = (chain_selector(c) for c in nucleic)
        out.append(cand(
            entry,
            ["Load {ID} and show the two DNA strands as cartoons: chain {X} in {c1} and "
             "chain {Y} in {c2}. Nothing else.",
             "From {ID}, show only the DNA: strand {X} as a {c1} cartoon and strand {Y} as "
             "a {c2} cartoon.",
             "{ID}: just the two DNA chains as cartoons, {X} {c1} and {Y} {c2}."],
            [C.drawn_comp(s1, "cartoon", c1), C.drawn_comp(s2, "cartoon", c2)],
            [C.part(s1, "cartoon", c1), C.part(s2, "cartoon", c2)],
            "one cartoon per DNA chain (author chain ids from the facts); nothing else "
            "is drawn", numbering=[s1, s2],
            X=nucleic[0]["auth_asym_id"], Y=nucleic[1]["auth_asym_id"],
            c1=C.say_colour(c1), c2=C.say_colour(c2)))
    return out


def t_glycans():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        if not C.facts(entry)["glycans"] or e["atoms"] > 15000:
            continue
        t = C.table(entry)
        chains = sugar_chains(entry)
        sel = [{"label_asym_id": a} for a in chains]
        sugar = t.static["branched"] & ~t.static["polymer"]
        assert t.selector(sel) == sugar, entry
        col = C.colours(1, "glycans", entry)[0]
        grey = C.drawn_comp("polymer", "cartoon", GREY)
        accepted = []
        if t.static["branched"] != sugar:
            accepted = [C.scene(entry, [grey, C.drawn_comp("branched", "ball_and_stick", col)])]
        out.append(cand(
            entry,
            ["Load {ID}; show the protein as a grey cartoon and the {sugars} as {c} "
             "ball-and-stick.",
             "Show {ID} as a grey cartoon with the {sugars} in {c} ball-and-stick.",
             "{ID}: grey cartoon for the protein, {c} ball-and-stick for the {sugars}."],
            [grey, C.drawn_comp(sel, "ball_and_stick", col)],
            [C.part(sel, "ball_and_stick", col)],
            f"a grey cartoon of the polymer plus every sugar residue ({len(chains)} sugar "
            "chains, by label chain id from the atom table: all atoms of Mol*'s `branched` "
            "selection that are not polymer) as ball-and-stick."
            + (" Accepted alternative: Mol*'s own `branched` selection, which also holds "
               "the protein residues the sugars are bonded to." if accepted else ""),
            accepted=accepted,
            sugars="glycans" if C.facts(entry)["glycosylation_sites"] else "bound sugar",
            c=C.say_colour(col)))
    return out


def t_colour_by_chain():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        chains = polymer_chains(entry)
        if len(chains) < 3 or len({c["auth_asym_id"] for c in chains}) != len(chains):
            continue
        out.append(cand(
            entry,
            ["Load {ID} and show it as a cartoon coloured by chain.",
             "Show {ID} as a cartoon with each of its {n} chains in a different colour.",
             "{ID}, cartoon, colour by chain."],
            [C.comp("polymer", C.rep("cartoon", C.theme("chain-id")))],
            [C.part("polymer", "cartoon", None)],
            f"one cartoon of the polymer with Mol*'s chain-id colour theme ({len(chains)} "
            "polymer chains). The grader also accepts any answer that gives every chain "
            "one colour of its own, all different",
            n=C.number(len(chains))))
    return out


def t_chains_named():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        chains = polymer_chains(entry)
        if not 3 <= len(chains) <= 6:
            continue
        cols = C.colours(len(chains), "chains-named", entry)
        sels = [chain_selector(c) for c in chains]
        spec = C.join([f"chain {c['auth_asym_id']} {C.say_colour(col)}"
                       for c, col in zip(chains, cols)])
        out.append(cand(
            entry,
            ["Load {ID} as a cartoon and colour {spec}.",
             "Show {ID} as a cartoon with these chain colours: {spec}.",
             "{ID}, cartoon: {spec}."],
            [C.drawn_comp(s, "cartoon", col) for s, col in zip(sels, cols)],
            [C.part(s, "cartoon", col) for s, col in zip(sels, cols)],
            "one cartoon per polymer chain (author chain ids from the facts), each in "
            "the colour the prompt gives it", numbering=sels, spec=spec))
    return out


REP_WORDINGS = {
    "line": ["Load {ID} and draw the protein in wireframe, coloured {c}.",
             "Show the protein of {ID} as {c} lines (wireframe).",
             "{ID}: protein as a {c} wireframe."],
    "spacefill": ["Load {ID} and show the protein as {c} space-filling spheres.",
                  "Show the protein of {ID} in CPK (space-filling) style, coloured {c}.",
                  "{ID}: protein as {c} spacefill."],
    "backbone": ["Load {ID} and show the protein as a {c} backbone trace.",
                 "Show only the backbone trace of the protein in {ID}, coloured {c}.",
                 "{ID}: protein backbone trace in {c}."],
}


def t_rep_word():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        if not protein_only(entry) or e["atoms"] > 5000:
            continue
        rtype = C.pick(sorted(REP_WORDINGS), "rep-word", entry)
        col = C.colours(1, "rep-word", entry)[0]
        out.append(cand(
            entry, REP_WORDINGS[rtype],
            [C.drawn_comp("polymer", rtype, col)],
            [C.part("polymer", rtype, col)],
            f"the whole polymer in the MVS representation `{rtype}`, which is what the "
            "prompt's word for it means in Mol* (wireframe = line, space-filling/CPK = "
            "spacefill, backbone trace = backbone); the entry's only polymer is protein",
            c=C.say_colour(col)))
    return out


def t_het_code():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        t = C.table(entry)
        groups = [g for g in C.facts(entry)["ligands"]
                  if g["kind"] == "ligand" and g["n_heavy_atoms"] >= 6
                  and len(g["comp_id"]) == 3 and len(g["copies"]) <= 6]
        if not groups:
            continue
        g = C.pick(groups, "het-code", entry)
        sel = {"label_comp_id": g["comp_id"]}
        col = C.colours(1, "het-code", entry)[0]
        n = len(g["copies"])
        assert C.n_atoms(t.selector(sel)) >= g["n_heavy_atoms"] * n
        out.append(cand(
            entry,
            ["Load {ID}; show the {what} as a grey cartoon and the {CODE} {mol} as {c} "
             "ball-and-stick.",
             "Show {ID} as a grey cartoon with {every} {CODE} residue{s} in {c} ball-and-stick.",
             "{ID}: grey cartoon, and the het group{s} {CODE} as {c} ball-and-stick."],
            [C.drawn_comp("polymer", "cartoon", GREY), C.drawn_comp(sel, "ball_and_stick", col)],
            [C.part(sel, "ball_and_stick", col)],
            f"a grey cartoon of the polymer plus every residue with the component code the "
            f"prompt gives ({g['comp_id']}: {g['name']}; {n} cop{'y' if n == 1 else 'ies'} in "
            "the facts) as ball-and-stick",
            what=what(entry), CODE=g["comp_id"], c=C.say_colour(col),
            mol="molecule" if n == 1 else "molecules", s="" if n == 1 else "s",
            every="the" if n == 1 else "every"))
    return out


def t_residue_focus():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        chains = [c for c in polymer_chains(entry, "protein") if c["n_observed"] >= 40]
        if not chains:
            continue
        chain = C.pick(chains, "residue-focus", entry)
        singles = plain_ranges(entry, chain, 1)
        if not singles:
            continue
        num, _ = C.pick(singles, "residue-focus-res", entry)
        sel = {"auth_asym_id": chain["auth_asym_id"], "auth_seq_id": num}
        col = C.colours(1, "residue-focus", entry)[0]
        many = len(polymer_chains(entry)) > 1
        out.append(cand(
            entry,
            ["Load {ID} as a grey cartoon, show residue {n}{of} as {c} ball-and-stick and "
             "zoom in on it.",
             "Show {ID} as a grey cartoon; add residue {n}{of} in {c} ball-and-stick and "
             "centre the view on that residue.",
             "{ID}: grey cartoon, residue {n}{of} as {c} ball-and-stick, camera focused on "
             "the residue."],
            [C.drawn_comp("polymer", "cartoon", GREY),
             C.comp(sel, C.rep("ball_and_stick", C.colour(col)), C.FOCUS)],
            [C.part(sel, "ball_and_stick", col)],
            "a grey cartoon of the polymer, the named residue (author numbering, from the "
            "atom table) as ball-and-stick, and a camera focus on that residue",
            numbering=sel, n=num, c=C.say_colour(col),
            of=f" of chain {chain['auth_asym_id']}" if many else ""))
    return out


# template id -> (candidates, how many tasks)
TEMPLATES = {
    "tr-colour-by-chain": (t_colour_by_chain, 5),
    "tr-strands": (t_strands, 3),
    "tr-glycans": (t_glycans, 4),
    "tr-chains-named": (t_chains_named, 4),
    "tr-ions": (t_ions, 4),
    "tr-ligands": (t_ligands, 4),
    "tr-het-code": (t_het_code, 4),
    "tr-chain-colour": (t_chain_colour, 4),
    "tr-chain-only": (t_chain_only, 4),
    "tr-range-rows": (t_range_rows, 4),
    "tr-range-sticks": (t_range_sticks, 5),
    "tr-residue-focus": (t_residue_focus, 4),
    "tr-water": (t_water, 3),
    "tr-surface": (t_surface, 4),
    "tr-rep-word": (t_rep_word, 4),
    "tr-cartoon": (t_cartoon, 4),
    "tr-range-labels": (t_range_labels, 4),      # added last: earlier choices are unchanged
}

DERIVED = {
    "tr-nucleic": "Mol*'s `nucleic` (and `protein`) selection, checked to be exactly the DNA "
                  "or RNA chains of the facts. Built by the grounded generator's template "
                  "on that tier's choice of structures; it needs no lookup, so it is here.",
    "tr-cartoon": "Mol*'s `polymer` selection (frozen atom table).",
    "tr-surface": "`polymer`, on entries whose only polymer is protein.",
    "tr-rep-word": "`polymer` in the representation the prompt's word means (wireframe = "
                   "`line`, space-filling / CPK = `spacefill`, backbone trace = `backbone`).",
    "tr-chain-colour": "Author chain id from the facts; one grey cartoon recoloured on it.",
    "tr-chain-only": "Author chain id from the facts; a cartoon of that chain only.",
    "tr-chains-named": "Every polymer chain of the facts (3 to 6), one cartoon each, in the "
                       "colour the prompt gives.",
    "tr-colour-by-chain": "`polymer` cartoon with the chain-id colour theme (3 or more "
                          "chains); the grader accepts any one-colour-per-chain answer.",
    "tr-range-sticks": "A run of 5 to 12 consecutive author-numbered residues from the atom "
                       "table (no insertion code; polymer atoms only).",
    "tr-range-rows": "Two or three such runs, each recoloured on one grey cartoon.",
    "tr-range-labels": "Two such runs, each recoloured on one grey cartoon and carrying a "
                       "text label; the label text is in the prompt (neutral names from a "
                       "fixed list).",
    "tr-residue-focus": "One author-numbered residue from the atom table, as ball-and-stick, "
                        "with a camera focus on it.",
    "tr-ligands": "Mol*'s `ligand` selection, only where it equals the entry's non-polymer, "
                  "non-water, non-sugar atoms. Where those are only crystallisation additives "
                  "(glycerol, DMSO) the prompt says \"small molecule\"; an entry with a ligand "
                  "and additives is not used.",
    "tr-het-code": "Every residue with the component code named in the prompt (facts).",
    "tr-ions": "Mol*'s `ion` selection, only where it equals the entry's single-atom ions "
               "(this is what excludes 1HHO, whose only \"ion\" is a phosphate).",
    "tr-water": "Mol*'s `water` selection.",
    "tr-strands": "The two DNA chains of the facts, one cartoon each.",
    "tr-glycans": "All sugar atoms (`branched` minus polymer), by label chain; Mol*'s "
                  "`branched` (sugars plus the residues they are bonded to) is accepted too.",
}


def build() -> list[dict]:
    picker = C.Picker(TIER)
    built = []
    for family, (fn, n) in TEMPLATES.items():
        chosen = picker.choose(family, fn(), n, entry_of=lambda c: c["entry"])
        C.enough(family, chosen, n)
        for c in chosen:
            entry = c["entry"]
            wording = C.pick(c["wordings"], "wording", family, entry)
            prompt = wording.format(ID=entry.upper(), **c["words"])
            built.append(C.make_task(
                f"{family}-{entry}", TIER, family, entry, prompt,
                C.scene(entry, c["children"]), c["target"], script=SCRIPT,
                input_files=C.inputs(entry, *c["extra_inputs"]),
                derivation=c["derivation"],
                difficulty=C.difficulty(entry, c["numbering"]),
                accepted=c["accepted"]))
    # templates built with the grounded tier's machinery that need no lookup
    built += grounded.moved_to_translation()
    return sorted(built, key=lambda t: t["id"])


def readme(built: list[dict]) -> str:
    rows = "\n".join(f"| `{f}` | {DERIVED[f]} |" for f in sorted(DERIVED))
    return f"""# Translation tier (MVS track)

Generated by `scripts/generate_mvs_tasks.py`; do not edit by hand. Everything the answer
needs is in the request: the entry, chains and residue numbers (author numbering),
representation and colour. The reference holds what the prompt states and nothing else
(FINAL_PLAN decision 17), and every value in it is read from the frozen facts and atom
table of the entry.

{C.summary_tables(built)}

## How each reference is derived

| template | reference |
|---|---|
{rows}

Each task records under `provenance.difficulty` whether the residues it selects have an
author number different from the label (SEQRES) number, an author chain id different
from the label chain id, or an insertion code. Each prompt is one of three wordings of
its template, chosen by seed. Colours come from the 19-colour task palette.

Replaces the 36 tasks of the old 7 x 6 grid and the five hand-written tasks of
`tasks/mvs/` (their requests live on as templates here or in the grounded tier).
"""


def main() -> int:
    args = C.cli(__doc__)
    built = C.verify(build(), OUT)
    return C.finish(built, OUT, args, readme(built))


if __name__ == "__main__":
    raise SystemExit(main())
