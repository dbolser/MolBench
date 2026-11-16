"""
One vocabulary for the "what makes this task hard" facts the generators record.

Every generator writes such facts into ``provenance.difficulty`` (the clinical one into
``provenance.clinical.difficulty``), each under key names of its own: the same fact is
``author_chain_differs_from_label`` in one tier, ``auth_label_chain`` in another and
``author_chain_differs_from_label_chain`` in a third, and ``needs_numbering_offset``
means "author number differs from the UniProt number" in the clinical tier but "author
number differs from the label number" in the follow-up and accept-set tiers. The task
files are not edited; this module is the one place the names are mapped, and the
scorecards and paper tables stratify on the names below only.

    normalised(task)  -> {key: True | False | None}   (None = this generator records
                                                        nothing about it)

Nothing here is read at grade time: these facts never change a score.
"""

from __future__ import annotations

from typing import Any, Callable

# The vocabulary: key -> what it says, in the words the paper uses.
VOCABULARY = {
    "needs_offset":
        "the residue number in the request (a UniProt position, or a mature-protein "
        "number) is not the residue's author number in the structure, so the right "
        "answer applies a numbering offset",
    "author_label_numbers_differ":
        "the target residue's author number differs from its label (mmCIF) number",
    "chain_mismatch":
        "the target's author chain id differs from its label chain id",
    "needs_ligand_identity":
        "the request names a compound in words and the answer needs its component id",
    "needs_uniprot_mapping":
        "the answer needs a UniProt-to-structure residue mapping",
    "needs_structure_lookup":
        "the atoms asked for are not named in the request and must be found in the entry",
    "needs_entry_lookup":
        "the request names a protein, not an entry: the answer needs a PDB id",
    "insertion_code":
        "a target residue has an insertion code",
    "needs_referent_from_context":
        "a follow-up request names its object only through the start state "
        "(\"it\", \"the red chain\")",
    "hide_toggle":
        "an API twin that reaches the MVS scene only by switching off something the "
        "viewer draws by default, which the request does not state",
    "number_in_name_as_author_number_is_right":
        "clinical tier: using the number in the variant name directly as the author "
        "residue number gives the right residue (no mapping needed to be right)",
    "name_in_mature_numbering":
        "clinical tier: the variant name counts from the first residue of the mature "
        "protein, and the request says so",
    "alphafold_model":
        "clinical tier: the structure is an AlphaFold DB model (numbered as UniProt)",
}
KEYS = tuple(VOCABULARY)
# The keys the clinical results are stratified on (plan rulings; CORPUS.md).
CLINICAL_STRATA = ("needs_offset", "chain_mismatch", "number_in_name_as_author_number_is_right",
                   "name_in_mature_numbering", "alphafold_model", "author_label_numbers_differ")


def _any_nonzero(v: Any) -> bool:
    return any(x != 0 for x in v) if isinstance(v, (list, tuple)) else bool(v)


# generator script -> {normalised key: raw key, or a function of the raw dict}.
# A normalised key that is absent here is None for that generator's tasks.
_MVS_CORE = {
    "author_label_numbers_differ": "author_number_differs_from_label",
    "chain_mismatch": "author_chain_differs_from_label",
    "needs_ligand_identity": "needs_ligand_identity",
    "needs_uniprot_mapping": "needs_uniprot_mapping",
    "needs_structure_lookup": "needs_structure_lookup",
    "insertion_code": "insertion_code",
    # these generators ask in author numbering (their tier READMEs say so)
    "needs_offset": lambda d: False,
}
_FOLLOWUP_ACCEPT = {
    # called needs_numbering_offset in these two generators, but computed as
    # auth_seq_id != label_seq_id; their requests use author numbering
    "author_label_numbers_differ": "needs_numbering_offset",
    "chain_mismatch": "author_chain_differs_from_label",
    "needs_ligand_identity": "needs_ligand_identity",
    "needs_uniprot_mapping": "needs_uniprot_mapping",
    "needs_offset": lambda d: False,
}
SOURCES: dict[str, dict[str, str | Callable[[dict], Any]]] = {
    "scripts/generate_mvs_tasks.py": _MVS_CORE,
    "scripts/generate_grounded_tasks.py": _MVS_CORE,
    "scripts/author_interaction_tasks.py": _MVS_CORE,
    "scripts/generate_resolve_tasks.py": {**_MVS_CORE, "needs_entry_lookup": "needs_entry_lookup"},
    "scripts/translate_mvs_to_api.py": {
        **_MVS_CORE,
        "hide_toggle": lambda d: bool(d.get("context_switched_off")),
    },
    "scripts/generate_followup_tasks.py": {
        **_FOLLOWUP_ACCEPT, "needs_referent_from_context": "needs_referent_from_context"},
    "scripts/generate_accept_set_tasks.py": _FOLLOWUP_ACCEPT,
    "scripts/generate_api_tasks.py": {
        "author_label_numbers_differ": "numbering_offset",
        "chain_mismatch": "auth_label_chain",
        "needs_ligand_identity": "ligand_identity_needed",
        "needs_uniprot_mapping": "uniprot_mapping",
        # only its UniProt-numbered tasks record author_minus_uniprot; the others ask
        # in author or label numbering as the request states
        "needs_offset": lambda d: _any_nonzero(d.get("author_minus_uniprot")),
        "insertion_code": lambda d: None,  # recorded per structure, not per target
    },
    "scripts/generate_clinical_tasks.py": {
        "needs_offset": "needs_numbering_offset",
        "author_label_numbers_differ": "author_number_differs_from_label_number",
        "chain_mismatch": "author_chain_differs_from_label_chain",
        "needs_ligand_identity": "needs_ligand_identity",
        "needs_uniprot_mapping": "needs_uniprot_mapping",
        "insertion_code": "insertion_code",
        "number_in_name_as_author_number_is_right": "number_in_name_as_author_number_is_right",
        "name_in_mature_numbering": "name_in_mature_numbering",
        "alphafold_model": "alphafold_model",
    },
}


class UnknownGenerator(KeyError):
    """A task was written by a generator this module has no key map for. Add the map:
    silently reporting "no difficulty facts" would drop the task from every stratum."""


def source_provenance(task: dict) -> dict:
    """The provenance of the task's original: its own, or - for a paraphrase, whose
    own provenance is the paraphrase generator's - the original's, kept under
    ``provenance.source``."""
    prov = task.get("provenance") or {}
    if task.get("paraphrase_of") and isinstance(prov.get("source"), dict):
        return prov["source"]
    return prov


def raw(task: dict) -> dict:
    """The difficulty facts as the generator wrote them (its own key names)."""
    prov = source_provenance(task)
    clinical = prov.get("clinical")
    if isinstance(clinical, dict) and isinstance(clinical.get("difficulty"), dict):
        return clinical["difficulty"]
    d = prov.get("difficulty")
    return d if isinstance(d, dict) else {}


def normalised(task: dict) -> dict[str, bool | None]:
    """The task's difficulty facts under the names of `VOCABULARY`. A key the task's
    generator does not record is None. A task with no difficulty block at all (the
    October tasks, test fixtures) gives None throughout."""
    facts = raw(task)
    out: dict[str, bool | None] = dict.fromkeys(KEYS)
    if not facts:
        return out
    script = source_provenance(task).get("script")
    if script not in SOURCES:
        raise UnknownGenerator(f"task {task.get('id')}: no difficulty key map for generator "
                               f"{script!r} (molbench/difficulty.py SOURCES)")
    for key, src in SOURCES[script].items():
        value = src(facts) if callable(src) else facts.get(src)
        out[key] = None if value is None else bool(value)
    return out


def true_keys(task: dict) -> list[str]:
    """The vocabulary keys that hold for the task, in vocabulary order."""
    return [k for k, v in normalised(task).items() if v]
