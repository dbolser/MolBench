#!/usr/bin/env python3
"""
Build the structure panel and its frozen data layer.

Input: ``data/panel/seed.json`` (hand-written: named entries with the features we
claim for them, disease proteins by UniProt accession, AlphaFold accessions).
The selection rule is written out in ``data/panel/README.md``; this script applies
it, verifies every claim against the deposited file, and writes:

  data/panel/panel.json            the panel: one record per entry (why, families, checks)
  data/panel/PANEL.md              the same as a table (generated, do not edit)
  data/panel/cif/<id>.cif.gz       the exact structure file everything below was built from
  data/panel/facts/<id>.json       grounding facts (chains, ligands, disulfides, glycans,
                                   assemblies, numbering offsets, ...)
  data/panel/variants/<ACC>.json   pathogenic ClinVar missense variants (UniProt Variation
                                   API), mapped to panel structures with the wild-type
                                   residue checked
  molbench/sifts_tables/<id>.json.gz   per-residue UniProt <-> label/auth numbering (SIFTS)

Atom tables are built separately (they need headless Mol*):
``python scripts/build_atom_tables.py --panel``.

Network is used at build time only: RCSB (files, GraphQL, holdings), PDBe (SIFTS
"updated" mmCIF, best_structures), UniProt (REST, Proteins Variation API) and
AlphaFold DB. Structure files are frozen in ``data/panel/cif/``; API responses are
cached under ``data/grounding_cache/`` (git-ignored) with their retrieval date.

A rebuild is **frozen-first**: whatever the tracked files already record (which
structure a disease protein got, each variant list, each SIFTS table, entry titles)
is kept, so a plain re-run needs no network and changes nothing — it re-derives the
facts, the variant mapping and the panel table from the frozen files. ``--refresh``
asks the services again instead (new ClinVar submissions, new PDB entries and SIFTS
releases will then move things; review the diff). A new entry in ``seed.json`` is
fetched either way.

    uv run --all-extras python scripts/build_panel.py            # rebuild from frozen data
    uv run --all-extras python scripts/build_panel.py --refresh  # ask the services again
    uv run --all-extras python scripts/build_panel.py --check    # verify frozen files only
"""

from __future__ import annotations

import argparse
import datetime
import gzip
import hashlib
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter

import gemmi

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import build_atom_tables as bat  # noqa: E402
from molbench import sifts  # noqa: E402

PANEL = REPO / "data" / "panel"
FACTS = PANEL / "facts"
VARIANTS = PANEL / "variants"
CACHE = REPO / "data" / "grounding_cache"

RULE = "panel-v1"
MAX_ATOMS = 15000           # deposited atoms; entries tasks already use are exempt
DISEASE_MAX_RESOLUTION = 2.5
DISEASE_FALLBACK_RESOLUTION = 3.5
DISEASE_SHORTLIST = 30      # candidates per protein that get RCSB metadata
MIN_DISEASE_PROTEINS = 12
MIN_OFFSET_PROTEINS = 8
MIN_VERIFIED_VARIANTS = 3   # a disease protein counts only with at least this many

UPDATED_CIF = "https://www.ebi.ac.uk/pdbe/entry-files/download/{}_updated.cif"
BEST = "https://www.ebi.ac.uk/pdbe/graph-api/mappings/best_structures/{}"
VARIATION = "https://www.ebi.ac.uk/proteins/api/variation/{}"
UNIPROT = ("https://rest.uniprot.org/uniprotkb/{}.json"
           "?fields=id,protein_name,gene_primary,organism_name,length")
AFDB = "https://alphafold.ebi.ac.uk/api/prediction/{}"
RCSB_GRAPHQL = "https://data.rcsb.org/graphql"
RCSB_STATUS = "https://data.rcsb.org/rest/v1/holdings/status?ids={}"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/{}.fcgi"
# ClinVar's aggregate germline classifications that count as pathogenic (a trailing
# qualifier such as "; risk factor" or ", low penetrance" is ignored).
CLINVAR_PATHOGENIC = {"Pathogenic", "Likely pathogenic", "Pathogenic/Likely pathogenic"}
NOT_PATHOGENIC_IN_CLINVAR = "ClinVar's aggregate germline classification is not pathogenic"

AA3 = {"ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q", "GLU": "E",
       "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F",
       "PRO": "P", "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V"}
NUCLEOTIDES = {"A", "C", "G", "U", "DA", "DC", "DG", "DT", "DU", "I", "DI"}
WATER = {"HOH", "DOD"}
UNKNOWN = {"UNK", "N", "DN", "UNX", "UNL"}   # placeholders for unidentified residues
HEMES = {"HEM", "HEC", "HEA", "HEB", "HDD", "HAS"}
METALS = set("LI NA K RB CS MG CA SR BA MN FE CO NI CU ZN CD HG MO W V CR PT AU AG PB AL "
             "GA TL SM GD TB YB LU LA EU HO ER IR OS RU RH PD".split())
MEMBRANE_SOURCES = {"PDBTM", "OPM", "MemProtMD", "mpstruc"}   # recorded per entry
TRANSMEMBRANE_SOURCES = {"PDBTM", "mpstruc"}  # 'membrane' needs one of these (OPM also
                                              # lists peripheral proteins, e.g. prothrombin)
REFRESH = False             # --refresh: ignore the cache and the frozen answers


def old_panel() -> dict:
    path = PANEL / "panel.json"
    return json.loads(path.read_text()) if path.exists() and not REFRESH else {}


def old_entry(entry: str) -> dict | None:
    return next((e for e in old_panel().get("entries", []) if e["id"] == entry), None)


# --- fetching (build time only) ----------------------------------------------------

def _get(url: str, data: bytes | None = None, headers: dict | None = None) -> bytes:
    hdr = {"User-Agent": "structure-panel-builder"}
    hdr.update(headers or {})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=hdr),
                                        timeout=180) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                raise
            err = e
        except OSError as e:
            err = e
        time.sleep(2 * (attempt + 1))
    raise err


def _today() -> str:
    return datetime.datetime.now(datetime.timezone.utc).date().isoformat()


def cached(name: str, url: str, fetch=None) -> dict:
    """{'url', 'retrieved', 'data'} for an API response, fetched once."""
    path = CACHE / f"panel_{name}.json"
    if path.exists() and not REFRESH:
        return json.loads(path.read_text())
    data = fetch() if fetch else json.loads(_get(url, headers={"Accept": "application/json"}))
    rec = {"url": url, "retrieved": _today(), "data": data}
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec, separators=(",", ":")))
    return rec


def graphql(query: str) -> dict:
    return json.loads(_get(RCSB_GRAPHQL, json.dumps({"query": query}).encode(),
                           {"Content-Type": "application/json"}))["data"]


_ENTRY_FIELDS = ("rcsb_id struct{title} rcsb_accession_info{deposit_date} "
                 "rcsb_entry_info{deposited_atom_count resolution_combined experimental_method "
                 "polymer_entity_count deposited_model_count} "
                 "polymer_entities{entity_poly{rcsb_mutation_count} "
                 "rcsb_polymer_entity_container_identifiers{uniprot_ids} "
                 "rcsb_polymer_entity_annotation{type}}")


def rcsb_entries(ids: list[str]) -> dict[str, dict]:
    """Summary metadata per entry id (lower case). Missing ids are absent."""
    out = {}
    for i in range(0, len(ids), 100):
        batch = json.dumps([x.upper() for x in ids[i:i + 100]])
        for e in graphql("{entries(entry_ids:%s){%s}}" % (batch, _ENTRY_FIELDS))["entries"] or []:
            info = e["rcsb_entry_info"]
            ents = e["polymer_entities"] or []
            out[e["rcsb_id"].lower()] = {
                "title": e["struct"]["title"],
                "deposited": e["rcsb_accession_info"]["deposit_date"][:10],
                "atoms": info["deposited_atom_count"],
                "resolution": (info.get("resolution_combined") or [None])[0],
                "method": info["experimental_method"],
                "models": info["deposited_model_count"],
                "polymer_entities": info["polymer_entity_count"],
                "mutations": sum((p["entity_poly"] or {}).get("rcsb_mutation_count") or 0
                                 for p in ents),
                "uniprot": sorted({u for p in ents for u in
                                   (p["rcsb_polymer_entity_container_identifiers"]
                                    .get("uniprot_ids") or [])}),
                "membrane_sources": sorted({a["type"] for p in ents
                                            for a in (p.get("rcsb_polymer_entity_annotation") or [])
                                            if a["type"] in MEMBRANE_SOURCES}),
            }
    return out


def rcsb_meta(pdb: str) -> dict:
    old = old_entry(pdb)
    if old and not (CACHE / f"panel_rcsb_{pdb}.json").exists():
        return {k: old[k] for k in ("title", "method", "resolution", "deposited",
                                    "membrane_sources")}
    return cached(f"rcsb_{pdb}", RCSB_GRAPHQL, lambda: rcsb_entries([pdb]).get(pdb))["data"]


def rcsb_status(pdb: str) -> str:
    if old_entry(pdb) and not (CACHE / f"panel_status_{pdb}.json").exists():
        return "CURRENT"  # as checked when it was frozen; --refresh asks again
    def fetch():
        got = json.loads(_get(RCSB_STATUS.format(pdb.upper())))
        return got[0]["rcsb_repository_holdings_combined"]["status"] if got else "MISSING"
    return cached(f"status_{pdb}", RCSB_STATUS.format(pdb.upper()), fetch)["data"]


def uniprot_info(acc: str) -> dict:
    d = cached(f"uniprot_{acc}", UNIPROT.format(acc))["data"]
    desc = d.get("proteinDescription", {})
    name = (desc.get("recommendedName") or (desc.get("submissionNames") or [{}])[0]
            ).get("fullName", {}).get("value", "")
    genes = d.get("genes") or [{}]
    return {"entry_name": d.get("uniProtkbId", ""), "protein": name,
            "gene": (genes[0].get("geneName") or {}).get("value", ""),
            "organism": (d.get("organism") or {}).get("scientificName", ""),
            "length": (d.get("sequence") or {}).get("length")}


def updated_cif(pdb: str) -> pathlib.Path:
    """PDBe's SIFTS-annotated mmCIF (the file the PDBe viewer loads). Cached, not frozen."""
    path = bat.CACHE / f"{pdb}_updated.cif"
    if not path.exists():
        bat.CACHE.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_get(UPDATED_CIF.format(pdb)))
    return path


def _retrieved(path: pathlib.Path) -> str:
    return datetime.datetime.fromtimestamp(path.stat().st_mtime,
                                           datetime.timezone.utc).date().isoformat()


def af_id(acc: str) -> str:
    """The panel id of an accession's current AlphaFold DB model, e.g. af-p04637-f1-model_v6."""
    old = next((e["id"] for e in old_panel().get("entries", [])
                if f"alphafold:{acc}" in e["origin"]), None)
    if old:
        return old
    d = cached(f"afdb_{acc}", AFDB.format(acc))["data"][0]
    return d["cifUrl"].rsplit("/", 1)[-1].rsplit(".", 1)[0].lower()


def af_meta(entry: str) -> dict:
    acc = entry.split("-")[1].upper()
    old = old_entry(entry)
    if old and not (CACHE / f"panel_afdb_{acc}.json").exists():
        return {k: old[k] for k in ("title", "method", "resolution", "deposited",
                                    "membrane_sources")}
    a = cached(f"afdb_{acc}", AFDB.format(acc))["data"][0]
    return {"title": f"AlphaFold DB model of {a['uniprotDescription']} "
                     f"({a['gene']}, {a['organismScientificName']})",
            "method": "AlphaFold prediction", "resolution": None,
            "deposited": a["modelCreatedDate"][:10], "membrane_sources": []}


# --- small mmCIF helpers ------------------------------------------------------------

def rows(block, prefix: str, tags: list[str]) -> list[dict]:
    """A category as dicts; absent columns and '.'/'?' values read as None."""
    have = [t for t in tags if block.find_values(prefix + t)]
    if not have:
        return []
    out = []
    for r in block.find(prefix, have):
        d = dict.fromkeys(tags)
        for t, v in zip(have, r):
            d[t] = None if v in (".", "?") else gemmi.cif.as_string(v)
        out.append(d)
    return out


def _int(v):
    return int(v) if v not in (None, "") else None


def residues_of(cols: dict[str, list]) -> list[dict]:
    """Model 1's residues in file order (Mol*'s residue segmentation), with atom rows."""
    out, prev = [], None
    for i, ri in enumerate(cols["residue_index"]):
        if ri != prev:
            out.append({"label_asym_id": cols["label_asym_id"][i],
                        "auth_asym_id": cols["auth_asym_id"][i],
                        "label_entity_id": cols["label_entity_id"][i],
                        "label_seq_id": cols["label_seq_id"][i],
                        "auth_seq_id": cols["auth_seq_id"][i],
                        "pdbx_PDB_ins_code": cols["pdbx_PDB_ins_code"][i],
                        "comp_id": cols["label_comp_id"][i], "first": i, "last": i})
            prev = ri
        out[-1]["last"] = i
    return out


# --- SIFTS tables -------------------------------------------------------------------

def build_sifts(entry: str, cols: dict[str, list]) -> dict | None:
    """The frozen per-residue UniProt mapping, or None if the entry has none.

    Observed residues come from ``_atom_site.pdbx_sifts_xref_db_*`` at each residue's
    first atom: the same columns, read the same way, as Mol*'s SIFTSMapping property
    that the PDBe viewer's ``uniprot_accession`` selections use. Residues in the
    construct but not in the model come from ``_pdbx_sifts_xref_db``.
    """
    if entry.startswith("af-"):
        path, source = bat.fetch_cif(entry), bat.source_url(entry)
    else:
        frozen = sifts.TABLES / f"{entry}.json.gz"
        cache = bat.CACHE / f"{entry}_updated.cif"
        if not REFRESH and not cache.exists() and (frozen.exists() or old_entry(entry)):
            return json.loads(gzip.decompress(frozen.read_bytes())) if frozen.exists() else None
        if REFRESH:
            cache.unlink(missing_ok=True)
        path, source = updated_cif(entry), UPDATED_CIF.format(entry)
    block = gemmi.cif.read(str(path)).sole_block()
    tags = ["label_asym_id", "label_seq_id", "auth_asym_id", "auth_seq_id", "pdbx_PDB_ins_code",
            "label_comp_id", "pdbx_PDB_model_num", "pdbx_sifts_xref_db_name",
            "pdbx_sifts_xref_db_acc", "pdbx_sifts_xref_db_num", "pdbx_sifts_xref_db_res"]
    if not block.find_values("_atom_site.pdbx_sifts_xref_db_acc"):
        return None
    table = block.find("_atom_site.", tags)
    first_model = table[0][6]
    ours = residues_of(cols)
    out_rows, seen, k, prev = [], set(), -1, None
    mismatched = 0
    for r in table:
        if r[6] != first_model:
            break
        key = (r[0], r[1], r[3], r[4], r[5])
        if key == prev:
            continue
        prev = key
        k += 1
        ins = "" if r[4] in (".", "?") else r[4]
        seq = 0 if r[1] in (".", "?") else int(r[1])
        o = ours[k] if k < len(ours) else None
        if o is None or (o["label_asym_id"], o["label_seq_id"], o["auth_asym_id"],
                         o["auth_seq_id"], o["pdbx_PDB_ins_code"], o["comp_id"]) != (
                             r[0], seq, r[2], int(r[3]), ins, r[5]):
            mismatched += 1
            continue
        if r[7] in (".", "?") or r[8] in (".", "?") or r[9] in (".", "?"):
            continue
        out_rows.append((r[8], int(r[9]), "" if r[10] in (".", "?") else r[10], r[0], seq, r[5],
                         r[2], int(r[3]), ins, 1))
        seen.add((r[0], seq, r[8]))
    if mismatched or k + 1 != len(ours):
        raise SystemExit(f"{entry}: the SIFTS file's residues differ from the frozen structure "
                         f"file ({mismatched} mismatched, {k + 1} vs {len(ours)} residues)")

    # Residues in the construct that were not modelled.
    scheme = {(s["asym_id"], _int(s["seq_id"])): s for s in
              rows(block, "_pdbx_poly_seq_scheme.",
                   ["asym_id", "seq_id", "pdb_strand_id", "pdb_seq_num", "pdb_ins_code"])}
    xref = rows(block, "_pdbx_sifts_xref_db.",
                ["asym_id", "seq_id", "mon_id", "unp_res", "unp_num", "unp_acc", "observed"])
    xref_observed = set()
    for x in xref:
        if not x["unp_acc"] or not x["unp_num"]:
            continue
        key = (x["asym_id"], int(x["seq_id"]), x["unp_acc"])
        if x["observed"] == "y":
            xref_observed.add(key)
            continue
        if key in seen:
            continue
        seen.add(key)
        s = scheme.get(key[:2]) or {}
        out_rows.append((x["unp_acc"], int(x["unp_num"]), x["unp_res"] or "", x["asym_id"],
                         int(x["seq_id"]), x["mon_id"], s.get("pdb_strand_id"),
                         _int(s.get("pdb_seq_num")), s.get("pdb_ins_code") or "", 0))
    observed = {(r[3], r[4], r[0]) for r in out_rows if r[9]}
    if not out_rows:
        return None
    accs = sorted({r[0] for r in out_rows})
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    old = sifts.load(entry)
    retrieved = old.retrieved if old and old.source_sha256 == sha else _retrieved(path)
    names = ("accession", "unp_num", "unp_res", "label_asym_id", "label_seq_id", "comp_id",
             "auth_asym_id", "auth_seq_id", "pdbx_PDB_ins_code", "observed")
    return {"id": entry, "source": source, "retrieved": retrieved, "source_sha256": sha,
            "accessions": {a: (old.accessions.get(a) if old and not REFRESH else None)
                           or uniprot_info(a.split("-")[0]) for a in accs},
            # Residues the per-residue category calls observed but atom_site does not map
            # (or the reverse); 0 for a self-consistent file.
            "xref_disagreements": len(observed ^ xref_observed) if xref else 0,
            "columns": {n: [r[i] for r in out_rows] for i, n in enumerate(names)}}


def write_sifts(entry: str, data: dict | None) -> None:
    out = sifts.TABLES / f"{entry}.json.gz"
    if data is None:
        out.unlink(missing_ok=True)
        return
    bat.write_gz_json(out, data)


# --- grounding facts ----------------------------------------------------------------

def _runs(res: list[dict], other: str) -> list[list]:
    """Residues -> runs [auth_first, auth_last, other_first, other_last] where both
    numberings step by +1 and no insertion code occurs (auth as text, with ins code)."""
    runs: list[list] = []
    for r in res:
        a, ins, x = r["auth_seq_id"], r["pdbx_PDB_ins_code"], r[other]
        if (runs and not ins and not runs[-1][4] and a == runs[-1][5] + 1
                and x == runs[-1][3] + 1):
            runs[-1][1], runs[-1][3], runs[-1][5] = str(a), x, a
        else:
            runs.append([f"{a}{ins}", f"{a}{ins}", x, x, bool(ins), a])
    return [r[:4] for r in runs]


def _where(r: dict) -> dict:
    return {"auth_asym_id": r["auth_asym_id"], "auth_seq_id": r["auth_seq_id"],
            "pdbx_PDB_ins_code": r["pdbx_PDB_ins_code"], "label_asym_id": r["label_asym_id"],
            "label_seq_id": r["label_seq_id"], "comp_id": r["comp_id"]}


def _oper_count(expr: str) -> tuple[int, list[str]]:
    """Operators in an oper_expression like '1,2', '(1-60)' or '(1-5)(61-88)'."""
    total, ids = 1, []
    for group in re.findall(r"\(([^)]*)\)", expr) or [expr]:
        part = []
        for item in group.split(","):
            m = re.fullmatch(r"\s*(\d+)-(\d+)\s*", item)
            part += [str(i) for i in range(int(m[1]), int(m[2]) + 1)] if m else [item.strip()]
        total *= len(part)
        ids += part
    return total, ids


def build_facts(entry: str, cols: dict[str, list], smap: dict | None) -> dict:
    block = gemmi.cif.read(str(bat.fetch_cif(entry))).sole_block()
    s = lambda tag: (lambda v: None if v in (None, "?", ".") else gemmi.cif.as_string(v))(
        block.find_value(tag))
    res = residues_of(cols)
    n_models = len(set(block.find_values("_atom_site.pdbx_PDB_model_num")))
    comp = {c["id"]: c for c in rows(block, "_chem_comp.", ["id", "type", "name", "formula"])}
    is_sugar = lambda c: "saccharide" in ((comp.get(c) or {}).get("type") or "").lower()

    # Entities and chains.
    poly = {p["entity_id"]: p for p in rows(block, "_entity_poly.", ["entity_id", "type"])}
    seqres = Counter(p["entity_id"] for p in rows(block, "_entity_poly_seq.", ["entity_id", "num"]))

    def polytype(eid):
        t = (poly.get(eid) or {}).get("type") or ""
        return ("protein" if "polypeptide" in t else "DNA/RNA" if "hybrid" in t else
                "DNA" if "deoxyribo" in t else "RNA" if "ribo" in t else t or None)

    asyms: dict[str, list[dict]] = {}
    for r in res:
        asyms.setdefault(r["label_asym_id"], []).append(r)
    entities = []
    etype = {}
    for e in rows(block, "_entity.", ["id", "type", "pdbx_description"]):
        etype[e["id"]] = e["type"]
        entities.append({"id": e["id"], "type": e["type"], "polymer_type": polytype(e["id"]),
                         "description": e["pdbx_description"],
                         "label_asym_ids": [a for a, rr in asyms.items()
                                            if rr[0]["label_entity_id"] == e["id"]]})

    by_sifts: dict[tuple, list] = {}
    if smap:
        c = smap["columns"]
        for i in range(len(c["accession"])):
            if c["observed"][i]:
                by_sifts.setdefault((c["label_asym_id"][i], c["accession"][i]), []).append(
                    {"unp_num": c["unp_num"][i], "auth_seq_id": c["auth_seq_id"][i],
                     "pdbx_PDB_ins_code": c["pdbx_PDB_ins_code"][i]})

    chains = []
    for a, rr in asyms.items():
        eid = rr[0]["label_entity_id"]
        if etype.get(eid) != "polymer":
            continue
        d = Counter(r["auth_seq_id"] - r["label_seq_id"] for r in rr)
        unp = []
        for (asym, acc), mm in sorted(by_sifts.items()):
            if asym != a:
                continue
            off = Counter(m["auth_seq_id"] - m["unp_num"] for m in mm)
            n_ins = sum(1 for m in mm if m["pdbx_PDB_ins_code"])
            unp.append({"accession": acc, "n_residues": len(mm),
                        "unp_first": min(m["unp_num"] for m in mm),
                        "unp_last": max(m["unp_num"] for m in mm),
                        "auth_minus_unp": {str(k): v for k, v in sorted(off.items())},
                        "n_insertion_codes": n_ins,
                        "same_numbering": set(off) == {0} and not n_ins,
                        "runs_auth_unp": _runs(mm, "unp_num")})
        chains.append({"auth_asym_id": rr[0]["auth_asym_id"], "label_asym_id": a,
                       "entity_id": eid, "polymer_type": polytype(eid),
                       "seqres_length": seqres.get(eid), "n_observed": len(rr),
                       "auth_minus_label": {str(k): v for k, v in sorted(d.items())},
                       "n_insertion_codes": sum(1 for r in rr if r["pdbx_PDB_ins_code"]),
                       "runs_auth_label": _runs(rr, "label_seq_id"), "uniprot": unp})

    # Hetero groups.
    def heavy(r):
        names = []
        for i in range(r["first"], r["last"] + 1):
            if cols["type_symbol"][i] not in ("H", "D") and cols["label_atom_id"][i] not in names:
                names.append(cols["label_atom_id"][i])
        return names

    def elements(r):
        return {cols["type_symbol"][i] for i in range(r["first"], r["last"] + 1)}

    groups: dict[str, list[dict]] = {}
    n_water = 0
    for r in res:
        t = etype.get(r["label_entity_id"])
        if r["comp_id"] in WATER:
            n_water += 1
        elif t == "non-polymer":
            groups.setdefault(r["comp_id"], []).append(r)
    ligands = []
    for c in sorted(groups):
        first = groups[c][0]
        names = heavy(first)
        metal = sorted(elements(first) & METALS)
        ligands.append({"comp_id": c, "name": (comp.get(c) or {}).get("name"),
                        "formula": (comp.get(c) or {}).get("formula"),
                        "kind": ("ion" if len(names) == 1 else "sugar" if is_sugar(c)
                                 else "ligand"),
                        "metals": metal, "heme": c in HEMES, "n_heavy_atoms": len(names),
                        "atoms": names,
                        "copies": [_where(r) for r in groups[c]]})

    # Bonds listed in the file.
    at = {(r["label_asym_id"], r["label_seq_id"], r["auth_seq_id"], r["pdbx_PDB_ins_code"]): r
          for r in res}
    conn = rows(block, "_struct_conn.", [
        "conn_type_id", "pdbx_dist_value", "ptnr1_symmetry", "ptnr2_symmetry",
        *[f"{p}{k}" for p in ("ptnr1_", "ptnr2_")
          for k in ("label_asym_id", "label_comp_id", "label_seq_id", "label_atom_id",
                    "auth_asym_id", "auth_seq_id")],
        "pdbx_ptnr1_PDB_ins_code", "pdbx_ptnr2_PDB_ins_code"])

    def partner(c, n):
        p = f"ptnr{n}_"
        return {"auth_asym_id": c[p + "auth_asym_id"], "auth_seq_id": _int(c[p + "auth_seq_id"]),
                "pdbx_PDB_ins_code": c[f"pdbx_ptnr{n}_PDB_ins_code"] or "",
                "label_asym_id": c[p + "label_asym_id"],
                "label_seq_id": _int(c[p + "label_seq_id"]) or 0,
                "comp_id": c[p + "label_comp_id"], "atom": c[p + "label_atom_id"]}

    disulfides, metal_bonds, covalent = [], [], []
    for c in conn:
        a, b = partner(c, 1), partner(c, 2)
        sym = (c["ptnr1_symmetry"] or "1_555") != (c["ptnr2_symmetry"] or "1_555")
        rec = {"a": a, "b": b, "distance": float(c["pdbx_dist_value"]) if c["pdbx_dist_value"]
               else None, "to_symmetry_copy": sym}
        kind = (c["conn_type_id"] or "").lower()
        if kind == "disulf":
            disulfides.append(rec)
        elif kind == "metalc":
            metal_bonds.append(rec)
        elif kind.startswith("covale"):
            covalent.append(rec)

    # Glycans: branched entities, and where sugars attach to the polymer.
    def is_poly(p):
        return etype.get((asyms.get(p["label_asym_id"]) or [{}])[0].get("label_entity_id")
                         ) == "polymer"
    sites = [{"residue": p, "sugar": q} for c in covalent
             for p, q in ((c["a"], c["b"]), (c["b"], c["a"]))
             if is_poly(p) and not is_poly(q) and is_sugar(q["comp_id"])]
    glycans = []
    for a, rr in asyms.items():
        eid = rr[0]["label_entity_id"]
        if etype.get(eid) != "branched":
            continue
        site = next((x["residue"] for x in sites if x["sugar"]["label_asym_id"] == a), None)
        glycans.append({"label_asym_id": a, "auth_asym_id": rr[0]["auth_asym_id"],
                        "entity_id": eid,
                        "description": next(e["description"] for e in entities
                                            if e["id"] == eid),
                        "residues": [{"comp_id": r["comp_id"], "auth_seq_id": r["auth_seq_id"]}
                                     for r in rr],
                        "attached_to": site})

    # Non-standard residues inside polymer chains.
    modified = [_where(r) for r in res
                if etype.get(r["label_entity_id"]) == "polymer"
                and r["comp_id"] not in AA3 and r["comp_id"] not in NUCLEOTIDES
                and r["comp_id"] not in UNKNOWN]

    # Assemblies.
    opers = {o["id"]: o for o in rows(block, "_pdbx_struct_oper_list.", ["id", "type", "name"])}
    gens: dict[str, list] = {}
    for g in rows(block, "_pdbx_struct_assembly_gen.",
                  ["assembly_id", "oper_expression", "asym_id_list"]):
        gens.setdefault(g["assembly_id"], []).append(g)
    polymer_asyms = {c["label_asym_id"] for c in chains}
    assemblies = []
    for a in rows(block, "_pdbx_struct_assembly.",
                  ["id", "details", "method_details", "oligomeric_details", "oligomeric_count"]):
        copies: Counter = Counter()
        identity_only = True
        for g in gens.get(a["id"], []):
            n, ids = _oper_count(g["oper_expression"])
            if any((opers.get(i) or {}).get("type") != "identity operation" for i in ids):
                identity_only = False
            for asym in g["asym_id_list"].split(","):
                copies[asym.strip()] += n
        used = {x for x in copies if x in polymer_asyms}
        relation = ("same as deposited" if identity_only and used == polymer_asyms else
                    "part of deposited" if identity_only else "built by symmetry")
        assemblies.append({
            "id": a["id"], "details": a["details"], "method": a["method_details"],
            "oligomeric_details": a["oligomeric_details"],
            "oligomeric_count": _int(a["oligomeric_count"]),
            "polymer_chain_copies": {x: copies[x] for x in sorted(used)},
            "n_polymer_chains": sum(copies[x] for x in used),
            "relation_to_deposited": relation})

    helices = [{"auth_asym_id": h["beg_auth_asym_id"], "beg_auth_seq_id": _int(h["beg_auth_seq_id"]),
                "end_auth_seq_id": _int(h["end_auth_seq_id"]),
                "label_asym_id": h["beg_label_asym_id"],
                "beg_label_seq_id": _int(h["beg_label_seq_id"]),
                "end_label_seq_id": _int(h["end_label_seq_id"])}
               for h in rows(block, "_struct_conf.", [
                   "conf_type_id", "beg_auth_asym_id", "beg_auth_seq_id", "end_auth_seq_id",
                   "beg_label_asym_id", "beg_label_seq_id", "end_label_seq_id"])
               if (h["conf_type_id"] or "").upper().startswith("HELX")]
    strands = [{"auth_asym_id": h["beg_auth_asym_id"], "beg_auth_seq_id": _int(h["beg_auth_seq_id"]),
                "end_auth_seq_id": _int(h["end_auth_seq_id"]),
                "label_asym_id": h["beg_label_asym_id"],
                "beg_label_seq_id": _int(h["beg_label_seq_id"]),
                "end_label_seq_id": _int(h["end_label_seq_id"]), "sheet_id": h["sheet_id"]}
               for h in rows(block, "_struct_sheet_range.", [
                   "sheet_id", "beg_auth_asym_id", "beg_auth_seq_id", "end_auth_seq_id",
                   "beg_label_asym_id", "beg_label_seq_id", "end_label_seq_id"])]

    res_tag = next((t for t in ("_refine.ls_d_res_high", "_em_3d_reconstruction.resolution")
                    if s(t)), None)
    facts = {
        "id": entry, "kind": "alphafold" if entry.startswith("af-") else "pdb",
        "source": bat.source_url(entry),
        "title": s("_struct.title"), "method": s("_exptl.method"),
        "resolution": float(s(res_tag)) if res_tag else None,
        "n_models": n_models, "n_atoms": len(cols["atom_id"]), "n_residues": len(res),
        "entities": entities, "chains": chains, "ligands": ligands,
        "disulfides": disulfides, "metal_bonds": metal_bonds, "covalent_links": covalent,
        "glycans": glycans, "glycosylation_sites": sites, "modified_residues": modified,
        "assemblies": assemblies, "helices": helices, "strands": strands, "waters": n_water,
        "numbering": {
            "auth_chain_differs_from_label_chain": any(
                c["auth_asym_id"] != c["label_asym_id"] for c in chains),
            "auth_number_differs_from_label_number": any(
                set(c["auth_minus_label"]) != {"0"} or c["n_insertion_codes"] for c in chains),
            "insertion_codes": any(c["n_insertion_codes"] for c in chains),
            "auth_number_differs_from_uniprot": any(
                not u["same_numbering"] for c in chains for u in c["uniprot"]),
        },
    }
    if facts["kind"] == "alphafold":
        b = [float(x) for x in block.find_values("_ma_qa_metric_local.metric_value")]
        facts["plddt"] = {"per_residue": b, "mean": round(sum(b) / len(b), 2) if b else None}
    return facts


def features(facts: dict, meta: dict) -> list[str]:
    """What the file shows, in the vocabulary seed.json claims are written in."""
    f = set()
    ptypes = {c["polymer_type"] for c in facts["chains"]}
    lig = facts["ligands"]
    if any(x["kind"] == "ligand" for x in lig):
        f.add("ligand")
    if any(x["heme"] for x in lig):
        f.add("heme")
    if any(x["metals"] for x in lig):
        f.add("metal")
    if facts["disulfides"]:
        f.add("disulfide")
    if ptypes & {"DNA", "RNA", "DNA/RNA"}:
        f.add("nucleic")
    if "protein" in ptypes and ptypes & {"DNA", "DNA/RNA"}:
        f.add("protein-dna")
    if facts["glycans"]:
        f.add("glycan")
    if facts["assemblies"] and facts["assemblies"][0]["relation_to_deposited"] != "same as deposited":
        f.add("assembly-differs")
    if facts["numbering"]["insertion_codes"]:
        f.add("insertion-codes")
    if facts["numbering"]["auth_chain_differs_from_label_chain"]:
        f.add("auth-label-chain")
    if facts["numbering"]["auth_number_differs_from_label_number"]:
        f.add("auth-label-number")
    if facts["numbering"]["auth_number_differs_from_uniprot"]:
        f.add("uniprot-offset")
    if facts["modified_residues"]:
        f.add("modified-residue")
    if len(facts["chains"]) > 1:
        f.add("multi-chain")
    if set(meta.get("membrane_sources") or ()) & TRANSMEMBRANE_SOURCES:
        f.add("membrane")
    method = (facts["method"] or "").upper()
    if "ELECTRON MICROSCOPY" in method:
        f.add("cryo-em")
    if "NMR" in method:
        f.add("nmr")
    if facts["kind"] == "alphafold":
        f.add("alphafold")
    return sorted(f)


FAMILY_OF = {  # feature -> task families it can serve (every entry serves 'basic')
    "ligand": ["ligand", "interactions"], "heme": ["ligand", "metal", "interactions"],
    "metal": ["metal"], "disulfide": ["disulfide"], "nucleic": ["nucleic"],
    "protein-dna": ["nucleic", "interactions"], "glycan": ["glycan"],
    "assembly-differs": ["assembly"], "insertion-codes": ["numbering"],
    "auth-label-chain": ["numbering"], "auth-label-number": ["numbering"],
    "uniprot-offset": ["numbering"], "multi-chain": ["chains"],
    "modified-residue": ["modified-residue"], "alphafold": ["alphafold"],
}


# --- clinical variants --------------------------------------------------------------

def clinvar_records(acc: str, rcvs: list[str]) -> dict:
    """ClinVar's own variant records (VCV) behind a list of RCV accessions, from NCBI
    E-utilities: [{vcv, title, classification, review_status, last_evaluated,
    protein_change, rcv}]. ``classification`` is the aggregate germline classification
    over all submitters, which is what ClinVar's web page shows for the variant."""
    def fetch():
        import urllib.parse

        def post(tool, **params):
            time.sleep(0.4)   # NCBI asks for at most 3 requests a second without a key
            body = urllib.parse.urlencode({"db": "clinvar", "retmode": "json", **params})
            return json.loads(_get(EUTILS.format(tool), body.encode()))
        uids: set[str] = set()
        for i in range(0, len(rcvs), 100):
            got = post("esearch", term=" OR ".join(rcvs[i:i + 100]), retmax=5000)
            uids |= set(got["esearchresult"]["idlist"])
        out = []
        ordered = sorted(uids, key=int)
        for i in range(0, len(ordered), 150):
            res = post("esummary", id=",".join(ordered[i:i + 150]))["result"]
            for uid in res.get("uids", []):
                x = res[uid]
                g = x.get("germline_classification") or {}
                out.append({"vcv": x.get("accession"), "title": x.get("title"),
                            "classification": g.get("description") or "",
                            "review_status": g.get("review_status") or "",
                            "last_evaluated": (g.get("last_evaluated") or "")[:10],
                            "protein_change": [p.strip() for p in
                                               (x.get("protein_change") or "").split(",")
                                               if p.strip()],
                            "rcv": sorted((x.get("supporting_submissions") or {}).get("rcv")
                                          or [])})
        return out
    return cached(f"clinvarvcv_{acc}", EUTILS.format("esummary") + "?db=clinvar", fetch)


def clinvar_is_pathogenic(classification: str) -> bool:
    return re.split(r"[;,]", classification)[0].strip() in CLINVAR_PATHOGENIC


def clinvar_protein_changes(record: dict) -> set[str]:
    """One-letter protein changes a ClinVar record names: its ``protein_change`` list
    (every transcript's numbering) plus the ``(p.Trp82Arg)`` of its title, which is the
    only place some records give it."""
    out = set(record["protein_change"])
    m = re.search(r"\(p\.([A-Z][a-z]{2})(\d+)([A-Z][a-z]{2})\)", record.get("title") or "")
    if m and m[1].upper() in AA3 and m[3].upper() in AA3:
        out.add(f"{AA3[m[1].upper()]}{m[2]}{AA3[m[3].upper()]}")
    return out


def clinvar_variants(acc: str) -> dict:
    """Pathogenic / likely pathogenic ClinVar missense variants of an accession."""
    frozen = VARIANTS / f"{acc}.json"
    if not REFRESH and frozen.exists() and not (CACHE / f"panel_variation_{acc}.json").exists():
        f = json.loads(frozen.read_text())
        return {"url": f["source"], "retrieved": f["retrieved"], "entry_name": f["entry_name"],
                "protein": f["protein"], "gene": f.get("uniprot_gene"),
                "length": f["uniprot_length"], "sequence_sha256": f["uniprot_sequence_sha256"],
                "variants": [{k: v for k, v in x.items() if k != "structures"}
                             for x in f["variants"]],
                "rejected": f["rejected"],
                "clinvar_url": f["clinvar_source"], "clinvar_retrieved": f["clinvar_retrieved"],
                "candidate_positions": sorted(
                    {x["position"] for x in f["variants"]}
                    | {x["position"] for x in f["rejected"]
                       if x["reason"] == NOT_PATHOGENIC_IN_CLINVAR}),
                "position_counts": f["pathogenic_single_residue_variants_per_position"]}
    rec = cached(f"variation_{acc}", VARIATION.format(acc))
    d = rec["data"]
    seq = d["sequence"]
    merged: dict[tuple, dict] = {}
    counts: Counter = Counter()
    rejected = []
    for f in d.get("features", []):
        if f.get("type") != "VARIANT" or f.get("begin") != f.get("end"):
            continue
        sig = sorted({x["type"] for x in f.get("clinicalSignificances") or []
                      if x.get("type") in ("Pathogenic", "Likely pathogenic")
                      and "ClinVar" in (x.get("sources") or [])})
        rcv = sorted({x["id"] for x in f.get("xrefs") or [] if x.get("name") == "ClinVar"})
        if not sig or not rcv:
            continue
        try:
            pos = int(f["begin"])
        except (KeyError, ValueError):
            continue
        counts[pos] += 1
        wt, alt = f.get("wildType", ""), f.get("mutatedType") or f.get("alternativeSequence", "")
        if (f.get("consequenceType") != "missense" or wt not in AA3.values()
                or alt not in AA3.values() or wt == alt):
            continue
        if not 1 <= pos <= len(seq) or seq[pos - 1] != wt:
            rejected.append({"variant": f"{wt}{pos}{alt}", "position": pos,
                             "reason": "wild type is not the UniProt canonical residue"})
            continue
        v = merged.setdefault((pos, wt, alt), {
            "variant": f"{wt}{pos}{alt}", "position": pos, "wild_type": wt, "mutant": alt,
            "significance": [], "clinvar": [], "dbsnp": [], "diseases": []})
        v["significance"] = sorted(set(v["significance"]) | set(sig))
        v["clinvar"] = sorted(set(v["clinvar"]) | set(rcv))
        v["dbsnp"] = sorted(set(v["dbsnp"]) | {x["id"] for x in f.get("xrefs") or []
                                              if x.get("name") == "dbSNP"})
        v["diseases"] = sorted(set(v["diseases"]) | {a["name"] for a in f.get("association") or []
                                                    if a.get("disease") and a.get("name")})
    # UniProt reports a variant as pathogenic if any one ClinVar submission says so.
    # ClinVar's own verdict is the aggregate over submitters, and it can be
    # "Conflicting classifications" or "Uncertain significance" for the same variant.
    # Keep a variant only if a ClinVar record with this protein change agrees.
    crec = clinvar_records(acc, sorted({r for v in merged.values() for r in v["clinvar"]}))
    kept = []
    for k in sorted(merged):
        v = merged[k]
        recs = [x for x in crec["data"] if set(x["rcv"]) & set(v["clinvar"])
                and v["variant"] in clinvar_protein_changes(x)]
        good = [x for x in recs if clinvar_is_pathogenic(x["classification"])]
        if not good:
            rejected.append({
                "variant": v["variant"], "position": v["position"],
                "reason": NOT_PATHOGENIC_IN_CLINVAR,
                "clinvar_vcv": sorted(x["vcv"] for x in recs),
                "clinvar_classification": sorted({x["classification"] or "none"
                                                  for x in recs})})
            continue
        v["clinvar"] = sorted(set(v["clinvar"]) & {r for x in good for r in x["rcv"]})
        v["clinvar_vcv"] = sorted(x["vcv"] for x in good)
        v["clinvar_classification"] = sorted({x["classification"] for x in good})
        v["clinvar_review_status"] = sorted({x["review_status"] for x in good})
        kept.append(v)
    return {"url": rec["url"], "retrieved": rec["retrieved"],
            "entry_name": d.get("entryName"), "protein": d.get("proteinName"),
            "gene": d.get("geneName"), "length": len(seq),
            "sequence_sha256": hashlib.sha256(seq.encode()).hexdigest(),
            "variants": kept, "rejected": rejected,
            "clinvar_url": crec["url"], "clinvar_retrieved": crec["retrieved"],
            "candidate_positions": sorted({k[0] for k in merged}),
            "position_counts": {str(k): counts[k] for k in sorted(counts)}}


def map_variants(acc: str, cv: dict, entries: list[str]) -> dict:
    """Attach verified structure residues to each variant (wild type must match)."""
    per_entry = {}
    mismatches = []
    for entry in entries:
        t = sifts.load(entry)
        stats = Counter()
        for v in cv["variants"]:
            hits = t.residues(acc, v["position"], observed_only=False) if t else []
            if not hits:
                stats["outside_construct"] += 1
                continue
            obs = [h for h in hits if h.observed]
            if not obs:
                stats["not_observed"] += 1
                continue
            good = [h for h in obs if AA3.get(h.comp_id) == v["wild_type"]]
            for h in obs:
                if h not in good:
                    mismatches.append({"variant": v["variant"], "entry": entry,
                                       "auth_asym_id": h.auth_asym_id,
                                       "auth_seq_id": h.auth_seq_id,
                                       "pdbx_PDB_ins_code": h.pdbx_PDB_ins_code,
                                       "structure_residue": h.comp_id,
                                       "reason": "wild-type residue differs in the structure"})
            if not good:
                stats["wild_type_mismatch"] += 1
                continue
            stats["verified"] += 1
            v.setdefault("structures", {})[entry] = [
                {"auth_asym_id": h.auth_asym_id, "auth_seq_id": h.auth_seq_id,
                 "pdbx_PDB_ins_code": h.pdbx_PDB_ins_code, "label_asym_id": h.label_asym_id,
                 "label_seq_id": h.label_seq_id, "comp_id": h.comp_id} for h in good]
        per_entry[entry] = dict(sorted(stats.items()))
    for v in cv["variants"]:
        v.setdefault("structures", {})
    return {"per_entry": per_entry, "mismatches": mismatches}


# --- choosing the structure for a disease protein -----------------------------------

def choose_structure(acc: str, positions: set[int], taken: set[str]) -> tuple[str, dict]:
    """The rule in README.md, section 'Disease proteins'. Returns (entry, audit trail)."""
    best = cached(f"best_{acc}", BEST.format(acc))["data"].get(acc, [])
    by_entry: dict[str, dict] = {}
    for b in best:
        e = by_entry.setdefault(b["pdb_id"], {"method": b["experimental_method"],
                                              "resolution": b["resolution"], "covered": set()})
        e["covered"] |= {p for p in positions if b["unp_start"] <= p <= b["unp_end"]}
    for limit, methods in ((DISEASE_MAX_RESOLUTION, ("X-ray diffraction",)),
                           (DISEASE_FALLBACK_RESOLUTION, ("X-ray diffraction",
                                                          "Electron Microscopy"))):
        pool = sorted(((-len(e["covered"]), e["resolution"], pdb) for pdb, e in by_entry.items()
                       if e["method"] in methods and e["resolution"] is not None
                       and e["resolution"] <= limit and e["covered"]))[:DISEASE_SHORTLIST]
        ids = [p for _, _, p in pool]
        meta = cached(f"shortlist_{acc}_{limit}", RCSB_GRAPHQL, lambda: rcsb_entries(ids))["data"]
        ranked = sorted((cov, meta[pdb]["mutations"], meta[pdb]["polymer_entities"], reso, pdb)
                        for cov, reso, pdb in pool
                        if pdb in meta and meta[pdb]["atoms"] <= MAX_ATOMS
                        and meta[pdb]["models"] == 1)
        if ranked:
            cov, mut, ents, reso, pdb = ranked[0]
            return pdb, {"candidates": len(by_entry), "shortlisted": len(pool),
                         "eligible": len(ranked), "resolution_limit": limit,
                         "positions_covered": -cov, "mutations": mut,
                         "polymer_entities": ents, "runner_up": ranked[1][4] if len(ranked) > 1
                         else None, "already_in_panel": pdb in taken}
    raise SystemExit(f"{acc}: no structure passes the disease-protein rule")


# --- the build ----------------------------------------------------------------------

def protein_offset(facts: dict, acc: str) -> dict | None:
    """How an accession's residues are numbered on an entry (all chains pooled)."""
    off: Counter = Counter()
    n_ins = 0
    chain_differs = False
    for c in facts["chains"]:
        for u in c["uniprot"]:
            if u["accession"] == acc:
                off.update({int(k): v for k, v in u["auth_minus_unp"].items()})
                n_ins += u["n_insertion_codes"]
                chain_differs |= c["auth_asym_id"] != c["label_asym_id"]
    if not off:
        return None
    return {"auth_minus_unp": {str(k): v for k, v in sorted(off.items())},
            "n_insertion_codes": n_ins, "offset": set(off) != {0} or bool(n_ins),
            "auth_chain_differs_from_label_chain": chain_differs}


def build(args) -> None:
    seed = json.loads((PANEL / "seed.json").read_text())
    in_use = bat.task_structures()
    records: dict[str, dict] = {}

    def add(entry: str, why: str, claims: list[str], origin: str) -> dict:
        rec = records.setdefault(entry, {"id": entry, "why": [], "claims": [], "origin": []})
        if why not in rec["why"]:
            rec["why"].append(why)
        rec["claims"] = sorted(set(rec["claims"]) | set(claims))
        rec["origin"].append(origin)
        return rec

    for e in seed["entries"]:
        add(e["id"].lower(), e["why"], e["claims"], "named")
    missing = sorted(set(in_use) - set(records) - {x for x in in_use if x.startswith("af-")})
    if missing:
        raise SystemExit(f"entries used by tasks but not in seed.json: {missing}")

    # Disease proteins: variants first (the rule ranks structures by them).
    disease = []
    for d in seed["disease_proteins"]:
        cv = clinvar_variants(d["accession"])
        positions = set(cv["candidate_positions"])
        before = next((p for p in old_panel().get("disease_proteins", [])
                       if p["accession"] == d["accession"]), None)
        if d.get("entry"):
            entry, trail = d["entry"].lower(), {"pinned": "already used by tasks"}
        elif before:
            entry, trail = before["entry"], before["selection"]
        else:
            entry, trail = choose_structure(d["accession"], positions, set(records))
        add(entry, f"{d['gene']} ({d['accession']}): {d['disease']}.", d.get("claims", []),
            f"disease:{d['accession']}")
        disease.append({**d, "entry": entry, "selection": trail, "clinvar": cv})
        print(f"  {d['gene']:9s} {d['accession']}  {len(cv['variants']):4d} variants -> {entry}  {trail}")

    for a in seed["alphafold"]:
        add(af_id(a["accession"]), a["why"], [], f"alphafold:{a['accession']}")

    # Per entry: structure file, SIFTS, facts.
    for entry, rec in sorted(records.items()):
        is_af = entry.startswith("af-")
        meta = af_meta(entry) if is_af else rcsb_meta(entry)
        status = "CURRENT" if is_af else rcsb_status(entry)
        if status != "CURRENT":
            raise SystemExit(f"{entry}: RCSB status is {status}")
        path = bat.fetch_cif(entry)
        bat.freeze_cif(entry)
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        before = old_entry(entry) or {}
        cols = bat.read_atom_site(path)
        smap = build_sifts(entry, cols)
        write_sifts(entry, smap)
        sifts.load.cache_clear()
        facts = build_facts(entry, cols, smap)
        FACTS.mkdir(parents=True, exist_ok=True)
        (FACTS / f"{entry}.json").write_text(json.dumps(facts, indent=1) + "\n")
        feats = features(facts, meta)
        unverified = sorted(set(rec["claims"]) - set(feats))
        if unverified:
            raise SystemExit(f"{entry}: seed.json claims {unverified} but the file shows {feats}")
        used = in_use.get(entry) or (in_use.get("-".join(entry.split("-")[:2]), [])
                                     if is_af else [])
        exempt = bool(used)
        if facts["n_atoms"] > MAX_ATOMS and not exempt:
            raise SystemExit(f"{entry}: {facts['n_atoms']} atoms is over the limit")
        rec.update({
            "kind": facts["kind"], "title": meta["title"], "method": meta["method"],
            "resolution": meta["resolution"], "deposited": meta["deposited"],
            "atoms": facts["n_atoms"], "models": facts["n_models"],
            "over_size_limit": facts["n_atoms"] > MAX_ATOMS,
            "used_by_tasks": used,
            "source": facts["source"], "sha256": sha,
            "retrieved": before.get("retrieved") if before.get("sha256") == sha and before.get("retrieved") else _today(),
            "membrane_sources": meta["membrane_sources"],
            "features": feats,
            "uniprot": sorted({u["accession"] for c in facts["chains"] for u in c["uniprot"]}),
            "sifts": smap is not None,
            "offset": facts["numbering"]["auth_number_differs_from_uniprot"],
            "why": " ".join(rec["why"]),
        })
        print(f"{entry}: {facts['n_atoms']} atoms, {feats}")

    # Variants, mapped to every panel entry that holds the protein.
    VARIANTS.mkdir(parents=True, exist_ok=True)
    keep = {d["accession"] for d in disease}
    for stale in VARIANTS.glob("*.json"):
        if stale.stem not in keep:
            stale.unlink()
    proteins = []
    for d in disease:
        acc, cv = d["accession"], d.pop("clinvar")
        holders = sorted(e for e, r in records.items() if acc in r["uniprot"])
        mapped = map_variants(acc, cv, holders)
        chosen_facts = json.loads((FACTS / f"{d['entry']}.json").read_text())
        offs = {e: protein_offset(json.loads((FACTS / f"{e}.json").read_text()), acc)
                for e in holders}
        doc = {"accession": acc, "gene": d["gene"], "entry_name": cv["entry_name"],
               "protein": cv["protein"], "uniprot_gene": cv["gene"], "disease": d["disease"],
               "source": cv["url"], "retrieved": cv["retrieved"],
               "clinvar_source": cv["clinvar_url"], "clinvar_retrieved": cv["clinvar_retrieved"],
               "filter": "UniProt Variation API features of type VARIANT, one residue, "
                         "consequenceType missense, clinical significance Pathogenic or "
                         "Likely pathogenic with ClinVar as a source, and a ClinVar "
                         "cross-reference; wild type must equal the UniProt canonical "
                         "residue; and a ClinVar variant record (VCV) with the same protein "
                         "change whose aggregate germline classification is Pathogenic, "
                         "Likely pathogenic or Pathogenic/Likely pathogenic",
               "uniprot_length": cv["length"], "uniprot_sequence_sha256": cv["sequence_sha256"],
               "primary_entry": d["entry"], "selection": d["selection"],
               "entries": {e: {"numbering": offs[e], **mapped["per_entry"][e]} for e in holders},
               "variants": cv["variants"], "rejected": cv["rejected"],
               "structure_mismatches": mapped["mismatches"],
               "pathogenic_single_residue_variants_per_position": cv["position_counts"]}
        (VARIANTS / f"{acc}.json").write_text(json.dumps(doc, indent=1) + "\n")
        verified = mapped["per_entry"].get(d["entry"], {}).get("verified", 0)
        off = protein_offset(chosen_facts, acc) or {}
        proteins.append({"accession": acc, "gene": d["gene"], "disease": d["disease"],
                         "entry": d["entry"], "entries": holders,
                         "variants": len(cv["variants"]), "verified_on_entry": verified,
                         "offset": bool(off.get("offset")),
                         "auth_minus_unp": off.get("auth_minus_unp"),
                         "n_insertion_codes": off.get("n_insertion_codes"),
                         "auth_chain_differs_from_label_chain":
                             bool(off.get("auth_chain_differs_from_label_chain")),
                         "selection": d["selection"]})
        for e in holders:
            if mapped["per_entry"][e].get("verified"):
                records[e]["features"] = sorted(set(records[e]["features"]) | {"clinical"})

    for rec in records.values():
        fam = {"basic"} | {x for f in rec["features"] for x in FAMILY_OF.get(f, [])}
        if "clinical" in rec["features"]:
            fam.add("clinical")
        rec["families"] = sorted(fam)
        rec.pop("claims")
        rec["origin"] = sorted(set(rec["origin"]))

    good = [p for p in proteins if p["verified_on_entry"] >= MIN_VERIFIED_VARIANTS]
    n_off = sum(p["offset"] for p in good)
    n_pdb = sum(r["kind"] == "pdb" for r in records.values())
    print(f"{n_pdb} PDB entries + {len(records) - n_pdb} AlphaFold models; "
          f"{len(good)} disease proteins with >= {MIN_VERIFIED_VARIANTS} verified variants, "
          f"{n_off} with a numbering offset")
    if len(good) < MIN_DISEASE_PROTEINS or n_off < MIN_OFFSET_PROTEINS or n_pdb < 55:
        raise SystemExit("the panel does not meet its own minimums")
    panel = {"rule": RULE, "max_atoms": MAX_ATOMS,
             "entries": [records[k] for k in sorted(records)],
             "disease_proteins": proteins}
    (PANEL / "panel.json").write_text(json.dumps(panel, indent=1) + "\n")
    (PANEL / "PANEL.md").write_text(panel_table(panel))


def panel_table(panel: dict) -> str:
    lines = ["# The structure panel (generated by scripts/build_panel.py; do not edit)", "",
             "Offset = author residue numbers differ from UniProt numbers for at least one "
             "mapped residue.", "",
             "| entry | title | method | atoms | offset | families | why |",
             "|---|---|---|---:|---|---|---|"]
    for r in panel["entries"]:
        reso = f" {r['resolution']:.2f} Å" if r["resolution"] else ""
        off = "–" if not r["sifts"] else "yes" if r["offset"] else "no"
        lines.append(f"| {r['id']} | {r['title'].replace('|', '/')} | {r['method']}{reso} | "
                     f"{r['atoms']} | {off} | {', '.join(r['families'])} | {r['why']} |")
    lines += ["", "## Disease proteins", "",
              "Verified = pathogenic ClinVar missense variants whose wild-type residue is "
              "present, with the right identity, in the entry.", "",
              "| gene | UniProt | entry | variants | verified | offset (author − UniProt: residues) "
              "| author chain ≠ label chain | disease |",
              "|---|---|---|---:|---:|---|---|---|"]
    for p in panel["disease_proteins"]:
        off = ", ".join(f"{k}: {v}" for k, v in (p["auth_minus_unp"] or {}).items())
        if p["n_insertion_codes"]:
            off += f"; {p['n_insertion_codes']} with insertion codes"
        lines.append(f"| {p['gene']} | {p['accession']} | {p['entry']} | {p['variants']} | "
                     f"{p['verified_on_entry']} | {'yes' if p['offset'] else 'no'} ({off}) | "
                     f"{'yes' if p['auth_chain_differs_from_label_chain'] else 'no'} | "
                     f"{p['disease']} |")
    lines += ["", "## Coverage", "",
              "Features are read from each file by the build (never taken on trust).", "",
              "| feature | entries | which |", "|---|---:|---|"]
    feats = sorted({f for r in panel["entries"] for f in r["features"]})
    for f in feats:
        ids = [r["id"] for r in panel["entries"] if f in r["features"]]
        lines.append(f"| {f} | {len(ids)} | {' '.join(ids)} |")
    return "\n".join(lines) + "\n"


def check() -> None:
    """Every frozen structure file still has the hash panel.json recorded."""
    panel = json.loads((PANEL / "panel.json").read_text())
    bad = 0
    for r in panel["entries"]:
        got = hashlib.sha256(gzip.decompress(
            (bat.FROZEN / f"{r['id']}.cif.gz").read_bytes())).hexdigest()
        if got != r["sha256"]:
            bad += 1
            print(f"  {r['id']}: frozen file does not match panel.json")
    print(f"{len(panel['entries'])} entries checked, {bad} bad")
    if bad:
        sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="verify frozen files; write nothing")
    ap.add_argument("--refresh", action="store_true",
                    help="ask the services again instead of keeping the frozen answers")
    args = ap.parse_args()
    global REFRESH
    REFRESH = args.refresh
    check() if args.check else build(args)


if __name__ == "__main__":
    main()
