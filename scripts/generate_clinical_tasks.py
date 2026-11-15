#!/usr/bin/env python3
"""
Generate the clinical-variant tier on both tracks: ``tasks/mvs_clinical/`` and its
twins in ``tasks/api_clinical/``.

Every task names a structure (a PDB entry, or an AlphaFold DB model) and one or more
missense variants of a disease protein by their protein-level name, and asks for the
residue each variant replaces to be shown. The model has to work out which residue of
the structure that is. Nothing here is hand-written per task: variants come from the
frozen ClinVar-confirmed lists (``data/panel/variants``), residues from the frozen
SIFTS mapping, secondary structure from the frozen facts, and every reference is
checked against the frozen atom table before it is written. No network.

    uv run --extra authoring python scripts/generate_clinical_tasks.py           # write
    uv run --extra authoring python scripts/generate_clinical_tasks.py --check   # fail if stale
    uv run python scripts/generate_clinical_tasks.py --refresh-processing        # (network)

``--refresh-processing`` is the only network path: it downloads, for the panel's
disease proteins, UniProt's processing features (signal peptide, propeptide, initiator
methionine, chain) and freezes them in ``data/clinical/uniprot_processing.json``. They
define the mature-protein numbering of the "legacy" templates.

The templates, what each reference is derived from, and the counts are written to
``tasks/mvs_clinical/README.md`` and ``tasks/api_clinical/README.md`` by this script.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import random
import re
import sys
from collections import Counter

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import drawn, grounding, runner, sifts, tasks as T, variants as V  # noqa: E402
from molbench import pdbe_state as ps  # noqa: E402
from molbench.atoms import load_table  # noqa: E402

SCRIPT = "scripts/generate_clinical_tasks.py"
OUT = {"mvs": REPO / "tasks" / "mvs_clinical", "api": REPO / "tasks" / "api_clinical"}
SEED = "molbench-clinical-v1"
DATE = "2026-11-13"            # fixed, so a rebuild is byte-identical
MAX_PER_STRUCTURE = 6          # tasks of this tier on one structure, per track
MAX_FAMILY_SHARE = 0.12
HELDBACK_SHARE = 0.20
# A structure is public or held back for the whole corpus, not per tier
# (scripts/validate_tasks.py). 8CE0 is already held back by the fixture tasks
# (tests/fixtures/tasks), so it is held back here too.
ALSO_HELDBACK = ("8ce0",)
# Structures another tier publishes, which this tier must therefore not hold back.
# Empty until the tiers' held-back sets are reconciled at integration.
NEVER_HELDBACK: tuple[str, ...] = ()
UNIPROT_URL = ("https://rest.uniprot.org/uniprotkb/{}.json?fields="
               "ft_signal,ft_propep,ft_init_met,ft_chain,ft_peptide,ft_transit")
AF_URL = "https://alphafold.ebi.ac.uk/files/AF-{}-F1-model_v6.cif"
PDB_URL = "https://files.rcsb.org/download/{}.cif"

# Well-known variants, used for a protein's first task when the frozen data confirms
# them (ClinVar-confirmed and verified on the structure); otherwise the choice is
# seeded. This list picks *which* variant is asked about, never what the answer is.
FEATURED = {"P04637": ["R175H", "R248Q", "R273H"], "P68871": ["E7V"], "P02766": ["V50M"],
            "P13569": ["G551D"], "P01009": ["E366K"], "P00441": ["A5V"], "P02649": ["R176C"],
            "P61626": ["I74T"], "P04062": ["N409S"], "P01112": ["G12S"]}

# Colours a request may name: plain words from the task palette.
HIGHLIGHT = ("red", "orange", "yellow", "green", "blue", "purple", "magenta", "cyan")
BACKDROP = ("gray", "white", "khaki")
SSE_COLOURS = ("teal", "salmon", "plum", "brown")
REPS = {"ball_and_stick": ("ball-and-stick", "ball-and-stick"),      # MVS: (API name, words)
        "spacefill": ("spacefill", "spacefill spheres")}
assert set(HIGHLIGHT + BACKDROP + SSE_COLOURS) <= set(drawn.TASK_PALETTE)

API_NOTE = ("pdbe-molstar resolves uniprot_accession + uniprot_residue_number itself (SIFTS), "
            "so this API task tests knowing that selector and supplying the accession; its MVS "
            "twin tests doing the UniProt-to-structure mapping.")

FAMILIES = {
    "clin-hgvs-target": "One variant, HGVS name (p.Arg175His); only the residue is requested.",
    "clin-hgvs-context": "One variant, HGVS name; residue on a cartoon of the whole structure.",
    "clin-short-target": "One variant, one-letter name (R175H); only the residue is requested.",
    "clin-short-context": "One variant, one-letter name; residue on a cartoon of the whole structure.",
    "clin-chain": "One variant, in one named chain of a structure with several copies; only the residue.",
    "clin-legacy-target": "One variant named in mature-protein numbering (TTR V30M); only the residue.",
    "clin-legacy-context": "One variant named in mature-protein numbering; residue on a cartoon of the whole structure.",
    "clin-multi-target": "Two to four variants of one protein; only the residues.",
    "clin-multi-context": "Two to four variants of one protein; residues on a cartoon of the whole structure.",
    "clin-sse-helix": "One variant and the annotated helix that contains its residue.",
    "clin-sse-strand": "One variant and the annotated beta strand that contains its residue.",
    "clin-pair-target": "The same variant asked on two structures of one protein (numbered differently, or a control pair); only the residue.",
    "clin-pair-context": "The same variant asked on two structures of one protein; residue on a cartoon of the whole structure.",
}


# --------------------------------------------------------------------------- #
# Frozen UniProt processing features (the one network path)
# --------------------------------------------------------------------------- #
def refresh_processing() -> None:
    import urllib.request
    proteins = {}
    for p in V.proteins():
        acc = p["accession"]
        req = urllib.request.Request(UNIPROT_URL.format(acc), headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.load(resp)
        feats = []
        for f in data.get("features", []):
            loc = f["location"]
            exact = loc["start"].get("modifier") == "EXACT" and loc["end"].get("modifier") == "EXACT"
            feats.append({"type": f["type"],
                          "start": loc["start"].get("value") if exact else None,
                          "end": loc["end"].get("value") if exact else None,
                          "description": f.get("description", "")})
        proteins[acc] = {"gene": p["gene"], "source": UNIPROT_URL.format(acc),
                         "features": sorted(feats, key=lambda f: (f["start"] or 0, f["type"]))}
        print(f"  {acc} {p['gene']}: " + ", ".join(
            f"{f['type']} {f['start']}-{f['end']}" for f in proteins[acc]["features"]))
    V.PROCESSING.parent.mkdir(parents=True, exist_ok=True)
    V.PROCESSING.write_text(json.dumps({
        "what": "UniProt processing features (signal peptide, propeptide, initiator "
                "methionine, transit peptide, chain, peptide) of the panel's disease "
                "proteins. A position without an exact value is null.",
        "retrieved": DATE, "proteins": proteins}, indent=1, sort_keys=True) + "\n")
    print(f"wrote {V.PROCESSING.relative_to(REPO)}")


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def rng(*key) -> random.Random:
    digest = hashlib.sha256(":".join(map(str, (SEED,) + key)).encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


def is_af(entry: str) -> bool:
    return entry.startswith("af-")


def entry_label(entry: str, protein: dict) -> str:
    """How a prompt names the structure."""
    if is_af(entry):
        acc = protein["accession"]
        return f"the AlphaFold DB model AF-{acc}-F1 (model version 6)"
    return f"PDB entry {entry.upper()}"


def entry_short(entry: str, protein: dict) -> str:
    return f"AF-{protein['accession']}-F1 (AlphaFold DB, model version 6)" if is_af(entry) \
        else entry.upper()


def res_selector(r: dict) -> dict:
    """A residue of the frozen variant file as an MVS expression in author terms."""
    sel = {"auth_asym_id": r["auth_asym_id"], "auth_seq_id": r["auth_seq_id"]}
    if r["pdbx_PDB_ins_code"]:
        sel["pdbx_PDB_ins_code"] = r["pdbx_PDB_ins_code"]
    return sel


def label_selector(r: dict) -> dict:
    return {"label_asym_id": r["label_asym_id"], "label_seq_id": r["label_seq_id"]}


def scene(entry: str, protein: dict, components: list[dict]) -> dict:
    url = AF_URL.format(protein["accession"]) if is_af(entry) else PDB_URL.format(entry)
    return {"root": {"kind": "root", "children": [
        {"kind": "download", "params": {"url": url},
         "children": [{"kind": "parse", "params": {"format": "mmcif"}, "children": [
             {"kind": "structure", "params": {"type": "model"}, "children": components}]}]}]}}


def component(selector, rep: str, color: str) -> dict:
    return {"kind": "component", "params": {"selector": selector}, "children": [
        {"kind": "representation", "params": {"type": rep},
         "children": [{"kind": "color", "params": {"color": color}}]}]}


def load_call(entry: str, protein: dict) -> dict:
    if is_af(entry):
        return {"action": "load", "custom_data": {"url": AF_URL.format(protein["accession"]),
                                                   "format": "cif", "binary": False}}
    return {"action": "load", "molecule_id": entry}


def join_words(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


# --------------------------------------------------------------------------- #
# Candidates: which variants can be asked on which structure
# --------------------------------------------------------------------------- #
class Site:
    """One variant on one structure: the residues it maps to, checked."""

    def __init__(self, protein: dict, entry: str, v: V.Variant):
        self.protein, self.entry, self.v = protein, entry, v
        self.residues = sorted(v.structures.get(entry, []),
                               key=lambda r: (r["auth_asym_id"], r["auth_seq_id"]))
        # The chains that hold this UniProt position: those whose modelled residues
        # span it (a protein deposited as several chains, such as insulin's A and B
        # chains, has the position in only some of them).
        self.chains = [c for c in grounding.facts(entry)["chains"]
                       if any(u["accession"] == v.accession
                              and u["unp_first"] <= v.position <= u["unp_last"]
                              for u in c.get("uniprot", []))]

    @property
    def complete(self) -> bool:
        """The wild-type residue is modelled in every chain that holds the position."""
        return bool(self.residues) and \
            {r["label_asym_id"] for r in self.residues} == {c["label_asym_id"] for c in self.chains}

    def offsets(self, residues=None) -> list[int]:
        return sorted({r["auth_seq_id"] - self.v.position for r in residues or self.residues})


def sites(protein: dict, entry: str) -> list[Site]:
    return [s for s in (Site(protein, entry, v) for v in V.confirmed(protein["accession"]))
            if s.complete]


def uniprot_residue_name(protein: dict, position: int) -> str | None:
    """The residue UniProt has at ``position``, as far as the frozen data says: its
    three-letter name, ``""`` when the position is past the end of the sequence, or
    None when no frozen file shows it (not modelled in any panel structure of the
    protein and not the site of a frozen variant)."""
    acc = protein["accession"]
    data = grounding.variants(acc)
    if position < 1 or position > data["uniprot_length"]:
        return ""
    for v in V.confirmed(acc):
        if v.position == position:
            return V.AA3[v.wild_type].upper()
    for entry in protein["entries"]:
        hits = {r.comp_id for r in sifts.uniprot_residues(entry, acc, position) or []}
        if len(hits) == 1:
            return hits.pop()
    return None


def mature_reading(protein: dict, v: V.Variant) -> bool | None:
    """Could a name written in UniProt numbering (R500Q) be taken for a name in
    mature-protein numbering? That reading puts it ``removed`` residues further along.
    False: the protein has no mature numbering there, or that other residue is a
    different amino acid (or past the end), so the wild-type letter settles it.
    True: it is the same amino acid. None: the frozen data does not show it."""
    m = V.mature_numbering(v.accession, v.position)
    if not m:
        return False
    other = uniprot_residue_name(protein, v.position + m["removed"])
    return None if other is None else other == V.AA3[v.wild_type].upper()


def pick(pool: list[Site], used: set, key: tuple, n: int = 1, featured: bool = False,
         want=None) -> list[Site]:
    """Choose ``n`` sites at positions not yet used on the structure: a featured variant
    first (when asked), then seeded among the strongly reviewed ones, then among all."""
    pool = [s for s in pool if (s.entry, s.v.position) not in used and (want is None or want(s))]
    by_pos: dict[int, list[Site]] = {}
    for s in pool:
        by_pos.setdefault(s.v.position, []).append(s)
    chosen: list[Site] = []
    if featured:
        for name in FEATURED.get(pool[0].v.accession if pool else "", []):
            hit = [s for s in pool if V.short(s.v) == name]
            if hit and len(chosen) < n:
                chosen.append(hit[0])
                by_pos.pop(hit[0].v.position, None)
                break
    r = rng("pick", *key)
    strong = sorted(p for p, ss in by_pos.items() if any(V.strongly_reviewed(s.v) for s in ss))
    rest = sorted(set(by_pos) - set(strong))
    r.shuffle(strong)
    r.shuffle(rest)
    for pos in strong + rest:
        if len(chosen) >= n:
            break
        ss = [s for s in by_pos[pos] if V.strongly_reviewed(s.v)] or by_pos[pos]
        chosen.append(r.choice(sorted(ss, key=lambda s: V.short(s.v))))
    if len(chosen) < n:
        return []
    for s in chosen:
        used.add((s.entry, s.v.position))
    return chosen


# --------------------------------------------------------------------------- #
# Wording
# --------------------------------------------------------------------------- #
def protein_phrase(protein: dict, with_accession: bool) -> str:
    data = grounding.variants(protein["accession"])
    name = data["protein"]
    if with_accession:
        return f"{protein['gene']} ({name}, UniProt {protein['accession']})"
    return f"{protein['gene']} ({name})"


def variant_names(naming: str, group: list[Site]) -> tuple[list[str], str]:
    """The variants as the prompt writes them, and a sentence about the numbering
    (empty unless the name is not in UniProt numbering)."""
    if naming == "hgvs":
        return [V.hgvs(s.v) for s in group], ""
    if naming == "short":
        return [V.short(s.v) for s in group], ""
    m = V.mature_numbering(group[0].v.accession, group[0].v.position)
    names = [V.short(s.v, V.mature_numbering(s.v.accession, s.v.position)["number"]) for s in group]
    note = (f" The name {names[0]} is in mature-protein numbering: residues are counted from "
            f"the first residue of the mature protein, that is, after {m['what']}.")
    return names, note


def scope_phrase(site: Site, scope: str, chain: dict | None, many: bool = False) -> str:
    if scope == "chain":
        differs = chain["auth_asym_id"] != chain["label_asym_id"]
        return f" in chain {chain['auth_asym_id']} only" + (" (author chain ID)" if differs else "")
    if len(site.chains) > 1:
        return " in every chain that has " + ("them" if many else "it")
    return ""


def make_prompt(naming: str, group: list[Site], entry: str, protein: dict,
                with_accession: bool, scope: str, chain, look: dict, wording: int,
                sse: dict | None = None) -> str:
    """The request. Three wordings per kind of request; ``wording`` picks one."""
    names, note = variant_names(naming, group)
    cls = V.classification_words([s.v for s in group])
    prot = protein_phrase(protein, with_accession)
    where = entry_label(entry, protein)
    Where = where[0].upper() + where[1:]
    rep = f"{look['color']} {REPS[look['rep']][1]}"
    sc = scope_phrase(group[0], scope, chain, len(group) > 1)
    if len(group) > 1:
        listed = join_words(names)
        lead = [f"the residues replaced by the {prot} variants {listed} (each {cls} in ClinVar)",
                f"the residues they replace",
                f"the wild-type residues at the positions of the {prot} missense variants "
                f"{listed} (each {cls} in ClinVar)"][wording]
        opener = f"{Where}: the {prot} variants {listed} are each classified as {cls} in ClinVar. "
    else:
        lead = [f"the residue replaced by the {cls} {prot} variant {names[0]} (ClinVar)",
                f"the residue it replaces",
                f"the wild-type residue at the position of the {prot} missense variant "
                f"{names[0]} ({cls} in ClinVar)"][wording]
        opener = f"{Where}: the {prot} variant {names[0]} is classified as {cls} in ClinVar. "
    if sse:
        kind = "helix" if sse["kind"] == "helix" else "beta strand"
        body = [
            f"In {where}, take {lead}{sc}. Show the {kind} that contains it (as annotated in "
            f"the entry) as a {sse['color']} cartoon and the residue itself as {rep}.",
            f"{opener}Show the {kind} (as annotated in the entry) that contains {lead}{sc} as a "
            f"{sse['color']} cartoon, and the residue itself as {rep}.",
            f"Using {where}, show the annotated {kind} that carries {lead}{sc} as a "
            f"{sse['color']} cartoon, with that residue as {rep}.",
        ][wording]
    elif look.get("backdrop"):
        b = look["backdrop"]
        body = [
            f"In {where}, show the whole structure as a {b} cartoon and {lead} as {rep}{sc}.",
            f"{opener}Show the whole structure as a {b} cartoon, with {lead} as {rep}{sc}.",
            f"Using {where}, draw a {b} cartoon of the whole structure and show, as {rep}, "
            f"{lead}{sc}.",
        ][wording]
    else:
        body = [
            f"In {where}, show {lead} as {rep}{sc}.",
            f"{opener}Show {lead} as {rep}{sc}.",
            f"Using {where}, show as {rep} {lead}{sc}.",
        ][wording]
    return body + note


# --------------------------------------------------------------------------- #
# Building one twin pair
# --------------------------------------------------------------------------- #
def build_pair(family: str, naming: str, group: list[Site], *, context: str, scope: str = "all",
               chain: dict | None = None, sse: dict | None = None, key: tuple = ()) -> list[dict]:
    """The MVS task and its API twin for one request. ``context`` is "none" (only the
    residue is requested), "structure" (a cartoon of the whole structure too) or "sse"
    (the helix or strand that contains the residue too)."""
    site = group[0]
    entry, protein, acc = site.entry, site.protein, site.v.accession
    # A bare one-letter name must not also make sense in mature-protein numbering
    # (prothrombin R500Q: 43 residues further along there is another arginine). Such
    # a variant is asked by its HGVS name, which says which numbering it is in.
    as_mature = [mature_reading(protein, s.v) for s in group]
    if naming == "short" and any(x is not False for x in as_mature):
        assert not family.startswith("clin-short"), (entry, [V.short(s.v) for s in group])
        naming = "hgvs"
    # The two structures of a pair get the same wording, colours and representation,
    # and both name the accession (an AlphaFold model's name holds it anyway), so that
    # the structure is the only thing that differs between them.
    paired = bool(key)
    r = rng("look", family, *([] if paired else [entry]), *[V.short(s.v) for s in group], *key)
    look = {"rep": r.choice(sorted(REPS)), "color": r.choice(HIGHLIGHT),
            "backdrop": r.choice(BACKDROP) if context == "structure" else None}
    if sse:
        sse = {**sse, "color": r.choice(SSE_COLOURS)}
        look["rep"] = "ball_and_stick"
    with_accession = r.random() < 0.5 or paired
    wording = r.randrange(3)
    prompt = make_prompt(naming, group, entry, protein, with_accession, scope, chain,
                         look, wording, sse)

    residues = [x for s in group for x in s.residues
                if chain is None or x["label_asym_id"] == chain["label_asym_id"]]
    assert residues
    table = load_table(entry)
    target_sel = [label_selector(x) for x in residues]
    target_mask = table.selector(target_sel)

    # --- MVS reference: author numbering, as a structural biologist would write it.
    mvs_sel = [res_selector(x) for x in residues]
    comps = []
    api_data = []
    if context == "structure":
        comps.append(component("all", "cartoon", look["backdrop"]))
    if sse:
        rng_sel = {"auth_asym_id": sse["auth_asym_id"], "beg_auth_seq_id": sse["beg_auth_seq_id"],
                   "end_auth_seq_id": sse["end_auth_seq_id"]}
        comps.append(component(rng_sel, "cartoon", sse["color"]))
        api_data.append({"auth_asym_id": sse["auth_asym_id"],
                         "start_auth_residue_number": sse["beg_auth_seq_id"],
                         "end_auth_residue_number": sse["end_auth_seq_id"], "color": sse["color"]})
    comps.append(component(mvs_sel if len(mvs_sel) > 1 else mvs_sel[0], look["rep"], look["color"]))
    mvs_ref = scene(entry, protein, comps)

    # --- API reference: the viewer's own UniProt selector, one item per variant.
    api_rep = REPS[look["rep"]][0]
    under = {"none": None, "structure": look["backdrop"], "sse": sse and sse["color"]}[context]

    meant: list[dict] = []     # per item of the reference's `color` call: the atoms meant

    def calls(ribbon, style: bool) -> list[dict]:
        """``ribbon``: the colour given to the residue's own stretch of cartoon."""
        items = list(api_data)
        meant.clear()
        if sse:
            meant.append({"atoms": {k: sse[k] for k in ("label_asym_id", "beg_label_seq_id",
                                                         "end_label_seq_id")},
                          "what": f"the annotated {sse['kind']}"})
        for s in group:
            mine = [x for x in s.residues
                    if chain is None or x["label_asym_id"] == chain["label_asym_id"]]
            if is_af(entry):
                meant.extend({"atoms": label_selector(x), "what": f"{V.hgvs(s.v)} residue"}
                             for x in mine)
            else:
                meant.append({"atoms": [label_selector(x) for x in mine],
                              "what": f"{V.hgvs(s.v)} residue(s)"})
            if is_af(entry):
                # The grader has no UniProt lookup for an AlphaFold model yet (see the
                # README); the model is numbered as UniProt, so author numbers say the same.
                sels = [{"auth_asym_id": x["auth_asym_id"], "auth_seq_id": x["auth_seq_id"]}
                        for x in s.residues]
            else:
                sels = [{"uniprot_accession": acc, "uniprot_residue_number": s.v.position}]
                if chain is not None:
                    sels = [{"auth_asym_id": chain["auth_asym_id"], **sels[0]}]
            items += [{**item, "color": ribbon, "representation": api_rep,
                       "representationColor": look["color"]} for item in sels]
        call = {"action": "color", "data": items}
        if context == "structure":
            call["non_selected_color"] = look["backdrop"]
        head = [load_call(entry, protein)]
        if style:
            head.append({"action": "set_visual_style", "style": "cartoon"})
        return head + [call]

    api_ref = calls(under, False)
    api_targets = [{"action": 1, "param": i, "atoms": m["atoms"], "what": m["what"],
                    "n_atoms": bin(table.selector(m["atoms"])).count("1")}
                   for i, m in enumerate(meant)]
    # Equally right: the residue's stretch of cartoon also takes the highlight colour
    # (the API's `color` key cannot simply be left out: that paints it orange); and,
    # with a whole-structure cartoon, setting the cartoon style explicitly.
    api_accepted = [calls(look["color"], False)]
    if context == "structure":
        api_accepted += [calls(under, True), calls(look["color"], True)]

    # --- checks against the frozen tables
    checks = []
    assert target_mask and table.selector(mvs_sel) == target_mask, (entry, mvs_sel)
    names3 = {x["comp_id"] for s in group for x in s.residues}
    for s in group:
        assert {x["comp_id"] for x in s.residues} == {V.AA3[s.v.wild_type].upper()}
    unp_mask = 0
    for s in group:
        unp_mask |= sifts.uniprot_atoms(entry, acc, s.v.position) or 0
    if chain is None:
        assert unp_mask == target_mask, (entry, [V.short(s.v) for s in group])
    else:
        chain_mask = table.selector({"label_asym_id": chain["label_asym_id"]})
        assert unp_mask & chain_mask == target_mask and unp_mask != target_mask
    n_atoms = bin(target_mask).count("1")
    checks.append(f"target ({len(residues)} residue(s), {n_atoms} atoms, residue name(s) "
                  f"{'/'.join(sorted(names3))} = the wild type) is the same atom set by three "
                  "routes on the frozen atom table: label numbering from the frozen variant "
                  "file, author numbering as written in the MVS reference, and the frozen "
                  "SIFTS lookup of the UniProt position")
    if sse:
        lab = table.selector({"label_asym_id": sse["label_asym_id"],
                              "beg_label_seq_id": sse["beg_label_seq_id"],
                              "end_label_seq_id": sse["end_label_seq_id"]})
        assert lab and table.selector(rng_sel) == lab and target_mask & lab == target_mask
        checks.append(f"the {sse['kind']} range is the same atom set in author and in label "
                      "numbering and contains the target residue")

    offsets = sorted({x["auth_seq_id"] - s.v.position for s in group for x in s.residues
                      if chain is None or x["label_asym_id"] == chain["label_asym_id"]})
    numbering = grounding.variants(acc)["entries"][entry]["numbering"]
    mature = [V.mature_numbering(acc, s.v.position) for s in group]
    difficulty = {
        "needs_uniprot_mapping": True,
        "needs_numbering_offset": any(o != 0 for o in offsets),
        "author_minus_uniprot": offsets,
        "structure_has_offset": bool(numbering["offset"]),
        "author_chain_differs_from_label_chain":
            any(x["auth_asym_id"] != x["label_asym_id"] for x in residues),
        "author_number_differs_from_label_number":
            any(x["auth_seq_id"] != x["label_seq_id"] or x["pdbx_PDB_ins_code"] for x in residues),
        "insertion_code": any(bool(x["pdbx_PDB_ins_code"]) for x in residues),
        "needs_ligand_identity": False,
        # An AlphaFold DB model is named by its accession (AF-P68871-F1).
        "accession_in_prompt": with_accession or is_af(entry),
        "protein_copies_in_structure": len(site.chains),
        "target_residues": len(residues),
        "alphafold_model": is_af(entry),
        "name_in_mature_numbering": naming == "legacy",
        "mature_number_equals_author_number":
            (all(m and all(x["auth_seq_id"] == m["number"] and not x["pdbx_PDB_ins_code"]
                           for x in s.residues) for s, m in zip(group, mature))
             if naming == "legacy" else None),
    }
    # A decoy: the residue that carries the name's number as its author number is a
    # different residue of the same amino acid, so checking the wild type does not
    # expose the face-value reading. An HGVS name (p.) and a name whose numbering the
    # prompt states leave no doubt; a bare one-letter name must not have a decoy.
    decoy = False
    for s, name in zip(group, variant_names(naming, group)[0]):
        number = int(re.search(r"\d+", name).group())
        for x in s.residues:
            if (chain is None or x["label_asym_id"] == chain["label_asym_id"]) and \
                    (x["auth_seq_id"] != number or x["pdbx_PDB_ins_code"]):
                decoy = decoy or bool(table.selector({
                    "auth_asym_id": x["auth_asym_id"], "auth_seq_id": number,
                    "label_comp_id": V.AA3[s.v.wild_type].upper()}))
    assert not (decoy and naming == "short"), (entry, [V.short(s.v) for s in group])
    difficulty["number_in_name_as_author_number_is_same_amino_acid"] = decoy
    # The other trap of a name in UniProt numbering: read as a mature-protein number it
    # lands on the same amino acid (None: the frozen data does not show that residue).
    # A bare one-letter name is used only where this is False (see above), so True and
    # None occur only under an HGVS name.
    difficulty["name_read_as_mature_number_is_same_amino_acid"] = (
        None if naming == "legacy" else
        True if any(x is True for x in as_mature) else
        None if any(x is None for x in as_mature) else False)
    clinical = {
        "gene": protein["gene"], "accession": acc,
        "protein": grounding.variants(acc)["protein"],
        "naming": naming, "scope": scope, "context": context,
        "chain": chain and {"auth_asym_id": chain["auth_asym_id"],
                            "label_asym_id": chain["label_asym_id"]},
        "wording": wording,
        "look": {k: v for k, v in look.items() if v},
        "variants": [{
            "name_in_prompt": n, "variant": V.short(s.v), "hgvs": V.hgvs(s.v),
            "uniprot_position": s.v.position,
            "mature_numbering": m if naming == "legacy" else None,
            "clinvar_vcv": list(s.v.vcv), "clinvar_classification": list(s.v.classification),
            "clinvar_review_status": list(s.v.review_status),
            "residues": [x for x in s.residues
                         if chain is None or x["label_asym_id"] == chain["label_asym_id"]],
        } for s, n, m in zip(group, variant_names(naming, group)[0], mature)],
        "secondary_structure": sse,
        "difficulty": difficulty,
        "pair": None,
    }
    stem = "-".join([family, protein["gene"].lower(), entry.split("-model")[0],
                     *[V.short(s.v).lower() for s in group]]
                    + ([f"chain{chain['auth_asym_id'].lower()}"] if chain else []))
    inputs = [f"data/panel/variants/{acc}.json", f"data/panel/facts/{entry}.json",
              f"molbench/sifts_tables/{entry}.json.gz", f"molbench/atom_tables/{entry}.json.gz"]
    if naming == "legacy":
        inputs.append(str(V.PROCESSING.relative_to(REPO)))
    skills = ["load", "selection", "clinical-variant", "representation", "color"]
    if context != "none":
        skills.append("context")

    def task(track: str, reference, accepted, rep_name: str) -> dict:
        prov = {"script": SCRIPT, "inputs": inputs, "date": DATE, "checks": list(checks),
                "clinical": json.loads(json.dumps(clinical))}
        if track == "api":
            prov["clinical"]["api_note"] = API_NOTE
            # What scripts/check_api_refs.py reads: the entry the calls load, and for
            # every selection the atoms it is meant to select, written independently
            # (label numbering from the frozen variant file and facts).
            prov["structure"] = ps.replay(json.loads(json.dumps(reference))).entry
            prov["derived"] = ("UniProt position of each variant from the frozen ClinVar-confirmed "
                               "list; structure residues from the frozen SIFTS mapping")
            prov["checked_by"] = f"{SCRIPT} (atom tables, SIFTS tables, grader) and scripts/check_api_refs.py"
            prov["targets"] = api_targets
            prov["accepted_differ"] = (
                "each alternative is another final state that the request equally describes: "
                "the residue's own stretch of cartoon in the highlight colour, and/or the "
                "cartoon style set explicitly")
        return {"id": f"{stem}-{track}", "track": track, "tier": "clinical", "family": family,
                "structures": [entry], "prompt": prompt, "reference": reference,
                "accepted": accepted, "context": None,
                "target": [{"selector": target_sel if len(target_sel) > 1 else target_sel[0],
                            "representation": rep_name, "color": look["color"]}],
                "twin_of": None, "paraphrase_of": None, "style": "full", "split": "public",
                "grounding": None, "provenance": prov, "skills": skills}

    a = task("mvs", mvs_ref, [], look["rep"])
    b = task("api", api_ref, api_accepted, api_rep)
    a["twin_of"], b["twin_of"] = b["id"], a["id"]
    return [a, b]


# --------------------------------------------------------------------------- #
# The plan: which templates on which structures
# --------------------------------------------------------------------------- #
def sse_candidates(site: Site, kind: str) -> list[dict]:
    """(chain, element) choices: the residue lies in exactly one annotated element of
    that kind in the chain (a strand listed in two sheets must have the same range),
    at least four residues long, with no insertion code and no numbering break."""
    facts = grounding.facts(site.entry)
    table = load_table(site.entry)
    out = []
    for x in site.residues:
        hits = [e for e in facts["helices" if kind == "helix" else "strands"]
                if e["label_asym_id"] == x["label_asym_id"]
                and e["beg_label_seq_id"] <= x["label_seq_id"] <= e["end_label_seq_id"]]
        ranges = {(e["beg_label_seq_id"], e["end_label_seq_id"]) for e in hits}
        if len(ranges) != 1:
            continue
        e = hits[0]
        n = e["end_label_seq_id"] - e["beg_label_seq_id"] + 1
        if n < 4 or e["end_auth_seq_id"] - e["beg_auth_seq_id"] + 1 != n:
            continue
        lab = table.selector({"label_asym_id": e["label_asym_id"],
                              "beg_label_seq_id": e["beg_label_seq_id"],
                              "end_label_seq_id": e["end_label_seq_id"]})
        auth = table.selector({"auth_asym_id": e["auth_asym_id"],
                               "beg_auth_seq_id": e["beg_auth_seq_id"],
                               "end_auth_seq_id": e["end_auth_seq_id"]})
        if not lab or lab != auth:
            continue
        chain = next(c for c in site.chains if c["label_asym_id"] == x["label_asym_id"])
        out.append((chain, {"kind": kind, **{k: e[k] for k in (
            "auth_asym_id", "beg_auth_seq_id", "end_auth_seq_id", "label_asym_id",
            "beg_label_seq_id", "end_label_seq_id")}}))
    return out


def legacy_ok(site: Site) -> bool:
    """The variant has a mature-protein number, and the structure's own author
    numbering is that numbering at this residue: the frozen structure records it."""
    m = V.mature_numbering(site.v.accession, site.v.position)
    return bool(m) and all(x["auth_seq_id"] == m["number"] and not x["pdbx_PDB_ins_code"]
                           for x in site.residues)


def plan() -> list[dict]:
    proteins = V.proteins()
    by_acc = {p["accession"]: p for p in proteins}
    pools = {(p["accession"], e): sites(p, e) for p in proteins for e in p["entries"]
             if e != T.WORKED_EXAMPLE}
    used: set = set()
    load: Counter = Counter()          # tasks per structure (per track)
    out: list[dict] = []

    def room(entry: str, n: int = 1) -> bool:
        return load[entry] + n <= MAX_PER_STRUCTURE

    def add(pair: list[dict]) -> list[dict]:
        load[pair[0]["structures"][0]] += 1
        out.extend(pair)
        return pair

    order = sorted(proteins, key=lambda p: p["accession"])
    rng("order").shuffle(order)

    # A. One variant per protein on its primary structure, cycling the four templates.
    cycle = ["clin-hgvs-target", "clin-short-context", "clin-short-target", "clin-hgvs-context",
             "clin-hgvs-target", "clin-short-target", "clin-hgvs-context", "clin-short-context",
             "clin-short-target"]
    for i, p in enumerate(order):
        family = cycle[i % len(cycle)]
        pool = pools[(p["accession"], p["entry"])]
        # A residue with an insertion code where the protein has one (one variant in the
        # panel does); a featured variant goes to the mature-numbering template where
        # there is one.
        coded = [s for s in pool if any(x["pdbx_PDB_ins_code"] for x in s.residues)]
        got = pick(coded or pool, used, ("single", p["accession"]),
                   featured=not any(legacy_ok(s) for s in pool))
        if got:
            add(build_pair(family, family.split("-")[1], got,
                           context="structure" if family.endswith("context") else "none"))

    # F. Pairs: the same variant, the same wording, on two structures of one protein.
    def pair_of(p, entries, family, naming, context, role, want=None, featured=False, k=0):
        common = [s for s in pools[(p["accession"], entries[0])]
                  if any(t.v == s.v for t in pools[(p["accession"], entries[1])])
                  and (s.entry, s.v.position) not in used
                  and (entries[1], s.v.position) not in used]
        got = pick(common, used, ("pair", p["accession"], *entries, k), featured=featured,
                   want=want)
        if not got or not all(room(e) for e in entries):
            return
        made = []
        for e in entries:
            twin_site = next(t for t in pools[(p["accession"], e)] if t.v == got[0].v)
            used.add((e, twin_site.v.position))
            made.append(add(build_pair(family, naming, [twin_site], context=context,
                                       key=("pair", k))))
        for mine, other, what in ((made[0], made[1], role[0]), (made[1], made[0], role[1])):
            for t, o in zip(mine, other):
                t["provenance"]["clinical"]["pair"] = {"with": o["id"], "this_structure": what}

    hbb, p53 = by_acc["P68871"], by_acc["P04637"]
    af_hbb, af_p53 = "af-p68871-f1-model_v6", "af-p04637-f1-model_v6"
    offs = ("author numbers differ from UniProt numbers", "author numbers are UniProt numbers")
    same = ("author numbers are UniProt numbers; three chains",
            "author numbers are UniProt numbers; one chain")
    # The mature-protein name asked on the structure numbered that way and on the
    # AlphaFold model, which is numbered as UniProt.
    n_legacy = [0, 0]

    def legacy_family() -> tuple[str, str]:
        i = 0 if n_legacy[0] <= n_legacy[1] else 1
        n_legacy[i] += 1
        return ("clin-legacy-target", "none") if i == 0 else ("clin-legacy-context", "structure")

    fam, ctx = legacy_family()
    pair_of(hbb, ("1hho", af_hbb), fam, "legacy", ctx,
            ("author numbers are the mature-protein numbers",
             "author numbers are UniProt numbers"),
            want=legacy_ok, featured=True, k=6)

    pair_of(hbb, ("2hhb", af_hbb), "clin-pair-target", "hgvs", "none", offs, featured=True, k=0)
    pair_of(hbb, ("2hhb", af_hbb), "clin-pair-context", "short", "structure", offs, k=1)
    pair_of(hbb, ("5ni1", af_hbb), "clin-pair-context", "hgvs", "structure", offs, k=2)
    pair_of(hbb, ("1hho", af_hbb), "clin-pair-target", "short", "none", offs, k=3)
    pair_of(p53, ("1tup", af_p53), "clin-pair-target", "hgvs", "none", same, featured=True, k=4)
    pair_of(p53, ("1tup", af_p53), "clin-pair-context", "short", "structure", same, k=5)
    # C. Mature-protein names, one per protein whose structure is numbered that way.
    spread = {"P68871": "5ni1", "P69905": "1hho"}     # keep 2HHB under the cap
    for p in order:
        entry = spread.get(p["accession"], p["entry"])
        if not room(entry):
            continue
        got = pick(pools[(p["accession"], entry)], used, ("legacy", p["accession"]),
                   featured=p is not hbb, want=legacy_ok)   # HBB's is in the pair above
        if got:
            fam, ctx = legacy_family()
            add(build_pair(fam, "legacy", got, context=ctx))

    # B. One named chain of a structure with several copies (author chain ids that
    # differ from the label chain ids first).
    several = sorted(order, key=lambda p: not p["auth_chain_differs_from_label_chain"])
    n = 0
    for p in several:
        entry = p["entry"]
        if n >= 8 or not room(entry):
            continue
        got = pick(pools[(p["accession"], entry)], used, ("chain", p["accession"]),
                   want=lambda s: len(s.chains) > 1)
        if not got:
            continue
        r = rng("chain", p["accession"])
        chain = r.choice(sorted(got[0].chains, key=lambda c: c["auth_asym_id"]))
        add(build_pair("clin-chain", r.choice(["hgvs", "short"]), got, context="none",
                       scope="chain", chain=chain))
        n += 1

    # D. Several variants of one protein (structures numbered differently from UniProt first).
    rich = [p for p in order if len(pools[(p["accession"], p["entry"])]) >= 8]
    rich.sort(key=lambda p: not p["offset"])
    n = 0
    for p in rich:
        if n >= 8 or not room(p["entry"]):
            continue
        r = rng("multi", p["accession"])
        got = pick(pools[(p["accession"], p["entry"])], used, ("multi", p["accession"]),
                   n=r.choice([2, 3, 3, 4]))
        if not got:
            continue
        got.sort(key=lambda s: s.v.position)
        family = "clin-multi-target" if n % 2 == 0 else "clin-multi-context"
        add(build_pair(family, "hgvs" if r.random() < 0.5 else "short", got,
                       context="structure" if family.endswith("context") else "none"))
        n += 1

    # E. The variant and the helix or strand that carries its residue.
    for kind, family in (("helix", "clin-sse-helix"), ("strand", "clin-sse-strand")):
        n = 0
        cands = sorted(order, key=lambda p: p["accession"])
        rng("sse-order", kind).shuffle(cands)
        cands.sort(key=lambda p: not p["offset"])
        for p in cands:
            entry = p["entry"]
            if n >= 5 or not room(entry):
                continue
            got = pick(pools[(p["accession"], entry)], used, ("sse", kind, p["accession"]),
                       want=lambda s: bool(sse_candidates(s, kind)))
            if not got:
                continue
            r = rng("sse", kind, p["accession"])
            chain, element = r.choice(sse_candidates(got[0], kind))
            single = len(got[0].chains) == 1
            add(build_pair(family, r.choice(["hgvs", "short"]), got, context="sse",
                           scope="all" if single else "chain", chain=None if single else chain,
                           sse=element))
            n += 1
    return out


# --------------------------------------------------------------------------- #
# Held-back split, packs, verification
# --------------------------------------------------------------------------- #
def assign_split(tasks: list[dict]) -> list[str]:
    """Hold back a seeded ~20% of the tier's structures. Candidates are structures no
    task published before this corpus uses (the panel records those) and that are not
    one side of a pair, so both sides of every pair stay in one split."""
    structures = sorted({t["structures"][0] for t in tasks})
    entries = {e["id"]: e for e in grounding.panel()["entries"]}
    paired = {t["structures"][0] for t in tasks if t["provenance"]["clinical"]["pair"]}
    cands = [s for s in structures if not entries[s]["used_by_tasks"] and s not in paired
             and s not in NEVER_HELDBACK]
    n = round(HELDBACK_SHARE * len(structures))
    offset = {s: entries[s].get("offset") for s in cands}
    r = rng("heldback")
    # Half from structures numbered differently from UniProt, half from the others.
    with_off = sorted(s for s in cands if offset[s])
    without = sorted(s for s in cands if not offset[s])
    r.shuffle(with_off)
    r.shuffle(without)
    forced = sorted(set(ALSO_HELDBACK) & set(structures))
    assert all(s in cands for s in forced), forced
    with_off = [s for s in with_off if s not in forced]
    without = [s for s in without if s not in forced]
    n -= len(forced)
    n_off = max(0, (n + 1) // 2 - sum(bool(offset[s]) for s in forced))
    held = sorted(forced + with_off[:n_off] + without[:n - n_off])
    for t in tasks:
        if t["structures"][0] in held:
            t["split"] = "heldback"
    return held


def pack_builder():
    spec = importlib.util.spec_from_file_location(
        "build_grounding_packs", REPO / "scripts" / "build_grounding_packs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def naive(task: dict, key: str) -> object:
    """The answer of someone who finds the right chains but takes the number in the
    variant's name for the structure's residue number (``key``: ``auth`` or ``label``
    numbering). Everything else is the reference."""
    c = task["provenance"]["clinical"]
    items = []
    for v in c["variants"]:
        n = int(re.search(r"\d+", v["name_in_prompt"]).group())
        for x in v["residues"]:
            items.append((x[f"{key}_asym_id"], n))
    if task["track"] == "mvs":
        sels = [{f"{key}_asym_id": ch, f"{key}_seq_id": n} for ch, n in items]
        root = json.loads(json.dumps(task["reference"]))
        comps = root["root"]["children"][0]["children"][0]["children"][0]["children"]
        comps[-1]["params"]["selector"] = sels if len(sels) > 1 else sels[0]
        return root
    chain_key, num_key = {"auth": ("auth_asym_id", "auth_seq_id"),
                          "label": ("struct_asym_id", "residue_number")}[key]
    calls = json.loads(json.dumps(task["reference"]))
    data = calls[-1]["data"]
    style = {k: v for k, v in next(d for d in data if "representation" in d).items()
             if k in ("color", "representation", "representationColor")}
    calls[-1]["data"] = [d for d in data if "representation" not in d] + [
        {chain_key: ch, num_key: n, **style} for ch, n in items]
    return calls


def verify(built: list[dict]) -> list[dict]:
    loaded = []
    for t in built:
        errors = T.validate_task(t)
        if errors:
            raise SystemExit(f"{t['id']}: " + "; ".join(errors))
        loaded.append(T._with_aliases({**t, "_path": f"{OUT[t['track']].name}/{t['id']}.json"}))
    errors, _ = T.check_corpus(loaded, grade=runner.grade_parsed, check=runner.grader_problems,
                               final=True)
    if errors:
        raise SystemExit("clinical tasks fail the corpus checks:\n  " + "\n  ".join(errors))
    for t, full in zip(built, loaded):
        c = t["provenance"]["clinical"]
        d = c["difficulty"]
        checks = t["provenance"]["checks"]
        checks.append("the reference grades as exactly right against the task (success, "
                      "F1 = 1, target score 1), and so does every accepted alternative")
        checks.append("the twin on the other track selects the same target atoms")
        # What the number in the name selects when taken at face value.
        for key in ("auth", "label"):
            res = runner.grade_parsed(full, naive(t, key))
            d[f"number_in_name_as_{'author' if key == 'auth' else 'label'}_number_is_right"] = \
                bool(res["success"])
        if not d["insertion_code"]:
            expect = (bool(d["mature_number_equals_author_number"])
                      if d["name_in_mature_numbering"] else not d["needs_numbering_offset"])
            assert d["number_in_name_as_author_number_is_right"] == expect, t["id"]
        checks.append("graded what the number in the variant's name selects when taken at face "
                      "value as the author residue number ("
                      + ("right" if d["number_in_name_as_author_number_is_right"] else "wrong")
                      + ") and as the label residue number ("
                      + ("right" if d["number_in_name_as_label_number_is_right"] else "wrong")
                      + "); recorded under clinical.difficulty")
    return built


def enforce_caps(tasks: list[dict]) -> None:
    for track in T.TRACKS:
        mine = [t for t in tasks if t["track"] == track]
        per = Counter(t["structures"][0] for t in mine)
        assert max(per.values()) <= MAX_PER_STRUCTURE, per.most_common(3)
        fam = Counter(t["family"] for t in mine)
        assert max(fam.values()) / len(mine) <= MAX_FAMILY_SHARE + 0.005, fam.most_common(3)
        assert len(mine) >= 60, len(mine)
        d = [t["provenance"]["clinical"]["difficulty"] for t in mine]
        assert sum(x["structure_has_offset"] for x in d) * 2 >= len(mine)
        assert all(T.WORKED_EXAMPLE not in json.dumps(t).lower() for t in mine)
    assert {t["family"] for t in tasks} <= set(FAMILIES)


# --------------------------------------------------------------------------- #
# README
# --------------------------------------------------------------------------- #
def readme(track: str, tasks: list[dict], held: list[str]) -> str:
    mine = [t for t in tasks if t["track"] == track]
    d = [t["provenance"]["clinical"]["difficulty"] for t in mine]
    c = [t["provenance"]["clinical"] for t in mine]
    n = len(mine)
    fam = Counter(t["family"] for t in mine)
    per = Counter(t["structures"][0] for t in mine)
    genes = sorted({x["gene"] for x in c})
    other = "api_clinical" if track == "mvs" else "mvs_clinical"
    name = "MVS" if track == "mvs" else "API (pdbe-molstar 3.3.2 calls)"
    L = [f"# Clinical-variant tier, {name} track",
         "",
         f"Generated by `{SCRIPT}`; do not edit by hand. {n} tasks on {len(per)} structures "
         f"of {len(genes)} disease proteins. Every task has a twin with the same prompt and the "
         f"same target atoms in `tasks/{other}/` (`twin_of`).",
         "",
         "Each task names a structure and one or more missense variants that ClinVar itself "
         "classifies as pathogenic or likely pathogenic (the frozen, ClinVar-confirmed lists "
         "in `data/panel/variants/`), and asks for the residue each variant replaces to be "
         "shown. The structure holds the wild-type residue; the task is to find it. The "
         "prompt names the structure and the variant, never which residue of the structure it is.",
         ""]
    if track == "api":
        L += [API_NOTE + " Half of the prompts give the UniProt accession and half give only "
              "the gene and protein name (`provenance.clinical.difficulty.accession_in_prompt`), "
              "so the second half also needs the accession from memory.", ""]
    L += ["## Templates", "", "| family | tasks | share | what is asked |", "|---|---:|---:|---|"]
    for f in FAMILIES:
        if fam[f]:
            L.append(f"| `{f}` | {fam[f]} | {100 * fam[f] / n:.0f}% | {FAMILIES[f]} |")
    L += ["",
          "Each template has three wordings; the wording, the colours, the representation "
          "(ball-and-stick or spacefill) and whether the accession is given are drawn from a "
          f"seeded generator (seed `{SEED}`), so a re-run reproduces every file byte for byte.",
          "",
          "## Counts", "",
          "| | tasks |", "|---|---:|",
          f"| all | {n} |",
          f"| only the residue requested (`context: none`) | {sum(x['context'] == 'none' for x in c)} |",
          f"| context requested: cartoon of the whole structure | {sum(x['context'] == 'structure' for x in c)} |",
          f"| context requested: the helix or strand | {sum(x['context'] == 'sse' for x in c)} |",
          f"| structure numbered differently from UniProt somewhere | {sum(x['structure_has_offset'] for x in d)} |",
          f"| target residue's author number differs from its UniProt number | {sum(x['needs_numbering_offset'] for x in d)} |",
          f"| target's author chain id differs from its label chain id | {sum(x['author_chain_differs_from_label_chain'] for x in d)} |",
          f"| target's author number differs from its label number | {sum(x['author_number_differs_from_label_number'] for x in d)} |",
          f"| target residue has an insertion code | {sum(x['insertion_code'] for x in d)} |",
          f"| the number in the name, used as the author residue number, is the right residue | {sum(x['number_in_name_as_author_number_is_right'] for x in d)} |",
          f"| the number in the name, used as the label residue number, is the right residue | {sum(x['number_in_name_as_label_number_is_right'] for x in d)} |",
          f"| the number in the name, used as the author residue number, is a different residue of the same amino acid | {sum(x['number_in_name_as_author_number_is_same_amino_acid'] for x in d)} |",
          f"| the name, read as a mature-protein number, lands on the same amino acid (HGVS names only) | {sum(x['name_read_as_mature_number_is_same_amino_acid'] is True for x in d)} |",
          f"| name in mature-protein numbering | {sum(x['name_in_mature_numbering'] for x in d)} |",
          f"| UniProt accession given in the prompt | {sum(x['accession_in_prompt'] for x in d)} |",
          f"| on an AlphaFold DB model | {sum(x['alphafold_model'] for x in d)} |",
          f"| in a pair (same variant on two structures) | {sum(bool(x['pair']) for x in c)} |",
          f"| split: public / held back | {sum(t['split'] == 'public' for t in mine)} / {sum(t['split'] == 'heldback' for t in mine)} |",
          "",
          f"Held-back structures ({len(held)}): {', '.join(s.upper() for s in held)}. They are "
          "in no public task of this tier. They were drawn (seeded) from the structures that "
          "no task published before this corpus uses, half from those numbered differently "
          "from UniProt.",
          "",
          "Proteins: " + ", ".join(genes) + ".",
          "",
          "| structure | tasks | split |", "|---|---:|---|"]
    for s in sorted(per):
        L.append(f"| {s} | {per[s]} | {'held back' if s in held else 'public'} |")
    L += ["",
          "## How each reference is derived", "",
          "| part of the reference | derived from | checked by |", "|---|---|---|",
          "| which variants | `data/panel/variants/<ACC>.json`: missense variants whose ClinVar "
          "variant record has the aggregate germline classification Pathogenic, Likely pathogenic "
          "or Pathogenic/Likely pathogenic. A short list of well-known variants (`FEATURED` in "
          "the script) is preferred when the frozen data confirms them; otherwise a seeded draw, "
          "strongly reviewed records first | the prompt's classification words are the frozen "
          "classification (`molbench.variants.classification_words`) |",
          "| the target residue(s) | the variant's `structures.<entry>` residues in the same "
          "file (SIFTS mapping; listed only where the structure has the wild-type amino acid), "
          "in every copy of the protein or in the one named chain. Only variants modelled in "
          "every copy are used | the atom set is the same by label numbering, by author "
          "numbering and by `molbench.sifts.uniprot_atoms`; the residue name is the wild type |",
          "| mature-protein name (legacy templates) | UniProt's processing features, frozen in "
          "`data/clinical/uniprot_processing.json`: number = UniProt position minus the residues "
          "before the single mature chain. Used only where the structure's author number of the "
          "residue is that number, or on the AlphaFold model paired with such a structure | "
          "`molbench.variants.mature_numbering` refuses proteins with several products or "
          "inexact features |",
          "| helix or strand (sse templates) | `helices` / `strands` of `data/panel/facts/"
          "<entry>.json` (the entry's own annotation); the element must be the only one holding "
          "the residue, at least four residues, with no numbering break | same atoms by author "
          "and by label range; contains the target |",
          "| representation, colours, wording | seeded draw from fixed lists | colours are in "
          "the task palette |",
          ]
    if track == "mvs":
        L += ["| scene | one component per requested thing and nothing else: the residue(s) in "
              "author numbering; with requested context also `all` as a cartoon, or the helix / "
              "strand range as a cartoon | grades itself: success, F1 = 1, target score 1 |"]
    else:
        L += ["| call list | `load`, then one `color` call: each variant as "
              "`uniprot_accession` + `uniprot_residue_number` (with `auth_asym_id` when one "
              "chain is named) with `representation` and `representationColor`; with a "
              "whole-structure cartoon also `non_selected_color`; with a helix or strand also "
              "its author range | grades itself: success, F1 = 1, target score 1 |",
              "| accepted alternatives | the residue's own stretch of cartoon may also take the "
              "highlight colour (`color` on the item; the reference leaves it as its "
              "surroundings); with a whole-structure cartoon, `set_visual_style: cartoon` may be "
              "set first. Nothing else is accepted | each grades as itself and is accepted by "
              "the task |"]
    L += ["",
          "Every task also carries a grounding pack (`grounding`, rule `clinical-v1`, built by "
          "`scripts/build_grounding_packs.py`): the entry's chains and numbering runs, the SIFTS "
          "mapping, and the structure residues at each variant's UniProt position.",
          "",
          "## What is recorded for analysis", "",
          "`provenance.clinical` holds the gene, accession, the variant(s) with their ClinVar "
          "records, the residues, the template choices, a `pair` link, and `difficulty`: "
          "whether the residue's author number differs from the UniProt number "
          "(`needs_numbering_offset`, `author_minus_uniprot`), whether author and label chain "
          "ids or numbers differ, insertion codes, whether the accession is in the prompt, the "
          "number of copies, and two graded facts: whether an answer that uses the number in "
          "the variant's name as the author residue number, or as the label residue number, "
          "is right. `number_in_name_as_author_number_is_same_amino_acid` marks the tasks "
          "where that face-value residue is a different residue of the same amino acid, so "
          "checking the wild type does not expose the mistake; this happens only under an "
          "HGVS name, never under a bare one-letter name (the generator refuses it). "
          "`name_read_as_mature_number_is_same_amino_acid` is the same question for the other "
          "misreading: a name in UniProt numbering taken for a mature-protein number (true, "
          "false, or null when the frozen data does not show that residue). A bare one-letter "
          "name is used only where it is false; otherwise the variant is asked by its HGVS "
          "name. The two tasks of a pair share the wording, the colours, the representation "
          "and the accession in the prompt, so only the structure differs.",
          "",
          "## Left out, and why", "",
          "- **A variant whose position is not modelled in the structure.** The right answer "
          "would be a scene that shows nothing, or a refusal; neither is a final viewer state "
          "the grader can score as right, so no such task is built. Variants are used only "
          "where every copy of the protein has the wild-type residue modelled.",
          "- **The residues contacting a bound ligand.** The frozen facts hold no contact "
          "lists, so this cannot be derived without a new, verified computation.",
          "- **\"Hotspot\" requests.** Dropped: the word has no computed definition a prompt "
          "could state briefly.",
          ""]
    return "\n".join(L)


# --------------------------------------------------------------------------- #
def build() -> tuple[dict[pathlib.Path, str], list[dict], list[str]]:
    if not V.processing():
        raise SystemExit(f"{V.PROCESSING.relative_to(REPO)} is missing: run with "
                         "--refresh-processing once (network)")
    tasks = plan()
    held = assign_split(tasks)
    packs = pack_builder()
    for t in tasks:
        t["grounding"] = packs.clinical_pack(t)
    tasks = verify(tasks)
    enforce_caps(tasks)
    files = {OUT[t["track"]] / f"{t['id']}.json": json.dumps(t, indent=1) + "\n" for t in tasks}
    assert len(files) == len(tasks), "task ids are not unique"
    for track in T.TRACKS:
        files[OUT[track] / "README.md"] = readme(track, tasks, held)
    return files, tasks, held


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if the files would change")
    ap.add_argument("--refresh-processing", action="store_true",
                    help="download and freeze UniProt's processing features (network)")
    a = ap.parse_args(argv)
    if a.refresh_processing:
        refresh_processing()
        return 0
    files, tasks, held = build()
    existing = {p for d in OUT.values() for p in d.glob("*") if p.is_file()}
    stale = sorted(existing - set(files))
    changed = [p for p, text in files.items()
               if not p.exists() or p.read_text(encoding="utf-8") != text]
    if a.check:
        if changed or stale:
            print("clinical tasks are out of date:", *[p.name for p in (changed + stale)[:10]])
            return 1
        print(f"{len(tasks)} clinical tasks are up to date")
        return 0
    for d in OUT.values():
        d.mkdir(parents=True, exist_ok=True)
    for p in stale:
        p.unlink()
    for p, text in files.items():
        p.write_text(text, encoding="utf-8")
    n = len(tasks) // 2
    print(f"wrote {n} MVS + {n} API clinical tasks ({len(changed)} files changed, "
          f"{len(stale)} removed); held back: {', '.join(held)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
