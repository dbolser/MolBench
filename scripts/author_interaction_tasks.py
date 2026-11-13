#!/usr/bin/env python3
"""
Interaction-tier MVS tasks (``tasks/mvs_interactions/``): named atoms and a
measurement or contact between them - a dashed line between two atoms labelled with
its length (hydrogen bond, salt bridge, metal contact, ligand contact, disulfide,
C-alpha distance), Mol*'s computed non-covalent interactions around a ligand, and a
semi-transparent surface over a ligand.

Every pair of atoms is found by this script in the frozen mmCIF with gemmi (a
neighbour search with stated distance limits), every atom named in a reference
resolves to exactly one atom of the frozen atom table, and every measured distance is
written into the task (``provenance.measured``). The prompt names the atoms, so the
reference is fully determined. As the human raters asked, the reference of a contact
task frames the atoms involved, and the prompt asks for that.

    uv run python scripts/author_interaction_tasks.py           # rewrite tasks/mvs_interactions/
    uv run python scripts/author_interaction_tasks.py --check   # fail if the files would change

No network. Templates, counts and derivations: ``tasks/mvs_interactions/README.md``.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import mvscore_common as C  # noqa: E402
import generate_grounded_tasks as G  # noqa: E402  (names of ligands and metals, shared checks)

OUT = C.REPO / "tasks" / "mvs_interactions"
SCRIPT = "scripts/author_interaction_tasks.py"
TIER = "interactions"
GREY = "gray"

AMINO = set(G.ONE_TO_THREE.values())
BACKBONE = {"N", "CA", "C", "O", "OXT"}
HYDROXYL = {("SER", "OG"), ("THR", "OG1"), ("TYR", "OH")}
CATION = {("LYS", "NZ"), ("ARG", "NE"), ("ARG", "NH1"), ("ARG", "NH2")}
ANION = {("ASP", "OD1"), ("ASP", "OD2"), ("GLU", "OE1"), ("GLU", "OE2")}
HBOND_MIN, HBOND_MAX = 2.5, 3.2      # A, between the two heavy atoms


# --------------------------------------------------------------------------- #
# Atoms of the frozen mmCIF
# --------------------------------------------------------------------------- #
def clean_residues(entry: str) -> dict:
    """Protein residues of model 1 that can be named without doubt: a standard amino
    acid in a protein chain, every atom at full occupancy with no alternate conformer.
    Key: (author chain, number, insertion code) -> (gemmi residue, sequence index)."""
    import gemmi
    st = C.cif_structure(entry)
    out = {}
    counts: dict = {}
    for chain in st[0]:
        for res in chain:
            key = (chain.name, res.seqid.num, res.seqid.icode.strip())
            counts[key] = counts.get(key, 0) + 1
    for chain in st[0]:
        for i, res in enumerate(chain.get_polymer()):
            key = (chain.name, res.seqid.num, res.seqid.icode.strip())
            if res.name in AMINO and res.entity_type == gemmi.EntityType.Polymer \
                    and counts[key] == 1 \
                    and all(a.altloc == "\0" and a.occ == 1.0 for a in res):
                out[key] = (res, i)
    return out


def record(key: tuple, res) -> dict:
    return {"auth_asym_id": key[0], "auth_seq_id": key[1], "pdbx_PDB_ins_code": key[2],
            "comp_id": res.name}


def one_atom(entry: str, selector: dict) -> bool:
    return C.n_atoms(C.mask_of(entry, selector)) == 1


def protein_chain_count(entry: str) -> int:
    return sum(c["polymer_type"] == "protein" for c in C.facts(entry)["chains"])


def res_name(entry: str, r: dict) -> str:
    """A residue as a prompt writes it: Ser195, with the chain when there are several."""
    text = f"{r['comp_id'].capitalize()}{r['auth_seq_id']}{r.get('pdbx_PDB_ins_code') or ''}"
    if len(C.facts(entry)["chains"]) > 1:
        text += f" of chain {r['auth_asym_id']}"
    return text


def side_chain_pairs(entry: str) -> list[tuple]:
    """Pairs of polar side-chain atoms (N or O) of two clean residues within
    ``HBOND_MAX`` of each other in the deposited model: (distance, residue a, atom a,
    residue b, atom b). Residues next to each other in the chain (fewer than three
    apart) are left out."""
    st = C.cif_structure(entry)
    ns = C._search(entry)
    clean = clean_residues(entry)
    found = {}
    for key, (res, idx) in clean.items():
        for a in res:
            if a.name in BACKBONE or a.element.name not in ("N", "O"):
                continue
            for mark in ns.find_atoms(a.pos, "\0", radius=HBOND_MAX):
                if mark.image_idx != 0:
                    continue
                cra = mark.to_cra(st[0])
                other = (cra.chain.name, cra.residue.seqid.num, cra.residue.seqid.icode.strip())
                if other == key or other not in clean or cra.residue is not clean[other][0] \
                        and clean[other][0].name != cra.residue.name:
                    continue
                b = cra.atom
                if b.name in BACKBONE or b.element.name not in ("N", "O"):
                    continue
                if other[0] == key[0] and abs(clean[other][1] - idx) < 3:
                    continue
                d = a.pos.dist(b.pos)
                if not HBOND_MIN <= d <= HBOND_MAX:
                    continue
                first, second = sorted([(key, a.name), (other, b.name)])
                found[(first, second)] = d
    out = []
    for ((ka, na), (kb, nb)), d in sorted(found.items()):
        out.append((d, record(ka, clean[ka][0]), na, record(kb, clean[kb][0]), nb))
    return out


def is_salt_bridge(a: dict, na: str, b: dict, nb: str) -> bool:
    x, y = (a["comp_id"], na), (b["comp_id"], nb)
    return (x in CATION and y in ANION) or (y in CATION and x in ANION)


def is_hydrogen_bond(a: dict, na: str, b: dict, nb: str) -> bool:
    """A donor and an acceptor by residue chemistry: donors are side-chain N atoms and
    the hydroxyl O of Ser, Thr and Tyr; acceptors are side-chain O atoms and the ring N
    of His. Charge pairs (Lys/Arg with Asp/Glu) are salt bridges, not counted here."""
    if is_salt_bridge(a, na, b, nb):
        return False

    def donor(r, n):
        return n.startswith("N") or (r["comp_id"], n) in HYDROXYL

    def acceptor(r, n):
        return n.startswith("O") or (r["comp_id"] == "HIS" and n in ("ND1", "NE2"))

    return (donor(a, na) and acceptor(b, nb)) or (donor(b, nb) and acceptor(a, na))


# --------------------------------------------------------------------------- #
# Templates
# --------------------------------------------------------------------------- #
def cand(entry, wordings, children, target, derivation, checks, measured, numbering=None,
         suffix="", flags=None, **words):
    return {"entry": entry, "wordings": wordings, "children": children, "target": target,
            "derivation": derivation, "checks": checks, "measured": measured,
            "numbering": numbering, "suffix": suffix, "flags": flags or {}, "words": words}


def grey_cartoon() -> dict:
    return C.drawn_comp("polymer", "cartoon", GREY)


def measure(entry: str, a: dict, na: str, b: dict, nb: str) -> dict:
    """One measured pair for ``provenance.measured``, re-read from the frozen mmCIF."""
    sa, sb = C.atom(a, na), C.atom(b, nb)
    if a.get("by_comp"):
        sa = {"label_comp_id": a["comp_id"], "label_atom_id": na}
    if b.get("by_comp"):
        sb = {"label_comp_id": b["comp_id"], "label_atom_id": nb}
    assert one_atom(entry, sa) and one_atom(entry, sb), f"{entry}: {sa} / {sb} is not one atom each"
    return {"start": sa, "end": sb,
            "distance_A": round(C.cif_distance(entry, a, na, b, nb), 2)}


def pair_task(entry, kind, a, na, b, nb, d, col, wordings, what):
    """Two residues as ball-and-stick on a grey cartoon, a labelled dashed line between
    two of their atoms, and the camera on the two residues."""
    m = measure(entry, a, na, b, nb)
    assert abs(m["distance_A"] - d) < 0.006, (entry, m, d)
    rsel = [C.residue(a), C.residue(b)]
    return cand(
        entry, wordings,
        [grey_cartoon(), C.comp(rsel, C.rep("ball_and_stick", C.colour(col)), C.FOCUS),
         C.primitives(C.distance(m["start"], m["end"]))],
        [C.part(rsel, "ball_and_stick", col)],
        f"{what}: {a['comp_id']}{a['auth_seq_id']} {na} and {b['comp_id']}{b['auth_seq_id']} "
        f"{nb}, {m['distance_A']:.2f} A apart in the frozen mmCIF. Both residues as "
        "ball-and-stick on a grey cartoon, a dashed line between the two atoms labelled "
        "with its length, camera on the two residues",
        ["each end of the line resolves to exactly one atom of the atom table",
         "both residues are standard amino acids with no alternate conformer and full "
         "occupancy"],
        [m], numbering=rsel,
        A=res_name(entry, a), B=res_name(entry, b), na=na, nb=nb, c=C.say_colour(col))


HBOND_WORDINGS = [
    "Load {ID} as a grey cartoon. Show {A} and {B} as {c} ball-and-stick, draw the hydrogen "
    "bond between the {na} atom of {A} and the {nb} atom of {B} as a dashed line labelled "
    "with its length, and zoom in on the two residues.",
    "In {ID} (grey cartoon), show the side-chain hydrogen bond from {na} of {A} to {nb} of {B}: "
    "both residues in {c} ball-and-stick, a dashed line between the two atoms with the "
    "distance as its label, and the view centred on the pair.",
    "{ID}: grey cartoon; {A} and {B} as {c} ball-and-stick; measure the hydrogen bond "
    "between {na} of {A} and {nb} of {B} with a labelled dashed line; focus the camera on "
    "these two residues.",
]
SALT_WORDINGS = [
    "Load {ID} as a grey cartoon. Show {A} and {B} as {c} ball-and-stick, draw the salt "
    "bridge between the {na} atom of {A} and the {nb} atom of {B} as a dashed line labelled "
    "with its length, and zoom in on the two residues.",
    "In {ID} (grey cartoon), show the salt bridge between {A} and {B}: both residues in "
    "{c} ball-and-stick, a dashed line from {na} of {A} to {nb} of {B} with the distance as its "
    "label, and the view centred on the pair.",
    "{ID}: grey cartoon; {A} and {B} as {c} ball-and-stick; measure the salt bridge "
    "between {na} of {A} and {nb} of {B} with a labelled dashed line; focus the camera on "
    "these two residues.",
]


def t_hbond():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        if C.facts(entry)["n_models"] != 1 or not protein_chain_count(entry):
            continue
        pairs = [p for p in side_chain_pairs(entry) if is_hydrogen_bond(*p[1:])
                 and p[0] <= 3.0]
        if not pairs:
            continue
        d, a, na, b, nb = C.pick(pairs, "in-hbond", entry)
        col = C.colours(1, "in-hbond", entry)[0]
        out.append(pair_task(entry, "hbond", a, na, b, nb, round(d, 2), col, HBOND_WORDINGS,
                             "a side-chain hydrogen bond found by neighbour search (a donor "
                             f"and an acceptor atom {HBOND_MIN}-3.0 A apart)"))
    return out


def t_salt_bridge():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        if C.facts(entry)["n_models"] != 1 or not protein_chain_count(entry):
            continue
        pairs = [p for p in side_chain_pairs(entry) if is_salt_bridge(*p[1:])]
        if not pairs:
            continue
        d, a, na, b, nb = C.pick(pairs, "in-salt", entry)
        col = C.colours(1, "in-salt", entry)[0]
        out.append(pair_task(entry, "salt", a, na, b, nb, round(d, 2), col, SALT_WORDINGS,
                             "a salt bridge found by neighbour search (a Lys or Arg "
                             "side-chain nitrogen and an Asp or Glu carboxylate oxygen "
                             f"{HBOND_MIN}-{HBOND_MAX} A apart)"))
    return out


def t_disulfide():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        f = C.facts(entry)
        if f["n_models"] != 1:
            continue
        clean = clean_residues(entry)
        bonds = [b for b in f["disulfides"] if not b["to_symmetry_copy"]
                 and C.rkey(b["a"]) in clean and C.rkey(b["b"]) in clean]
        if not bonds:
            continue
        b = C.pick(bonds, "in-disulfide", entry)
        a_, b_ = b["a"], b["b"]
        d = round(C.cif_distance(entry, a_, "SG", b_, "SG"), 2)
        if not 1.9 < d < 2.3:
            continue
        col = C.colours(1, "in-disulfide", entry)[0]
        out.append(pair_task(
            entry, "disulfide", a_, "SG", b_, "SG", d, col,
            ["Load {ID} as a grey cartoon. Show the disulfide between {A} and {B}: both "
             "cysteines as {c} ball-and-stick, with the sulfur-sulfur distance measured as a "
             "dashed line (SG to SG) labelled with its length, and zoom in on the bridge.",
             "In {ID} (grey cartoon), measure the S-S bond of the disulfide between {A} and {B}: the two "
             "cysteines in {c} ball-and-stick, a labelled dashed line between their SG atoms, "
             "and the view centred on them.",
             "{ID}: grey cartoon; cysteines {A} and {B} as {c} ball-and-stick; a dashed line "
             "with the distance between their two SG atoms; camera on the two residues."],
            "a disulfide record of the facts (`_struct_conn`, `disulf`), sulfur to sulfur"))
    return out


def t_ca_distance():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        if C.facts(entry)["n_models"] != 1:
            continue
        clean = clean_residues(entry)
        chains = sorted({k[0] for k in clean})
        if not chains:
            continue
        chain = C.pick(chains, "in-ca-chain", entry)
        keys = sorted((k for k in clean if k[0] == chain and not k[2]), key=lambda k: clean[k][1])
        if len(keys) < 30:
            continue
        r = C.rng("in-ca", entry)
        pair = None
        for _ in range(200):
            ka, kb = sorted(r.sample(keys, 2), key=lambda k: clean[k][1])
            if clean[kb][1] - clean[ka][1] < 10:
                continue
            a, b = record(ka, clean[ka][0]), record(kb, clean[kb][0])
            d = C.cif_distance(entry, a, "CA", b, "CA")
            if 6.0 <= d <= 30.0:
                pair = (a, b, round(d, 2))
                break
        if pair is None:
            continue
        a, b, d = pair
        m = measure(entry, a, "CA", b, "CA")
        rsel = [C.residue(a), C.residue(b)]
        col = C.colours(1, "in-ca", entry)[0]
        out.append(cand(
            entry,
            ["Load {ID} as a {c} cartoon and measure the distance between the alpha carbons "
             "of {A} and {B}: a dashed line between the two CA atoms, labelled with its "
             "length.",
             "Show {ID} as a {c} cartoon. Add a distance measurement (dashed line with the "
             "value as label) from the CA atom of {A} to the CA atom of {B}.",
             "{ID}, {c} cartoon; how far apart are the C-alpha atoms of {A} and {B}? Draw the "
             "distance as a labelled dashed line."],
            [C.drawn_comp("polymer", "cartoon", col), C.primitives(C.distance(m["start"], m["end"]))],
            [C.part([m["start"], m["end"]], None, None)],
            f"two residues of chain {chain} chosen by seed (at least 10 apart in sequence, "
            f"CA atoms 6-30 A apart): {a['comp_id']}{a['auth_seq_id']} and "
            f"{b['comp_id']}{b['auth_seq_id']}, {d:.2f} A in the frozen mmCIF. A cartoon of "
            "the polymer and one labelled dashed line between the two CA atoms",
            ["each end of the line resolves to exactly one atom of the atom table"],
            [m], numbering=rsel, A=res_name(entry, a), B=res_name(entry, b),
            c=C.say_colour(col)))
    return out


def single_metal_sites(entry: str) -> list[dict]:
    """Metal atoms a prompt can name without a residue number: the only copy of a metal
    ion in the entry, or the iron of the entry's only heme. Each with its coordinating
    polymer atoms from the facts, checked as in the grounded tier."""
    f = C.facts(entry)
    out = []
    groups = []
    for g in f["ligands"]:
        if len(g["copies"]) != 1:
            continue
        if g.get("heme"):
            groups.append((g, "FE", "heme iron", "heme"))
        elif g["comp_id"] in G.METAL_WORDS and g["n_heavy_atoms"] == 1:
            groups.append((g, g["comp_id"], f"{G.METAL_WORDS[g['comp_id']]} ion", None))
    for g, atom_name, word, heme in groups:
        comp = g["comp_id"]
        bonds = [b for b in f["metal_bonds"]
                 if any(x["comp_id"] == comp and x["atom"] == atom_name for x in (b["a"], b["b"]))]
        if not bonds or any(b["to_symmetry_copy"] for b in bonds):
            continue
        partners = []
        for b in bonds:
            other = b["b"] if (b["a"]["comp_id"] == comp and b["a"]["atom"] == atom_name) else b["a"]
            if G.polymer_record(entry, other):
                partners.append(other)
        if not 1 <= len(partners) <= 5:
            continue
        near = C.cif_neighbours(entry, g["copies"], atom_name, 2.6)
        if near != {C.rkey(p) for p in partners}:
            continue
        if any(len(C.cif_atoms(entry, p, p["atom"])) != 1 for p in partners) \
                or len(C.cif_atoms(entry, g["copies"][0], atom_name)) != 1:
            continue
        out.append({"group": g, "atom": atom_name, "word": word, "heme": heme,
                    "partners": partners})
    return out


def t_metal_contact():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        if C.facts(entry)["n_models"] != 1:
            continue
        sites = single_metal_sites(entry)
        if not sites:
            continue
        s = C.pick(sites, "in-metal", entry)
        g, partners = s["group"], s["partners"]
        metal_rec = {**g["copies"][0], "by_comp": True}
        measured = [measure(entry, metal_rec, s["atom"], p, p["atom"]) for p in partners]
        if max(m["distance_A"] for m in measured) > 3.0:
            continue
        msel = {"label_comp_id": g["comp_id"]}
        rsel = [C.residue(p) for p in partners]
        c1, c2 = C.colours(2, "in-metal", entry)
        atoms = C.join([f"{p['atom']} of {res_name(entry, p)}" for p in partners])
        n = len(partners)
        focus_sel = [msel] + rsel
        out.append(cand(
            entry,
            ["Load {ID} as a grey cartoon. Show the {group} as {c1} {rep} and {residues} as "
             "{c2} ball-and-stick. Draw a dashed line, labelled with its length, from the "
             "{metal} to {atoms}, and zoom in on the site.",
             "In {ID} (grey cartoon), show the {metal} site: the {group} as {c1} {rep}, "
             "{residues} in {c2} ball-and-stick, and the metal-ligand {distances} from the "
             "{metal} to {atoms} as {a_line}. Centre the view on the site.",
             "{ID}: grey cartoon; {group} as {c1} {rep}; {residues} as {c2} ball-and-stick; "
             "measure the distance from the {metal} to {atoms} with {a_line}; focus on these groups."],
            [grey_cartoon(),
             C.drawn_comp(msel, "ball_and_stick" if s["heme"] else "spacefill", c1),
             C.drawn_comp(rsel, "ball_and_stick", c2),
             C.comp(focus_sel, C.FOCUS),
             C.primitives(*[C.distance(m["start"], m["end"]) for m in measured])],
            [C.part(focus_sel, None, None)],
            f"the metal-coordination records (`_struct_conn`, `metalc`) of the facts between "
            f"the {s['word']} and polymer atoms: "
            + "; ".join(f"{p['comp_id']}{p['auth_seq_id']} {p['atom']} "
                        f"{m['distance_A']:.2f} A" for p, m in zip(partners, measured))
            + ". The metal group and the residues are drawn, one labelled dashed line per "
              "bond, camera on the site",
            ["each end of every line resolves to exactly one atom of the atom table",
             "a neighbour search (with crystal symmetry) finds exactly these residues, and "
             "no other polymer N, O or S atom, within 2.6 A of the metal",
             f"the metal is the only {g['comp_id']} in the entry, so the prompt's name for "
             "it is unambiguous"],
            measured, numbering=rsel, suffix=g["comp_id"].lower(),
            flags={"ligand_identity": bool(s["heme"])},
            group="heme" if s["heme"] else s["word"],
            rep="ball-and-stick" if s["heme"] else "sphere", metal=s["word"],
            residues=C.join([res_name(entry, p) for p in partners]), atoms=atoms,
            a_line="a labelled dashed line" if n == 1 else "labelled dashed lines",
            distances="distance" if n == 1 else "distances",
            c1=C.say_colour(c1) if s["heme"] else C.article(C.say_colour(c1)) + C.say_colour(c1),
            c2=C.say_colour(c2)))
    return out


def named_single_ligands(entry: str) -> list[tuple[dict, str]]:
    """Ligands a prompt can name: exactly one copy in the entry, with a checked name."""
    out = []
    for g in C.facts(entry)["ligands"]:
        if len(g["copies"]) != 1 or g["n_heavy_atoms"] < 6:
            continue
        named = G.checked_name(G.LIGAND_NAMES, g["comp_id"], entry)
        if g.get("heme"):
            out.append((g, "heme"))
        elif named:
            out.append((g, named[0]))
    return out


def ligand_contacts(entry: str, g: dict) -> list[tuple]:
    """Polar contacts between a ligand and clean protein residues: a ligand N or O atom
    and a protein N or O atom ``HBOND_MIN``-``HBOND_MAX`` apart, except oxygen-oxygen
    pairs where the protein oxygen is not a hydroxyl (two acceptors)."""
    st = C.cif_structure(entry)
    ns = C._search(entry)
    clean = clean_residues(entry)
    copy = g["copies"][0]
    out = []
    for name in g["atoms"]:
        atoms = C.cif_atoms(entry, copy, name)
        if len(atoms) != 1 or atoms[0].element.name not in ("N", "O") or atoms[0].occ != 1.0:
            continue
        a = atoms[0]
        for mark in ns.find_atoms(a.pos, "\0", radius=HBOND_MAX):
            if mark.image_idx != 0:
                continue
            cra = mark.to_cra(st[0])
            key = (cra.chain.name, cra.residue.seqid.num, cra.residue.seqid.icode.strip())
            if key not in clean or clean[key][0].name != cra.residue.name:
                continue
            b = cra.atom
            if b.element.name not in ("N", "O"):
                continue
            if a.element.name == "O" and b.element.name == "O" \
                    and (cra.residue.name, b.name) not in HYDROXYL:
                continue
            d = a.pos.dist(b.pos)
            if HBOND_MIN <= d <= HBOND_MAX:
                out.append((d, name, record(key, cra.residue), b.name))
    return sorted(out, key=lambda x: (x[1], C.rkey(x[2]), x[3]))


def t_ligand_contact():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        if C.facts(entry)["n_models"] != 1:
            continue
        options = []
        for g, name in named_single_ligands(entry):
            for contact in ligand_contacts(entry, g):
                options.append((g, name, contact))
        if not options:
            continue
        g, name, (d, lname, res, rname) = options[C.rng("in-ligand", entry).randrange(len(options))]
        lig = {**g["copies"][0], "by_comp": True}
        m = measure(entry, lig, lname, res, rname)
        lsel = {"label_comp_id": g["comp_id"]}
        rsel = C.residue(res)
        c1, c2 = C.colours(2, "in-ligand", entry)
        out.append(cand(
            entry,
            ["Load {ID} as a grey cartoon. Show the {name} as {c1} ball-and-stick and {R} as "
             "{c2} ball-and-stick, draw the polar contact between atom {la} of the {name} and "
             "the {ra} atom of {R} as a dashed line labelled with its length, and zoom in on "
             "the two.",
             "In {ID} (grey cartoon), show how the {name} contacts {R}: the {name} in {c1} "
             "ball-and-stick, {R} in {c2} ball-and-stick, a dashed line from {name} atom {la} "
             "to {ra} of {R} with the distance as its label, and the view centred on the two.",
             "{ID}: grey cartoon; {name} as {c1} ball-and-stick; {R} as {c2} ball-and-stick; "
             "measure the contact between {name} atom {la} and {ra} of {R} with a labelled dashed line; focus "
             "the camera on the ligand and the residue."],
            [grey_cartoon(), C.drawn_comp(lsel, "ball_and_stick", c1),
             C.drawn_comp(rsel, "ball_and_stick", c2), C.comp([lsel, rsel], C.FOCUS),
             C.primitives(C.distance(m["start"], m["end"]))],
            [C.part([lsel, rsel], None, None)],
            f"a polar contact found by neighbour search between the entry's only "
            f"{g['comp_id']} ({name}) and a protein residue: {g['comp_id']} {lname} and "
            f"{res['comp_id']}{res['auth_seq_id']} {rname}, {m['distance_A']:.2f} A apart in "
            "the frozen mmCIF. Ligand and residue as ball-and-stick on a grey cartoon, one "
            "labelled dashed line, camera on the two",
            ["each end of the line resolves to exactly one atom of the atom table",
             f"the ligand is the only {g['comp_id']} in the entry; its name was checked "
             "against the frozen component record or the entry title"],
            [m], numbering=rsel, suffix=g["comp_id"].lower(),
            flags={"ligand_identity": name.upper() != g["comp_id"]},
            name=name, la=lname, ra=rname, R=res_name(entry, res),
            c1=C.say_colour(c1), c2=C.say_colour(c2)))
    return out


def t_computed():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        if C.facts(entry)["n_models"] != 1 or not protein_chain_count(entry):
            continue
        ligands = named_single_ligands(entry)
        if not ligands:
            continue
        g, name = C.pick(ligands, "in-computed", entry)
        sel = {"label_comp_id": g["comp_id"]}
        col = C.colours(1, "in-computed", entry)[0]
        out.append(cand(
            entry,
            ["Load {ID} as a grey cartoon, show the {name} as {c} ball-and-stick, turn on the "
             "viewer's non-covalent interaction display for the {name} (hydrogen bonds and "
             "other contacts with its surroundings), and zoom in on the {name}.",
             "In {ID} (grey cartoon), show the {name} in {c} ball-and-stick and let Mol* "
             "compute and draw its non-covalent interactions with the protein. Centre the "
             "view on the {name}.",
             "{ID}: grey cartoon; {name} as {c} ball-and-stick with its computed non-covalent "
             "interactions shown; camera on the {name}."],
            [grey_cartoon(),
             C.comp(sel, C.rep("ball_and_stick", C.colour(col)), C.FOCUS,
                    custom={"molstar_show_non_covalent_interactions": True})],
            [C.part(sel, "ball_and_stick", col)],
            f"the entry's only {g['comp_id']} ({name}) as ball-and-stick on a grey cartoon, "
            "with Mol*'s computed non-covalent interactions switched on for that component "
            "(`molstar_show_non_covalent_interactions`, default radius) and the camera on it. "
            "Which contacts Mol* then draws is the viewer's computation, not part of the "
            "reference",
            [f"the ligand is the only {g['comp_id']} in the entry; its name was checked "
             "against the frozen component record or the entry title"],
            [], suffix=g["comp_id"].lower(),
            flags={"ligand_identity": name.upper() != g["comp_id"]},
            name=name, c=C.say_colour(col)))
    return out


def t_transparent():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        t = C.table(entry)
        if C.facts(entry)["n_models"] != 1 or e["atoms"] > 6000 \
                or t.static.get("polymer") != t.static.get("protein"):
            continue
        ligands = named_single_ligands(entry)
        if not ligands:
            continue
        g, name = C.pick(ligands, "in-transparent", entry)
        sel = {"label_comp_id": g["comp_id"]}
        c1, c2 = C.colours(2, "in-transparent", entry)
        opacity = C.pick([0.3, 0.4, 0.5], "in-transparent-opacity", entry)
        out.append(cand(
            entry,
            ["Load {ID}; show the protein as a {c1} surface at {pct}% opacity and the {name} "
             "inside it as {c2} ball-and-stick.",
             "Show {ID} with a semi-transparent {c1} protein surface (opacity {op}) so that "
             "the {name}, drawn in {c2} ball-and-stick, can be seen through it.",
             "{ID}: protein surface in {c1}, {pct}% opaque; {name} as {c2} ball-and-stick."],
            [C.drawn_comp("polymer", "surface", c1, opacity=opacity),
             C.drawn_comp(sel, "ball_and_stick", c2)],
            [C.part(sel, "ball_and_stick", c2)],
            f"the polymer (protein only in this entry) as a surface with opacity {opacity}, "
            f"and the entry's only {g['comp_id']} ({name}) as opaque ball-and-stick",
            [f"the ligand is the only {g['comp_id']} in the entry; its name was checked "
             "against the frozen component record or the entry title"],
            [], suffix=g["comp_id"].lower(),
            flags={"ligand_identity": name.upper() != g["comp_id"]},
            name=name, c1=C.say_colour(c1), c2=C.say_colour(c2),
            pct=round(opacity * 100), op=opacity))
    return out


TEMPLATES = {
    "in-metal-contact": (t_metal_contact, 5),
    "in-ligand-contact": (t_ligand_contact, 5),
    "in-computed": (t_computed, 5),
    "in-transparent": (t_transparent, 5),
    "in-disulfide": (t_disulfide, 5),
    "in-salt-bridge": (t_salt_bridge, 5),
    "in-hbond": (t_hbond, 5),
    "in-ca-distance": (t_ca_distance, 5),
}

DERIVED = {
    "in-hbond": "A side-chain donor and acceptor atom of two residues 2.5-3.0 A apart "
                "(gemmi neighbour search; donors: side-chain N, hydroxyl O of Ser/Thr/Tyr; "
                "acceptors: side-chain O, His ring N; not a charge pair; at least three "
                "residues apart). One pair per entry, by seed.",
    "in-salt-bridge": "A Lys NZ or Arg NE/NH1/NH2 and an Asp or Glu carboxylate oxygen "
                      "2.5-3.2 A apart (neighbour search). One pair per entry, by seed.",
    "in-disulfide": "One `disulf` record of the facts; SG-SG re-measured (1.9-2.3 A).",
    "in-metal-contact": "The `metalc` records between the entry's only copy of a metal ion "
                        "(or the iron of its only heme) and polymer atoms; neighbour search "
                        "within 2.6 A, with symmetry, must agree. One line per bond.",
    "in-ligand-contact": "A ligand N or O atom and a protein N or O atom 2.5-3.2 A apart "
                         "(neighbour search; not two plain acceptor oxygens), for the only "
                         "copy of a named ligand. One contact per entry, by seed.",
    "in-ca-distance": "Two residues of one chain, by seed (10 or more apart in sequence, CA "
                      "atoms 6-30 A apart); the line joins the two CA atoms.",
    "in-computed": "The only copy of a named ligand with Mol*'s computed non-covalent "
                   "interactions switched on for it, and the camera on it.",
    "in-transparent": "Protein surface with the stated opacity (0.3, 0.4 or 0.5) over the "
                      "only copy of a named ligand in ball-and-stick.",
}


def build() -> list[dict]:
    picker = C.Picker(TIER)
    built = []
    for family, (fn, n) in TEMPLATES.items():
        chosen = picker.choose(family, fn(), n, entry_of=lambda c: c["entry"])
        C.enough(family, chosen, n)
        for c in chosen:
            entry = c["entry"]
            tid = f"{family}-{entry}" + (f"-{c['suffix']}" if c["suffix"] else "")
            wording = C.pick(c["wordings"], "wording", family, tid)
            prompt = wording.format(ID=entry.upper(), **c["words"])
            built.append(C.make_task(
                tid, TIER, family, entry, prompt, C.scene(entry, c["children"]), c["target"],
                script=SCRIPT, input_files=C.inputs(entry, C.cif_input(entry)),
                derivation=c["derivation"], checks=c["checks"],
                difficulty=C.difficulty(entry, c["numbering"], **c["flags"]),
                provenance={"measured": c["measured"]}))
    return sorted(built, key=lambda t: t["id"])


def readme(built: list[dict]) -> str:
    rows = "\n".join(f"| `{f}` | {DERIVED[f]} |" for f in sorted(DERIVED))
    n_lines = sum(len(t["provenance"]["measured"]) for t in built)
    return f"""# Interactions tier (MVS track)

Generated by `scripts/author_interaction_tasks.py`; do not edit by hand. Named atoms
and a measurement or contact between them. The prompt names the atoms (PDB atom names,
author residue numbers), so the reference is fully determined; the script finds the
pairs in the frozen mmCIF with gemmi and writes each measured distance into
`provenance.measured` ({n_lines} measured lines in this tier, each end checked to
resolve to exactly one atom of the frozen atom table).

The human raters of the first study could not see what an interaction reference was
about (it was not framed), so every contact task here asks for the view to be centred
on the atoms involved, and the reference has that camera focus. The C-alpha distance
and transparency templates have no focus, because their subject is the whole molecule.

{C.summary_tables(built)}

## How each reference is derived

| template | reference |
|---|---|
{rows}

Only residues that can be named without doubt are used: standard amino acids, full
occupancy, no alternate conformer. A measured line is graded by the two atoms it joins
(either direction); its label text, dash length and colour are styling and are not
graded. What Mol* draws for `in-computed` is the viewer's own computation; the graded
fact is that the display is switched on for the right atoms.

Replaces the six hand-written interaction tasks (`int-001` to `int-006`): the same
requests are now templates, with atoms found and checked by script.
"""


def main() -> int:
    args = C.cli(__doc__)
    built = C.verify(build(), OUT)
    return C.write_all(built, OUT, args.check, readme(built))


if __name__ == "__main__":
    raise SystemExit(main())
