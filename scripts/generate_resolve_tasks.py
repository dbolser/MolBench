#!/usr/bin/env python3
"""
Resolve-tier MVS tasks (``tasks/mvs_resolve/``): the request names a protein, not a
PDB entry. Real users do this ("I wanna see a structure of PDE5A"), and models answer
with made-up ids or real ids of another protein.

Many entries are a right answer, so every task lists them (``accepted_structures``):
the PDB entries in which RCSB aligns a polymer entity to the protein's UniProt
accession over a domain-sized stretch (`COVERAGE_RULE`), plus what the request adds (a
bound ligand, DNA, a second protein). The lists are frozen with their date in
``data/mvscore/resolve_entries.json``. The reference is drawn on one of them, a panel
entry, and uses only selections that mean the same on every entry (``polymer``,
``protein``, ``nucleic``, a component code), so an answer on another accepted entry
can be compared with it.

    uv run python scripts/generate_resolve_tasks.py            # rewrite tasks/mvs_resolve/
    uv run python scripts/generate_resolve_tasks.py --check    # fail if the files would change
    uv run python scripts/generate_resolve_tasks.py --refresh  # re-download the frozen lists
                                                               # (RCSB + UniProt), then rewrite

Without ``--refresh`` nothing touches the network. ``--refresh`` also freezes the list
of every current PDB id (``data/mvscore/pdb_ids.txt.gz``), so that a wrong answer can
be told apart as "a real entry of another protein" or "an id that does not exist"
(`pdb_id_exists`). Templates, counts and derivations: ``tasks/mvs_resolve/README.md``.
"""

from __future__ import annotations

import functools
import gzip
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import mvscore_common as C  # noqa: E402
import generate_grounded_tasks as G  # noqa: E402  (checked ligand names)

OUT = C.REPO / "tasks" / "mvs_resolve"
SCRIPT = "scripts/generate_resolve_tasks.py"
TIER = "resolve"
ENTRIES = C.DATA / "resolve_entries.json"
PDB_IDS = C.DATA / "pdb_ids.txt.gz"
INPUT_FILES = ["data/mvscore/resolve_entries.json"]

MIN_RESIDUES = 50
MIN_SHARE = 0.5
COVERAGE_RULE = (f"RCSB aligns the entry's polymer entities to the UniProt accession over at "
                 f"least {MIN_RESIDUES} residues in total (each entity counted once), or over at "
                 f"least half of the UniProt sequence if that is shorter")
HELD_SHARE = C.HELDBACK_SHARE

# --------------------------------------------------------------------------- #
# Hand-written wording (checked by script against the frozen UniProt record; never a
# reference). accession -> (what a prompt calls the protein, the piece of that phrase
# that must be one of the record's protein names or gene names, the organism word of
# the phrase or None). `protein_phrase` refuses anything the record does not support.
# Proteins of the panel that are left out, and why: ubiquitin, calmodulin, histones
# and antibody chains (several genes or accessions carry the same protein, so a list by
# one accession would reject right answers); HIV-1 protease, gp120, thrombin (pieces of
# a polyprotein or precursor whose UniProt name is not what a prompt would say); T4
# lysozyme (present only as a fusion partner).
# --------------------------------------------------------------------------- #
PROTEINS = {
    "P17931": ("human galectin-3", "galectin-3", "human"),
    "P02185": ("sperm whale myoglobin", "myoglobin", "sperm whale"),
    "P69441": ("E. coli adenylate kinase", "adenylate kinase", "E. coli"),
    "P00698": ("hen egg-white lysozyme", "lysozyme", "hen"),
    "P02945": ("bacteriorhodopsin from Halobacterium salinarum", "bacteriorhodopsin",
               "Halobacterium salinarum"),
    "P29373": ("human cellular retinoic acid-binding protein 2 (CRABP-II)", "CRABP-II", "human"),
    "P01542": ("crambin", "crambin", None),
    "P01112": ("human H-Ras", "H-Ras", "human"),
    "P60484": ("the human tumour suppressor PTEN", "PTEN", "human"),
    "P42212": ("green fluorescent protein from Aequorea victoria", "green fluorescent protein",
               "Aequorea victoria"),
    "P02699": ("bovine rhodopsin", "rhodopsin", "bovine"),
    "P61823": ("bovine pancreatic ribonuclease (RNase A)", "RNase A", "bovine"),
    "P07320": ("human gamma-D-crystallin", "gamma-D-crystallin", "human"),
    "P00004": ("horse heart cytochrome c", "cytochrome c", "horse"),
    "P00520": ("the mouse tyrosine kinase c-Abl", "c-Abl", "mouse"),
    "P00268": ("rubredoxin from Clostridium pasteurianum", "rubredoxin",
               "Clostridium pasteurianum"),
    "P03034": ("the cI repressor of bacteriophage lambda", "cI", "bacteriophage lambda"),
    "P00299": ("poplar plastocyanin", "plastocyanin", "poplar"),
    "P0ABQ4": ("E. coli dihydrofolate reductase", "dihydrofolate reductase", "E. coli"),
    "P22629": ("streptavidin", "streptavidin", None),
    "P07477": ("human trypsin-1", "trypsin-1", "human"),
    "P04637": ("human p53", "p53", "human"),
    "O76074": ("human phosphodiesterase 5A (PDE5A)", "PDE5A", "human"),
    "P00441": ("human superoxide dismutase 1", "superoxide dismutase 1", "human"),
    "P00183": ("cytochrome P450cam from Pseudomonas putida", "cytochrome P450cam",
               "Pseudomonas putida"),
    "P61626": ("human lysozyme", "lysozyme", "human"),
    "P02931": ("the E. coli porin OmpF", "porin OmpF", "E. coli"),
    "Q8NBP7": ("human PCSK9", "PCSK9", "human"),
    "P00760": ("bovine trypsin", "trypsin", "bovine"),
    "P29274": ("the human adenosine receptor A2a", "adenosine receptor A2a", "human"),
    "P03372": ("human estrogen receptor alpha (ER-alpha)", "ER-alpha", "human"),
    "P35557": ("human glucokinase", "glucokinase", "human"),
    "P00918": ("human carbonic anhydrase II", "carbonic anhydrase II", "human"),
    "P10275": ("the human androgen receptor", "androgen receptor", "human"),
    "P13569": ("the human cystic fibrosis transmembrane conductance regulator (CFTR)", "CFTR",
               "human"),
    "P00439": ("human phenylalanine hydroxylase (PAH)", "PAH", "human"),
    "P11166": ("the human glucose transporter GLUT1", "GLUT1", "human"),
    "P0DTC2": ("the SARS-CoV-2 spike glycoprotein", "spike glycoprotein", "SARS-CoV-2"),
    "P09528": ("mouse ferritin heavy chain", "ferritin heavy chain", "mouse"),
    "P02766": ("human transthyretin", "transthyretin", "human"),
    "P02649": ("human apolipoprotein E", "apolipoprotein E", "human"),
    "P00740": ("human coagulation factor IX", "coagulation factor IX", "human"),
    "P06280": ("human alpha-galactosidase A", "alpha-galactosidase A", "human"),
    "P01009": ("human alpha-1-antitrypsin", "alpha-1-antitrypsin", "human"),
    "P60174": ("human triosephosphate isomerase", "triosephosphate isomerase", "human"),
    "P04062": ("human glucocerebrosidase", "glucocerebrosidase", "human"),
    "P08046": ("the mouse transcription factor Zif268", "transcription factor Zif268", "mouse"),
    "P0A334": ("the KcsA potassium channel of Streptomyces lividans", "KcsA",
               "Streptomyces lividans"),
    "P05132": ("the catalytic subunit of mouse protein kinase A (PKA C-alpha)", "PKA C-alpha",
               "mouse"),
    "P01308": ("human insulin", "insulin", "human"),
    "P01315": ("pig insulin", "insulin", "pig"),
    # named only as partners in a complex
    "P00974": ("bovine pancreatic trypsin inhibitor (BPTI)", "BPTI", "bovine"),
    "P01008": ("human antithrombin", "antithrombin", "human"),
    "P40337": ("the human von Hippel-Lindau protein (pVHL)", "pVHL", "human"),
    "Q15369": ("elongin-C", "elongin-C", None),
    "Q15370": ("elongin-B", "elongin-B", None),
    "P68871": ("human hemoglobin beta chain", "hemoglobin beta chain", "human"),
    "P69905": ("human hemoglobin alpha chain", "hemoglobin alpha chain", "human"),
}
PARTNER_ONLY = {"P00974", "P01008", "P40337", "Q15369", "Q15370", "P68871", "P69905"}
# Organism word of a phrase -> text that must be in the record's scientific or common
# organism name.
ORGANISM_WORDS = {
    "human": "Homo sapiens", "mouse": "Mus musculus", "bovine": "Bos taurus",
    "horse": "Equus caballus", "sperm whale": "Sperm whale", "E. coli": "Escherichia coli",
    "hen": "Gallus gallus", "poplar": "poplar", "pig": "Sus scrofa",
    "Halobacterium salinarum": "Halobacterium salinarum", "Aequorea victoria": "Aequorea victoria",
    "Clostridium pasteurianum": "Clostridium pasteurianum",
    "Pseudomonas putida": "Pseudomonas putida", "bacteriophage lambda": "Bacteriophage lambda",
    "Streptomyces lividans": "Streptomyces lividans",
    "SARS-CoV-2": "Severe acute respiratory syndrome coronavirus 2",
}
# Complexes a prompt can name: panel entry -> (the accessions that must all be in an
# accepted entry, the prompt's phrase or None to join the proteins' own phrases).
COMPLEXES = {
    "2ptc": (["P00760", "P00974"], None),
    "3kcg": (["P00740", "P01008"], None),
    "9gio": (["P40337", "Q15369", "Q15370"], None),
    "1hho": (["P69905", "P68871"], "human hemoglobin (alpha and beta chains together)"),
    "2hhb": (["P69905", "P68871"], "human hemoglobin (alpha and beta chains together)"),
    "5ni1": (["P69905", "P68871"], "human hemoglobin (alpha and beta chains together)"),
}
# Ligands not asked for by name here, although the grounded tier names them: the same
# compound is deposited under more than one component code (glucose: GLC or BGC; NADP+
# or NADPH: NAP or NDP), so a list by one code would reject right answers.
LIGANDS_LEFT_OUT = {"GLC", "NAP"}
MIN_LIGAND_ENTRIES = 3       # a protein-ligand pair is asked for only if this many entries hold it


# --------------------------------------------------------------------------- #
# The frozen lists
# --------------------------------------------------------------------------- #
def panel_accessions() -> list[str]:
    return sorted({a.split("-")[0] for e in C.usable_entries() if e["kind"] == "pdb"
                   for a in e.get("uniprot", [])})


def refresh() -> None:
    """Download and freeze, for every UniProt accession of the panel: its UniProt names,
    genes, organism and length, and every PDB entry with a polymer entity RCSB maps to
    it (aligned length, DNA or RNA in the entry, non-polymer component codes). Also the
    list of all current PDB ids. Free public APIs (RCSB search, RCSB GraphQL, UniProt)."""
    import datetime
    import urllib.request

    def call(url: str, body: dict | None = None):
        req = urllib.request.Request(
            url, data=json.dumps(body).encode() if body is not None else None,
            headers={"Accept": "application/json", "content-type": "application/json",
                     "User-Agent": "molbench-build"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.load(resp) if resp.status == 200 else None

    attr = "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers."
    fields = ("rcsb_id entity_poly{rcsb_entity_polymer_type} "
              "rcsb_polymer_entity_align{reference_database_name reference_database_accession "
              "aligned_regions{length}} "
              "entry{rcsb_entry_info{polymer_entity_count_DNA polymer_entity_count_RNA "
              "resolution_combined experimental_method} "
              "nonpolymer_entities{pdbx_entity_nonpoly{comp_id}}}")
    today = datetime.date.today().isoformat()
    proteins = {}
    for acc in panel_accessions():
        u = call(f"https://rest.uniprot.org/uniprotkb/{acc}.json"
                 "?fields=id,protein_name,gene_names,organism_name,length")
        desc = u["proteinDescription"]
        names = []
        for block in [desc.get("recommendedName"), *desc.get("alternativeNames", [])]:
            if block:
                names.append(block["fullName"]["value"])
                names += [s["value"] for s in block.get("shortNames", [])]
        genes = []
        for g in u.get("genes", []):
            if "geneName" in g:
                genes.append(g["geneName"]["value"])
            genes += [s["value"] for s in g.get("synonyms", [])]
        hits = call("https://search.rcsb.org/rcsbsearch/v2/query", {
            "query": {"type": "group", "logical_operator": "and", "nodes": [
                {"type": "terminal", "service": "text", "parameters": {
                    "attribute": attr + "database_accession", "operator": "exact_match",
                    "value": acc}},
                {"type": "terminal", "service": "text", "parameters": {
                    "attribute": attr + "database_name", "operator": "exact_match",
                    "value": "UniProt"}}]},
            "return_type": "polymer_entity", "request_options": {"return_all_hits": True}})
        ids = sorted(h["identifier"] for h in (hits or {}).get("result_set", []))
        entries: dict[str, list] = {}
        for i in range(0, len(ids), 200):
            got = call("https://data.rcsb.org/graphql", {
                "query": "{polymer_entities(entity_ids:%s){%s}}" % (json.dumps(ids[i:i + 200]),
                                                                    fields)})
            for ent in got["data"]["polymer_entities"]:
                aligned = sum(r["length"] for a in ent["rcsb_polymer_entity_align"] or []
                              if a["reference_database_name"] == "UniProt"
                              and a["reference_database_accession"] == acc
                              for r in a["aligned_regions"])
                entry = ent["rcsb_id"].split("_")[0].lower()
                info = ent["entry"]["rcsb_entry_info"]
                comps = sorted({n["pdbx_entity_nonpoly"]["comp_id"]
                                for n in ent["entry"]["nonpolymer_entities"] or []})
                old = entries.get(entry)
                entries[entry] = [aligned + (old[0] if old else 0),
                                  int(bool(info["polymer_entity_count_DNA"])),
                                  int(bool(info["polymer_entity_count_RNA"])), " ".join(comps),
                                  info.get("experimental_method") or "",
                                  (info.get("resolution_combined") or [None])[0]]
        proteins[acc] = {
            "uniprot_id": u["uniProtkbId"], "names": names, "genes": genes,
            "organism": u["organism"]["scientificName"],
            "organism_common": u["organism"].get("commonName", ""),
            "length": u["sequence"]["length"], "entries": dict(sorted(entries.items()))}
        print(f"{acc} {u['uniProtkbId']:14s} {len(entries):5d} entries")
    text = json.dumps(
        {"source": "RCSB search API (polymer entities whose reference sequence is the UniProt "
                   "accession), RCSB GraphQL (rcsb_polymer_entity_align, rcsb_entry_info, "
                   "nonpolymer_entities) and UniProt REST (protein_name, gene_names, "
                   "organism_name, length)",
         "retrieved": today,
         "entry_columns": ["residues aligned to the accession (summed over the entry's "
                           "polymer entities, each counted once)", "has DNA",
                           "has RNA", "non-polymer component codes", "experimental method",
                           "resolution in A (null if none)"],
         "proteins": proteins}, indent=0, ensure_ascii=False, sort_keys=True)
    C.DATA.mkdir(parents=True, exist_ok=True)
    ENTRIES.write_text(text + "\n", encoding="utf-8")
    ids = sorted(i.lower() for i in call("https://data.rcsb.org/rest/v1/holdings/current/entry_ids"))
    with open(PDB_IDS, "wb") as fh:
        with gzip.GzipFile(fileobj=fh, mode="wb", mtime=0, filename="") as gz:
            gz.write((f"# every current PDB entry id; RCSB holdings/current/entry_ids; "
                      f"retrieved {today}\n" + "\n".join(ids) + "\n").encode())
    print(f"froze {len(proteins)} proteins and {len(ids)} PDB ids on {today}")


@functools.lru_cache(maxsize=None)
def frozen() -> dict:
    return json.loads(ENTRIES.read_text(encoding="utf-8"))


def protein(acc: str) -> dict:
    return frozen()["proteins"][acc]


@functools.lru_cache(maxsize=None)
def pdb_ids() -> tuple[frozenset[str], str]:
    """Every PDB id current on the retrieval date, and that date."""
    with gzip.open(PDB_IDS, "rt", encoding="utf-8") as fh:
        head, *ids = fh.read().split("\n")
    return frozenset(i for i in ids if i), head.rsplit(" ", 1)[-1]


def pdb_id_exists(pdb_id: str) -> bool:
    """Whether the id was a current PDB entry when the list was frozen (LEDGER L-041)."""
    return pdb_id.lower() in pdb_ids()[0]


def answer_outcome(task: dict, pdb_id: str) -> str:
    """What kind of answer an entry id is for a resolve task: ``accepted``,
    ``wrong_entry`` (a real PDB entry that is not one of the task's) or ``no_such_entry``
    (not a PDB id on the day the list was frozen)."""
    pdb_id = pdb_id.lower()
    if pdb_id in task["accepted_structures"] or pdb_id in task["structures"]:
        return "accepted"
    return "wrong_entry" if pdb_id_exists(pdb_id) else "no_such_entry"


def threshold(acc: str) -> int:
    return min(MIN_RESIDUES, -(-protein(acc)["length"] // 2))


def accepted_entries(accessions: list[str], comp: str | None = None, dna: bool = False) -> list[str]:
    """The entries that answer a request naming these proteins (all of them in one
    entry, each over `COVERAGE_RULE`), with the component and with DNA if asked."""
    out = None
    for acc in accessions:
        mine = {e for e, (aligned, has_dna, _rna, comps, *_) in protein(acc)["entries"].items()
                if aligned >= threshold(acc) and (not dna or has_dna)
                and (comp is None or comp in comps.split())}
        out = mine if out is None else out & mine
    return sorted(out or [])


def protein_phrase(acc: str) -> str:
    """The prompt's phrase for a protein, after checking it against the frozen UniProt
    record: the named piece is one of the record's protein or gene names, and the
    organism word belongs to the record's organism."""
    phrase, piece, organism = PROTEINS[acc]
    rec = protein(acc)
    assert G._phrase_in(piece, phrase), f"{acc}: {piece!r} is not in {phrase!r}"
    if not any(G._phrase_in(piece, n) for n in rec["names"] + rec["genes"]):
        raise SystemExit(f"{acc}: {piece!r} is not a name of {rec['uniprot_id']}: {rec['names']}")
    if organism is not None:
        assert organism in phrase, f"{acc}: {organism!r} is not in {phrase!r}"
        text = f"{rec['organism']} / {rec['organism_common']}".lower()
        if ORGANISM_WORDS[organism].lower() not in text:
            raise SystemExit(f"{acc}: {organism!r} does not fit the organism {text!r}")
    return phrase


def panel_entries_of(acc: str) -> list[str]:
    return sorted(e["id"] for e in C.pdb_entries()
                  if acc in {a.split("-")[0] for a in e.get("uniprot", [])})


def sifts_residues(entry: str, acc: str) -> int:
    """Observed residues the frozen PDBe SIFTS mapping of a panel entry assigns to the
    accession (the largest chain): the check, from a second source, that the reference's
    entry really is this protein."""
    return max((u["n_residues"] for c in C.facts(entry)["chains"] for u in c["uniprot"]
                if u["accession"].split("-")[0] == acc), default=0)


# --------------------------------------------------------------------------- #
# Templates
# --------------------------------------------------------------------------- #
def a_colour(c: str) -> str:
    word = C.say_colour(c)
    return C.article(word) + word


def cand(entry, accessions, wordings, children, alternatives, target, accepted, derivation,
         suffix, named_by, flags=None, pack_extra="", alt_targets=None, **words):
    """``alt_targets``: one target per alternative, written with the alternative's own
    selection. On an accepted entry outside the panel there is no atom table, so the
    grader compares a target by how it is written; with the reference's target alone, a
    right answer that says ``protein`` where the reference says ``polymer`` would be a
    success with target score 0."""
    assert len(alt_targets or []) == len(alternatives), suffix
    return {"entry": entry, "accessions": accessions, "wordings": wordings, "children": children,
            "alternatives": alternatives, "alt_targets": alt_targets or [],
            "target": target, "accepted": accepted,
            "derivation": derivation, "suffix": suffix, "named_by": named_by,
            "flags": flags or {}, "pack_extra": pack_extra, "words": words}


def cartoon_namings(entry: str) -> list[str]:
    """Selections that draw the same cartoon as ``polymer`` on the reference's entry.
    An answer on another accepted entry has no atom table to prove them equal, so each
    is listed as an accepted way of writing the answer."""
    t = C.table(entry)
    out = ["polymer", "all"]
    if t.static.get("protein") == t.static.get("polymer"):
        out.append("protein")
    return out


def whole_cartoon(entry, accessions, phrase, wordings, family, key, accepted, how, named_by,
                  **flags):
    col = C.colours(1, family, key)[0]
    namings = cartoon_namings(entry)
    scenes = [[C.drawn_comp(sel, "cartoon", col)] for sel in namings]
    return cand(entry, accessions, wordings, scenes[0], scenes[1:],
                [C.part("polymer", "cartoon", col)], accepted,
                f"{how}. The reference is a cartoon of the polymer of {entry.upper()}, one of "
                f"the {len(accepted)} accepted entries", key, named_by, flags,
                alt_targets=[[C.part(sel, "cartoon", col)] for sel in namings[1:]],
                P=phrase, c=a_colour(col))


NAME_WORDINGS = [
    "Show me a structure of {P} as {c} cartoon.",
    "Find a PDB entry of {P} and show it as {c} cartoon.",
    "I'd like to look at {P}. Any PDB structure of it will do; draw it as {c} cartoon.",
]
GENE_WORDINGS = [
    "Show me a structure of the protein encoded by the human gene {P}, as {c} cartoon.",
    "Find a PDB entry of human {P} and show it as {c} cartoon.",
    "I want to see a structure of human {P}; {c} cartoon will do.",
]


def single_proteins() -> list[tuple[str, str]]:
    """(accession, panel entry) for every protein a prompt can name on its own, on each
    of its panel entries that is itself an accepted entry."""
    out = []
    for acc in sorted(PROTEINS):
        if acc in PARTNER_ONLY:
            continue
        ok = set(accepted_entries([acc]))
        out += [(acc, e) for e in panel_entries_of(acc) if e in ok]
    return out


def gene_symbol(acc: str) -> str | None:
    """The gene symbol a prompt can use: the primary symbol of a human protein, three
    letters or more."""
    rec = protein(acc)
    if rec["organism"] != "Homo sapiens" or not rec["genes"] or len(rec["genes"][0]) < 3:
        return None
    return rec["genes"][0]


def t_name():
    out = []
    for acc, entry in single_proteins():
        phrase, piece, _ = PROTEINS[acc]
        if any(piece.lower() == g.lower() for g in protein(acc)["genes"]):
            continue                       # named by its gene symbol: the gene template
        out.append(whole_cartoon(
            entry, [acc], protein_phrase(acc), NAME_WORDINGS, "res-name", acc.lower(),
            accepted_entries([acc]),
            f"the prompt names {protein(acc)['uniprot_id']} ({acc}) by protein name; accepted "
            f"are the PDB entries of that accession", "protein name"))
    return out


def t_gene():
    out = []
    for acc, entry in single_proteins():
        symbol = gene_symbol(acc)
        if symbol is None:
            continue
        protein_phrase(acc)
        out.append(whole_cartoon(
            entry, [acc], symbol, GENE_WORDINGS, "res-gene", acc.lower(),
            accepted_entries([acc]),
            f"the prompt names {protein(acc)['uniprot_id']} ({acc}) by its human gene symbol "
            f"{symbol} (UniProt primary gene name); accepted are the PDB entries of that "
            "accession", "gene symbol"))
    return out


def t_complex():
    out = []
    for entry, (accessions, phrase) in sorted(COMPLEXES.items()):
        phrases = [protein_phrase(a) for a in accessions]
        accepted = accepted_entries(accessions)
        if entry not in accepted:
            continue
        if phrase is None:
            phrase = f"{phrases[0]} in complex with {C.join(phrases[1:])}"
        ids = C.join([f"{protein(a)['uniprot_id']} ({a})" for a in accessions])
        out.append(whole_cartoon(
            entry, accessions, phrase, NAME_WORDINGS, "res-complex",
            "-".join(a.lower() for a in accessions), accepted,
            f"the prompt names a complex of {ids}; accepted are the PDB entries that hold "
            "all of them", "complex of named proteins"))
    return out


def t_dna():
    out = []
    for acc, entry in single_proteins():
        t = C.table(entry)
        dna = [c for c in C.facts(entry)["chains"] if c["polymer_type"] == "DNA"]
        if not dna or t.static["protein"] | t.static["nucleic"] != t.static["polymer"] \
                or any(c["polymer_type"] not in ("DNA", "protein") for c in C.facts(entry)["chains"]):
            continue
        accepted = accepted_entries([acc], dna=True)
        assert entry in accepted, f"{entry}: RCSB reports no DNA entity"
        c1, c2 = C.colours(2, "res-dna", acc)
        out.append(cand(
            entry, [acc],
            ["Show me a structure of {P} bound to DNA: the protein as {c1} cartoon and the DNA "
             "as {c2} cartoon.",
             "Find a PDB entry of {P} in complex with DNA; draw the protein as {c1} cartoon and "
             "the DNA as {c2} cartoon.",
             "I want to see how {P} sits on DNA. Any PDB structure of the complex will do: "
             "protein as {c1} cartoon, DNA as {c2} cartoon."],
            [C.drawn_comp("protein", "cartoon", c1), C.drawn_comp("nucleic", "cartoon", c2)], [],
            [C.part("nucleic", "cartoon", c2)], accepted,
            f"the prompt names {protein(acc)['uniprot_id']} ({acc}) and asks for it on DNA; "
            f"accepted are the PDB entries of that accession that also hold a DNA entity. The "
            f"reference draws the protein and the nucleic acid of {entry.upper()}, one of the "
            f"{len(accepted)} accepted entries", acc.lower(), "protein name, bound to DNA",
            pack_extra=" and DNA",
            P=protein_phrase(acc), c1=a_colour(c1), c2=a_colour(c2)))
    return out


def t_ligand():
    out = []
    for acc, entry in single_proteins():
        t = C.table(entry)
        for g in C.facts(entry)["ligands"]:
            comp = g["comp_id"]
            named = G.checked_name(G.LIGAND_NAMES, comp, entry)
            if named is None or comp in LIGANDS_LEFT_OUT:
                continue
            accepted = accepted_entries([acc], comp=comp)
            assert entry in accepted, f"{entry}: RCSB lists no {comp}"
            if len(accepted) < MIN_LIGAND_ENTRIES:
                continue                   # a one-off additive, not a complex one asks for
            c1, c2 = C.colours(2, "res-ligand", acc, comp)
            sel = {"label_comp_id": comp}
            ligand_namings = [sel] + (["ligand"] if t.static.get("ligand") == C.mask_of(entry, sel)
                                      else [])
            pairs = [(p, l) for p in cartoon_namings(entry) for l in ligand_namings]
            scenes = [[C.drawn_comp(p, "cartoon", c1), C.drawn_comp(l, "ball_and_stick", c2)]
                      for p, l in pairs]
            out.append(cand(
                entry, [acc],
                ["Show me a structure of {P} with {L} bound: the protein as {c1} cartoon and "
                 "the {L} as {c2} ball-and-stick.",
                 "Find a PDB entry of {P} in complex with {L}; draw the protein as {c1} cartoon "
                 "and the {L} in {c2} ball-and-stick.",
                 "I want to see {L} bound to {P}. Any PDB structure of the complex will do: "
                 "protein as {c1} cartoon, {L} as {c2} ball-and-stick."],
                scenes[0], scenes[1:], [C.part(sel, "ball_and_stick", c2)], accepted,
                f"the prompt names {protein(acc)['uniprot_id']} ({acc}) and the ligand "
                f"{named[0]} (component {comp}; name checked against {named[1]}); accepted "
                f"are the PDB entries of that accession that hold a non-polymer {comp}. The "
                f"reference draws the polymer and every {comp} of {entry.upper()}, one of the "
                f"{len(accepted)} accepted entries",
                f"{acc.lower()}-{comp.lower()}", "protein name, with a named ligand",
                {"ligand_identity": named[0].upper() != comp},
                pack_extra=f" and {G.chem()[comp]['name']} (chemical code {comp})",
                alt_targets=[[C.part(l, "ball_and_stick", c2)] for _, l in pairs[1:]],
                P=protein_phrase(acc), L=named[0], c1=a_colour(c1), c2=C.say_colour(c2)))
    return out


# Order matters: a protein is claimed for one split by the first template that uses it.
TEMPLATES = {
    "res-complex": (t_complex, 4),
    "res-dna": (t_dna, 3),
    "res-ligand": (t_ligand, 11),
    "res-gene": (t_gene, 11),
    "res-name": (t_name, 12),
}

DERIVED = {
    "res-name": ("a protein, by name and organism",
                 "PDB entries of the protein's UniProt accession."),
    "res-gene": ("a human protein, by gene symbol",
                 "PDB entries of the accession whose primary gene name is the symbol."),
    "res-ligand": ("a protein and a ligand bound to it",
                   "PDB entries of the accession that hold the ligand's component as a "
                   "non-polymer entity (pairs found in fewer than three entries are not asked)."),
    "res-dna": ("a protein bound to DNA",
                "PDB entries of the accession that also hold a DNA entity."),
    "res-complex": ("a complex of two or three proteins",
                    "PDB entries that hold every one of the accessions."),
}


def choose() -> list[tuple[str, dict]]:
    """The candidates that become tasks. Per template: about 20% on held-back structures;
    one task per protein (or set of proteins); the least-used protein and structure
    first, then a seeded order. Across the tier, no protein is in both splits: the first
    task that uses a protein fixes its split, and later candidates that would put it in
    the other split are skipped."""
    claimed: dict[str, str] = {}
    per_protein: dict[str, int] = {}
    per_entry: dict[str, int] = {}
    out = []
    for family, (fn, n) in TEMPLATES.items():
        pool = C.shuffled(fn(), TIER, family)
        n_held = max(1, round(n * HELD_SHARE))
        quota = {"heldback": n_held, "public": n - n_held}
        done: set[frozenset] = set()
        while True:
            best = None
            for c in pool:
                split = C.split_of(c["entry"])
                if not quota[split] or frozenset(c["accessions"]) in done \
                        or per_entry.get(c["entry"], 0) >= C.MAX_PER_STRUCTURE \
                        or any(claimed.get(a, split) != split for a in c["accessions"]):
                    continue
                load = (max(per_protein.get(a, 0) for a in c["accessions"]),
                        per_entry.get(c["entry"], 0))
                if best is None or load < best[0]:
                    best = (load, c)
            if best is None:
                break
            c = best[1]
            split = C.split_of(c["entry"])
            quota[split] -= 1
            done.add(frozenset(c["accessions"]))
            per_entry[c["entry"]] = per_entry.get(c["entry"], 0) + 1
            for a in c["accessions"]:
                claimed[a] = split
                per_protein[a] = per_protein.get(a, 0) + 1
            out.append((family, c))
    return out


def repoint(scene: dict, entry: str, other: str) -> dict:
    return json.loads(json.dumps(scene).replace(C.url(entry), C.url(other)))


PACK_RULE = "resolve-v1"
PACK_ENTRIES = 10


def pack(accessions: list[str], accepted: list[str], extra: str) -> str:
    """The grounding pack of a resolve task: what an offline lookup of the names in the
    request would return. The UniProt record of each protein named, and the number of
    PDB entries that fit the request with the ``PACK_ENTRIES`` best-resolved of them
    (ties and entries without a resolution by id). It states facts and never says what
    to draw; the reference's entry gets no special mention."""
    lines = []
    for acc in accessions:
        rec = protein(acc)
        lines.append(f"Protein named in the request: UniProt {acc} ({rec['uniprot_id']}, "
                     f"{rec['names'][0]}; {rec['organism']}), {rec['length']} residues")
    info = protein(accessions[0])["entries"]

    def key(e: str):
        res = info[e][5]
        return (res if res is not None else float("inf"), e)

    best = sorted(accepted, key=key)[:PACK_ENTRIES]
    listed = ", ".join(
        f"{e.upper()} ({info[e][4] or 'method not given'}"
        + (f", {info[e][5]:.2f} A" if info[e][5] is not None else "") + ")" for e in best)
    what = "this protein" if len(accessions) == 1 else "all of these proteins together"
    lines.append(f"PDB entries with {what}{extra} (RCSB, {frozen()['retrieved']}): "
                 f"{len(accepted)}. " + (f"The {len(best)} with the best resolution: "
                                         if len(accepted) > len(best) else "They are: ") + listed)
    return "\n".join(lines)


def build() -> list[dict]:
    ids, ids_date = pdb_ids()
    retrieved = frozen()["retrieved"]
    built = []
    for family, c in choose():
        entry, accessions = c["entry"], c["accessions"]
        tid = f"{family}-{c['suffix']}"
        prompt = C.pick(c["wordings"], "wording", family, tid).format(**c["words"])
        accepted = c["accepted"]
        assert entry in accepted and set(accepted) <= ids, tid
        mapped = {a: sifts_residues(entry, a) for a in accessions}
        assert all(mapped.values()), f"{tid}: the frozen SIFTS table does not map {entry} to {mapped}"
        others = [e for e in accepted if e != entry]
        task = C.make_task(
            tid, TIER, family, entry, prompt, C.scene(entry, c["children"]), c["target"],
            script=SCRIPT, input_files=C.inputs(entry, *INPUT_FILES, "data/mvscore/pdb_ids.txt.gz"),
            derivation=c["derivation"],
            checks=[f"{entry.upper()} is in the accepted list, and the frozen PDBe SIFTS mapping "
                    "of the panel (a second source) maps it to "
                    + C.join([f"{a} ({n} observed residues)" for a, n in mapped.items()]),
                    f"every accepted id is a current PDB entry in the id list frozen on {ids_date}"],
            accepted=[C.scene(entry, kids) for kids in c["alternatives"]],
            difficulty=C.difficulty(entry, None, needs_entry_lookup=True, named_by=c["named_by"],
                                    **c["flags"]),
            extra_skills=["resolve"],
            provenance={"uniprot": accessions[0], "accessions": accessions,
                        "accepted_rule": COVERAGE_RULE, "n_accepted": len(accepted),
                        "accepted_retrieved": retrieved,
                        "accepted_source": "RCSB search API and GraphQL, frozen in "
                                           "data/mvscore/resolve_entries.json"},
            accepted_structures=others,
            **({"accepted_targets": c["alt_targets"]} if c["alt_targets"] else {}))
        task["grounding"] = {"rule": PACK_RULE, "text": pack(accessions, accepted, c["pack_extra"])}
        built.append(task)
    return sorted(built, key=lambda t: t["id"])


def check_answers(built: list[dict]) -> None:
    """Grade three made-up answers per task with the benchmark's grader: the reference's
    drawing on another accepted entry (must be exactly right), on a real PDB entry of
    something else, and on an id that does not exist (both must fail)."""
    ids = sorted(pdb_ids()[0])
    missing = next(f"{d}zzz" for d in "987654321" if f"{d}zzz" not in pdb_ids()[0])
    for t in built:
        entry = t["structures"][0]
        loaded = C.T._with_aliases({**json.loads(json.dumps(t)), "_path": f"tasks/mvs_resolve/{t['id']}.json"})
        own = set(t["accepted_structures"]) | {entry}
        wrong = C.pick([i for i in ids[:2000] if i not in own], "wrong-entry", t["id"])
        said = []
        if t["accepted_structures"]:
            other = C.pick(t["accepted_structures"], "other-entry", t["id"])
            res = C.runner.grade_parsed(loaded, repoint(t["reference"], entry, other))
            assert res["success"] and res["f1"] == 1.0, (t["id"], other, res)
            assert answer_outcome(t, other) == "accepted"
            for alt in t["accepted"]:
                res = C.runner.grade_parsed(loaded, repoint(alt, entry, other))
                assert res["success"] and res["target_f1"] == 1.0, (t["id"], other, res)
            said.append(f"the same drawing on another accepted entry ({other.upper()}) grades as "
                        "exactly right"
                        + (", and so does every accepted naming of it (success and target "
                           "score 1)" if t["accepted"] else ""))
        for bad, kind in ((wrong, "wrong_entry"), (missing, "no_such_entry")):
            res = C.runner.grade_parsed(loaded, repoint(t["reference"], entry, bad))
            assert not res["success"] and res["f1"] < 1.0, (t["id"], bad, res)
            assert answer_outcome(t, bad) == kind, (t["id"], bad)
        said.append(f"the same drawing on a PDB entry outside the list ({wrong.upper()}) and on "
                    f"an id that does not exist ({missing.upper()}) both fail")
        t["provenance"]["checks"] += said


def readme(built: list[dict]) -> str:
    rows = "\n".join(f"| `{f}` | {DERIVED[f][0]} | {DERIVED[f][1]} |" for f in sorted(DERIVED))
    sizes = sorted(t["provenance"]["n_accepted"] for t in built)
    proteins = {a for t in built for a in t["provenance"]["accessions"]}
    ids, ids_date = pdb_ids()
    return f"""# Resolve tier (MVS track)

Generated by `scripts/generate_resolve_tasks.py`; do not edit by hand. The request names
a protein, not a PDB entry, as real users do ("I wanna see a structure of PDE5A"); the
answer has to load an entry that really is that protein. A lookup tier: it also runs in
the grounding-pack condition.

Many entries are right, so each task lists them in `accepted_structures` (between
{sizes[0]} and {sizes[-1]} per task, median {sizes[len(sizes) // 2]}). The lists were retrieved from RCSB on
**{frozen()['retrieved']}** and are frozen in `data/mvscore/resolve_entries.json`; nothing is
looked up at grading time. An entry is accepted when {COVERAGE_RULE}. The
{MIN_RESIDUES}-residue floor keeps out entries that hold only a short peptide of the protein.

The reference is drawn on a panel entry from the list. It uses only selections that
mean the same on every entry (`polymer`, `protein`, `nucleic`, a component code), and
the grader re-reads it on whichever accepted entry the answer loaded.

{C.summary_tables(built)}

Proteins named: {len(proteins)}. No protein is in both splits. This tier has five
templates because there are few distinct ways to name a protein, so the largest
template holds more than the 12% aimed at in the other tiers.

## How each reference is derived

| template | the request names | accepted entries |
|---|---|---|
{rows}

Every prompt phrase for a protein is hand-written and checked by the script against
the frozen UniProt record: the name must be one of the record's protein or gene names,
and the organism word must fit the record's organism. Each reference entry is checked
against a second source, the panel's frozen PDBe SIFTS mapping. For every task the
script also grades three made-up answers with the benchmark's grader: the reference's
drawing on another accepted entry (exactly right), on a real entry of something else,
and on an id that does not exist (both fail).

## Known limits

- **Answers on entries outside the panel are compared by how the selection is written,
  not by atoms**, because only panel entries have a frozen atom table. So that harmless
  namings still pass there, each task lists them under `accepted` (the cartoon on
  `polymer`, `all` or, where the reference entry is all protein, `protein`; the ligand by
  component code or, where equal on the reference entry, `ligand`). A selection by chain
  id on a non-panel entry cannot be credited. Each accepted naming has its own
  target (`accepted_targets`), so a right answer there also has target score 1.
- **The lists follow UniProt accessions.** An entry of the right protein that RCSB maps
  to no accession, or to another one (an orthologue the prompt's organism word
  excludes), is not accepted. Proteins carried by several genes, and ligands deposited
  under several component codes, are left out of this tier for that reason.
- **The lists are a snapshot** of {frozen()['retrieved']}; entries released later are not in them.

## Made-up ids

`data/mvscore/pdb_ids.txt.gz` is the list of all {len(ids)} PDB ids current on {ids_date}
(RCSB holdings). `generate_resolve_tasks.answer_outcome(task, pdb_id)` uses it to sort
an answer's entry into `accepted`, `wrong_entry` (a real entry of something else) or
`no_such_entry` (the id does not exist), the three-way outcome of LEDGER L-041.

Replaces the six earlier tasks (PDE5A, PCSK9, CFTR, GFP, myoglobin, lysozyme); the
same proteins are named here by the templates above.
"""


def main() -> int:
    args = C.cli(__doc__)
    if args.refresh:
        refresh()
        frozen.cache_clear()
        pdb_ids.cache_clear()
    built = C.verify(build(), OUT)
    check_answers(built)
    return C.finish(built, OUT, args, readme(built))


if __name__ == "__main__":
    raise SystemExit(main())
