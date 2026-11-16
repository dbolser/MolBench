"""
Clinical variants, from frozen data only.

The structure panel freezes, per disease protein, the missense variants that ClinVar
itself classifies as pathogenic or likely pathogenic (``data/panel/variants/<ACC>.json``,
built by ``scripts/build_panel.py``; the rule is in ``data/panel/README.md``). This
module reads those files and nothing else: it never opens a connection. It gives the
clinical task generator and the grounding packs

* the confirmed variants of a protein, each with the residues it maps to in a panel
  structure (:func:`confirmed`);
* the ways a variant is written (:func:`hgvs`, :func:`short`), and the words that may
  be used for its ClinVar classification (:func:`classification_words`);
* the *mature-protein numbering* of a position (:func:`mature_numbering`): older
  literature numbers many secreted proteins from the first residue of the processed
  chain ("TTR V30M" is p.Val50Met, "HBB E6V" is p.Glu7Val). The offset is read from
  UniProt's own processing features (signal peptide, propeptide, initiator
  methionine, chain), frozen in ``data/clinical/uniprot_processing.json`` by
  ``scripts/generate_clinical_tasks.py --refresh-processing``.

A variant is always named in UniProt numbering here (``position``), which is the
numbering of the HGVS protein-level name on the canonical isoform; the panel build
kept a variant only when a ClinVar record names the same protein change.
"""

from __future__ import annotations

import functools
import json
import pathlib
import re
from typing import NamedTuple

from . import grounding

REPO = pathlib.Path(__file__).resolve().parent.parent
PROCESSING = REPO / "data" / "clinical" / "uniprot_processing.json"

AA3 = {"A": "Ala", "R": "Arg", "N": "Asn", "D": "Asp", "C": "Cys", "Q": "Gln", "E": "Glu",
       "G": "Gly", "H": "His", "I": "Ile", "L": "Leu", "K": "Lys", "M": "Met", "F": "Phe",
       "P": "Pro", "S": "Ser", "T": "Thr", "W": "Trp", "Y": "Tyr", "V": "Val"}

# ClinVar's aggregate germline classifications the panel accepts, and the words a
# prompt may use for each. Nothing else is ever called pathogenic.
_CLASS_WORDS = {"Pathogenic": "pathogenic", "Likely pathogenic": "likely pathogenic",
                "Pathogenic/Likely pathogenic": "pathogenic/likely pathogenic"}
# Review statuses with more than one submitter behind the call, or a panel.
STRONG_REVIEW = ("criteria provided, multiple submitters, no conflicts",
                 "reviewed by expert panel", "practice guideline")


class Variant(NamedTuple):
    accession: str
    position: int            # UniProt residue number
    wild_type: str           # one-letter
    mutant: str              # one-letter
    classification: tuple[str, ...]   # ClinVar aggregate classification(s), as frozen
    review_status: tuple[str, ...]
    vcv: tuple[str, ...]     # the confirming ClinVar variation records
    structures: dict         # {entry: [residue, ...]} (wild-type identity verified)

    # The older four-field reading (position, wild type, mutant, significance).
    @property
    def unp_pos(self) -> int:
        return self.position

    @property
    def alt(self) -> str:
        return self.mutant

    @property
    def significance(self) -> str:
        return "; ".join(self.classification)


def proteins() -> list[dict]:
    """The panel's disease proteins (``panel.json``: accession, gene, entry, entries...)."""
    return list(grounding.panel()["disease_proteins"])


# --- ClinVar's own records behind a variant (audit of 2026-11-16) ----------------------
#
# The panel build kept a variant when *a* ClinVar record with the same protein change is
# classified pathogenic. Three kinds of record do not back the sentence "the <gene>
# variant ... is classified as pathogenic in ClinVar", and are not counted here:
#   * a record of another gene that encodes the same protein (CALM2/CALM3, HBA2);
#   * a haplotype record (two changes in cis: it says nothing about the single variant);
# and a variant whose every remaining record has no assertion criteria (zero stars) is
# kept apart (`criteria_provided`): the task generator does not ask about it.
CLINVAR_RECORDS = REPO / "data" / "panel" / "clinvar_records.json"
NOT_ONE_VARIANT = ("Haplotype", "Diplotype", "CompoundHeterozygote", "Phase unknown",
                   "Distinct chromosomes")
NO_CRITERIA = "no assertion criteria provided"
_TITLE_GENE = re.compile(r"^[^()\s]+\(([^()]+)\):")


def proteins_by_accession() -> dict[str, str]:
    """accession -> gene symbol, for the panel's disease proteins."""
    return {p["accession"]: p["gene"] for p in proteins()}


@functools.lru_cache(maxsize=None)
def clinvar_records() -> dict:
    """``{VCV: {title, kind, genes, classification, review_status, conditions}}``, frozen
    by ``scripts/freeze_clinvar_records.py``; with ``"retrieved"`` under the key ``""``."""
    data = json.loads(CLINVAR_RECORDS.read_text(encoding="utf-8"))
    return {**data["records"], "": {"retrieved": data["retrieved"], "source": data["source"]}}


def clinvar_snapshot() -> str:
    """The date the ClinVar classifications were read (``YYYY-MM-DD``)."""
    return clinvar_records()[""]["retrieved"]


def record_gene(record: dict) -> str | None:
    """The gene a ClinVar record's title names: ``NM_001743.6(CALM2):c.287A>T`` is CALM2."""
    m = _TITLE_GENE.match(record.get("title") or "")
    return m.group(1) if m else None


def own_records(gene: str, vcvs) -> list[tuple[str, dict]]:
    """The records among ``vcvs`` that are about one variant of ``gene``: the title
    names the gene (or a read-through locus that contains it, ``INS-IGF2`` for INS), the
    record is not a haplotype, and its classification is one the panel accepts."""
    out = []
    for vcv in vcvs:
        rec = clinvar_records().get(vcv)
        if rec is None:
            continue
        titled = record_gene(rec) or ""
        if titled != gene and gene not in titled.split("-"):
            continue
        if rec["kind"] in NOT_ONE_VARIANT or "c.[" in rec["title"] or "g.[" in rec["title"]:
            continue
        if rec["classification"].split(";")[0].strip() not in _CLASS_WORDS:
            continue
        out.append((vcv, rec))
    return out


@functools.lru_cache(maxsize=None)
def _sorted_variants(accession: str) -> tuple[tuple, tuple]:
    data = grounding.variants(accession)
    if data is None:
        return (), ()
    gene = data["gene"]
    kept, dropped = [], []
    for v in data["variants"]:
        own = own_records(gene, v["clinvar_vcv"])
        if not own:
            recs = [clinvar_records().get(x) or {} for x in v["clinvar_vcv"]]
            why = ("haplotype record only" if any(
                (record_gene(r) or "") == gene for r in recs) else
                "record of another gene only (" + ", ".join(sorted(
                    {record_gene(r) or "?" for r in recs})) + ")")
            dropped.append({"variant": f"{v['wild_type']}{v['position']}{v['mutant']}",
                            "reason": why, "clinvar_vcv": list(v["clinvar_vcv"])})
            continue
        # The words of a prompt come from the single-nucleotide record(s) when there is
        # one; an indel record with the same protein change counts only without one.
        snv = [x for x in own if x[1]["kind"] == "single nucleotide variant"] or own
        kept.append(Variant(accession, v["position"], v["wild_type"], v["mutant"],
                            tuple(sorted({r["classification"] for _, r in snv})),
                            tuple(sorted({r["review_status"] for _, r in snv})),
                            tuple(sorted(x for x, _ in snv)), v["structures"]))
    return tuple(kept), tuple(dropped)


def confirmed(accession: str) -> tuple[Variant, ...]:
    """The ClinVar-confirmed missense variants of a panel disease protein, in the
    frozen file's order: those with a ClinVar record of their own (`own_records`).
    Empty if the accession is not a panel disease protein."""
    return _sorted_variants(accession)[0]


def _forget() -> None:
    _sorted_variants.cache_clear()
    clinvar_records.cache_clear()


confirmed.cache_clear = _forget          # as when `confirmed` itself was the cached function


def not_confirmed(accession: str) -> tuple[dict, ...]:
    """Variants of the frozen list with no ClinVar record of their own, each with the
    reason (another gene's record only; a haplotype record only)."""
    return _sorted_variants(accession)[1]


def criteria_provided(v: Variant) -> bool:
    """At least one confirming record has assertion criteria (one star or more)."""
    return any(s != NO_CRITERIA for s in v.review_status)


def pathogenic_clinvar(acc: str) -> list[tuple[int, str, str, str]]:
    """``(UniProt position, wild type, mutant, classification)`` for every confirmed
    variant. Kept for older callers; it used to ask the UniProt service and now reads
    the frozen file."""
    return [(v.position, v.wild_type, v.mutant, v.significance) for v in confirmed(acc)]


def short(v: Variant, number: int | None = None) -> str:
    """``R175H``; with ``number``, the same change at another residue number."""
    return f"{v.wild_type}{v.position if number is None else number}{v.mutant}"


def hgvs(v: Variant) -> str:
    """The HGVS protein-level name, ``p.Arg175His``."""
    return f"p.{AA3[v.wild_type]}{v.position}{AA3[v.mutant]}"


def three_letter(v: Variant, number: int | None = None) -> str:
    """``Arg175His`` (no ``p.``: used for a name that is not in HGVS numbering)."""
    return f"{AA3[v.wild_type]}{v.position if number is None else number}{AA3[v.mutant]}"


def classification_words(variants: list[Variant] | Variant) -> str:
    """The words a prompt may use for ClinVar's verdict on one variant or on several:
    exactly the frozen classification when there is one ("pathogenic", "likely
    pathogenic", "pathogenic/likely pathogenic"; a trailing qualifier such as
    "; other" is dropped), and "pathogenic or likely pathogenic" when records differ.
    Raises if a classification is not one of the three the panel accepts."""
    many = [variants] if isinstance(variants, Variant) else list(variants)
    words = set()
    for v in many:
        for c in v.classification:
            base = c.split(";")[0].strip()
            if base not in _CLASS_WORDS:
                raise ValueError(f"{short(v)}: ClinVar classification {c!r} is not pathogenic")
            words.add(_CLASS_WORDS[base])
    if not words:
        raise ValueError("no ClinVar classification")
    return words.pop() if len(words) == 1 else "pathogenic or likely pathogenic"


def strongly_reviewed(v: Variant) -> bool:
    """More than one submitter, an expert panel or a practice guideline is behind
    at least one of the confirming ClinVar records."""
    return any(s in STRONG_REVIEW for s in v.review_status)


# --- mature-protein ("legacy") numbering ---------------------------------------------

@functools.lru_cache(maxsize=None)
def processing() -> dict:
    """The frozen UniProt processing features per accession (``{}`` if not built)."""
    return json.loads(PROCESSING.read_text())["proteins"] if PROCESSING.exists() else {}


def mature_numbering(accession: str, position: int) -> dict | None:
    """How ``position`` is numbered on the mature protein, or None when UniProt's
    features do not define one such numbering for it.

    The residues removed from the N-terminus are the features that follow one another
    from residue 1: an initiator methionine, or a signal or transit peptide, then
    possibly a propeptide. The mature numbering exists when a ``Chain`` feature starts
    at the very next residue and holds the position, and no ``Chain`` feature starts at
    residue 1 (a form that keeps the first residue would make the name ambiguous).
    Products cut out further along (bioactive peptides, activation fragments) do not
    change the numbering and are ignored; a protein whose first product is a
    ``Peptide`` (insulin's B chain) has none.

    Returns ``{"number": position - removed, "removed": n, "what": words}``, where
    ``what`` says what the removed residues are ("the initiator methionine", "the
    20-residue signal peptide", "the 46-residue signal peptide and propeptide")."""
    p = processing().get(accession)
    if not p:
        return None
    feats = [f for f in p["features"] if f["start"] is not None and f["end"] is not None]
    if len(feats) != len(p["features"]):
        return None            # an inexact boundary somewhere: do not guess
    removed, kinds = 0, []
    while True:
        nxt = [f for f in feats if f["start"] == removed + 1
               and f["type"] in ("Initiator methionine", "Signal", "Transit peptide", "Propeptide")]
        if len(nxt) != 1:
            break
        removed = nxt[0]["end"]
        kinds.append(nxt[0]["type"])
    chains = [f for f in feats if f["type"] == "Chain"]
    if (removed == 0 or any(f["start"] == 1 for f in chains)
            or not any(f["start"] == removed + 1 and f["end"] >= position for f in chains)
            or position <= removed):
        return None
    what = {("Initiator methionine",): "the initiator methionine",
            ("Signal",): f"the {removed}-residue signal peptide",
            ("Transit peptide",): f"the {removed}-residue transit peptide",
            ("Signal", "Propeptide"): f"the {removed}-residue signal peptide and propeptide",
            ("Transit peptide", "Propeptide"):
                f"the {removed}-residue transit peptide and propeptide"}.get(tuple(kinds))
    if what is None:
        return None
    return {"number": position - removed, "removed": removed, "what": what}
