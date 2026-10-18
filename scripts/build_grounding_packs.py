#!/usr/bin/env python3
"""
Build the grounding packs ("dossiers") for the MVS tasks — ROADMAP item R6.

A grounding pack is a short, frozen block of **facts about the structure(s) a task
involves** that an offline lookup pipeline could have produced. With
``python -m molbench.runner --grounding`` it is appended to the user message; the
system prompt is unchanged. Comparing runs with and without it measures how much
*facts* (not MVS knowledge) lift a score — the second axis of the 2x2 in ROADMAP
("bare/spec x no-grounding/grounding pack").

Storage: the pack is written into each task JSON as
``"grounding": {"rule": RULE, "text": ...}``. It is frozen with the task it
describes, travels with it in git, and the runner's existing loader picks it up;
a sidecar would need a second lookup and could drift from its task. Re-running a
task generator (``generate_*_tasks.py``, ``author_*_tasks.py``) rewrites the task
without its pack, so re-run this script afterwards.

The rule (the same for every MVS task; no per-task edits)
-----------------------------------------------------------
Structures covered: every PDB id written in the prompt, in sorted order. Never the
answer key's: a resolve task names a protein, not an entry, so its pack lists
candidate entries (below) without singling out the reference's. For each structure, from its
mmCIF (gemmi, first model):

  * title, experimental method and resolution;
  * entities: id, type (polymer type) and description;
  * polymer chains: auth and label chain id, entity, and the observed residues as
    runs ``auth a-b = label c-d`` (a new run starts at any gap, numbering jump or
    insertion code), plus the SEQRES length;
  * SIFTS UniProt mapping per polymer chain (as served by RCSB):
    ``UniProt a-b = label c-d`` for each mapped segment, plus the observed residues
    as ``UniProt a-b = auth c-d`` runs;
  * hetero groups (non-polymer and branched): comp id, chemical name, every copy as
    auth chain + auth residue number (label chain in brackets), and the heavy-atom
    names for groups with at most ``MAX_LIGAND_ATOMS`` heavy atoms;
  * waters: count, or "none".

Task-derived facts, only from things **named in the prompt**:

  * a residue written as three-letter code + number ("His64") -> every chain where
    that residue type sits at that author number, with its label numbering and
    heavy-atom names;
  * a UniProt position ("UniProt position 143") or a variant token ("D281Y") in a
    prompt that mentions ClinVar or a variant -> the structure residues that SIFTS
    maps the UniProt position to (and whether the wild-type residue matches);
  * a prompt that mentions ClinVar -> the ``N_HOTSPOT_POSITIONS`` mapped UniProt
    positions with the most pathogenic single-residue ClinVar variants (UniProt
    Proteins API), with counts, ties broken by position;
  * a prompt that names no PDB id (the resolve tasks: a protein named by name) ->
    the UniProt accession the name resolves to (the task's ``provenance.uniprot``)
    with its UniProt name, and up to ``MAX_ENTRIES`` of the task's ``accepted_ids``,
    best resolution first (ties and unknown resolution by id).

The pack states facts. It never contains MVS, a scene tree, colours or
representations, and never says what to draw.

Network is used at build time only (RCSB mmCIF + GraphQL, UniProt REST + Proteins API).
Every response is cached under ``data/cif/`` and ``data/grounding_cache/``; with a
warm cache the build is offline and byte-for-byte deterministic (sorted output, no
timestamps in the pack).

    pip install -e ".[authoring]"
    python scripts/build_grounding_packs.py           # write packs into tasks/mvs*/
    python scripts/build_grounding_packs.py --check   # exit 1 if any pack is stale
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
import urllib.request
from collections import Counter

import gemmi

REPO = pathlib.Path(__file__).resolve().parent.parent
TASKS = REPO / "tasks"
CIF_DIR = REPO / "data" / "cif"
CACHE = REPO / "data" / "grounding_cache"

RULE = "r6-v1"            # bump whenever the generation rule below changes
MAX_LIGAND_ATOMS = 50     # list atom names only for groups this small (heavy atoms)
MAX_COPIES = 12           # hetero-group copies listed before "... (+N more)"
MAX_ENTRIES = 10          # candidate entries listed for a protein named by name
N_HOTSPOT_POSITIONS = 10  # ClinVar positions listed, by pathogenic-variant count

CIF_URL = "https://files.rcsb.org/download/{}.cif"
UNIPROT_URL = "https://rest.uniprot.org/uniprotkb/{}.json?fields=protein_name,id"
RCSB_GRAPHQL = "https://data.rcsb.org/graphql"

AA3 = ("Ala Arg Asn Asp Cys Gln Glu Gly His Ile Leu Lys Met Phe Pro Ser Thr Trp Tyr Val"
       .split())
AA1_TO_3 = dict(zip("ARNDCQEGHILKMFPSTWYV", (a.upper() for a in AA3)))
WATER = {"HOH", "DOD"}

RE_PDB = re.compile(r"\b(\d[a-z0-9]{3})\b", re.I)
RE_RESIDUE = re.compile(r"\b(" + "|".join(AA3) + r")(\d+)\b")
RE_VARIANT = re.compile(r"\b([ACDEFGHIKLMNPQRSTVWY])(\d+)([ACDEFGHIKLMNPQRSTVWY])\b")
RE_UNP_POS = re.compile(r"\bUniProt position (\d+)\b", re.I)


# --- fetching (build time only, cached) --------------------------------------------

def _get(url: str, data: bytes | None = None, headers: dict | None = None) -> bytes:
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def _cached_json(name: str, fetch):
    path = CACHE / f"{name}.json"
    if path.exists():
        return json.loads(path.read_text())
    value = fetch()
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=1, sort_keys=True))
    return value


def cif_path(pdb: str) -> pathlib.Path:
    path = CIF_DIR / f"{pdb}.cif"
    if not path.exists():
        CIF_DIR.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_get(CIF_URL.format(pdb)))
    return path


def sifts_alignments(pdb: str) -> list[dict]:
    """SIFTS UniProt alignments per polymer entity, as served by RCSB (PDBe's own API
    has no mapping for some entries, e.g. 5UAK): [{entity, acc, name, regions:
    [[label_seq_start, unp_start, length], ...]}]."""
    def fetch():
        q = ('{entry(entry_id:"%s"){polymer_entities{rcsb_id rcsb_polymer_entity_align'
             '{provenance_source reference_database_name reference_database_accession '
             'aligned_regions{entity_beg_seq_id ref_beg_seq_id length}}}}}' % pdb.upper())
        d = json.loads(_get(RCSB_GRAPHQL, json.dumps({"query": q}).encode(),
                            {"Content-Type": "application/json"}))
        out = []
        for ent in d["data"]["entry"]["polymer_entities"] or []:
            for al in ent.get("rcsb_polymer_entity_align") or []:
                if (al["provenance_source"] != "SIFTS"
                        or al["reference_database_name"] != "UniProt"):
                    continue
                acc = al["reference_database_accession"]
                out.append({"entity": ent["rcsb_id"].split("_")[-1], "acc": acc,
                            "name": uniprot_name(acc)[0],
                            "regions": sorted([r["entity_beg_seq_id"], r["ref_beg_seq_id"],
                                               r["length"]] for r in al["aligned_regions"])})
        return sorted(out, key=lambda x: (x["entity"], x["acc"]))
    return _cached_json(f"sifts_{pdb}", fetch)


def sifts_segments(aligns: list[dict], st) -> list[dict]:
    """Per auth chain: [{acc, name, chain, label_asym, label_start, label_end,
    unp_start, unp_end}], sorted. ``label_*`` is label_seq_id (SEQRES index)."""
    subchains = {e.name: set(e.subchains) for e in st.entities}
    segs = []
    for al in aligns:
        for chain in st[0]:
            sub = chain.get_polymer().subchain_id() if len(chain.get_polymer()) else None
            if sub not in subchains.get(al["entity"], ()):
                continue
            for label0, unp0, n in al["regions"]:
                segs.append({"acc": al["acc"], "name": al["name"], "chain": chain.name,
                             "label_asym": sub, "label_start": label0,
                             "label_end": label0 + n - 1, "unp_start": unp0,
                             "unp_end": unp0 + n - 1})
    return sorted(segs, key=lambda s: (s["chain"], s["label_start"], s["acc"]))


def uniprot_name(acc: str) -> tuple[str, str]:
    """(entry name, recommended protein name) for an accession."""
    def fetch():
        d = json.loads(_get(UNIPROT_URL.format(acc), headers={"Accept": "application/json"}))
        desc = d.get("proteinDescription", {})
        full = (desc.get("recommendedName") or (desc.get("submissionNames") or [{}])[0]
                ).get("fullName", {}).get("value", "")
        return {"id": d.get("uniProtkbId", ""), "name": full}
    got = _cached_json(f"uniprot_{acc}", fetch)
    return got["id"], got["name"]


def pathogenic_counts(acc: str) -> dict[int, int]:
    """Pathogenic, ClinVar-linked single-residue variants per UniProt position."""
    from molbench import variants
    got = _cached_json(f"clinvar_{acc}",
                       lambda: [list(v) for v in variants.pathogenic_clinvar(acc)])
    return dict(Counter(int(v[0]) for v in got))


def entry_resolutions(ids: list[str]) -> dict[str, list]:
    """{id: [resolution or None, method]} from RCSB GraphQL (batched)."""
    key = "resolution_" + hashlib.sha256(",".join(sorted(ids)).encode()).hexdigest()[:16]
    def fetch():
        out = {}
        for i in range(0, len(ids), 200):
            batch = [x.upper() for x in ids[i:i + 200]]
            q = ("{entries(entry_ids:%s){rcsb_id rcsb_entry_info"
                 "{resolution_combined experimental_method}}}" % json.dumps(batch))
            d = json.loads(_get(RCSB_GRAPHQL, json.dumps({"query": q}).encode(),
                                {"Content-Type": "application/json"}))
            for e in d["data"]["entries"] or []:
                info = e.get("rcsb_entry_info") or {}
                res = info.get("resolution_combined") or [None]
                out[e["rcsb_id"].lower()] = [res[0], info.get("experimental_method") or ""]
        return out
    return _cached_json(key, fetch)


# --- structure facts (pure: CIF + SIFTS in, lines out) -----------------------------

def _auth(res) -> str:
    icode = res.seqid.icode.strip()
    return f"{res.seqid.num}{icode}"


def _runs(rows: list[tuple[int, int, str]]) -> list[tuple[tuple, tuple]]:
    """Group (x, y_num, y_icode) rows into runs where both x and y step by +1 and no
    insertion code occurs. Returns [((x0, y0), (x1, y1)), ...] with y as text."""
    runs: list[list] = []
    for x, y, icode in rows:
        ytxt = f"{y}{icode}"
        if (runs and not icode and not runs[-1][2] and x == runs[-1][1][0] + 1
                and y == runs[-1][1][1] + 1):
            runs[-1][1] = (x, y, ytxt)
        else:
            runs.append([(x, y, ytxt), (x, y, ytxt), bool(icode)])
    return [((a[0], a[2]), (b[0], b[2])) for a, b, _ in runs]


def _fmt_range(a, b) -> str:
    return str(a) if a == b else f"{a}-{b}"


def _heavy_atoms(res) -> list[str]:
    names: list[str] = []
    for atom in res:
        if not atom.element.is_hydrogen and atom.name not in names:
            names.append(atom.name)
    return names


def _polytype(ent) -> str:
    t = ent.polymer_type
    return {gemmi.PolymerType.PeptideL: "protein", gemmi.PolymerType.Dna: "DNA",
            gemmi.PolymerType.Rna: "RNA", gemmi.PolymerType.DnaRnaHybrid: "DNA/RNA"
            }.get(t, str(t).split(".")[-1])


def load(path: pathlib.Path):
    """(CIF block, gemmi Structure) for an mmCIF file (.cif or .cif.gz)."""
    block = gemmi.cif.read(str(path)).sole_block()
    st = gemmi.make_structure_from_block(block)
    st.merge_chain_parts()   # one gemmi chain per auth chain (polymer + its ligands)
    st.setup_entities()
    return block, st


def _observed(st) -> dict[str, list]:
    """Auth chain -> its observed polymer residues (one per label_seq_id)."""
    out = {}
    for chain in st[0]:
        seen, rows = set(), []
        for r in chain.get_polymer():
            if r.label_seq is not None and r.label_seq not in seen:
                seen.add(r.label_seq)
                rows.append(r)
        out[chain.name] = rows
    return out


def structure_facts(pdb: str, block, st, segs: list[dict]) -> list[str]:
    """The per-structure part of a pack. Pure given (CIF block, structure, SIFTS)."""
    s = gemmi.cif.as_string
    title = s(block.find_value("_struct.title") or "?")
    method = s(block.find_value("_exptl.method") or "?")
    reso = f", {st.resolution:.2f} Å" if st.resolution else ""
    lines = [f"PDB {pdb.upper()}: {title}", f"Method: {method}{reso}"
             + (f"; {len(st)} models (first model described)" if len(st) > 1 else "")]

    desc = {s(r[0]): s(r[1]) for r in block.find("_entity.", ["id", "pdbx_description"])}
    comp_names = {s(r[0]): s(r[1]) for r in block.find("_chem_comp.", ["id", "name"])}
    lines.append("Entities:")
    ent_of: dict[str, gemmi.Entity] = {}
    for ent in sorted(st.entities, key=lambda e: int(e.name) if e.name.isdigit() else 0):
        kind = str(ent.entity_type).split(".")[-1].lower()
        if ent.entity_type == gemmi.EntityType.Polymer:
            kind = f"polymer, {_polytype(ent)}"
        lines.append(f"  {ent.name}: {kind}: {desc.get(ent.name, '?')}")
        for sub in ent.subchains:
            ent_of[sub] = ent

    model = st[0]
    lines.append("Polymer chains (auth chain [label chain]; observed residues as "
                 "auth numbering = label numbering):")
    observed = _observed(st)
    for chain in model:
        rows = observed.get(chain.name)
        if not rows:
            continue
        poly = chain.get_polymer()
        ent = ent_of.get(poly.subchain_id())
        runs = _runs([(r.label_seq, r.seqid.num, r.seqid.icode.strip()) for r in rows])
        txt = "; ".join(f"auth {_fmt_range(a[1], b[1])} = label {_fmt_range(a[0], b[0])}"
                        for a, b in runs)
        nseq = len(ent.full_sequence) if ent else "?"
        lines.append(f"  {chain.name} [{poly.subchain_id()}]: entity {ent.name if ent else '?'}"
                     f", {len(rows)} of {nseq} SEQRES residues observed: {txt}")

    if segs:
        lines.append("UniProt mapping (SIFTS; label numbering = SEQRES index):")
        for g in segs:
            rows = [r for r in observed.get(g["chain"], [])
                    if g["label_start"] <= r.label_seq <= g["label_end"]]
            d = g["unp_start"] - g["label_start"]
            runs = _runs([(r.label_seq + d, r.seqid.num, r.seqid.icode.strip()) for r in rows])
            obs = "; ".join(f"UniProt {_fmt_range(a[0], b[0])} = auth {_fmt_range(a[1], b[1])}"
                            for a, b in runs) or "none observed"
            lines.append(f"  {g['chain']}: {g['acc']} ({g['name']}) UniProt "
                         f"{g['unp_start']}-{g['unp_end']} = label {g['label_start']}-"
                         f"{g['label_end']}; observed: {obs}")
    else:
        lines.append("UniProt mapping (SIFTS): none")

    groups: dict[str, list] = {}
    n_water = 0
    for chain in model:
        for r in chain:
            if r.name in WATER:
                n_water += 1
            elif r.entity_type in (gemmi.EntityType.NonPolymer, gemmi.EntityType.Branched):
                groups.setdefault(r.name, []).append((chain.name, r))
    if groups:
        lines.append("Hetero groups (auth chain + auth residue number [label chain]):")
        for comp in sorted(groups):
            copies = groups[comp]
            where = [f"{ch} {_auth(r)} [{r.subchain}]" for ch, r in copies]
            more = f" ... (+{len(where) - MAX_COPIES} more)" if len(where) > MAX_COPIES else ""
            line = (f"  {comp} ({comp_names.get(comp, '?')}), {len(copies)} "
                    f"cop{'y' if len(copies) == 1 else 'ies'}: "
                    f"{', '.join(where[:MAX_COPIES])}{more}")
            atoms = _heavy_atoms(copies[0][1])
            if len(atoms) <= MAX_LIGAND_ATOMS:
                line += f"; atoms: {' '.join(atoms)}"
            lines.append(line)
    else:
        lines.append("Hetero groups: none")
    lines.append(f"Waters: {n_water}" if n_water else "Waters: none")
    return lines


# --- task-derived facts ------------------------------------------------------------

def _prompt_pdbs(prompt: str) -> list[str]:
    """PDB ids written in the prompt (four characters, digit first, at least one letter)."""
    return sorted({m.lower() for m in RE_PDB.findall(prompt) if re.search("[a-z]", m, re.I)})


def _structures(task: dict) -> list[str]:
    return sorted(set(_prompt_pdbs(task["prompt"])))


def _unp_to_residues(segs, observed, acc, pos) -> list[tuple[str, str | None]]:
    """[(fact text, residue name or None if unobserved)] for one UniProt position."""
    out = []
    for g in segs:
        if g["acc"] != acc or not g["unp_start"] <= pos <= g["unp_end"]:
            continue
        label = pos - g["unp_start"] + g["label_start"]
        hit = next((r for r in observed.get(g["chain"], []) if r.label_seq == label), None)
        out.append((f"auth {g['chain']} {_auth(hit)} {hit.name} (label {g['label_asym']} {label})",
                    hit.name) if hit else
                   (f"chain {g['chain']} label {label} (not observed)", None))
    return out


def task_facts(task: dict, loaded: dict) -> list[str]:
    prompt = task["prompt"]
    lines: list[str] = []

    # Residues named as three-letter code + number.
    for name3, num in sorted(set(RE_RESIDUE.findall(prompt)), key=lambda x: (int(x[1]), x[0])):
        hits = []
        for pdb, (_, st, _) in sorted(loaded.items()):
            for chain in st[0]:
                for r in chain.get_polymer():
                    if (r.seqid.num == int(num) and not r.seqid.icode.strip()
                            and r.name == name3.upper()):
                        hits.append(f"{pdb.upper()} auth {chain.name} {_auth(r)} {r.name} "
                                    f"(label {r.subchain} {r.label_seq}); atoms: "
                                    f"{' '.join(_heavy_atoms(r))}")
        lines.append(f"{name3}{num}: " + ("; ".join(hits) if hits else
                     f"no {name3.upper()} at author number {num}"))

    # UniProt positions / variants (only in prompts about variants or ClinVar).
    clinical = re.search(r"clinvar|variant", prompt, re.I)
    positions: list[tuple[str, int, str | None]] = []
    for m in RE_UNP_POS.finditer(prompt):
        positions.append((f"UniProt position {m.group(1)}", int(m.group(1)), None))
    if clinical:
        for wt, pos, alt in RE_VARIANT.findall(prompt):
            positions.append((f"Variant {wt}{pos}{alt}", int(pos), AA1_TO_3[wt]))
    for label, pos, wt in positions:
        for pdb, (_, _, segs) in sorted(loaded.items()):
            observed = _observed(loaded[pdb][1])
            for acc in sorted({g["acc"] for g in segs}):
                res = _unp_to_residues(segs, observed, acc, pos)
                if not res:
                    continue
                check = ""
                if wt:
                    names = {name for _, name in res if name}
                    check = (" (wild type matches)" if names == {wt} else
                             f" (structure has {'/'.join(sorted(names)) or 'nothing observed'})")
                lines.append(f"{label} = {acc} position {pos} -> in {pdb.upper()}: "
                             f"{', '.join(text for text, _ in res)}{check}")

    # ClinVar hotspots: positions with the most pathogenic variants.
    if re.search(r"clinvar", prompt, re.I):
        for pdb, (_, _, segs) in sorted(loaded.items()):
            for acc in sorted({g["acc"] for g in segs}):
                counts = pathogenic_counts(acc)
                mapped = {p: n for p, n in counts.items()
                          if any(g["acc"] == acc and g["unp_start"] <= p <= g["unp_end"]
                                 for g in segs)}
                top = sorted(mapped.items(), key=lambda pn: (-pn[1], pn[0]))[:N_HOTSPOT_POSITIONS]
                if top:
                    lines.append(
                        f"Pathogenic ClinVar single-residue variants for {acc}, UniProt "
                        f"positions in {pdb.upper()} with the most variants (position: "
                        f"count): " + ", ".join(f"{p}: {n}" for p, n in top))

    # A protein named by name (no PDB id in the prompt).
    acc = (task.get("provenance") or {}).get("uniprot")
    if not _prompt_pdbs(prompt) and acc and task.get("accepted_ids"):
        entry, pname = uniprot_name(acc)
        ids = sorted(task["accepted_ids"])
        info = entry_resolutions(ids)
        def key(x):
            r = (info.get(x) or [None])[0]
            return (r if r is not None else float("inf"), x)
        best = sorted(ids, key=key)[:MAX_ENTRIES]
        fmt = []
        for x in best:
            r, meth = info.get(x) or [None, ""]
            fmt.append(f"{x.upper()} ({meth}{f', {r:.2f} Å' if r is not None else ''})")
        lines.append(f"Protein named in the prompt: UniProt {acc} ({entry}, {pname})")
        lines.append(f"PDB entries containing it: {len(ids)}; the {len(best)} with the best "
                     f"resolution: " + ", ".join(fmt))
    return lines


def build_pack(task: dict) -> str | None:
    pdbs = _structures(task)
    loaded = {}
    for pdb in pdbs:
        block, st = load(cif_path(pdb))
        loaded[pdb] = (block, st, sifts_segments(sifts_alignments(pdb), st))
    parts = ["\n".join(structure_facts(pdb, *loaded[pdb])) for pdb in pdbs]
    extra = task_facts(task, loaded)
    if extra:
        parts.append("From the request:\n" + "\n".join(f"  {x}" for x in extra))
    return "\n\n".join(parts) or None


# --- writing ------------------------------------------------------------------------

def mvs_task_paths() -> list[pathlib.Path]:
    out = []
    for path in sorted(TASKS.rglob("*.json")):
        if json.loads(path.read_text()).get("category") == "mvs":
            out.append(path)
    return out


def write_pack(path: pathlib.Path, check: bool = False) -> tuple[bool, int]:
    """Insert/refresh the pack in one task file. Returns (changed, n_chars)."""
    text = path.read_text()
    task = json.loads(text)
    pack = build_pack(task)
    new = {k: v for k, v in task.items() if k != "grounding"}
    if pack is not None:
        new["grounding"] = {"rule": RULE, "text": pack}
    out = json.dumps(new, indent=2) + ("\n" if text.endswith("\n") else "")
    changed = out != text
    if changed and not check:
        path.write_text(out)
    return changed, len(pack or "")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--check", action="store_true", help="report stale packs, write nothing")
    args = ap.parse_args(argv)
    stale, sizes = [], []
    for path in mvs_task_paths():
        changed, n = write_pack(path, check=args.check)
        sizes.append(n)
        if changed:
            stale.append(path.relative_to(REPO))
        print(f"{'*' if changed else ' '} {path.relative_to(REPO)}  {n} chars")
    print(f"{len(sizes)} MVS tasks; {len(stale)} {'stale' if args.check else 'written'}")
    if args.check and stale:
        sys.exit(1)


if __name__ == "__main__":
    main()
