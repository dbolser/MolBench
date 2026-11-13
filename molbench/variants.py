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


@functools.lru_cache(maxsize=None)
def confirmed(accession: str) -> tuple[Variant, ...]:
    """The ClinVar-confirmed missense variants of a panel disease protein, in the
    frozen file's order. Empty if the accession is not a panel disease protein."""
    data = grounding.variants(accession)
    if data is None:
        return ()
    return tuple(Variant(accession, v["position"], v["wild_type"], v["mutant"],
                         tuple(v["clinvar_classification"]), tuple(v["clinvar_review_status"]),
                         tuple(v["clinvar_vcv"]), v["structures"])
                 for v in data["variants"])


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
