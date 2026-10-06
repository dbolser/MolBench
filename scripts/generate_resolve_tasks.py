#!/usr/bin/env python3
"""
Entry-resolution tasks: the prompt names a protein, not a PDB id.

Every other MVS task hands the model the id. Real users don't: the first evaluator
prompt to fail in the wild was "I wanna see a structure of PDE5A", answered with
PDB 1UJ7 — an entry that does not exist. Probing further found the quieter failure:
real ids for the wrong protein (a SARS-CoV-2 RBD for "nanobody bound to GFP").

Many entries are a right answer here, so each task lists ``accepted_ids``: every PDB
entry whose polymer maps to the protein's UniProt accession, pulled from RCSB search
at authoring time and recorded under ``provenance``. The reference carries one
canonical entry; the grader folds any accepted id onto it (``mvs._fold_accepted_refs``).
The scene itself is deliberately minimal (a polymer cartoon) so the task measures
resolution, not styling.

    python scripts/generate_resolve_tasks.py     # -> tasks/mvs_resolve/*.json
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import urllib.request

from molbench.mvs import categorize

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "tasks" / "mvs_resolve"
CIF = "https://files.rcsb.org/download/{}.cif"
SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"

# (slug, prompt, UniProt accession, canonical PDB id, note[, min coverage]). Prompts are
# verbatim or lightly edited from the evaluator corpus; the canonical id is a well-known
# entry. A min coverage (fraction of the UniProt sequence one polymer entity must span)
# is set where the prompt asks for the whole protein: "the CFTR channel" is not answered
# by an isolated NBD1 domain.
SPECS = [
    ("pde5a", "I wanna see a structure of PDE5A", "O76074", "1udt",
     "Evaluator prompt (2026-09-30). Haiku answered 1UJ7, which does not exist."),
    ("pcsk9", "show the structure of PCSK9", "Q8NBP7", "2p4e",
     "Probe: Haiku answered 1D0G (death receptor 5 / TRAIL)."),
    ("cftr", "show me the CFTR channel", "P13569", "5uak",
     "Probe: Haiku answered 5UAY (a plant Toc75 POTRA domain).", 0.7),
    ("gfp", "show green fluorescent protein", "P42212", "1ema",
     "The starter chip's target; the model tends to be right here — a control."),
    ("myoglobin", "Show me sperm whale myoglobin", "P02185", "1mbn",
     "Corpus prompt asked for 'crab myoglobin' (no such entry); sperm whale is the classic."),
    ("lysozyme", "Show me hen egg white lysozyme", "P00698", "1lyz",
     "Starter chip; hundreds of valid entries — a control."),
]


def uniprot_length(accession: str) -> int:
    url = f"https://rest.uniprot.org/uniprotkb/{accession}.json?fields=length"
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.load(resp)["sequence"]["length"]


def entries_for(accession: str, min_length: int | None = None) -> list[str]:
    """All PDB entries with a polymer entity mapped to this UniProt accession (and, if
    ``min_length`` is set, at least that many residues in the same entity)."""
    nodes = [{"type": "terminal", "service": "text", "parameters": {
        "attribute": "rcsb_polymer_entity_container_identifiers."
                     "reference_sequence_identifiers.database_accession",
        "operator": "exact_match", "value": accession}}]
    if min_length:
        nodes.append({"type": "terminal", "service": "text", "parameters": {
            "attribute": "entity_poly.rcsb_sample_sequence_length",
            "operator": "greater_or_equal", "value": min_length}})
    query = {
        "query": {"type": "group", "logical_operator": "and", "nodes": nodes},
        # Entity-level, so both conditions hold for the same polymer entity.
        "return_type": "polymer_entity",
        "request_options": {"paginate": {"start": 0, "rows": 10000}},
    }
    req = urllib.request.Request(SEARCH, data=json.dumps(query).encode(),
                                 headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        if resp.status == 204:
            return []
        hits = json.load(resp)["result_set"]
    return sorted({hit["identifier"].split("_")[0].lower() for hit in hits})


def reference(pdb: str) -> dict:
    return {"kind": "root", "children": [{
        "kind": "download", "params": {"url": CIF.format(pdb)}, "children": [{
            "kind": "parse", "params": {"format": "mmcif"}, "children": [{
                "kind": "structure", "params": {"type": "model"}, "children": [{
                    "kind": "component", "params": {"selector": "polymer"}, "children": [{
                        "kind": "representation", "params": {"type": "cartoon"}}]}]}]}]}]}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    for slug, prompt, accession, canonical, note, *rest in SPECS:
        min_coverage = rest[0] if rest else None
        min_length = round(min_coverage * uniprot_length(accession)) if min_coverage else None
        ids = entries_for(accession, min_length)
        if canonical not in ids:
            raise SystemExit(f"{slug}: canonical {canonical} is not mapped to {accession}")
        ref = reference(canonical)
        task = {
            "id": f"res-{slug}",
            "category": "mvs",
            "source": "resolve",
            "title": f"Resolve by name: {slug}",
            "prompt": prompt,
            "reference_mvs": ref,
            "accepted_ids": ids,
            "categories": categorize(ref) + ["resolve"],
            "skills": ["resolve", "download", "component", "representation"],
            "notes": note,
            "provenance": {"uniprot": accession, "n_entries": len(ids),
                           "source": "RCSB search, reference_sequence_identifiers", "fetched": today,
                           **({"min_coverage": min_coverage, "min_length": min_length}
                              if min_coverage else {})},
        }
        (OUT / f"res-{slug}.json").write_text(json.dumps(task, indent=2) + "\n")
        print(f"res-{slug:10s} {accession}  {len(ids):4d} accepted entries  canonical {canonical}")


if __name__ == "__main__":
    main()
