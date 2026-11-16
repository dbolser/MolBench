#!/usr/bin/env python3
"""
Write paraphrases of existing tasks (FINAL_PLAN decision 20): the same request in
three phrasings - the original full sentence, a terse command the way people really
type into the chat box ("1tup chain A red", "hide water"), and an indirect, polite
one. Same reference, same accepted alternatives, same target; only the prompt, the
``style`` and ``paraphrase_of`` differ, so any change in score is due to the wording.

    uv run python scripts/generate_paraphrases.py ID [ID ...]        # these tasks
    uv run python scripts/generate_paraphrases.py --select-seeded 30 # a seeded, stratified 30
    uv run python scripts/generate_paraphrases.py                    # rebuild the recorded selection
    uv run python scripts/generate_paraphrases.py --check            # fail if files would change
    uv run python scripts/generate_paraphrases.py --list-families    # what can be paraphrased

Each source task gets two new files in ``tasks/paraphrases/`` (``<id>.terse.json``,
``<id>.indirect.json``); with the original that makes three phrasings. A task with a
twin on the other track is one *request*: both twins are paraphrased with the same
words, and the paraphrases are twins of each other (TASK_FORMAT.md). The selection is
recorded in ``tasks/paraphrases/SELECTION.txt`` so a bare re-run reproduces the
directory byte for byte. No network; nothing here calls a model.

Where the words come from. Every phrasing is written by hand, once per request, in
``WORDINGS`` below, because it has to read as natural English: the terse form the way
people really type into a chat box (lower-case id first, no verbs or articles,
comma-separated; modelled on the anonymised real-user request categories in LEDGER.md:
U1 colour by chain, U6 terse range specs, U13 hide/show, U14 representation names), the
indirect form as a colleague would ask. (An earlier version rewrote the prompt
mechanically; its output was clumsy and is gone.)

A paraphrase must still determine the reference, and that is checked by rule
(``lost``): every token of the original with a digit (ids, residue names, numbers,
variant names), every code in capitals, every chain letter, every quoted text, every
colour word and every representation word must be in the wording. A request that is
selected and has no wording, or whose wording drops something, stops the script.

Accept-set tasks are never paraphrased (``NEVER``): such a request is open on purpose,
and a rewording could close or widen what it leaves open.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import pathlib
import re
import sys
from collections import Counter

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import runner, tasks as T  # noqa: E402

SCRIPT = "scripts/generate_paraphrases.py"
SEED = "molbench-paraphrases-v1"
DATE = "2026-11-13"                      # fixed, so a rebuild is byte-identical
OUT = REPO / "tasks" / "paraphrases"
SELECTION = "SELECTION.txt"
STYLES = ("terse", "indirect")
API_CHECK_KEYS = ("structure", "derived", "checked_by", "accepted_differ", "targets")

# --------------------------------------------------------------------------- #
# The wordings. One entry per paraphrased request, keyed by the id of its first task
# (a twin gets the same words). Written by hand, because a phrasing has to read as
# natural English (ruling of 2026-11-15; the mechanical rewrite this replaced gave
# "Find PDB entry human SERPINA1, it brown cartoon"), and checked by rule: `lost`.
# --------------------------------------------------------------------------- #
WORDINGS: dict[str, dict[str, str]] = {
    'api-010': {
        "terse": '1ubq cartoon, glossy lighting, black background, no waters, slow spin',
        "indirect": "I'd like a slowly spinning view of ubiquitin (1UBQ) for a talk: a cartoon with glossy lighting on a black background and without the waters, if you could."},
    'api-alphafold-af-p07320-f1': {
        "terse": "AlphaFold DB model of gamma-crystallin D (P07320), pLDDT colouring, tooltip 'residues 117-133' on residues 117 to 133",
        "indirect": "Could you bring up the AlphaFold DB model of Gamma-crystallin D (P07320), coloured by confidence (pLDDT)? I'd also like residues 117 to 133 to show the tooltip 'residues 117-133' when I hover over them."},
    'api-assembly-7a4m': {
        "terse": '7a4m assembly 1 (the 24-mer), residues 75 to 79 orange',
        "indirect": "I'd like to look at the whole 24-mer of 7A4M, that is, biological assembly 1. Could you load it and make residues 75 to 79 orange?"},
    'api-atoms-1hvr': {
        "terse": '1hvr: atoms N2 and O1 of XK2 purple, rest of the ligand unchanged',
        "indirect": 'Could you pick out two atoms of the ligand XK2 in 1HVR for me? Just N2 and O1, in purple, please; leave the other atoms of the ligand as they are.'},
    'api-domain-overlay-5cj6': {
        "terse": '5cj6, sequence panel on, domain annotations on',
        "indirect": 'When you open 5CJ6, could you keep the sequence panel visible and turn on the domain annotations as well?'},
    'api-highlight-7a4m': {
        "terse": '7a4m: highlight Ser31 and Asn125, highlight colour steel blue, centre the view on them',
        "indirect": "I'd like to find Ser31 and Asn125 in 7A4M. Could you highlight the two residues, with steel blue as the highlight colour, and centre the view on them?"},
    'clin-chain-hbb-2hhb-v68m-chainb-api': {
        "terse": '2hhb, HBB p.Val68Met (pathogenic, ClinVar): the residue it replaces as red spacefill spheres, chain B only',
        "indirect": "I'm looking at the pathogenic HBB (hemoglobin subunit beta) variant p.Val68Met from ClinVar. Could you show me, in PDB entry 2HHB, the residue it replaces as red spacefill spheres, but only in chain B?"},
    'clin-hgvs-context-serpina1-8pi2-m409t-api': {
        "terse": '8pi2 white cartoon; SERPINA1 (alpha-1-antitrypsin) p.Met409Thr, pathogenic/likely pathogenic in ClinVar: the residue it replaces as orange ball-and-stick',
        "indirect": "ClinVar lists the SERPINA1 (Alpha-1-antitrypsin) variant p.Met409Thr as pathogenic/likely pathogenic, and I'd like to see where it sits. Could you show PDB entry 8PI2 as a white cartoon of the whole structure and draw the residue the variant replaces as orange ball-and-stick?"},
    'clin-hgvs-target-ar-5cj6-l702f-api': {
        "terse": '5cj6, AR (androgen receptor) p.Leu702Phe, likely pathogenic in ClinVar: the residue it replaces as purple ball-and-stick',
        "indirect": "ClinVar lists the AR (Androgen receptor) variant p.Leu702Phe as likely pathogenic. Could you show me, in PDB entry 5CJ6, the residue that this variant replaces, drawn as purple ball-and-stick?"},
    'clin-hgvs-target-f9-8eph-i344t-api': {
        "terse": '8eph, F9 (coagulation factor IX, UniProt P00740) p.Ile344Thr, pathogenic in ClinVar: the residue it replaces as blue spacefill spheres, in every chain that has it',
        "indirect": "Could you help me locate a pathogenic ClinVar variant of F9 (Coagulation factor IX, UniProt P00740), p.Ile344Thr, in PDB entry 8EPH? I'd like the residue it replaces drawn as blue spacefill spheres in every chain that has it."},
    'clin-legacy-context-f9-8eph-p101a-api': {
        "terse": '8eph grey cartoon; F9 (coagulation factor IX) P55A, pathogenic in ClinVar: the wild-type residue at that position as orange ball-and-stick, in every chain that has it. P55A is in mature-protein numbering (counted after the 46-residue signal peptide and propeptide)',
        "indirect": "I'm reading about the F9 (Coagulation factor IX) missense variant P55A, which ClinVar calls pathogenic. Could you take PDB entry 8EPH, draw the whole structure as a grey cartoon, and show the wild-type residue at the variant's position as orange ball-and-stick in every chain that has it? Note that P55A is a mature-protein name: residues are counted from the first residue of the mature protein, that is, after the 46-residue signal peptide and propeptide."},
    'clin-legacy-target-hbb-af-p68871-f1-e7v-api': {
        "terse": 'AlphaFold DB model AF-P68871-F1 (version 6); HBB (hemoglobin subunit beta, UniProt P68871) E6V, pathogenic in ClinVar: the wild-type residue at that position as purple spacefill spheres. E6V is in mature-protein numbering (counted after the initiator methionine)',
        "indirect": "I'd like to see where the HBB (Hemoglobin subunit beta, UniProt P68871) missense variant E6V, pathogenic in ClinVar, falls on the AlphaFold DB model AF-P68871-F1 (model version 6). Could you show the wild-type residue at that position as purple spacefill spheres? Bear in mind that E6V is in mature-protein numbering: residues are counted from the first residue of the mature protein, that is, after the initiator methionine."},
    'fu-add-chain-3ave-mvs': {
        "terse": 'chain B too, grey cartoon',
        "indirect": 'Could I see chain B as well? A grey cartoon would be fine.'},
    'fu-add-label-3ptb-mvs': {
        "terse": 'label on the benzamidine (BEN): "ligand"',
        "indirect": 'It would help to have the benzamidine (BEN) marked. Could you put a label on it that says "ligand"?'},
    'fu-add-ligand-1mbn-mvs': {
        "terse": 'add ligand HEM, plum ball-and-stick',
        "indirect": "I'd like to see the ligand HEM as well now. Could you add it in plum ball-and-stick?"},
    'fu-api-stop-spin-1atp-api': {
        "terse": 'spin off',
        "indirect": 'The rotation is making it hard to look at. Could you stop it spinning, please?'},
    'fu-api-style-8eph-api': {
        "terse": 'cartoon-only style (no ligands, no waters), keep the two chain colours',
        "indirect": 'Could you switch to the cartoon-only style, so that the ligands and waters are gone, while keeping the same colours on the two chains?'},
    'gr-all-but-chain-4ins': {
        "terse": '4ins green cartoon, every chain except chain C',
        "indirect": "I'd like to see 4INS as a green cartoon, but chain C is in the way. Could you leave that chain out and show all the others?"},
    'gr-attachment-1c3w-ret': {
        "terse": '1c3w grey cartoon, retinal steel blue ball-and-stick, the lysine covalently bound to it lime green ball-and-stick',
        "indirect": "I'm interested in how the retinal is attached in 1C3W. Could you show the structure as a grey cartoon, the retinal as steel blue ball-and-stick, and the lysine it is covalently bound to as lime green ball-and-stick?"},
    'gr-catalytic-1aki-p00698': {
        "terse": '1aki grey cartoon + its two catalytic residues, green ball-and-stick',
        "indirect": 'Could you show me where the active site of 1AKI is? A grey cartoon with its two catalytic residues as green ball-and-stick would do nicely.'},
    'gr-disulfides-9fb2': {
        "terse": '9fb2 protein grey cartoon, disulfide-bonded cysteines teal ball-and-stick',
        "indirect": "I'd like to see where the disulfide bonds of 9FB2 are. Could you draw the protein as a grey cartoon and every cysteine that is in a disulfide bond as teal ball-and-stick?"},
    'in-ca-distance-9fb2': {
        "terse": '9fb2 hot pink cartoon, labelled dashed line for the C-alpha to C-alpha distance from Pro189 to Phe436',
        "indirect": 'Could you tell me how far apart Pro189 and Phe436 are in 9FB2? Please show the structure as a hot pink cartoon and draw the distance between their C-alpha atoms as a labelled dashed line.'},
    'in-computed-3ptb-ben': {
        "terse": "3ptb grey cartoon, benzamidine steel blue ball-and-stick, viewer's non-covalent interactions on for the benzamidine (hydrogen bonds and other contacts), zoom on the benzamidine",
        "indirect": "I'd like to see how the benzamidine is held in 3PTB. Could you draw the structure as a grey cartoon and the benzamidine as steel blue ball-and-stick, switch on the viewer's display of non-covalent interactions for the benzamidine (hydrogen bonds and other contacts with its surroundings), and zoom in on it?"},
    'in-disulfide-1trn': {
        "terse": '1trn grey cartoon; disulfide Cys136-Cys201 in chain B: both cysteines hot pink ball-and-stick, dashed line SG to SG labelled with its length, zoom in on the bridge',
        "indirect": "Could you show me the disulfide between Cys136 and Cys201 of chain B in 1TRN? I'd like the structure as a grey cartoon, the two cysteines as hot pink ball-and-stick, the sulfur-sulfur distance (SG to SG) drawn as a dashed line labelled with its length, and the view zoomed in on the bridge."},
    'in-hbond-1a3k': {
        "terse": '1a3k grey cartoon, Asn174 + Arg224 magenta ball-and-stick, labelled dashed line from OD1 of Asn174 to NH1 of Arg224 (hydrogen bond), camera on the two residues',
        "indirect": "I'd like to check the hydrogen bond between Asn174 and Arg224 in 1A3K. Could you show the structure as a grey cartoon and the two residues as magenta ball-and-stick, measure the bond from OD1 of Asn174 to NH1 of Arg224 with a labelled dashed line, and focus the camera on the two residues?"},
    'res-complex-p69905-p68871': {
        "terse": 'human hemoglobin, alpha and beta chains together, plum cartoon',
        "indirect": "I'd like to look at human hemoglobin with its alpha and beta chains together. Could you find a structure and show it as a plum cartoon?"},
    'res-dna-p08046': {
        "terse": 'mouse Zif268 bound to DNA, any PDB structure of the complex: protein red cartoon, DNA magenta cartoon',
        "indirect": "Could you find me a PDB structure of the mouse transcription factor Zif268 bound to DNA? Any entry of the complex is fine. I'd like the protein as a red cartoon and the DNA as a magenta cartoon."},
    'res-gene-p01009': {
        "terse": 'human SERPINA1, any PDB entry, brown cartoon',
        "indirect": "I'd like to see what human SERPINA1 looks like. Could you pick a PDB entry of it and show it as a brown cartoon?"},
    'res-ligand-p29373-rea': {
        "terse": 'human cellular retinoic acid-binding protein 2 (CRABP-II) with retinoic acid bound, any PDB entry: protein teal cartoon, retinoic acid khaki ball-and-stick',
        "indirect": "I'm interested in how retinoic acid binds to human cellular retinoic acid-binding protein 2 (CRABP-II). Could you find a PDB entry of the complex and draw the protein as a teal cartoon and the retinoic acid as khaki ball-and-stick?"},
    'tr-cartoon-9f69': {
        "terse": '9f69 whole protein, hot pink cartoon',
        "indirect": 'Could you open PDB entry 9F69 for me and show the whole protein as a hot pink cartoon?'},
    'tr-chain-colour-1trn': {
        "terse": '1trn cartoon, chain B orange, the rest grey',
        "indirect": "I'd like chain B to stand out in 1TRN. Could you show the structure as a cartoon with chain B in orange and everything else in grey?"},
}

#: Tiers that are never paraphrased. An accept-set request is open on purpose, and a
#: rewording could close or widen what it leaves open (ruling of 2026-11-15).
NEVER = ("accept_set",)

COLOUR_WORDS = ("red", "orange", "yellow", "green", "blue", "purple", "magenta", "cyan", "teal",
                "salmon", "plum", "brown", "khaki", "white", "black", "grey", "pink", "lime", "steel")
SHAPE_WORDS = {"cartoon": ("cartoon",), "ball-and-stick": ("ball-and-stick",),
               "spacefill": ("spacefill", "space-filling", "spheres", "sphere"),
               "space-filling": ("spacefill", "space-filling", "spheres"),
               "spheres": ("spheres", "spacefill", "sphere"), "sphere": ("sphere", "spheres", "spacefill"),
               "surface": ("surface",), "putty": ("putty",), "wireframe": ("wireframe",),
               "backbone": ("backbone",), "label": ("label",), "tooltip": ("tooltip",),
               "tooltips": ("tooltip",), "transparent": ("transparent", "transparency", "opacity", "see-through"),
               "opacity": ("opacity", "transparent")}
NOT_VALUES = ("PDB", "DB")            # capitals that name no value ("PDB entry", "AlphaFold DB")
_TOKEN = re.compile(r"[A-Za-z0-9]+(?:[.'][A-Za-z0-9]+)*")
_QUOTED = re.compile(r"""(?:"([^"]+)"|'([^']+)')""")


def lost(original: str, wording: str) -> list[str]:
    """What a rewording drops that the request needs. Everything of the original that
    carries a value must be in the wording: every token with a digit (ids, residues,
    numbers, variant names; a range "14-23" as its two numbers), every code in capitals
    (HEM, DNA), every single capital letter (a chain id), every quoted text, every
    colour word and every representation word. Compared ignoring case, except chain
    letters and codes; grey and gray are one word."""
    def norm(text: str) -> str:
        return text.replace("gray", "grey").replace("Gray", "Grey")
    original, wording = norm(original), norm(wording)
    have = _TOKEN.findall(wording)
    have_low = {t.lower() for t in have}
    out = []
    for q in _QUOTED.findall(original):
        text = q[0] or q[1]
        if text not in wording:
            out.append(f'"{text}"')
    tokens = _TOKEN.findall(original)
    for n, t in enumerate(tokens):
        low = t.lower()
        if any(ch.isdigit() for ch in t):
            if low not in have_low:
                out.append(t)
        elif len(t) > 1 and t.isupper() and t not in NOT_VALUES:
            if t not in have:
                out.append(t)
        elif len(t) == 1 and t.isupper() and t != "I" and not (t == "A" and (n == 0 or tokens[n - 1].endswith("."))):
            if t not in have:
                out.append(f"chain {t}")
        elif low in COLOUR_WORDS:
            if low not in have_low:
                out.append(t)
    for word, same in SHAPE_WORDS.items():
        if re.search(rf"(?<![A-Za-z-]){re.escape(word)}(?![A-Za-z])", original.lower()) \
                and not any(x in wording.lower() for x in same):
            out.append(word)
    return sorted(set(out))


# --------------------------------------------------------------------------- #
# Corpus
# --------------------------------------------------------------------------- #
def rank(*key) -> str:
    return hashlib.sha256("|".join([SEED, *map(str, key)]).encode()).hexdigest()


def load_sources(tasks_dir: pathlib.Path, out: pathlib.Path) -> dict[str, dict]:
    """Every new-format original under ``tasks_dir`` (not the paraphrases this script
    writes, not old-format files), by id, with its repository path in ``_file``."""
    sources = {}
    for path in sorted(tasks_dir.rglob("*.json")):
        if out in path.parents:
            continue
        task = T.load_task(path)
        if task is None or task.get("_legacy") or task["paraphrase_of"] is not None:
            continue
        try:
            task["_file"] = str(path.resolve().relative_to(REPO))
        except ValueError:
            task["_file"] = str(path)
        sources[task["id"]] = task
    return sources


def request_of(task: dict) -> tuple[str, ...]:
    """The ids of one request: a task and, if it has one, its twin; sorted."""
    return tuple(sorted(filter(None, [task["id"], task["twin_of"]])))


def phrasings(task: dict, key: str, generic: bool = False) -> tuple[dict[str, str] | None, str]:
    """``({"terse": ..., "indirect": ...}, method)`` for a task, or ``(None, why not)``.
    ``key`` is the request's first id: the entry of `WORDINGS` (twins get the same words)."""
    if task["tier"] in NEVER:
        return None, f"a task of the {task['tier']} tier is never paraphrased"
    words = WORDINGS.get(key)
    if words is None:
        return None, f"no wording written for this request yet (WORDINGS[{key!r}])"
    for style in STYLES:
        gone = lost(task["prompt"], words[style])
        if gone:
            return None, f"the {style} wording drops {gone}"
        if words[style].strip() == task["prompt"].strip():
            return None, f"the {style} wording is the original prompt"
    return ({s: words[s] for s in STYLES},
            "written wording (scripts/generate_paraphrases.py WORDINGS), checked by rule: every "
            "id, number, code, chain letter, quoted text, colour and representation word of the "
            "original is in it")


def select_seeded(sources: dict[str, dict], n: int, generic: bool,
                  tiers: list[str] | None, public_only: bool = False) -> list[str]:
    """``n`` requests, spread over tiers and then families: round-robin over the tiers,
    inside a tier round-robin over its families (those with an MVS task and the API-only
    ones in turn), inside a family by seed. Only requests
    outside the tiers in ``NEVER`` are eligible; with ``public_only``, only requests of
    the public split. Returns one id per request (its first)."""
    by_tier: dict[str, dict[str, list[tuple[str, ...]]]] = {}
    seen = set()
    for task in sources.values():
        req = request_of(task)
        if req in seen or (tiers and task["tier"] not in tiers):
            continue
        if public_only and task["split"] != "public":
            continue
        seen.add(req)
        if any(i not in sources or sources[i]["tier"] in NEVER for i in req):
            continue
        by_tier.setdefault(task["tier"], {}).setdefault(task["family"], []).append(req)
    queues = []
    for tier in sorted(by_tier):
        fams = by_tier[tier]
        for reqs in fams.values():
            reqs.sort(key=lambda r: rank("select", r[0]))
        # Families whose requests include an MVS task, and API-only families, taken in
        # turn, so that a tier with both kinds is paraphrased on both tracks.
        with_mvs = [f for f in sorted(fams)
                    if any(sources[i]["track"] == "mvs" for i in fams[f][0])]
        api_only = [f for f in sorted(fams) if f not in with_mvs]
        names = [f for pair in itertools.zip_longest(with_mvs, api_only) for f in pair if f]
        order = []
        for depth in range(max(map(len, fams.values()))):
            order += [fams[f][depth] for f in names if depth < len(fams[f])]
        queues.append(order)
    chosen: list[str] = []
    depth = 0
    while len(chosen) < n and any(depth < len(q) for q in queues):
        for q in queues:
            if depth < len(q) and len(chosen) < n:
                chosen.append(q[depth][0])
        depth += 1
    return sorted(chosen)


def paraphrase(task: dict, style: str, prompt: str, method: str, twin: str | None) -> dict:
    src = T.public_form(task)
    src.pop("_file", None)
    out = {**src, "id": f"{task['id']}.{style}", "prompt": prompt, "twin_of": twin,
           "paraphrase_of": task["id"], "style": style,
           "provenance": {
               "script": SCRIPT,
               "inputs": [task["_file"]],
               "date": DATE,
               "checks": ["(filled in below, once passed)"],
               "seed": SEED,
               "method": method,
               "original_prompt": task["prompt"],
               "source": src["provenance"],
               # An API original's own check record (scripts/check_api_refs.py reads it at
               # the top level): the reference is the same, so the record is too.
               **{k: src["provenance"][k] for k in API_CHECK_KEYS if k in src["provenance"]},
           }}
    return out


def build(sources: dict[str, dict], ids: list[str], generic: bool) -> tuple[list[dict], list[str]]:
    built, skipped, done = [], [], set()
    for tid in ids:
        if tid not in sources:
            skipped.append(f"{tid}: not an original new-format task under tasks/")
            continue
        req = request_of(sources[tid])
        if req in done:
            continue
        done.add(req)
        missing = [i for i in req if i not in sources]
        if missing:
            skipped.append(f"{tid}: its twin {missing} is not in the corpus")
            continue
        words = {i: phrasings(sources[i], req[0], generic) for i in req}
        bad = [f"{i}: {why}" for i, (w, why) in words.items() if w is None]
        if bad:
            skipped += bad
            continue
        if len({json.dumps(w, sort_keys=True) for w, _ in words.values()}) != 1:
            skipped.append(f"{tid}: its twins would get different words")
            continue
        for style in STYLES:
            for i in req:
                other = [j for j in req if j != i]
                w, method = words[i]
                built.append(paraphrase(sources[i], style, w[style], method,
                                        f"{other[0]}.{style}" if other else None))
    return built, skipped


def verify(built: list[dict], sources: dict[str, dict]) -> None:
    """Schema, links and grading of the paraphrases together with their originals."""
    loaded = []
    for t in built:
        errors = T.validate_task(t)
        if errors:
            raise SystemExit(f"{t['id']}: " + "; ".join(errors))
        loaded.append(T._with_aliases({**t, "_path": f"paraphrases/{t['id']}.json"}))
    needed = {t["paraphrase_of"] for t in built}
    originals = [sources[i] for i in sorted(needed)]
    errors, _ = T.check_corpus(originals + loaded, grade=runner.grade_parsed,
                               check=runner.grader_problems)
    if errors:
        raise SystemExit("paraphrases fail the corpus checks:\n  " + "\n  ".join(errors))
    prompts: dict[tuple, str] = {}
    for t in built:
        src = sources[t["paraphrase_of"]]
        key = (src["track"], t["prompt"])
        if key in prompts and prompts[key] != t["paraphrase_of"]:
            raise SystemExit(f"{t['id']}: the same words as a paraphrase of {prompts[key]}")
        prompts[key] = t["paraphrase_of"]
        t["provenance"]["checks"] = [
            "same reference, accepted alternatives, target, structures, split, tier and "
            "family as the original (molbench.tasks.check_corpus)",
            "the reference grades as exactly right against the paraphrase (runner.grade_parsed)",
            "every id, number, code, chain letter, quoted text, colour and representation word "
            "of the original is in the wording (scripts/generate_paraphrases.py, lost)",
        ]
        if t["twin_of"]:
            checks = t["provenance"]["checks"]
            checks.append("its twin on the other track has the same words and the same style")


def cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def readme(built: list[dict], skipped: list[str], command: str) -> str:
    originals = sorted({t["paraphrase_of"] for t in built})
    requests = {tuple(sorted(filter(None, [t["paraphrase_of"],
                                           (t["twin_of"] or "").rsplit(".", 1)[0] or None])))
                for t in built}
    fam = Counter(t["family"] for t in built if t["style"] == "terse")
    lines = [
        "# Paraphrases",
        "",
        "Generated by `scripts/generate_paraphrases.py` (seed `" + SEED + "`); do not edit.",
        "Each task here rewords one original task (`paraphrase_of`): same reference, same",
        "accepted alternatives, same target, another `prompt` and `style`. With the original",
        "(`full`) that gives three phrasings per request: full sentence, terse command, and",
        "indirect/polite. Every wording is written by hand in the script (`WORDINGS`) and",
        "checked by rule: every id, number, code, chain letter, quoted text, colour and",
        "representation word of the original must be in it. Accept-set tasks are never",
        "paraphrased. Only public-split requests are.",
        "",
        f"{len(built)} paraphrase tasks of {len(originals)} originals "
        f"({len(requests)} requests; a twin pair is one request). Rebuild with:",
        "",
        "```bash",
        "uv run python scripts/generate_paraphrases.py            # the recorded selection",
        f"uv run python scripts/generate_paraphrases.py {command}".rstrip(),
        "```",
        "",
        "| family | originals paraphrased |", "|---|---:|",
    ]
    lines += [f"| `{f}` | {n} |" for f, n in sorted(fam.items())]
    lines += ["", "## The three phrasings", "",
              "| original | tier | full | terse | indirect |", "|---|---|---|---|---|"]
    by = {(t["paraphrase_of"], t["style"]): t for t in built}
    shown = set()
    for tid in originals:
        full = by[(tid, "terse")]["provenance"]["original_prompt"]
        if full in shown:              # the twin on the other track: same words
            continue
        shown.add(full)
        how = by[(tid, "terse")]["tier"]
        lines.append(f"| `{tid}` | {how} | {cell(full)} | {cell(by[(tid, 'terse')]['prompt'])} | "
                     f"{cell(by[(tid, 'indirect')]['prompt'])} |")
    if skipped:
        lines += ["", "## Asked for but not paraphrased", ""] + [f"- {s}" for s in skipped]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ids", nargs="*", help="ids of the tasks to paraphrase")
    ap.add_argument("--select-seeded", type=int, metavar="N",
                    help="choose N requests by seed, spread over tiers and families")
    ap.add_argument("--tiers", nargs="+", help="with --select-seeded: only these tiers")
    ap.add_argument("--public-only", action="store_true",
                    help="with --select-seeded: only requests of the public split")
    ap.add_argument("--list-families", action="store_true",
                    help="say which families can be paraphrased, and stop")
    ap.add_argument("--check", action="store_true", help="fail if the files would change")
    ap.add_argument("--tasks-dir", type=pathlib.Path, default=T.TASKS_DIR)
    ap.add_argument("--out", type=pathlib.Path, default=None,
                    help="where to write (default: <tasks-dir>/paraphrases)")
    a = ap.parse_args(argv)
    out = (a.out or a.tasks_dir / "paraphrases").resolve()
    sources = load_sources(a.tasks_dir.resolve(), out)

    if a.list_families:
        per: dict[tuple, Counter] = {}
        for t in sources.values():
            ok, why = phrasings(t, request_of(t)[0])
            per.setdefault((t["tier"], t["family"]), Counter())[
                "yes: " + why if ok else "no: " + why] += 1
        for (tier, family), counts in sorted(per.items()):
            for why, n in sorted(counts.items()):
                print(f"{tier:<12} {family:<28} {n:>4}  {why}")
        return 0

    record = out / SELECTION
    generic = False
    if a.select_seeded is not None:
        ids = select_seeded(sources, a.select_seeded, generic, a.tiers, a.public_only)
        command = f"--select-seeded {a.select_seeded}" + (
            " --tiers " + " ".join(a.tiers) if a.tiers else "") + (
            " --public-only" if a.public_only else "")
        if len(ids) < a.select_seeded:
            print(f"note: only {len(ids)} of {a.select_seeded} requests can be paraphrased "
                  "(see --list-families)")
    elif a.ids:
        ids, command = sorted(a.ids), " ".join(sorted(a.ids))
    elif record.exists():
        lines = record.read_text(encoding="utf-8").splitlines()
        head = [x[1:].strip() for x in lines if x.startswith("#")]
        command = next((x[len("command:"):].strip() for x in head if x.startswith("command:")), "")
        ids = [x.strip() for x in lines if x.strip() and not x.startswith("#")]
    else:
        ap.error("give task ids or --select-seeded N (no recorded selection yet)")

    built, skipped = build(sources, ids, generic)
    verify(built, sources)
    files = {out / f"{t['id']}.json": json.dumps(t, indent=1) + "\n" for t in built}
    files[record] = (f"# command: {command}\n# one request per line (its first task id); "
                     "a twin is paraphrased with it\n" + "".join(f"{i}\n" for i in ids))
    files[out / "README.md"] = readme(built, skipped, command)
    stale = sorted(p for p in out.glob("*") if p not in files) if out.exists() else []
    changed = [p for p, text in files.items()
               if not p.exists() or p.read_text(encoding="utf-8") != text]
    for s in skipped:
        print(f"skipped: {s}")
    if skipped:      # a selected request with no usable wording: write one (WORDINGS)
        return 1
    if a.check:
        if changed or stale:
            print("paraphrases are out of date:", *[p.name for p in changed + stale])
            return 1
        print(f"{len(built)} paraphrase tasks are up to date")
        return 0
    out.mkdir(parents=True, exist_ok=True)
    for p in stale:
        p.unlink()
    for p, text in files.items():
        p.write_text(text, encoding="utf-8")
    print(f"wrote {len(built)} paraphrase tasks of {len({t['paraphrase_of'] for t in built})} "
          f"originals to {out} ({len(changed)} files changed, {len(stale)} removed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
