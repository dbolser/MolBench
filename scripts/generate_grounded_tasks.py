#!/usr/bin/env python3
"""
Grounded-tier MVS tasks (``tasks/mvs_grounded/``): the request names something that
has to be found in the structure - the heme, the disulfide-bonded cysteines, the
residues holding the zinc, the catalytic residues - and gives no residue numbers.

Every reference is extracted by this script from frozen data and checked against the
frozen mmCIF with gemmi (bond lengths re-measured, neighbour searches around metals,
secondary-structure records re-read). Templates, counts and how each reference is
derived: ``tasks/mvs_grounded/README.md`` (written by this script).

    uv run python scripts/generate_grounded_tasks.py            # rewrite tasks/mvs_grounded/
    uv run python scripts/generate_grounded_tasks.py --check    # fail if the files would change
    uv run python scripts/generate_grounded_tasks.py --refresh  # re-download the two frozen
                                                                # inputs below (network)

Frozen inputs beyond the panel (``data/mvscore/``, written by ``--refresh``):

* ``chem_comp.json`` - name and synonyms of every non-polymer and modified-residue
  component of the panel, from the RCSB chemical component records. A compound is named
  in a prompt only by a name found there or in the entry's own title.
* ``uniprot_sites.json`` - the "Active site" features of the panel's UniProt entries:
  the authoritative source of the catalytic residues. Positions are mapped to structure
  residues through the frozen SIFTS tables, and a residue is used only if the structure
  has the amino acid UniProt has there.

Without ``--refresh`` nothing touches the network.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import mvscore_common as C  # noqa: E402
from molbench import grounding, sifts  # noqa: E402

OUT = C.REPO / "tasks" / "mvs_grounded"
SCRIPT = "scripts/generate_grounded_tasks.py"
TIER = "grounded"
GREY = "gray"
CHEM = C.DATA / "chem_comp.json"
SITES = C.DATA / "uniprot_sites.json"

# --------------------------------------------------------------------------- #
# Hand-written wording (checked by script; never a reference)
# --------------------------------------------------------------------------- #
# The name a prompt uses for a compound. `ligand_name` refuses a name that is not a
# whole phrase of the component's frozen name or synonyms, or of the entry's title.
LIGAND_NAMES = {
    "REA": "retinoic acid", "BTN": "biotin", "BEN": "benzamidine", "OHT": "4-hydroxytamoxifen",
    "STI": "imatinib", "VIA": "sildenafil", "FOL": "folic acid", "NAP": "NADP", "CAM": "camphor",
    "RET": "retinal", "ADE": "adenine", "AP5": "AP5A", "GNP": "GppNHp", "ZMA": "ZM241385",
    "KN9": "KN93", "HC4": "p-coumaric acid", "DXX": "methylmalonic acid", "GLC": "glucose",
    "ATP": "ATP",
}
MODRES_NAMES = {
    "TPO": "phosphothreonine", "SEP": "phosphoserine", "PTR": "phosphotyrosine",
    "MSE": "selenomethionine", "CSO": "S-hydroxycysteine", "CRO": "chromophore",
    "CGU": "gamma-carboxy-glutamic acid",
}
METAL_WORDS = {"ZN": "zinc", "FE": "iron", "CU": "copper", "MN": "manganese", "CA": "calcium",
               "MG": "magnesium"}
# A metal site is asked only when nothing else sits between the annotated bonds (checked
# to 2.6 A) and this distance: a polymer N, O or S atom there is a weak ligand that the
# entry does not annotate and an expert may count.
AMBIGUOUS_REACH = 3.2
RESIDUE_WORDS = {"HIS": "histidine", "CYS": "cysteine", "MET": "methionine", "LYS": "lysine",
                 "ASN": "asparagine", "SER": "serine", "THR": "threonine"}
# What a prompt calls each polymer entity of a complex: entry -> [(pattern on the
# entity description of the facts, name, name when the entity has several chains)].
# `entity_groups` fails unless every pattern matches exactly one polymer entity.
ENTITY_NAMES = {
    "1aoi": [(r"HISTONE H3", "histone H3", "two H3 histones"),
             (r"HISTONE H4", "histone H4", "two H4 histones"),
             (r"HISTONE H2A", "histone H2A", "two H2A histones"),
             (r"HISTONE H2B", "histone H2B", "two H2B histones")],
    "1atp": [(r"PROTEIN KINASE", "kinase", None), (r"PEPTIDE INHIBITOR", "inhibitor peptide", None)],
    "1hho": [(r"ALPHA CHAIN", "alpha chain", None), (r"BETA CHAIN", "beta chain", None)],
    "2hhb": [(r"ALPHA CHAIN", "alpha chain", "alpha chains"),
             (r"BETA CHAIN", "beta chain", "beta chains")],
    "5ni1": [(r"subunit alpha", "alpha subunit", "alpha subunits"),
             (r"subunit beta", "beta subunit", "beta subunits")],
    "1k4c": [(r"Fab fragment heavy chain", "Fab heavy chain", None),
             (r"Fab fragment light chain", "Fab light chain", None),
             (r"potassium channel KcsA", "KcsA channel subunit", None)],
    "2ptc": [(r"^BETA-TRYPSIN$", "trypsin", None), (r"TRYPSIN INHIBITOR", "trypsin inhibitor", None)],
    "3kcg": [(r"factor IXa light chain", "factor IXa light chain", None),
             (r"factor IXa heavy chain", "factor IXa heavy chain", None),
             (r"Antithrombin", "antithrombin", None)],
    "4ins": [(r"INSULIN \(CHAIN A\)", "insulin A chain", "insulin A chains"),
             (r"INSULIN \(CHAIN B\)", "insulin B chain", "insulin B chains")],
    "8eph": [(r"factor IXa light chain", "factor IXa light chain", "factor IXa light chains"),
             (r"factor IXa heavy chain", "factor IXa heavy chain", "factor IXa heavy chains")],
    "9gio": [(r"Elongin-B", "elongin B", None), (r"Elongin-C", "elongin C", None),
             (r"von Hippel-Lindau", "VHL protein", None)],
    "5cj6": [(r"Androgen receptor", "androgen receptor", None), (r"small peptide", "bound peptide", None)],
}
ONE_TO_THREE = {"A": "ALA", "R": "ARG", "N": "ASN", "D": "ASP", "C": "CYS", "Q": "GLN",
                "E": "GLU", "G": "GLY", "H": "HIS", "I": "ILE", "L": "LEU", "K": "LYS",
                "M": "MET", "F": "PHE", "P": "PRO", "S": "SER", "T": "THR", "W": "TRP",
                "Y": "TYR", "V": "VAL"}


# --------------------------------------------------------------------------- #
# Frozen extra inputs
# --------------------------------------------------------------------------- #
def refresh() -> None:
    """Download and freeze chem_comp.json and uniprot_sites.json (free public APIs)."""
    import datetime
    import urllib.request

    def get(url: str) -> dict:
        req = urllib.request.Request(url, headers={"Accept": "application/json",
                                                   "User-Agent": "molbench-build"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)

    today = datetime.date.today().isoformat()
    comps: set[str] = set()
    accessions: set[str] = set()
    for e in grounding.panel()["entries"]:
        f = grounding.facts(e["id"])
        comps |= {g["comp_id"] for g in f["ligands"]} | {m["comp_id"] for m in f["modified_residues"]}
        accessions |= {a.split("-")[0] for a in e.get("uniprot", [])}
    chem = {}
    for comp in sorted(comps):
        d = get(f"https://data.rcsb.org/rest/v1/core/chemcomp/{comp}")
        names = sorted({s["name"] for s in d.get("rcsb_chem_comp_synonyms") or []})
        chem[comp] = {"name": d["chem_comp"]["name"], "synonyms": names}
    C.DATA.mkdir(parents=True, exist_ok=True)
    CHEM.write_text(json.dumps(
        {"source": "https://data.rcsb.org/rest/v1/core/chemcomp/<id> (chem_comp.name, "
                   "rcsb_chem_comp_synonyms)", "retrieved": today, "components": chem},
        indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    sites = {}
    for acc in sorted(accessions):
        d = get(f"https://rest.uniprot.org/uniprotkb/{acc}.json?fields=accession,id,ft_act_site")
        sites[acc] = {"id": d["uniProtkbId"], "active_sites": [
            {"position": f["location"]["start"]["value"], "description": f.get("description", "")}
            for f in d.get("features", [])
            if f["type"] == "Active site"
            and f["location"]["start"]["value"] == f["location"]["end"]["value"]]}
    SITES.write_text(json.dumps(
        {"source": "https://rest.uniprot.org/uniprotkb/<accession>.json?fields=ft_act_site "
                   "(features of type 'Active site')", "retrieved": today, "accessions": sites},
        indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"froze {len(chem)} components and {len(sites)} UniProt entries on {today}")


def chem() -> dict:
    return json.loads(CHEM.read_text(encoding="utf-8"))["components"]


def uniprot_sites() -> dict:
    return json.loads(SITES.read_text(encoding="utf-8"))["accessions"]


def _phrase_in(name: str, text: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9]){re.escape(name)}(?![A-Za-z0-9])", text, re.I) is not None


def checked_name(table: dict, comp: str, entry: str) -> tuple[str, str] | None:
    """The hand-written name of a component and where it was found: in the component's
    frozen name or synonyms, or in the entry's title. None if there is no name for it;
    an error if the name is found nowhere."""
    name = table.get(comp)
    if name is None:
        return None
    if name.upper() == comp:
        return name, "the component code itself"
    rec = chem()[comp]
    if any(_phrase_in(name, s) for s in [rec["name"], *rec["synonyms"]]):
        return name, "the component's name or synonyms (data/mvscore/chem_comp.json)"
    if _phrase_in(name, C.facts(entry)["title"]):
        return name, f"the title of {entry.upper()}"
    raise SystemExit(f"{comp}: the name {name!r} is in neither chem_comp.json nor the title "
                     f"of {entry}")


# --------------------------------------------------------------------------- #
# Checks against the frozen mmCIF (gemmi)
# --------------------------------------------------------------------------- #
def cand(entry, wordings, children, target, derivation, checks, numbering=None,
         extra_inputs=(), suffix="", flags=None, more=None, **words):
    return {"entry": entry, "wordings": wordings, "children": children, "target": target,
            "derivation": derivation, "checks": checks, "numbering": numbering,
            "extra_inputs": [C.cif_input(entry), *extra_inputs], "suffix": suffix,
            "flags": flags or {}, "more": more or {}, "words": words}


def grey_cartoon() -> dict:
    return C.drawn_comp("polymer", "cartoon", GREY)


def polymer_record(entry: str, r: dict) -> bool:
    return bool(C.mask_of(entry, C.residue(r)) & C.table(entry).static.get("polymer", 0))


def measured(entry: str, a: dict, b: dict) -> float:
    """The distance between the two atoms of a bond record, re-measured in the frozen
    mmCIF (first conformer of each)."""
    return C.cif_distance(entry, a, a["atom"], b, b["atom"])


# --------------------------------------------------------------------------- #
# Templates
# --------------------------------------------------------------------------- #
def t_ligand():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        f = C.facts(entry)
        for g in f["ligands"]:
            named = checked_name(LIGAND_NAMES, g["comp_id"], entry)
            if named is None or f["n_models"] != 1 or g.get("heme"):
                continue
            name, where = named
            sel = {"label_comp_id": g["comp_id"]}
            n = len(g["copies"])
            col = C.colours(1, "g-ligand", entry, g["comp_id"])[0]
            atoms = C.n_atoms(C.mask_of(entry, sel))
            out.append(cand(
                entry,
                ["Load {ID}; show the {what} as a grey cartoon and the bound {name} as {c} "
                 "ball-and-stick.",
                 "Show {ID} as a grey cartoon with the {name} {mol} in {c} ball-and-stick.",
                 "In {ID}, draw the {what} as a grey cartoon and pick out the {name} in {c} "
                 "ball-and-stick."],
                [grey_cartoon(), C.drawn_comp(sel, "ball_and_stick", col)],
                [C.part(sel, "ball_and_stick", col)],
                f"the component whose frozen name matches the prompt's \"{name}\" is "
                f"{g['comp_id']} ({g['name']}); every copy of it ({n}) as ball-and-stick on a "
                "grey cartoon of the polymer",
                [f"the name \"{name}\" was found in {where}",
                 f"{g['comp_id']} has {n} cop{'y' if n == 1 else 'ies'} and {atoms} atoms in "
                 "the atom table, as the facts list"],
                extra_inputs=["data/mvscore/chem_comp.json"], suffix=g["comp_id"].lower(),
                flags={"ligand_identity": name.upper() != g["comp_id"]},
                what=tr_what(entry), name=name, c=C.say_colour(col),
                mol="molecule" if n == 1 else "molecules"))
    return out


def tr_what(entry: str) -> str:
    t = C.table(entry)
    if t.static.get("protein") and t.static["protein"] == t.static["polymer"]:
        return "protein"
    if not t.static.get("protein"):
        return "RNA" if {c["polymer_type"] for c in C.facts(entry)["chains"]} == {"RNA"} else "DNA"
    return "complex"


def heme_groups(entry: str) -> list[dict]:
    return [g for g in C.facts(entry)["ligands"] if g.get("heme")]


def t_heme():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        groups = heme_groups(entry)
        if not groups:
            continue
        sel = [{"label_comp_id": g["comp_id"]} for g in groups]
        sel = sel[0] if len(sel) == 1 else sel
        n = sum(len(g["copies"]) for g in groups)
        col = C.colours(1, "g-heme", entry)[0]
        rep = C.pick(["ball_and_stick", "spacefill"], "g-heme-rep", entry)
        out.append(cand(
            entry,
            ["Load {ID}; show the protein as a grey cartoon and the heme {groups} as {c} {rep}.",
             "Show {ID} as a grey cartoon with {its} heme {groups} in {c} {rep}.",
             "{ID}: grey cartoon for the protein, {c} {rep} for the heme{s}."],
            [grey_cartoon(), C.drawn_comp(sel, rep, col)],
            [C.part(sel, rep, col)],
            "the components the facts flag as heme ("
            + ", ".join(f"{g['comp_id']} x{len(g['copies'])}" for g in groups)
            + "), every copy, on a grey cartoon of the polymer",
            [f"{n} heme group(s) in the facts; each holds one iron atom in the frozen mmCIF "
             f"({iron_count(entry, groups)} found)"],
            flags={"ligand_identity": True},
            groups="group" if n == 1 else "groups", s="" if n == 1 else "s",
            its="its" if n == 1 else f"its {C.number(n)}", c=C.say_colour(col),
            rep=C.REP_WORDS[rep]))
    return out


def iron_count(entry: str, groups: list[dict]) -> int:
    n = 0
    for g in groups:
        for copy in g["copies"]:
            atoms = C.cif_atoms(entry, copy, "FE")
            assert len(atoms) == 1, f"{entry}: heme copy without exactly one FE"
            n += 1
    return n


def t_heme_axial():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        hemes = {g["comp_id"] for g in heme_groups(entry)}
        if not hemes:
            continue
        bonds = [b for b in C.facts(entry)["metal_bonds"]
                 if any(x["comp_id"] in hemes and x["atom"] == "FE" for x in (b["a"], b["b"]))]
        if any(b["to_symmetry_copy"] for b in bonds):
            continue
        partners, dists = [], []
        for b in bonds:
            other = b["b"] if b["a"]["comp_id"] in hemes else b["a"]
            if polymer_record(entry, other):
                partners.append(other)
                d = measured(entry, b["a"], b["b"])
                assert d < 2.8, f"{entry}: heme iron bond of {d:.2f} A"
                dists.append(f"{other['comp_id']}{other['auth_seq_id']} {other['atom']} {d:.2f} A")
        partners = C.unique(partners)
        if not partners:
            continue
        near = C.cif_neighbours(entry, [c for g in heme_groups(entry) for c in g["copies"]],
                                "FE", 2.6)
        assert near == {C.rkey(p) for p in partners}, \
            f"{entry}: polymer atoms within 2.6 A of a heme iron {near} are not the bonded set"
        hsel = [{"label_comp_id": h} for h in sorted(hemes)]
        hsel = hsel[0] if len(hsel) == 1 else hsel
        rsel = [C.residue(p) for p in partners]
        c1, c2 = C.colours(2, "g-heme-axial", entry)
        n = len(partners)
        n_heme = sum(len(g["copies"]) for g in heme_groups(entry))
        out.append(cand(
            entry,
            ["Load {ID}; show the protein as a grey cartoon, the heme{hs} as {c1} "
             "ball-and-stick, and the protein {residues} bonded to the heme iron{hs} as {c2} "
             "ball-and-stick.",
             "Show {ID} as a grey cartoon. Add the heme{hs} in {c1} ball-and-stick and, in "
             "{c2} ball-and-stick, the amino-acid {residues} that coordinate{vs} the iron.",
             "{ID}: grey cartoon; heme{hs} as {c1} ball-and-stick; the {residues} of the "
             "protein that bind{vs} the heme iron{hs} directly, as {c2} ball-and-stick."],
            [grey_cartoon(), C.drawn_comp(hsel, "ball_and_stick", c1),
             C.drawn_comp(rsel, "ball_and_stick", c2)],
            [C.part(rsel, "ball_and_stick", c2)],
            "the polymer residues with a metal-coordination record (`_struct_conn`, "
            "`metalc`) to a heme iron in the facts: "
            + ", ".join(f"{p['comp_id']}{p['auth_seq_id']} of chain {p['auth_asym_id']}"
                        for p in partners),
            ["each bond re-measured in the frozen mmCIF: " + "; ".join(dists),
             "a neighbour search finds no other polymer N, O or S atom within 2.6 A of a "
             "heme iron"],
            numbering=rsel, flags={"ligand_identity": True, "structure_lookup": True},
            hs="" if n_heme == 1 else "s", c1=C.say_colour(c1), c2=C.say_colour(c2),
            residues="residue" if n == 1 else "residues", vs="s" if n == 1 else ""))
    return out


def t_disulfides():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        f = C.facts(entry)
        bonds = f["disulfides"]
        if not 1 <= len(bonds) <= 12 or f["n_models"] != 1:
            continue
        ends = C.unique([x for b in bonds for x in (b["a"], b["b"])])
        assert all(x["comp_id"] == "CYS" and x["atom"] == "SG" for x in ends), entry
        dists = []
        for b in bonds:
            if not b["to_symmetry_copy"]:
                d = measured(entry, b["a"], b["b"])
                dists.append(d)
        if dists and not (1.9 < min(dists) and max(dists) < 2.3):
            continue                     # a stretched or broken bridge (1K4C: 2.72 A): not used
        close = C.cif_close_pairs(entry, "CYS", "SG", 2.5)
        listed = {frozenset((C.rkey(b["a"]), C.rkey(b["b"]))) for b in bonds
                  if not b["to_symmetry_copy"]}
        if close != listed:
            continue                     # an S-S contact the entry does not annotate
        sel = [C.residue(x) for x in ends]
        col = C.colours(1, "g-disulfides", entry)[0]
        n = len(bonds)
        out.append(cand(
            entry,
            ["Load {ID}; show the protein as a grey cartoon and the cysteines that form "
             "disulfide bonds as {c} ball-and-stick.",
             "Show {ID} as a grey cartoon and highlight its disulfide {bridges}: the bonded "
             "cysteines in {c} ball-and-stick.",
             "{ID}: grey cartoon, with every disulfide-bonded cysteine drawn in {c} "
             "ball-and-stick."],
            [grey_cartoon(), C.drawn_comp(sel, "ball_and_stick", col)],
            [C.part(sel, "ball_and_stick", col)],
            f"both cysteines of each of the {n} disulfide records (`_struct_conn`, `disulf`) "
            f"in the facts: {len(ends)} residues; free cysteines are not included",
            [f"S-S distances re-measured in the frozen mmCIF: {min(dists):.2f} to "
             f"{max(dists):.2f} A" if dists else "all bonds are to symmetry copies",
             "no other pair of cysteine SG atoms is within 2.5 A in the deposited model"],
            numbering=sel, flags={"structure_lookup": True},
            c=C.say_colour(col), bridges="bridge" if n == 1 else "bridges"))
    return out


def t_metal_site():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        f = C.facts(entry)
        if f["n_models"] != 1:
            continue
        for g in f["ligands"]:
            comp = g["comp_id"]
            if comp not in METAL_WORDS or g["n_heavy_atoms"] != 1 or len(g["copies"]) > 4:
                continue
            bonds = [b for b in f["metal_bonds"] if comp in (b["a"]["comp_id"], b["b"]["comp_id"])]
            if not bonds or any(b["to_symmetry_copy"] for b in bonds):
                continue
            partners, per_site, dists = [], {}, []
            for b in bonds:
                metal, other = (b["a"], b["b"]) if b["a"]["comp_id"] == comp else (b["b"], b["a"])
                if not polymer_record(entry, other):
                    continue
                partners.append(other)
                per_site.setdefault(C.rkey(metal), set()).add(C.rkey(other))
                d = measured(entry, b["a"], b["b"])
                dists.append(d)
            partners = C.unique(partners)
            if len(per_site) != len(g["copies"]) or min(len(v) for v in per_site.values()) < 3 \
                    or max(dists) > 3.0:
                continue
            near = C.cif_neighbours(entry, g["copies"], comp, 2.6)
            if near != {C.rkey(p) for p in partners}:
                continue                 # geometry and annotation disagree: not used
            if C.cif_neighbours(entry, g["copies"], comp, AMBIGUOUS_REACH) != near:
                continue                 # a long bond the entry does not annotate (the
                                         # Met92 SD of plastocyanin 1PLC, 2.82 A from the
                                         # copper): experts count it, so the site is not asked
            msel = {"label_comp_id": comp}
            rsel = [C.residue(p) for p in partners]
            c1, c2 = C.colours(2, "g-metal-site", entry, comp)
            n = len(g["copies"])
            word = METAL_WORDS[comp]
            out.append(cand(
                entry,
                ["Load {ID}; show the {what} as a grey cartoon, the {metal} {ions} as {a_}{c1} "
                 "{spheres}, and the residues that coordinate {it} as {c2} ball-and-stick.",
                 "Show {ID} as a grey cartoon with the {metal} {sites}: the {ions} as "
                 "{a_}{c1} {spheres} and the {what_adj} residues bound to {it} in {c2} "
                 "ball-and-stick.",
                 "{ID}: grey cartoon; {metal} {ions} as {a_}{c1} {spheres}; every residue of "
                 "the {what} that coordinates {a_metal} {metal} ion, as {c2} ball-and-stick."],
                [grey_cartoon(), C.drawn_comp(msel, "spacefill", c1),
                 C.drawn_comp(rsel, "ball_and_stick", c2)],
                [C.part(rsel, "ball_and_stick", c2)],
                f"every {comp} ion of the facts ({n}) as a sphere, and the polymer residues "
                f"with a metal-coordination record (`_struct_conn`, `metalc`) to one of them: "
                + ", ".join(f"{p['comp_id']}{p['auth_seq_id']}{p.get('pdbx_PDB_ins_code') or ''}"
                            f" ({p['auth_asym_id']})" for p in partners)
                + ". Water and other non-polymer partners are not residues and are left out",
                [f"{len(dists)} metal-residue bonds re-measured in the frozen mmCIF: "
                 f"{min(dists):.2f} to {max(dists):.2f} A",
                 f"a neighbour search (with crystal symmetry) finds exactly these residues, "
                 f"and no other polymer N, O or S atom, within 2.6 A of a {comp} ion; none "
                 f"is added out to {AMBIGUOUS_REACH} A, so no weak ligand is left to argue over"],
                numbering=rsel, suffix=comp.lower(), flags={"structure_lookup": True},
                what=tr_what(entry), what_adj="protein" if tr_what(entry) == "protein" else "polymer",
                metal=word, ions="ion" if n == 1 else "ions",
                sites="site" if n == 1 else "sites", it="it" if n == 1 else "them",
                a_="a " if n == 1 else "", a_metal="the" if n == 1 else "a",
                spheres="sphere" if n == 1 else "spheres",
                c1=C.say_colour(c1), c2=C.say_colour(c2)))
    return out


def t_modres():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        f = C.facts(entry)
        mods = f["modified_residues"]
        kinds = sorted({m["comp_id"] for m in mods})
        named = [k for k in kinds if k in MODRES_NAMES]
        if len(named) > 1 and "MSE" in named:
            named.remove("MSE")          # the selenium label is not the entry's point
        if not named or f["n_models"] != 1:
            continue
        if set(named) <= {"TPO", "SEP", "PTR"} and len(named) > 1:
            groups = [(named, "phosphorylated residues", "the component names are "
                       "phosphothreonine, phosphoserine or phosphotyrosine")]
        else:
            groups = []
            for k in named:
                name, where = checked_name(MODRES_NAMES, k, entry)
                n = sum(m["comp_id"] == k for m in mods)
                if k == "CRO":
                    word = "chromophore"
                elif k == "CGU":
                    word = "gamma-carboxyglutamate " + ("residue" if n == 1 else "residues")
                    assert _phrase_in("GAMMA-CARBOXY-GLUTAMIC ACID", chem()[k]["name"])
                else:
                    word = name + (" residue" if n == 1 else " residues")
                groups.append(([k], word, f"the name \"{name}\" was found in {where}"))
        for comps_, word, why in groups:
            hits = [m for m in mods if m["comp_id"] in comps_]
            sel = [C.residue(m) for m in hits]
            assert C.mask_of(entry, sel) == C.mask_of(
                entry, [{"label_comp_id": k} for k in comps_]) & C.table(entry).static["polymer"]
            col = C.colours(1, "g-modres", entry, comps_[0])[0]
            out.append(cand(
                entry,
                ["Load {ID}; show the protein as a grey cartoon and the {word} as {c} "
                 "ball-and-stick.",
                 "Show {ID} as a grey cartoon and highlight the {word} in {c} ball-and-stick.",
                 "{ID}: grey cartoon, with the {word} drawn in {c} ball-and-stick."],
                [grey_cartoon(), C.drawn_comp(sel, "ball_and_stick", col)],
                [C.part(sel, "ball_and_stick", col)],
                f"the modified residues of the facts with component {' / '.join(comps_)}: "
                + ", ".join(f"{m['comp_id']}{m['auth_seq_id']} ({m['auth_asym_id']})" for m in hits),
                [why, f"the {len(hits)} residues are exactly the polymer residues with "
                      f"that component in the atom table"],
                numbering=sel, extra_inputs=["data/mvscore/chem_comp.json"],
                suffix=comps_[0].lower(),
                flags={"ligand_identity": True, "structure_lookup": True},
                word=word, c=C.say_colour(col)))
    return out


def t_glyco_sites():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        f = C.facts(entry)
        sites = f["glycosylation_sites"]
        if not 1 <= len(sites) <= 8 or f["n_models"] != 1:
            continue
        residues = C.unique([s["residue"] for s in sites])
        dists = [measured(entry, s["residue"], s["sugar"]) for s in sites]
        assert max(dists) < 1.7, f"{entry}: glycosidic bond of {max(dists):.2f} A"
        linked = C.table(entry).static["branched"] & C.table(entry).static["polymer"]
        sel = [C.residue(r) for r in residues]
        if C.mask_of(entry, sel) != linked:
            continue                     # Mol* sees another sugar-protein bond: not used
        kinds = {r["comp_id"] for r in residues}
        n = len(residues)
        word = (("asparagine" if n == 1 else "asparagines") if kinds == {"ASN"}
                else ("residue" if n == 1 else "residues"))
        col = C.colours(1, "g-glyco", entry)[0]
        out.append(cand(
            entry,
            ["Load {ID}; show the protein as a grey cartoon and the glycosylated {word} as {c} "
             "ball-and-stick (the amino acids, not the sugars).",
             "Show {ID} as a grey cartoon and mark the glycosylation {sites}: the {word} that "
             "{carry} a sugar, in {c} ball-and-stick. Do not draw the sugars.",
             "{ID}: grey cartoon; the protein {word} with a glycan attached as {c} "
             "ball-and-stick; no sugars."],
            [grey_cartoon(), C.drawn_comp(sel, "ball_and_stick", col)],
            [C.part(sel, "ball_and_stick", col)],
            "the polymer residues with a covalent bond to a sugar in the facts "
            "(`_struct_conn`): "
            + ", ".join(f"{r['comp_id']}{r['auth_seq_id']} ({r['auth_asym_id']})" for r in residues),
            [f"each sugar-residue bond re-measured in the frozen mmCIF: {min(dists):.2f} to "
             f"{max(dists):.2f} A",
             "the residues are exactly the polymer part of Mol*'s `branched` selection"],
            numbering=sel, flags={"structure_lookup": True},
            word=word, c=C.say_colour(col), sites="site" if n == 1 else "sites",
            carry="carries" if n == 1 else "carry"))
    return out


def ss_elements(entry: str) -> tuple[list[dict], list[dict]] | None:
    """Helices and strands of the facts, after re-reading the records from the frozen
    mmCIF and checking that they agree. Strands that take part in two sheets are listed
    once. None when the entry has insertion codes in an element (not used)."""
    f = C.facts(entry)
    helices = f["helices"]
    strands = []
    seen = set()
    for s in f["strands"]:
        key = (s["label_asym_id"], s["beg_label_seq_id"], s["end_label_seq_id"])
        if key not in seen:
            seen.add(key)
            strands.append(s)
    cif_h, cif_s = C.cif_secondary(entry)
    mine_h = sorted((h["auth_asym_id"], h["beg_auth_seq_id"], h["end_auth_seq_id"]) for h in helices)
    mine_s = sorted({(s["auth_asym_id"], s["beg_auth_seq_id"], s["end_auth_seq_id"]) for s in strands})
    assert mine_h == cif_h and mine_s == cif_s, f"{entry}: facts and mmCIF disagree on helices/strands"
    return helices, strands


def element_selector(x: dict) -> dict:
    return {"label_asym_id": x["label_asym_id"], "beg_label_seq_id": x["beg_label_seq_id"],
            "end_label_seq_id": x["end_label_seq_id"]}


def element_text(x: dict) -> str:
    return f"{x['auth_asym_id']} {x['beg_auth_seq_id']}-{x['end_auth_seq_id']}"


def t_secstruct():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        f = C.facts(entry)
        if f["n_models"] != 1 or tr_what(entry) != "protein" or len(f["chains"]) != 1:
            continue
        helices, strands = ss_elements(entry)
        if not 2 <= len(helices) + len(strands) <= 16:
            continue
        hsel = [element_selector(h) for h in helices]
        ssel = [element_selector(s) for s in strands]
        hm = C.mask_of(entry, hsel) if hsel else 0
        sm = C.mask_of(entry, ssel) if ssel else 0
        if hm & sm:
            continue
        c1, c2 = C.colours(2, "g-secstruct", entry)
        if helices and strands:
            layers = [C.colour(c1, s) for s in hsel] + [C.colour(c2, s) for s in ssel]
            target = [C.part(hsel, "cartoon", c1), C.part(ssel, "cartoon", c2)]
            what = f"the helices {C.say_colour(c1)} and the beta strands {C.say_colour(c2)}"
        elif helices:
            layers = [C.colour(c1, s) for s in hsel]
            target = [C.part(hsel, "cartoon", c1)]
            what = f"the helices {C.say_colour(c1)}"
        else:
            continue
        out.append(cand(
            entry,
            ["Load {ID} as a cartoon and colour {what}, with everything else grey. Use the "
             "secondary structure assigned in the PDB entry.",
             "Show {ID} as a grey cartoon, then colour {what}, following the helix and "
             "sheet records of the entry.",
             "{ID}, cartoon: {what}, the rest grey (secondary structure as annotated in the "
             "deposited file)."],
            [C.comp("polymer", C.rep("cartoon", C.colour(GREY), *layers))],
            target,
            f"one grey cartoon recoloured on the {len(helices)} helix record(s) (`_struct_conf`) "
            f"and {len(strands)} strand record(s) (`_struct_sheet_range`) of the facts; author ranges: "
            "helices " + ", ".join(element_text(h) for h in helices)
            + ("; strands " + ", ".join(element_text(s) for s in strands) if strands else ""),
            ["the helix and strand records were re-read from the frozen mmCIF and agree "
             "with the facts", "no residue is in both a helix and a strand"],
            numbering=hsel + ssel, flags={"structure_lookup": True}, what=what))
    return out


def t_longest_helix():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        f = C.facts(entry)
        if f["n_models"] != 1 or not f["helices"]:
            continue
        helices, _ = ss_elements(entry)
        sized = sorted(((len(C.residue_rows(entry, element_selector(h))), i)
                        for i, h in enumerate(helices)), reverse=True)
        if len(sized) < 3 or sized[0][0] - sized[1][0] < 3:
            continue
        h = helices[sized[0][1]]
        sel = element_selector(h)
        col = C.colours(1, "g-longest-helix", entry)[0]
        out.append(cand(
            entry,
            ["Load {ID} as a grey cartoon and colour its longest helix {c}, going by the "
             "helix records of the entry.",
             "Show {ID} as a cartoon, grey throughout except the longest helix annotated in "
             "the deposited file, which should be {c}.",
             "{ID}: grey cartoon, longest helix (as annotated in the entry) in {c}."],
            [C.comp("polymer", C.rep("cartoon", C.colour(GREY), C.colour(col, sel)))],
            [C.part(sel, "cartoon", col)],
            f"the helix record (`_struct_conf`) with the most observed residues: chain "
            f"{h['auth_asym_id']}, residues {h['beg_auth_seq_id']}-{h['end_auth_seq_id']} "
            f"({sized[0][0]} residues; the next longest has {sized[1][0]})",
            ["the helix records were re-read from the frozen mmCIF and agree with the facts",
             "the longest helix is at least 3 residues longer than any other"],
            numbering=sel, flags={"structure_lookup": True}, c=C.say_colour(col)))
    return out


def t_nucleic():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        t = C.table(entry)
        f = C.facts(entry)
        kinds = {c["polymer_type"] for c in f["chains"]} - {"protein"}
        if len(kinds) != 1 or not t.static.get("nucleic") or f["n_models"] != 1:
            continue
        na = kinds.pop()
        c1, c2 = C.colours(2, "g-nucleic", entry)
        chains = ", ".join(c["auth_asym_id"] for c in f["chains"] if c["polymer_type"] == na)
        checks = [f"Mol*'s `nucleic` selection is exactly the {na} chains of the facts ({chains})"]
        na_mask = C.mask_of(entry, [{"label_asym_id": c["label_asym_id"]} for c in f["chains"]
                                    if c["polymer_type"] == na])
        assert na_mask == t.static["nucleic"], entry
        if t.static.get("protein"):
            out.append(cand(
                entry,
                ["Load {ID}; show the {na} as {a1}{c1} cartoon and the protein as {a2}{c2} cartoon.",
                 "Show {ID} as a cartoon with the {na} in {c1} and the protein in {c2}.",
                 "{ID}, cartoon: {na} {c1}, protein {c2}."],
                [C.drawn_comp("nucleic", "cartoon", c1), C.drawn_comp("protein", "cartoon", c2)],
                [C.part("nucleic", "cartoon", c1)],
                f"Mol*'s `nucleic` and `protein` selections, one cartoon each",
                checks, flags={"structure_lookup": True},
                na=na, c1=C.say_colour(c1), c2=C.say_colour(c2),
                a1=C.article(C.say_colour(c1)), a2=C.article(C.say_colour(c2))))
        else:
            rep = C.pick(["ball_and_stick", "cartoon"], "g-nucleic-rep", entry)
            out.append(cand(
                entry,
                ["Load {ID} and show only the {na}, as {rep_a}. No water, no ions.",
                 "From {ID}, show just the {na} itself as {rep_a}, leaving out waters and ions.",
                 "{ID}: the {na} alone, as {rep_a}."],
                [C.drawn_comp("nucleic", rep, c1)],
                [C.part("nucleic", rep, c1)],
                f"Mol*'s `nucleic` selection in one representation; nothing else is drawn",
                checks, flags={"structure_lookup": True},
                na=na, rep_a=f"{C.say_colour(c1)} {C.REP_WORDS[rep]}"
                if rep != "cartoon" else f"{C.article(C.say_colour(c1))}{C.say_colour(c1)} cartoon"))
    return out


def entity_groups(entry: str) -> list[tuple[dict, str]]:
    f = C.facts(entry)
    polymers = [x for x in f["entities"] if x["type"] == "polymer"]
    out = []
    for pattern, one, many in ENTITY_NAMES[entry]:
        hits = [x for x in polymers if re.search(pattern, x["description"], re.I)]
        assert len(hits) == 1, f"{entry}: {pattern!r} matches {len(hits)} polymer entities"
        x = hits[0]
        n = len(x["label_asym_ids"])
        assert (many is None) == (n == 1), f"{entry}: {pattern!r} has {n} chains"
        out.append((x, f"the {one}" if n == 1 else f"the {many}"))
    assert len({x["id"] for x, _ in out}) == len(out), entry
    return out


def t_entity():
    out = []
    for entry in sorted(ENTITY_NAMES):
        if entry not in {e["id"] for e in C.pdb_entries()}:
            continue
        groups = entity_groups(entry)
        f = C.facts(entry)
        named = {x["id"] for x, _ in groups}
        rest = [x for x in f["entities"] if x["type"] == "polymer" and x["id"] not in named]
        cols = C.colours(len(groups), "g-entity", entry)
        sels = [[{"label_asym_id": a} for a in x["label_asym_ids"]] for x, _ in groups]
        sels = [s[0] if len(s) == 1 else s for s in sels]
        items = [f"{name} {C.say_colour(col)}" for (_, name), col in zip(groups, cols)]
        layers = [C.colour(col, s) for col, s in zip(cols, sels)]
        if rest:
            layers = [C.colour(GREY)] + layers
            items.append("everything else grey")
        spec = C.join(items)
        tail = ""
        chain_text = "; ".join(
            f"{name[4:]} = entity {x['id']} (\"{x['description']}\"), author chain"
            f"{'s' if len(x['label_asym_ids']) > 1 else ''} "
            + ", ".join(c["auth_asym_id"] for c in f["chains"] if c["entity_id"] == x["id"])
            for x, name in groups)
        out.append(cand(
            entry,
            ["Load {ID} as a cartoon and colour {spec}{tail}.",
             "Show {ID} as a cartoon coloured by molecule: {spec}{tail}.",
             "{ID}, cartoon: {spec}{tail}."],
            [C.comp("polymer", C.rep("cartoon", *layers))],
            [C.part(s, "cartoon", col) for s, col in zip(sels, cols)],
            "one cartoon of the polymer, coloured per entity; which chains belong to which "
            f"molecule is read from the entity records of the facts: {chain_text}",
            ["each name in the prompt matches the description of exactly one polymer entity",
             "the chains of the named entities are disjoint"
             + ("" if rest else " and together are the whole polymer")],
            numbering=[x for s in sels for x in (s if isinstance(s, list) else [s])],
            flags={"structure_lookup": True}, spec=spec, tail=tail))
        covered = 0
        for s in sels:
            m = C.mask_of(entry, s)
            assert not covered & m, entry
            covered |= m
        poly = C.table(entry).static["polymer"]
        assert (covered & poly == poly) == (not rest), entry
    return out


def t_catalytic():
    out = []
    sites = uniprot_sites()
    for e in C.pdb_entries():
        entry = e["id"]
        f = C.facts(entry)
        if f["n_models"] != 1:
            continue
        for acc in e.get("uniprot", []):
            rec = sites.get(acc.split("-")[0])
            if rec is None or len(rec["active_sites"]) < 2 or acc == "P00720":
                continue                 # P00720: the T4 lysozyme fused into 3EML
            residues, lines, ok = [], [], True
            for s in rec["active_sites"]:
                rows = [r for r in (sifts.uniprot_residues(entry, acc, s["position"]) or [])
                        if r.observed]
                if not rows or any(r.comp_id != ONE_TO_THREE.get(r.unp_res) for r in rows):
                    ok = False           # not observed, or an engineered substitution
                    break
                for r in rows:
                    residues.append({"auth_asym_id": r.auth_asym_id, "auth_seq_id": r.auth_seq_id,
                                     "pdbx_PDB_ins_code": r.pdbx_PDB_ins_code, "comp_id": r.comp_id})
                lines.append(f"UniProt {s['position']} ({rows[0].unp_res}"
                             + (f", {s['description']}" if s["description"] else "") + ") = "
                             + ", ".join(f"{r.comp_id}{r.auth_seq_id}{r.pdbx_PDB_ins_code} "
                                         f"({r.auth_asym_id})" for r in rows))
            if not ok:
                continue
            residues = C.unique(residues)
            copies = len({r["auth_asym_id"] for r in residues})
            n_sites = len(rec["active_sites"])
            triad = n_sites == 3 and all(s["description"] == "Charge relay system"
                                         for s in rec["active_sites"])
            sel = [C.residue(r) for r in residues]
            for r, s in zip(residues, sel):
                m = C.mask_of(entry, s)
                assert m and C.table(entry).columns["label_comp_id"][
                    C.residue_rows(entry, s)[0]] == r["comp_id"], entry
            col = C.colours(1, "g-catalytic", entry)[0]
            many = len([c for c in f["chains"] if c["polymer_type"] == "protein"]) > 1
            where = ""
            if copies > 1:
                where = f" in each of the {C.number(copies)} copies of the enzyme"
            elif many:
                where = " of the enzyme"
            out.append(cand(
                entry,
                ["Load {ID}; show the {what} as a grey cartoon and the {cat}{where} as {c} "
                 "ball-and-stick.",
                 "Show {ID} as a grey cartoon and highlight the {cat}{where} in {c} "
                 "ball-and-stick.",
                 "{ID}: grey cartoon, with the {cat}{where} drawn as {c} ball-and-stick."],
                [grey_cartoon(), C.drawn_comp(sel, "ball_and_stick", col)],
                [C.part(sel, "ball_and_stick", col)],
                f"the 'Active site' positions of UniProt {acc} ({rec['id']}), mapped to the "
                f"structure through the frozen SIFTS table: " + "; ".join(lines),
                ["every mapped residue is observed and has the amino acid UniProt has at "
                 "that position",
                 f"all {n_sites} active-site positions of the UniProt entry are present in "
                 "the structure"],
                numbering=sel, suffix=acc.split("-")[0].lower(),
                extra_inputs=["data/mvscore/uniprot_sites.json",
                              f"molbench/sifts_tables/{entry}.json.gz"],
                flags={"structure_lookup": True},
                more={"uniprot": acc, "uniprot_positions": [s["position"] for s in rec["active_sites"]]},
                what=tr_what(entry), where=where, c=C.say_colour(col),
                cat="catalytic triad" if triad else
                    f"{C.number(n_sites)} catalytic residues"))
    return out


def t_attachment():
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        f = C.facts(entry)
        groups = {g["comp_id"]: g for g in f["ligands"] if g["kind"] == "ligand"}
        links = {}
        for b in f["covalent_links"]:
            for lig, res in ((b["a"], b["b"]), (b["b"], b["a"])):
                if lig["comp_id"] in groups and polymer_record(entry, res) \
                        and not b["to_symmetry_copy"]:
                    links.setdefault(lig["comp_id"], []).append((lig, res, b))
        for comp, found in links.items():
            g = groups[comp]
            if comp in ("BME", "ISP") or g["n_heavy_atoms"] < 8:
                continue                 # buffer adducts and inhibitor fragments: not named
            if len({C.rkey(lig) for lig, _, _ in found}) != len(g["copies"]):
                continue                 # only some copies are attached
            named = checked_name(LIGAND_NAMES, comp, entry)
            if g.get("heme"):
                name = "heme"
            elif named:
                name = named[0]
            elif len(links) == 1 and len([x for x in groups.values() if x["n_heavy_atoms"] >= 8]) >= 1 \
                    and _phrase_in("covalent compound", f["title"]):
                name = "covalently bound compound"
            else:
                continue
            residues = C.unique([res for _, res, _ in found])
            dists = [measured(entry, b["a"], b["b"]) for _, _, b in found]
            assert max(dists) < 2.0, f"{entry}: covalent link of {max(dists):.2f} A"
            lsel = {"label_comp_id": comp}
            rsel = [C.residue(r) for r in residues]
            c1, c2 = C.colours(2, "g-attachment", entry)
            kinds = {r["comp_id"] for r in residues}
            n = len(residues)
            word = RESIDUE_WORDS[kinds.pop()] if len(kinds) == 1 else "residue"
            word += "" if n == 1 else "s"
            out.append(cand(
                entry,
                ["Load {ID}; show the protein as a grey cartoon, the {name} as {c1} "
                 "ball-and-stick, and the {word} it is covalently attached to as {c2} "
                 "ball-and-stick.",
                 "Show {ID} as a grey cartoon with the {name} in {c1} ball-and-stick and the "
                 "{word} that {hold} it covalently in {c2} ball-and-stick.",
                 "{ID}: grey cartoon; {name} as {c1} ball-and-stick; the {word} covalently "
                 "linked to it as {c2} ball-and-stick."],
                [grey_cartoon(), C.drawn_comp(lsel, "ball_and_stick", c1),
                 C.drawn_comp(rsel, "ball_and_stick", c2)],
                [C.part(rsel, "ball_and_stick", c2)],
                f"every copy of {comp} ({g['name'][:60]}) and the polymer residues with a "
                "covalent link record (`_struct_conn`, `covale`) to it in the facts: "
                + ", ".join(f"{r['comp_id']}{r['auth_seq_id']} ({r['auth_asym_id']})"
                            for r in residues),
                ["each link re-measured in the frozen mmCIF: "
                 + ", ".join(f"{d:.2f} A" for d in dists)],
                numbering=rsel, suffix=comp.lower(),
                flags={"ligand_identity": True, "structure_lookup": True},
                name=name, word=word, hold="holds" if n == 1 else "hold",
                c1=C.say_colour(c1), c2=C.say_colour(c2)))
    return out


def t_all_but_chain():
    """Everything except one chain (LEDGER S12, U13). MVS has no "all but": the answer
    must list the other chains, so it needs the chain ids of the entry."""
    out = []
    for e in C.pdb_entries():
        entry = e["id"]
        chains = [c for c in C.facts(entry)["chains"]]
        auth = [c["auth_asym_id"] for c in chains]
        if not 3 <= len(chains) <= 8 or len(set(auth)) != len(auth):
            continue
        t = C.table(entry)
        drop = C.pick(chains, "g-all-but", entry)
        kept = [c for c in chains if c is not drop]
        sel = [{"label_asym_id": c["label_asym_id"]} for c in kept]
        gone = t.selector({"label_asym_id": drop["label_asym_id"]})
        mask = t.selector(sel)
        if not gone or mask & gone or (mask | gone) != t.static["polymer"]:
            continue
        col = C.colours(1, "g-all-but", entry)[0]
        out.append(cand(
            entry,
            ["Show {ID} as {a_c} cartoon, but leave out chain {X}.",
             "Load {ID} and draw every chain except chain {X} as {a_c} cartoon.",
             "{ID} as {a_c} cartoon without chain {X}: hide that chain and keep all the "
             "others."],
            [C.drawn_comp(sel, "cartoon", col)],
            [C.part(sel, "cartoon", col)],
            f"a cartoon of every polymer chain of the facts except author chain "
            f"{drop['auth_asym_id']}: author chains "
            f"{', '.join(c['auth_asym_id'] for c in kept)}",
            ["every polymer chain has its own author chain id",
             "the chains drawn and the chain left out are disjoint and together are the "
             "whole polymer (atom table)"],
            numbering=sel, flags={"structure_lookup": True},
            X=drop["auth_asym_id"], a_c=C.article(C.say_colour(col)) + C.say_colour(col)))
    return out


TEMPLATES = {
    "gr-attachment": (t_attachment, 4),
    "gr-heme-axial": (t_heme_axial, 4),
    "gr-heme": (t_heme, 4),
    "gr-glyco-sites": (t_glyco_sites, 5),
    "gr-modres": (t_modres, 5),
    "gr-catalytic": (t_catalytic, 6),
    "gr-entity": (t_entity, 6),
    "gr-nucleic": (t_nucleic, 5),
    "gr-metal-site": (t_metal_site, 6),
    "gr-disulfides": (t_disulfides, 6),
    "gr-ligand": (t_ligand, 6),
    "gr-secstruct": (t_secstruct, 4),
    "gr-longest-helix": (t_longest_helix, 4),
    "gr-all-but-chain": (t_all_but_chain, 3),    # added last: earlier choices are unchanged
}

DERIVED = {
    "gr-ligand": ("named ligand", "The component whose frozen name or synonym (RCSB chemical "
                  "component record), or the entry title, contains the prompt's name; every copy."),
    "gr-heme": ("heme", "Components the facts flag as heme (an iron porphyrin), every copy; "
                "one FE atom per copy confirmed in the mmCIF."),
    "gr-heme-axial": ("residues on the heme iron", "Polymer residues with a `metalc` record to "
                      "a heme FE; bond re-measured; neighbour search within 2.6 A agrees."),
    "gr-disulfides": ("disulfide-bonded cysteines", "Both ends of every `disulf` record; S-S "
                      "re-measured (1.9-2.3 A); no unannotated SG-SG pair within 2.5 A."),
    "gr-metal-site": ("a metal and its coordinating residues", "Every copy of one metal ion, "
                      "plus the polymer residues with a `metalc` record to it (3 or more per "
                      "site, none to a symmetry copy); used only if a neighbour search "
                      "within 2.6 A, with symmetry, finds exactly those residues and none is "
                      "added out to 3.2 A (a weak ligand the entry does not annotate, such as "
                      "Met92 of plastocyanin 1PLC, would make the answer arguable)."),
    "gr-modres": ("modified residues", "Non-standard residues inside polymer chains (facts), "
                  "by component; the name is checked against the component record."),
    "gr-glyco-sites": ("glycosylation sites", "Polymer residues covalently bonded to a sugar "
                       "(`_struct_conn`); bond re-measured; equal to the polymer part of "
                       "Mol*'s `branched` selection."),
    "gr-secstruct": ("helices and strands", "`_struct_conf` and `_struct_sheet_range` ranges, "
                     "re-read from the mmCIF; single-chain proteins with 2 to 16 elements."),
    "gr-longest-helix": ("the longest helix", "The helix record with the most observed "
                         "residues, when it leads by 3 or more; the prompt says the "
                         "entry's own helix annotation is meant."),
    "gr-nucleic": ("the DNA / the RNA", "Mol*'s `nucleic` selection, checked to be exactly the "
                   "DNA or RNA chains of the facts."),
    "gr-entity": ("named subunits", "Chains of each polymer entity; the prompt's name for an "
                  "entity must match exactly one entity description."),
    "gr-catalytic": ("catalytic residues", "UniProt 'Active site' features (frozen), mapped "
                     "through the frozen SIFTS table; residue identity must match UniProt."),
    "gr-all-but-chain": ("one chain to leave out", "Every other polymer chain of the facts; "
                         "drawn and left-out chains together are the whole polymer."),
    "gr-attachment": ("ligand and the residue it is bonded to", "Polymer residues with a "
                      "`covale` record to the named ligand; link re-measured (< 2.0 A)."),
}


def one_per_protein(cands: list[dict]) -> list[dict]:
    """One candidate per UniProt accession (seeded), so that hen lysozyme or bovine
    trypsin is not asked about twice."""
    by_acc: dict[str, list[dict]] = {}
    for c in cands:
        by_acc.setdefault(c["more"]["uniprot"], []).append(c)
    return [C.pick(sorted(v, key=lambda c: c["entry"]), "one-per-protein", acc)
            for acc, v in sorted(by_acc.items())]


def build() -> list[dict]:
    picker = C.Picker(TIER)
    built = []
    for family, (fn, n) in TEMPLATES.items():
        cands = fn()
        if family == "gr-catalytic":
            cands = one_per_protein(cands)
        chosen = picker.choose(family, cands, n, entry_of=lambda c: c["entry"])
        C.enough(family, chosen, n)
        for c in chosen:
            entry = c["entry"]
            tid = f"{family}-{entry}" + (f"-{c['suffix']}" if c["suffix"] else "")
            wording = C.pick(c["wordings"], "wording", family, tid)
            prompt = wording.format(ID=entry.upper(), **c["words"])
            built.append(C.make_task(
                tid, TIER, family, entry, prompt, C.scene(entry, c["children"]), c["target"],
                script=SCRIPT, input_files=C.inputs(entry, *c["extra_inputs"]),
                derivation=c["derivation"], checks=c["checks"],
                difficulty=C.difficulty(entry, c["numbering"], **c["flags"]),
                provenance=c["more"]))
    return sorted(built, key=lambda t: t["id"])


def readme(built: list[dict]) -> str:
    rows = "\n".join(f"| `{f}` | {what} | {how} |" for f, (what, how) in sorted(DERIVED.items()))
    return f"""# Grounded tier (MVS track)

Generated by `scripts/generate_grounded_tasks.py`; do not edit by hand. The request
names something that has to be found in the structure and gives no residue numbers.
Every reference is extracted from the frozen facts of the entry and checked against the
frozen mmCIF with gemmi; the check and its numbers are in each task's
`provenance.checks`. A reference holds only what the prompt states (the grey cartoon is
there because the prompt asks for it).

{C.summary_tables(built)}

## How each reference is derived

| template | the request names | reference |
|---|---|---|
{rows}

Frozen inputs beyond the panel: `data/mvscore/chem_comp.json` (component names and
synonyms, RCSB) and `data/mvscore/uniprot_sites.json` (UniProt active-site features),
both with source and retrieval date. Catalytic residues are asked for only where UniProt
lists two or more active-site positions and every one of them is observed in the
structure with the amino acid UniProt has (so the S195A factor IXa of 8EPH and 3KCG is
not used).

`provenance.difficulty` records per task: `needs_ligand_identity` (a compound or
modification is named in words), `needs_structure_lookup` (the residues are not named in
the prompt), `needs_uniprot_mapping` (never in this tier: answers use author numbering),
and the three numbering flags of the residues the answer selects.

Replaces the eight earlier grounded tasks; their two requests (the named ligand, the
disulfide cysteines) are templates `gr-ligand` and `gr-disulfides` here.
"""


def main() -> int:
    args = C.cli(__doc__)
    if args.refresh:
        refresh()
    built = C.verify(build(), OUT)
    return C.finish(built, OUT, args, readme(built))


if __name__ == "__main__":
    raise SystemExit(main())
