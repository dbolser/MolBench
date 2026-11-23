#!/usr/bin/env python3
"""Numbers of the paper that do not come from a model run.

    uv run python paper/corpus_values.py            # writes paper/generated/corpus_values.json
    uv run python paper/corpus_values.py --check    # exit 1 if the committed files are stale

``scripts/paper_tables.py`` turns run archives into ``paper/generated/values.json``. This
script adds everything else the text quotes, and nothing is typed by hand:

* the corpus as built (counted through ``molbench.tasks.load_corpus``);
* the structure panel and the clinical variant lists (``data/panel``);
* the grader control set (``tests/controls``);
* the October 2026 predictions regraded on drawn state (``tests/controls/october_regrade.json``);
* the pilot rating study (``paper/a4/tables/agreement.json``);
* the run plan (``run/final_run.toml``);
* the running example of the paper, graded here with the benchmark's own grader.

It also writes the tables that are built from the same sources (``table_corpus.md``, the
empty result tables ``shape_*.md``, and the Supporting Information tables ``si_*.md``).
``paper/build.py`` reads ``values.json`` and ``corpus_values.json`` together; a key present
in both is an error. No network, no model call.
"""

from __future__ import annotations

import argparse
import collections
import copy
import datetime
import glob
import json
import pathlib
import re
import statistics
import sys
import tomllib

PAPER = pathlib.Path(__file__).resolve().parent
REPO = PAPER.parent
GEN = PAPER / "generated"
sys.path.insert(0, str(REPO))

from molbench import atoms, runner, tasks as T  # noqa: E402

PENDING = "⟦PENDING: final run⟧"

TIERS = ["translation", "grounded", "interactions", "resolve", "clinical", "followup",
         "accept_set", "tool_only"]
TIER_NAME = {"translation": "Translation", "grounded": "Structure-grounded",
             "interactions": "Interactions", "resolve": "Name resolution",
             "clinical": "Clinical variant", "followup": "Follow-up turn",
             "accept_set": "Several right answers", "tool_only": "Viewer settings"}
TIER_ASKS = {
    "translation": "Everything needed is in the request; write it in the format.",
    "grounded": "The request names a feature (the ligand, the disulfides); the model must know which atoms these are.",
    "interactions": "Named atoms and a measurement or contact between them.",
    "resolve": "The structure is named by protein, not by identifier.",
    "clinical": "A variant is named in UniProt numbering or in traditional numbering; its residue must be found in the structure, where its number often differs.",
    "followup": "A start state plus an edit request; the full new state is returned.",
    "accept_set": "The request leaves one countable thing open; several drawn states are right.",
    "tool_only": "A viewer setting that only the call-list format can express.",
}
# LYZ p.W82R on 2NWD: a ClinVar record of its own with assertion criteria, an offset of
# 18 residues, and a partner task on the AlphaFold model (the earlier example, F75I,
# rested on a record without assertion criteria and is no longer a task).
EXAMPLE = "clin-pair-target-lyz-2nwd-w82r"


def jload(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def pct(a, b):
    return round(a / b, 4) if b else None


# --------------------------------------------------------------------------- #
# Corpus
# --------------------------------------------------------------------------- #
def corpus_values(V: dict, corpus: list[dict]) -> dict:
    orig = [t for t in corpus if not t.get("paraphrase_of")]
    para = [t for t in corpus if t.get("paraphrase_of")]
    by_id = {t["id"]: t for t in corpus}
    V["corpus.n_files"] = len(corpus)
    V["corpus.n_tasks"] = len(orig)
    V["corpus.n_paraphrase_files"] = len(para)
    V["corpus.n_tasks_paraphrased"] = len({t["paraphrase_of"] for t in para})
    cells = collections.Counter((t["track"], t["tier"], t["split"]) for t in orig)
    for track in ("mvs", "api"):
        sub = [t for t in orig if t["track"] == track]
        V[f"corpus.{track}.n"] = len(sub)
        for split in ("public", "heldback"):
            V[f"corpus.{track}.{split}"] = sum(t["split"] == split for t in sub)
        for tier in TIERS:
            n = sum(t["tier"] == tier for t in sub)
            V[f"corpus.{track}.{tier}.n"] = n
            for split in ("public", "heldback"):
                V[f"corpus.{track}.{tier}.{split}"] = cells[(track, tier, split)]
        V[f"corpus.{track}.n_paraphrase_files"] = sum(t["track"] == track for t in para)
    V["corpus.n_tiers"] = len({t["tier"] for t in orig})
    V["corpus.n_mvs_tiers"] = len({t["tier"] for t in orig if t["track"] == "mvs"})
    V["corpus.n_templates"] = len({t["family"] for t in orig})

    # Requests: a twin pair is one request.
    twins = [t for t in orig if t["track"] == "mvs" and t.get("twin_of")]
    V["corpus.n_twin_pairs"] = len(twins)
    V["corpus.twin_share_of_mvs"] = pct(len(twins), V["corpus.mvs.n"])
    V["corpus.n_mvs_without_twin"] = V["corpus.mvs.n"] - len(twins)
    V["corpus.n_api_without_twin"] = V["corpus.api.n"] - len(twins)
    V["corpus.n_requests"] = len(orig) - len(twins)
    for tier in TIERS:
        V[f"corpus.twins.{tier}"] = sum(t["tier"] == tier for t in twins)
    hide = [t for t in orig if t["track"] == "api" and t.get("twin_of")
            and (t["provenance"].get("difficulty") or {}).get("context_switched_off")]
    V["corpus.twins.need_hide_toggle"] = len(hide)
    V["corpus.twins.hide_example"] = min((" ".join(t["prompt"].split()) for t in hide), key=lambda q: (len(q), q))
    V["corpus.twins.written_by_translator"] = sum(
        1 for t in orig if t["track"] == "api" and "translate_mvs_to_api" in t["provenance"]["script"])

    # Paraphrases: requests reworded (a twin pair is one request).
    req = set()
    for t in para:
        o = by_id[t["paraphrase_of"]]
        req.add(tuple(sorted([o["id"], o.get("twin_of") or o["id"]])))
    V["corpus.n_requests_paraphrased"] = len(req)
    V["corpus.n_paraphrased_pairs"] = V["corpus.n_tasks_paraphrased"] - len(req)
    V["corpus.n_paraphrased_scene_tasks"] = sum(by_id[i]["track"] == "mvs" for i in {t["paraphrase_of"] for t in para})
    V["corpus.n_paraphrased_call_tasks"] = V["corpus.n_tasks_paraphrased"] - V["corpus.n_paraphrased_scene_tasks"]
    # One request in its three phrasings: the shortest full request that has both others.
    styles: dict = {}
    for t in para:
        styles.setdefault(t["paraphrase_of"], {})[t["style"]] = " ".join(t["prompt"].split())
    full = min((i for i, d in styles.items() if {"terse", "indirect"} <= set(d) and by_id[i]["track"] == "mvs"),
               key=lambda i: (len(by_id[i]["prompt"]), i))
    V["corpus.paraphrase_example.full"] = " ".join(by_id[full]["prompt"].split())
    V["corpus.paraphrase_example.terse"] = styles[full]["terse"]
    V["corpus.paraphrase_example.indirect"] = styles[full]["indirect"]
    V["corpus.paraphrase_styles"] = "full, terse and indirect"

    # Structures and the held-back split.
    used = collections.Counter()
    per_tier = collections.Counter()
    for t in orig:
        for s in t["structures"]:
            used[s] += 1
            per_tier[(t["track"], t["tier"], s)] += 1
    V["corpus.n_structures"] = len(used)
    V["corpus.n_alphafold_models"] = sum(s.startswith("af-") for s in used)
    V["corpus.n_pdb_entries"] = V["corpus.n_structures"] - V["corpus.n_alphafold_models"]
    V["corpus.max_tasks_per_structure"] = max(used.values())
    V["corpus.min_tasks_per_structure"] = min(used.values())
    V["corpus.max_tasks_per_structure_tier_track"] = max(per_tier.values())
    held = jload(REPO / "data/panel/heldback.json")
    V["corpus.heldback.n_structures"] = len(held)
    V["corpus.heldback.n_tasks"] = sum(t["split"] == "heldback" for t in orig)
    V["corpus.heldback.share"] = pct(V["corpus.heldback.n_tasks"], len(orig))
    V["corpus.public.n_tasks"] = len(orig) - V["corpus.heldback.n_tasks"]
    pub_structs = {s for t in orig if t["split"] == "public" for s in t["structures"]}
    assert not pub_structs & set(held), "a held-back structure is used by a public task"
    V["corpus.n_tasks_without_structure"] = sum(not t["structures"] for t in orig)
    # Structures per category and track: the units that the bootstrap resamples.
    for track in ("mvs", "api"):
        for tier in TIERS:
            V[f"corpus.{track}.{tier}.n_structures"] = len(
                {T.cluster_key(t) for t in orig if t["track"] == track and t["tier"] == tier})
    # Which structures did tasks published before this corpus use? (frozen in the panel file)
    earlier = {e["id"] for e in jload(REPO / "data/panel/panel.json")["entries"] if e.get("used_by_tasks")}
    V["corpus.public.n_structures"] = len(pub_structs)
    V["corpus.public.n_structures_used_earlier"] = len(pub_structs & earlier)
    V["corpus.public.n_structures_not_used_earlier"] = len(pub_structs - earlier)
    assert not earlier & set(held), "a held-back structure was used by an earlier task"
    # Targets: tasks that are about no atoms store none and get no target score.
    V["corpus.n_with_target"] = sum(t.get("target") is not None for t in orig)
    V["corpus.n_without_target"] = len(orig) - V["corpus.n_with_target"]
    no_target = collections.Counter((t["track"], t["tier"]) for t in orig if t.get("target") is None)
    assert set(k[1] for k in no_target) <= {"followup", "tool_only", "translation"}, no_target
    assert not any(t.get("target") is None for t in orig if t["track"] == "mvs" and t["tier"] != "followup")
    V["corpus.n_without_target_followup"] = sum(n for (_, tier), n in no_target.items() if tier == "followup")
    V["corpus.n_without_target_settings"] = V["corpus.n_without_target"] - V["corpus.n_without_target_followup"]
    V["corpus.twins.n_without_target"] = sum(t.get("target") is None for t in twins)
    assert all(t["tier"] == "followup" and by_id[t["twin_of"]].get("target") is None
               for t in twins if t.get("target") is None)
    V["corpus.twins.n_with_target"] = len(twins) - V["corpus.twins.n_without_target"]
    # A task has a target score if it stores a target or is a single request without one.
    V["corpus.n_with_target_score"] = V["corpus.n_with_target"] + V["corpus.n_without_target_settings"]
    assert V["corpus.n_with_target_score"] + V["corpus.n_without_target_followup"] == len(orig)
    # The pairs without a target score are not among those whose call list must hide the default view.
    hide_ids = {t["twin_of"] for t in hide}
    assert not hide_ids & {t["id"] for t in twins if t.get("target") is None}
    per_cell = [V[f"corpus.{track}.{tier}.n"] for track in ("mvs", "api") for tier in TIERS
                if V[f"corpus.{track}.{tier}.n"]]
    V["corpus.tier_tasks_min"], V["corpus.tier_tasks_max"] = min(per_cell), max(per_cell)
    # Requests that ask for a lone metal ion as a sphere (SI Section S4.8).
    ion = [t for t in orig if t["family"] == "tr-ions"]
    assert all("sphere" in t["prompt"] for t in ion)
    assert sum(t["track"] == "mvs" for t in ion) * 2 == len(ion)      # "half of them on each track"
    V["corpus.n_ion_sphere_tasks"] = len(ion)
    # Translation on the call-list track: templates for calls that a scene has no partner for.
    api_tr = [t for t in orig if t["track"] == "api" and t["tier"] == "translation"]
    V["corpus.api.translation.n_call_only"] = sum(not t.get("twin_of") for t in api_tr)
    V["corpus.api.translation.n_call_only_templates"] = len(
        {t["family"] for t in api_tr} - {t["family"] for t in api_tr if t.get("twin_of")})

    # Follow-up turns and accept sets.
    for track in ("mvs", "api"):
        fu = [t for t in orig if t["track"] == track and t["tier"] == "followup"]
        V[f"corpus.followup.{track}.noop"] = sum(bool((t.get("context") or {}).get("noop")) for t in fu)
        acc = [t for t in orig if t["track"] == track and t["tier"] == "accept_set"]
        n_states = [1 + len(t["accepted"]) for t in acc]
        V[f"corpus.accept.{track}.max_states"] = max(n_states)
        V[f"corpus.accept.{track}.median_states"] = statistics.median(n_states)
        readings = [(t["provenance"].get("difficulty") or {}).get("n_readings") for t in acc]
        if all(isinstance(r, int) for r in readings):
            V[f"corpus.accept.{track}.median_readings"] = statistics.median(readings)
            V[f"corpus.accept.{track}.max_readings"] = max(readings)
    # Name resolution: how the list of accepted entries was made (frozen with the tasks).
    res_data = jload(REPO / "data/mvscore/resolve_entries.json")
    V["resolve.retrieved"] = res_data["retrieved"]
    src = (REPO / "scripts/generate_resolve_tasks.py").read_text(encoding="utf-8")
    V["resolve.min_residues"] = int(re.search(r"^MIN_RESIDUES = (\d+)$", src, flags=re.M).group(1))
    assert re.search(r"^MIN_SHARE = 0\.5$", src, flags=re.M) and "RCSB" in res_data["source"]   # "half", "RCSB PDB"
    V["corpus.n_other_tasks_with_alternatives"] = sum(
        1 for t in orig if t["accepted"] and t["tier"] != "accept_set")

    # Largest template share per tier and track.
    worst = {}
    for track in ("mvs", "api"):
        for tier in TIERS:
            sub = [t for t in orig if t["track"] == track and t["tier"] == tier]
            if sub:
                fam, n = collections.Counter(t["family"] for t in sub).most_common(1)[0]
                worst[(track, tier)] = (n / len(sub), fam)
    V["corpus.max_template_share_resolve"] = round(worst[("mvs", "resolve")][0], 4)
    rest = [v[0] for k, v in worst.items() if k not in (("mvs", "resolve"), ("api", "accept_set"))]
    V["corpus.max_template_share_other"] = round(max(rest), 4)

    # Clinical tier.
    clin = [t for t in orig if t["track"] == "mvs" and t["tier"] == "clinical"]
    d = [t["provenance"]["clinical"]["difficulty"] for t in clin]
    c = [t["provenance"]["clinical"] for t in clin]
    n = len(clin)
    V["clin.n"] = n
    V["clin.n_proteins"] = len({x["gene"] for x in c})
    panel_genes = {p["gene"] for p in jload(REPO / "data/panel/panel.json")["disease_proteins"]}
    V["_genes_without_task"] = panel_genes - {x["gene"] for x in c}
    V["clin.n_structures"] = len({s for t in clin for s in t["structures"]})
    V["clin.n_alphafold_tasks"] = sum(bool(x["alphafold_model"]) for x in d)
    V["clin.n_offset"] = sum(bool(x["needs_numbering_offset"]) for x in d)
    V["clin.offset_share"] = pct(V["clin.n_offset"], n)
    V["clin.n_no_offset"] = n - V["clin.n_offset"]
    V["clin.n_chain_differs"] = sum(bool(x["author_chain_differs_from_label_chain"]) for x in d)
    V["clin.chain_differs_share"] = pct(V["clin.n_chain_differs"], n)
    V["clin.n_insertion_code"] = sum(bool(x["insertion_code"]) for x in d)
    V["clin.n_mature_name"] = sum(bool(x["name_in_mature_numbering"]) for x in d)
    V["clin.n_face_value_right"] = sum(bool(x["number_in_name_as_author_number_is_right"]) for x in d)
    V["clin.n_face_value_wrong"] = n - V["clin.n_face_value_right"]
    V["clin.n_accession_in_prompt"] = sum(bool(x["accession_in_prompt"]) for x in d)
    V["clin.n_no_accession"] = n - V["clin.n_accession_in_prompt"]
    V["clin.n_context_none"] = sum(x["context"] == "none" for x in c)
    V["clin.n_context_cartoon"] = sum(x["context"] not in ("none",) and not x.get("secondary_structure") for x in c)
    V["clin.n_sse"] = sum(bool(x.get("secondary_structure")) for x in c)
    V["clin.n_in_pairs"] = sum(bool(x.get("pair")) for x in c)
    V["clin.n_multi"] = sum(len(x["variants"]) > 1 for x in c)
    offs = sorted({abs(o) for x in d for o in x["author_minus_uniprot"] if o})
    V["clin.offset_min"], V["clin.offset_max"] = offs[0], offs[-1]
    V["clin.n_offset_proteins"] = len({x["gene"] for x, y in zip(c, d) if y["needs_numbering_offset"]})
    V["clin.n_templates"] = len({t["family"] for t in clin})
    # Why "numbered as UniProt" and "number in the name is the author number" are two splits.
    face = [bool(x["number_in_name_as_author_number_is_right"]) for x in d]
    off = [bool(x["needs_numbering_offset"]) for x in d]
    V["clin.n_face_right_no_offset"] = sum(f and not o for f, o in zip(face, off))
    V["clin.n_face_right_offset"] = sum(f and o for f, o in zip(face, off))
    V["clin.n_face_wrong_no_offset"] = sum(not f and not o for f, o in zip(face, off))
    V["clin.n_face_wrong_offset"] = sum(not f and o for f, o in zip(face, off))
    assert all(x["name_in_mature_numbering"] for x, f, o in zip(d, face, off) if f == o), \
        "the two clinical splits differ for a reason other than a mature-protein name"
    # The same variant on two structures of one protein.
    seen, kinds = set(), collections.Counter()
    pair_genes = set()
    for t in clin:
        p = t["provenance"]["clinical"].get("pair")
        if not p:
            continue
        key = tuple(sorted([t["id"], p["with"]]))
        if key in seen:
            continue
        seen.add(key)
        o2 = by_id[p["with"]]["provenance"]["clinical"]["difficulty"]
        o1 = t["provenance"]["clinical"]["difficulty"]
        differs = bool(o1["needs_numbering_offset"]) != bool(o2["needs_numbering_offset"])
        kinds[differs] += 1
        if differs:
            pair_genes.add(t["provenance"]["clinical"]["gene"])
            assert o1["alphafold_model"] != o2["alphafold_model"]
    V["clin.n_structure_pairs"] = len(seen)
    V["clin.n_offset_pairs"] = kinds[True]
    V["clin.n_same_numbering_pairs"] = kinds[False]
    V["clin.n_offset_pair_proteins"] = len(pair_genes)
    per_gene = collections.defaultdict(set)
    for t in clin:
        per_gene[t["provenance"]["clinical"]["gene"]].update(t["structures"])
    V["clin.n_proteins_several_structures"] = sum(len(v) > 1 for v in per_gene.values())
    V["clin.n_alphafold_structures"] = sum(s.startswith("af-") for s in {s for v in per_gene.values() for s in v})
    V["clin.n_pdb_structures"] = V["clin.n_structures"] - V["clin.n_alphafold_structures"]
    V["clin.n_proteins_one_structure"] = V["clin.n_proteins"] - V["clin.n_proteins_several_structures"]
    # An entry that holds two of the proteins (the haemoglobin entries hold alpha and beta chains).
    holders = collections.defaultdict(set)
    for g, ss in per_gene.items():
        for s_ in ss:
            holders[s_].add(g)
    shared = {s_: g for s_, g in holders.items() if len(g) > 1}
    V["clin.n_structures_two_proteins"] = len(shared)
    assert all(g == {"HBA1", "HBB"} for g in shared.values()), shared   # the text names haemoglobin
    V["clin.max_tasks_per_structure"] = max(collections.Counter(s_ for t in clin for s_ in t["structures"]).values())
    V["clin.n_variants"] = len({(x["gene"], v["variant"]) for x in c for v in x["variants"]})
    V["clin.n_one_variant"] = sum(len(x["variants"]) == 1 for x in c)
    V["clin.max_variants_per_task"] = max(len(x["variants"]) for x in c)
    # A request that uses a traditional name, quoted in full: the shortest one with no context.
    trad = [t for t in clin if t["provenance"]["clinical"]["difficulty"]["name_in_mature_numbering"]
            and t["provenance"]["clinical"]["context"] == "none"]
    q = min(trad, key=lambda t: (len(t["prompt"]), t["id"]))
    V["clin.mature_example.prompt"] = " ".join(q["prompt"].split())
    qv = q["provenance"]["clinical"]["variants"][0]
    V["clin.mature_example.name"] = qv["name_in_prompt"]
    V["clin.mature_example.hgvs"] = qv["hgvs"]
    assert "mature-protein numbering" in q["prompt"]
    # The one variant kept by name although its only record has no assertion criteria.
    kept = [t for t in clin if any(v["variant"] == "I74T" for v in t["provenance"]["clinical"]["variants"])
            and t["provenance"]["clinical"]["gene"] == "LYZ"]
    assert kept and all("classified as pathogenic in ClinVar" in t["prompt"] or "pathogenic" in t["prompt"]
                        for t in kept)
    V["clin.n_tasks_kept_by_name"] = len(kept)
    kv = [v for v in kept[0]["provenance"]["clinical"]["variants"] if v["variant"] == "I74T"][0]
    assert kv["clinvar_review_status"] == ["no assertion criteria provided"]
    V["clin.kept_by_name.classification"] = kv["clinvar_classification"][0].lower()
    assert V["clin.n_insertion_code"] == 0      # the text says no clinical target has one
    # Section 3.3.1 says in words where the tasks with several variants and the helix and
    # strand tasks sit in Table 2: all of them have an offset, and copying is wrong in all.
    for x, y in zip(c, d):
        if len(x["variants"]) > 1 or x.get("secondary_structure"):
            assert y["needs_numbering_offset"] and not y["number_in_name_as_author_number_is_right"], x
    assert V["clin.n_multi"] == n - V["clin.n_one_variant"]
    return {"orig": orig, "para": para, "by_id": by_id, "used": used}


def clinical_groupings_table(V: dict) -> str:
    """The two groupings of the clinical tasks, crossed (Section 3.3.1)."""
    n = V
    return "\n".join([
        "| | Copying the number is right | Copying the number is wrong | All |",
        "|:-----------------|---:|---:|---:|",
        f"| **No offset**: the target's author number is its UniProt number | {n['clin.n_face_right_no_offset']} "
        f"| {n['clin.n_face_wrong_no_offset']} | {n['clin.n_no_offset']} |",
        f"| **Offset**: the target's author number differs from its UniProt number | {n['clin.n_face_right_offset']} "
        f"| {n['clin.n_face_wrong_offset']} | {n['clin.n_offset']} |",
        f"| **All** | **{n['clin.n_face_value_right']}** | **{n['clin.n_face_value_wrong']}** | **{n['clin.n']}** |",
    ]) + "\n"


def corpus_table(V: dict) -> str:
    rows = ["| Category | What is asked | Scene track (public + held back) | Call-list track (public + held back) | Pairs |",
            "|:------|:----------------|-----:|-----:|--:|"]
    for tier in TIERS:
        cells = []
        for track in ("mvs", "api"):
            n = V[f"corpus.{track}.{tier}.n"]
            cells.append(f"{n} ({V[f'corpus.{track}.{tier}.public']} + {V[f'corpus.{track}.{tier}.heldback']})"
                         if n else "–")
        pairs = V[f"corpus.twins.{tier}"]
        rows.append(f"| {TIER_NAME[tier]} | {TIER_ASKS[tier]} | {cells[0]} | {cells[1]} | {pairs or '–'} |")
    rows.append(f"| **All** | | **{V['corpus.mvs.n']}** ({V['corpus.mvs.public']} + {V['corpus.mvs.heldback']}) "
                f"| **{V['corpus.api.n']}** ({V['corpus.api.public']} + {V['corpus.api.heldback']}) "
                f"| **{V['corpus.n_twin_pairs']}** |")
    return "\n".join(rows) + "\n"


# --------------------------------------------------------------------------- #
# Panel and variants
# --------------------------------------------------------------------------- #
def panel_values(V: dict, used) -> list[dict]:
    panel = jload(REPO / "data/panel/panel.json")
    entries = panel["entries"]
    V["panel.n"] = len(entries)
    V["panel.n_pdb"] = sum(e["kind"] == "pdb" for e in entries)
    V["panel.n_alphafold"] = V["panel.n"] - V["panel.n_pdb"]
    V["panel.n_unused"] = sum(e["id"] not in used for e in entries)
    V["panel.max_atoms"] = panel["max_atoms"]
    meth = collections.Counter(e["method"] for e in entries if e["kind"] == "pdb")
    V["panel.n_xray"] = meth.get("X-ray", 0)
    V["panel.n_nmr"] = meth.get("NMR", 0)
    V["panel.n_cryoem"] = sum(v for k, v in meth.items() if k not in ("X-ray", "NMR"))
    years = sorted(int(e["deposited"][:4]) for e in entries if e.get("deposited") and e["kind"] == "pdb")
    V["panel.deposited_first"], V["panel.deposited_last"] = years[0], years[-1]
    V["panel.deposited_median"] = int(statistics.median(years))
    V["panel.n_deposited_before_2010"] = sum(y < 2010 for y in years)
    V["panel.n_deposited_2020_on"] = sum(y >= 2020 for y in years)
    V["panel.n_offset"] = sum(bool(e.get("offset")) for e in entries)
    V["panel.n_over_size_limit"] = sum(bool(e.get("over_size_limit")) for e in entries)
    V["panel.n_disease_proteins"] = len(panel["disease_proteins"])
    V["panel.n_disease_proteins_without_task"] = V["panel.n_disease_proteins"] - V["clin.n_proteins"]
    af = [re.match(r"AlphaFold model of ([^:]+):", e["why"]).group(1).replace("full-length ", "").replace("human ", "")
          for e in entries if e["kind"] != "pdb"]
    V["panel.alphafold_proteins"] = ", ".join(af[:-1]) + " and " + af[-1]
    V["panel.retrieved"] = max(e["retrieved"] for e in entries)
    blank = ("", ".", "?", None)
    alt = hyd = 0
    for e in entries:
        cols = atoms.load_table(e["id"]).columns
        alt += any(a not in blank for a in cols["label_alt_id"])
        hyd += any(x in ("H", "D") for x in cols["type_symbol"])
    V["panel.n_with_alternate_conformers"] = alt
    V["panel.n_with_hydrogens"] = hyd
    feats = collections.Counter(f for e in entries for f in e.get("features", []))
    for f in ("ligand", "heme", "metal", "disulfide", "nucleic", "glycan", "membrane",
              "insertion-codes", "auth-label-chain", "modified-residue", "assembly-differs"):
        V[f"panel.feature.{f}"] = feats.get(f, 0)
    kept = rej_clinvar = rej_other = 0
    retrieved = set()
    for f in sorted(glob.glob(str(REPO / "data/panel/variants/*.json"))):
        d = jload(f)
        kept += len(d["variants"])
        retrieved.add(d.get("clinvar_retrieved") or d.get("retrieved"))
        for r in d["rejected"]:
            if "ClinVar" in str(r.get("reason")):
                rej_clinvar += 1
            else:
                rej_other += 1
    V["variants.n_confirmed"] = kept
    V["variants.n_removed_by_clinvar"] = rej_clinvar
    V["variants.n_candidates"] = kept + rej_clinvar
    V["variants.removed_share"] = pct(rej_clinvar, kept + rej_clinvar)
    V["variants.n_wild_type_mismatch"] = rej_other
    V["variants.clinvar_retrieved"] = max(str(r)[:10] for r in retrieved if r)
    # The second pass (audit of 2026-11-16): a ClinVar record of the variant's own.
    from molbench import variants as variants_mod
    own = other_gene = haplotype = zero_star = 0
    for p in variants_mod.proteins():
        ok = variants_mod.confirmed(p["accession"])
        own += len(ok)
        zero_star += sum(not variants_mod.criteria_provided(v) for v in ok)
        for d in variants_mod.not_confirmed(p["accession"]):
            if d["reason"].startswith("haplotype"):
                haplotype += 1
            else:
                other_gene += 1
    V["variants.n_own_record"] = own
    V["variants.n_other_gene_only"] = other_gene
    V["variants.n_haplotype_only"] = haplotype
    V["variants.n_no_criteria"] = zero_star
    V["variants.n_usable"] = own - zero_star
    V["variants.n_second_pass_removed"] = other_gene + haplotype + zero_star
    assert V["variants.n_confirmed"] - V["variants.n_second_pass_removed"] == V["variants.n_usable"]
    V["variants.records_retrieved"] = variants_mod.clinvar_snapshot()
    usable = {p["gene"]: [v for v in variants_mod.confirmed(p["accession"]) if variants_mod.criteria_provided(v)]
              for p in variants_mod.proteins()}
    V["variants.n_several_records"] = sum(len(v.vcv) > 1 for vs in usable.values() for v in vs)
    V["variants.max_usable_per_protein_without_task"] = max(
        len(vs) for g, vs in usable.items() if g in V["_genes_without_task"])
    without = V.pop("_genes_without_task")
    V["variants.proteins_without_task"] = " and ".join(sorted(without))
    # Section 3.1 says in words: triosephosphate isomerase kept no variant, carbonic anhydrase 2
    # kept one, and that one is observed in no panel structure.
    assert without == {"CA2", "TPI1"} and len(usable["TPI1"]) == 0 and len(usable["CA2"]) == 1
    ca2 = jload(REPO / "data/panel/variants/P00918.json")
    assert [v["structures"] for v in ca2["variants"] if v["variant"] == variants_mod.short(usable["CA2"][0])] == [{}]
    return entries


def variants_table(V: dict) -> str:
    """The variant list step by step (Section 3.1)."""
    rows = ["| Step | Rule | Removed | Left |", "|:--|:----------------------------------|---:|---:|",
            f"| 1 | Single-residue missense variants of the {V['panel.n_disease_proteins']} proteins that UniProt reports as "
            f"pathogenic or likely pathogenic, with ClinVar as a source | | {V['variants.n_candidates']:,} |",
            f"| 2 | Keep if a ClinVar variation record, reached through UniProt's cross-references, lists the same "
            f"amino-acid change at that position and has the aggregate germline classification \"Pathogenic\", "
            f"\"Likely pathogenic\" or \"Pathogenic/Likely pathogenic\" (a *qualifying record*) "
            f"| {V['variants.n_removed_by_clinvar']:,} | {V['variants.n_confirmed']:,} |",
            f"| 3a | Remove if no qualifying record is of the gene that the request names "
            f"| {V['variants.n_other_gene_only']} | |",
            f"| 3b | Remove if every qualifying record of that gene is a haplotype (two changes on one chromosome) "
            f"| {V['variants.n_haplotype_only']} | |",
            f"| 3c | Remove if every remaining qualifying record has the review status \"no assertion criteria provided\" "
            f"| {V['variants.n_no_criteria']} | {V['variants.n_usable']:,} |"]
    return "\n".join(rows) + "\n"


def si_panel_table(entries, used, held) -> str:
    rows = ["| Entry | Title (as deposited) | Method | Deposited | Atoms | Author numbering differs from UniProt | Split | Tasks |",
            "|:---|:------------|:----|:----|---:|:---|:---|---:|"]
    for e in entries:
        res = f" {e['resolution']:.2f} Å" if e.get("resolution") else ""
        off = "–" if not e.get("sifts") else ("yes" if e.get("offset") else "no")
        split = "not used (worked example of the call-list prompt)" if e["id"] not in used else (
            "held back" if e["id"] in held else "public")
        title = " ".join(str(e.get("title", "")).split()).replace("|", "/")
        if len(title) > 90:
            title = title[:87].rstrip() + "…"
        rows.append(f"| {e['id'].upper() if e['kind'] == 'pdb' else e['id']} | {title} | {e['method']}{res} "
                    f"| {e.get('deposited') or '–'} | {e['atoms']} | {off} | {split} | {used.get(e['id'], 0)} |")
    return "\n".join(rows) + "\n"


# --------------------------------------------------------------------------- #
# Grader control set
# --------------------------------------------------------------------------- #
def controls_values(V: dict) -> dict:
    s = jload(REPO / "tests/controls/summary.json")
    for track, tr in s["tracks"].items():
        p = f"controls.{track}"
        for k in ("n_controls", "n_identical", "n_equivalent", "n_wrong", "n_equivalent_kinds",
                  "n_wrong_kinds", "n_entries"):
            V[f"{p}.{k}"] = tr[k]
        for who, key in (("grader", "new"), ("previous_grader", "old")):
            g = tr[who]
            for kind in ("false_pass", "false_fail"):
                V[f"{p}.{key}.{kind}"] = g[kind]["errors"]
                V[f"{p}.{key}.{kind}_n"] = g[kind]["n"]
                V[f"{p}.{key}.{kind}_rate"] = g[kind]["rate"]
        V[f"{p}.old.what"] = tr["previous_grader"]["what"].split(",")[0]
    V["controls.n"] = V["controls.mvs.n_controls"] + V["controls.api.n_controls"]
    v = jload(REPO / "tests/controls/viewer_check.json")
    m, a = v["mvs"], v["api"]
    V["controls.viewer.molstar"] = m["molstar"]
    V["controls.viewer.mvs.checked"] = m["controls_checked"]
    V["controls.viewer.mvs.agree"] = m["verdict_agrees"]
    V["controls.viewer.mvs.skipped"] = m["skipped"]
    # The read-back is on record for the control set as it stood when it was run.
    V["controls.viewer.mvs.n_at_check"] = m["controls_checked"] + m["skipped"] + len(m["problems"])
    V["controls.viewer.mvs.n_added_since"] = V["controls.mvs.n_controls"] - V["controls.viewer.mvs.n_at_check"]
    V["controls.viewer.api.not_runnable"] = a.get("not_runnable", 0)
    V["controls.viewer.mvs.scenes"] = m["scenes_checked"]
    V["controls.viewer.mvs.scenes_agree"] = m["grader_state_agrees"]
    V["controls.viewer.mvs.probe_draws"] = m["rule_probes"]["draws_compared"]
    V["controls.viewer.mvs.probe_agree"] = m["rule_probes"]["agree"]
    V["controls.viewer.pdbe_molstar"] = a["pdbe_molstar"]
    V["controls.viewer.api.lists"] = a["lists_run"]
    # Each control has two call lists (reference and answer); the replay record counts lists.
    ents = {tr: {json.loads(line)["entry"] for line in (REPO / f"tests/controls/{tr}.jsonl").open(encoding="utf-8")}
            for tr in ("mvs", "api")}
    missing = sorted(ents["mvs"] - ents["api"])
    assert not ents["api"] - ents["mvs"] and len(ents["api"]) == V["controls.api.n_entries"]
    feats = {e["id"]: e for e in jload(REPO / "data/panel/panel.json")["entries"]}
    # The text says these hold only DNA or RNA: no chain of theirs is mapped to UniProt.
    assert all("nucleic" in feats[i]["features"] and not feats[i].get("sifts") for i in missing), missing
    names = [i.upper() for i in missing]
    V["controls.api.n_entries_without"] = len(names)
    V["controls.api.entries_without"] = ", ".join(names[:-1]) + " and " + names[-1]
    V["controls.viewer.api.agree"] = a["agree"]
    V["controls.viewer.api.bare_loads"] = a["bare_loads"]["entries"]
    V["controls.viewer.api.bare_agree"] = a["bare_loads"]["agree"]
    c = jload(REPO / "tests/controls/colour_evidence.json")
    V["colour.tolerance"] = c["tolerance"]
    from molbench import drawn
    V["colour.opacity_tolerance"] = drawn.OPACITY_TOLERANCE
    assert drawn.PARTIAL == 0.5      # the text says "half credit"
    V["colour.palette_n"] = len(c["palette"])
    V["colour.closest_pair_distance"] = c["closest_palette_pairs"][0]["distance"]
    V["colour.closest_pair"] = f"{c['closest_palette_pairs'][0]['a']} and {c['closest_palette_pairs'][0]['b']}"
    oc = c["october_colours"]
    V["colour.oct.n_comparable"] = oc["n"] - oc["no_reference_colour"]
    V["colour.oct.exact"] = oc["exact"]
    V["colour.oct.inexact"] = V["colour.oct.n_comparable"] - oc["exact"]
    V["colour.oct.closest_inexact"] = min(x["distance"] for x in oc["closest_inexact"])
    return s


def si_controls_table(s: dict) -> str:
    out = []
    for track, name in (("mvs", "Scene track"), ("api", "Call-list track")):
        out += [f"**{name}.**", "",
                "| Verdict known from construction | Kind of control | Controls | Graded as success | Graded as success by the earlier grader |",
                "|:-----|:----------------------|---:|---:|---:|"]
        for k in s["tracks"][track]["kinds"]:
            verdict = {"identical": "must pass (identical)", "equivalent": "must pass (equivalent)",
                       "wrong": "must fail (wrong)"}.get(k["group"], k["group"])
            what = k['what'].replace('|', '/').replace('the deposited model', 'the deposited coordinates')
            out.append(f"| {verdict} | {what} | {k['n']} | {k['graded_success']} "
                       f"| {k.get('old_grader_success', '–')} |")
        out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# October predictions regraded on drawn state
# --------------------------------------------------------------------------- #
def october_values(V: dict) -> None:
    o = jload(REPO / "tests/controls/october_regrade.json")["conditions"]
    for cond in ("spec", "spec_grounded"):
        a = o[cond]["all"]
        p = f"oct.{cond}"
        V[f"{p}.n"], V[f"{p}.n_valid"] = a["n"], a["valid"]
        V[f"{p}.f1"], V[f"{p}.success"], V[f"{p}.target"] = a["new_f1"], a["success"], a["target_f1"]
        V[f"{p}.old_f1"] = a["old_f1"]
        V[f"{p}.old_exact"] = a["old_f1_was_1"]
        V[f"{p}.success_strict_focus"] = a["success_if_any_focus_counts"]
        V[f"{p}.valid.f1"] = a["valid_only"]["new_f1"]
        V[f"{p}.valid.success"] = a["valid_only"]["success"]
        for tier, key in (("translation", "translation"), ("structure-grounded", "grounded"),
                          ("clinical", "clinical")):
            t = o[cond]["by_tier"][tier]
            q = f"{p}.{key}"
            V[f"{q}.n"], V[f"{q}.n_valid"] = t["n"], t["valid"]
            V[f"{q}.f1"], V[f"{q}.success"] = t["new_f1"], t["success"]
            V[f"{q}.old_f1"] = t["old_f1"]
            V[f"{q}.valid.f1"] = t["valid_only"]["new_f1"]
            V[f"{q}.valid.success"] = t["valid_only"]["success"]
            V[f"{q}.highlight_n"] = t["n_with_highlight_target"]
            V[f"{q}.highlight_exact"] = t["highlight_exactly_right"]
            V[f"{q}.highlight_exact_n"] = round(t["highlight_exactly_right"] * t["n_with_highlight_target"])
    by_model = o["spec"]["by_model"]
    succ = sorted((m["success"], k) for k, m in by_model.items())
    V["oct.spec.n_models"] = len(by_model)
    V["oct.spec.success_min"], V["oct.spec.success_max"] = succ[0][0], succ[-1][0]
    f1 = sorted(m["new_f1"] for m in by_model.values())
    V["oct.spec.f1_min"], V["oct.spec.f1_max"] = f1[0], f1[-1]
    V["oct.spec.clinical.success_n"] = round(V["oct.spec.clinical.success"] * V["oct.spec.clinical.n"])
    # Per model: does the share of valid outputs explain the strict score?
    xs = [m["valid"] / m["n"] for m in by_model.values()]
    ys = [m["new_f1"] for m in by_model.values()]
    V["oct.spec.r_valid_f1"] = round(statistics.correlation(xs, ys), 3)
    V["oct.spec.valid_share"] = round(V["oct.spec.n_valid"] / V["oct.spec.n"], 4)
    V["oct.spec.valid_share_min"], V["oct.spec.valid_share_max"] = round(min(xs), 4), round(max(xs), 4)
    vf = sorted(m["valid_only"]["new_f1"] for m in by_model.values())
    V["oct.spec.valid.f1_min"], V["oct.spec.valid.f1_max"] = vf[0], vf[-1]
    V["oct.spec.clinical.target_f1"] = o["spec"]["by_tier"]["clinical"]["target_f1"]
    V["oct.spec.clinical.highlight_valid_share"] = round(
        V["oct.spec.clinical.highlight_exact_n"] / V["oct.spec.clinical.n_valid"], 4)
    V["oct.grounding.success_delta"] = round(V["oct.spec_grounded.success"] - V["oct.spec.success"], 4)
    V["oct.grounding.valid_delta_n"] = V["oct.spec_grounded.n_valid"] - V["oct.spec.n_valid"]


def october_models_table() -> str:
    """One row per model of the October run, regraded on drawn state, best task success first."""
    by_model = jload(REPO / "tests/controls/october_regrade.json")["conditions"]["spec"]["by_model"]
    info = jload(PAPER / "inputs.json")["model_info"]
    alias = jload(PAPER / "inputs.json")["aliases"]
    weights = {k.split("/")[-1]: v["weights"] for k, v in info.items()}
    rows = ["| Model | Weights | Valid answers | F1 (strict) | Task success rate (strict) | F1, valid-only | Task success rate, valid-only |",
            "|:--------|:---|---:|---:|---:|---:|---:|"]
    for k, m in sorted(by_model.items(), key=lambda kv: (-kv[1]["success"], -kv[1]["new_f1"], kv[0])):
        name = alias.get(k, k).split("/")[-1]
        rows.append(f"| {name} | {weights.get(name, '?')} | {m['valid']} of {m['n']} | {m['new_f1']:.2f} "
                    f"| {m['success']:.1%} | {m['valid_only']['new_f1']:.2f} | {m['valid_only']['success']:.1%} |")
    return "\n".join(rows) + "\n"


def october_table(V: dict) -> str:
    rows = ["| Category (October corpus) | Answers | Valid | F1, earlier grader | F1 | Task success rate | Requested part exactly right |",
            "|:-----------|---:|---:|---:|---:|---:|---:|"]
    for key, name in (("translation", "Translation"), ("grounded", "Structure-grounded, name resolution and interactions"),
                      ("clinical", "Clinical variant")):
        q = f"oct.spec.{key}"
        rows.append(f"| {name} | {V[q + '.n']:,} | {V[q + '.n_valid']:,} | {V[q + '.old_f1']:.2f} | {V[q + '.f1']:.2f} "
                    f"| {V[q + '.success']:.1%} | {V[q + '.highlight_exact']:.1%} of {V[q + '.highlight_n']} |")
    rows.append(f"| **All** | {V['oct.spec.n']:,} | {V['oct.spec.n_valid']:,} | {V['oct.spec.old_f1']:.2f} "
                f"| {V['oct.spec.f1']:.2f} | {V['oct.spec.success']:.1%} | |")
    return "\n".join(rows) + "\n"


# --------------------------------------------------------------------------- #
# Pilot rating study
# --------------------------------------------------------------------------- #
def pilot_values(V: dict) -> None:
    a = jload(PAPER / "a4/tables/agreement.json")
    V["pilot.exported"] = a["exported_at"][:10]
    V["pilot.n_raters"] = len(a["raters"])
    V["pilot.n_independent_raters"] = sum(r["role"] != "author" for r in a["raters"].values())
    V["pilot.n_raters_passing_checks"] = sum(bool(r["passed_checks"]) for r in a["raters"].values())
    V["pilot.n_items"] = a["rating_set"]["items"]
    V["pilot.n_pairs"] = a["rating_set"]["judged_pairs"]
    V["pilot.n_tasks"] = a["rating_set"]["tasks"]
    V["pilot.n_judge_same"] = a["rating_set"]["judge_same"]
    V["pilot.n_judge_different"] = a["rating_set"]["judge_different"]
    V["pilot.n_checks"] = sum(a["rating_set"]["checks"].values())
    V["pilot.n_ratings"] = a["ratings"]["analysed"]
    V["pilot.check_rule"] = a["min_checks"]
    for cohort, key in (("all", "all"), ("no_author", "indep")):
        c = a["cohorts"][cohort]
        u = c["unweighted"]
        p = f"pilot.{key}"
        V[f"{p}.n_labelled"] = u["ratings"]
        V[f"{p}.n_pairs"] = c["pairs_rated"]
        V[f"{p}.n_cant_tell"] = c["cant_tell"]

        for name, short in (("agreement", "agreement"), ("cohen_kappa", "kappa"),
                            ("rescue_precision", "rescue")):
            x = u["per_rating"][name]
            V[f"{p}.{short}"] = round(x["est"], 4)
            V[f"{p}.{short}_lo"], V[f"{p}.{short}_hi"] = round(x["lo"], 4), round(x["hi"], 4)
        hh = c["human_vs_human"]
        V[f"{p}.pairs_two_raters"] = hh["pairs"]
        V[f"{p}.pairs_split"] = hh["pairs_split"]
    V["pilot.flag_reference_wrong"] = a["flags"]["ref_wrong_ratings"]
    V["pilot.flag_model_better"] = a["flags"]["model_better_ratings"]


def study_values(V: dict) -> None:
    """Design numbers of the second rating study, read from its design note."""
    import re
    text = (PAPER / "a4/FINAL_CALL.md").read_text(encoding="utf-8")
    V["study.n_pairs"] = int(re.search(r"\*\*Size: (\d+) judged pairs", text).group(1))
    V["study.n_grader_check_pairs"] = int(re.search(r"small grader check \((\d+) pairs", text).group(1))
    V["study.raters_per_pair"] = int(re.search(r"with\s+(\d+) raters per pair", text).group(1))
    V["study.max_model_share"] = int(re.search(r"no model above (\d+)% of the set", text).group(1)) / 100
    V["study.max_per_task"] = int(re.search(r"at most (\d+) pairs per task", text).group(1))
    V["study.max_per_task_model"] = {"one": 1}[re.search(r"at most (\w+) sample per \(task, model\)", text).group(1)]


# --------------------------------------------------------------------------- #
# Run plan
# --------------------------------------------------------------------------- #
def plan_values(V: dict) -> list[dict]:
    m = tomllib.loads((REPO / "run/final_run.toml").read_text(encoding="utf-8"))
    models = m["models"]
    core = [x for x in models if not x.get("optional") and x["route"] != "baseline"]
    opt = [x for x in models if x.get("optional")]
    V["plan.samples"] = m["run"]["samples"]
    V["plan.max_tokens"] = m["run"]["max_tokens"]
    V["plan.n_core_models"] = len(core)
    V["plan.n_core_open"] = sum(bool(x["open_weights"]) for x in core)
    V["plan.n_core_closed"] = len(core) - V["plan.n_core_open"]
    V["plan.n_optional_models"] = len(opt)
    V["plan.n_conditions"] = len(m["conditions"])
    V["plan.n_bare_models"] = len([c for c in m["conditions"] if c["name"] == "bare"][0]["models"])
    V["plan.corpus_version"] = m["corpus"]["version"]
    V["plan.corpus_frozen"] = bool(m["corpus"]["sha256"])
    V["plan.price_date"] = max(x["price"]["date"] for x in models)
    short = lambda i: i.split("/")[-1]  # noqa: E731
    V["plan.bare_models"] = ", ".join(short(i) for i in [c for c in m["conditions"] if c["name"] == "bare"][0]["models"])
    pilot = {short(k) for k in jload(REPO / "tests/controls/october_regrade.json")["conditions"]["spec"]["by_model"]}
    V["plan.n_core_in_pilot"] = sum(short(x["id"]) in pilot for x in core)
    V["plan.core_not_in_pilot"] = ", ".join(short(x["id"]) for x in core if short(x["id"]) not in pilot)
    V["plan.n_models_max"] = len(core) + len(opt)
    V["plan.n_json_mode_models"] = sum(x.get("structured") not in (None, "none") for x in core)
    V["plan.core_without_json_mode"] = ", ".join(short(x["id"]) for x in core if x.get("structured") in (None, "none"))
    V["plan.core_models"] = ", ".join(short(x["id"]) for x in core)
    V["plan.n_optional_json_mode"] = sum(x.get("structured") not in (None, "none") for x in opt)
    assert V["plan.n_optional_json_mode"] == len(opt)     # the text says "each optional model that is run"
    # The system prompts as sent, in words (no tokenizer is used: token counts differ by model).
    nwords = lambda text: len(text.split())  # noqa: E731
    sent = runner.build_system_prompts("spec")
    from molbench import schema
    guide = {"mvs": runner.MVS_REFERENCE.read_text(encoding="utf-8"),
             "api": schema.schema_text() + "\n" + runner.API_REFERENCE.read_text(encoding="utf-8")}
    V["prompt.mvs.words"], V["prompt.api.words"] = nwords(sent["mvs"]), nwords(sent["api_calling"])
    V["prompt.mvs.guide_words"], V["prompt.api.guide_words"] = nwords(guide["mvs"]), nwords(guide["api"])
    V["prompt.longer_track"] = "call-list" if V["prompt.api.words"] > V["prompt.mvs.words"] else "scene"
    # What Section 5.2 says the guides document, and what they do not mention.
    assert "auth_seq_id" in guide["mvs"] and "label_seq_id" in guide["mvs"] and "uniprot" not in guide["mvs"].lower()
    assert "uniprot_residue_number" in guide["api"] and "auth_seq_id" in guide["api"]
    assert "uniprot" not in runner.PROMPT_MVS.read_text(encoding="utf-8").lower()
    V["plan.reasoning_max_tokens"] = m["run"]["reasoning_max_tokens"]
    V["plan.n_core_reasoning"] = sum(bool(x.get("reasoning")) for x in core)
    assert not any(x.get("max_tokens") for x in models), "a model has a token limit of its own; the text gives two"
    V["plan.core_price_output_min"] = min(x["price"]["output"] for x in core)
    V["plan.core_price_output_max"] = max(x["price"]["output"] for x in core)
    V["plan.optional_price_output_min"] = min(x["price"]["output"] for x in opt)
    V["plan.optional_price_output_max"] = max(x["price"]["output"] for x in opt)
    V["plan.n_table_rows_max"] = len(models)
    return models


def shape_tables(V: dict, models: list[dict]) -> dict[str, str]:
    """The result tables in their final shape, every result cell pending."""
    P = PENDING
    names = [("Keyword script (no model)" if x["route"] == "baseline" else x["id"].split("/")[-1])
             + (" †" if x.get("optional") else "") for x in models]
    weights = ["–" if x["route"] == "baseline" else ("open" if x["open_weights"] else "closed") for x in models]
    out = {}
    head = ("| Model | Weights | Valid answers | Task success rate (strict) | Target score (strict) | F1 (strict) "
            "| Task success rate, valid-only | Target score, valid-only | All-3 rate | Cost (USD) |\n"
            "|:-------|:---|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    # The review draft shows the first rows; the final table has one row per model (SI Table S6).
    shown = 3
    body = "".join(f"| {n} | {w} | {P} | {P} | {P} | {P} | {P} | {P} | {P} | {P} |\n"
                   for n, w in list(zip(names, weights))[:shown])
    n_core = sum(not x.get("optional") for x in models)
    body += (f"| … {n_core - shown} further rows for the other core models and up to {len(names) - n_core} "
             f"for the optional models (SI Table S6) | | {P} | | | | | | | |\n")
    out["shape_leaderboard.md"] = head + body
    tiers = ("| Category | Tasks | Structures | Task success rate (strict) | Target score (strict) | F1 (strict) "
             "| Task success rate, valid-only | Target score, valid-only |\n"
             "|:------------------------|---:|---:|---:|---:|---:|---:|---:|\n")
    for track, label in (("mvs", "Scene track"), ("api", "Call-list track")):
        tiers += f"| **{label}** | | | | | | | |\n"
        for tier in TIERS:
            n = V[f"corpus.{track}.{tier}.n"]
            if n:
                tiers += (f"| {TIER_NAME[tier]} | {n} | {V[f'corpus.{track}.{tier}.n_structures']} "
                          f"| {P} | {P} | {P} | {P} | {P} |\n")
            if n and tier == "resolve":
                for which in ("answers on the reference entry", "answers on another accepted entry"):
                    tiers += f"| \u2003*of which:* {which} | – | – | {P} | {P} | {P} | {P} | {P} |\n"
    out["shape_tiers.md"] = tiers
    out["shape_clinical.md"] = (
        "| Clinical tasks (scene track) | Tasks | Target score | Task success rate | Target score with grounding pack "
        "| Task success rate with grounding pack |\n"
        "|:------------------|--:|---:|---:|---:|---:|\n"
        f"| **Copying the number** (primary grouping): copying is right | {V['clin.n_face_value_right']} | {P} | {P} | {P} | {P} |\n"
        f"| **Copying the number**: copying is wrong | {V['clin.n_face_value_wrong']} | {P} | {P} | {P} | {P} |\n"
        f"| Difference between these two rows (95% interval) | | {P} | {P} | {P} | {P} |\n"
        f"| **Offset** (descriptive grouping): no offset | {V['clin.n_no_offset']} | {P} | {P} | {P} | {P} |\n"
        f"| **Offset**: offset | {V['clin.n_offset']} | {P} | {P} | {P} | {P} |\n"
        f"| Matched tasks, structure with an offset | {V['clin.n_offset_pairs']} | {P} | {P} | {P} | {P} |\n"
        f"| Matched tasks, predicted structure without an offset | {V['clin.n_offset_pairs']} | {P} | {P} | {P} | {P} |\n"
        f"| Helix or strand requested (a subset, reported apart) | {V['clin.n_sse']} | {P} | {P} | {P} | {P} |\n")
    lm = [n for n, x in zip(names, models) if x["route"] != "baseline"]
    def paired(title: str, n_pairs: int) -> str:
        return (f"**{title}**\n\n"
                "| Model | Pairs | Right on both sides | Right in the scene only | Right in the call list only "
                "| Right on neither side | McNemar p |\n"
                "|:--------|--:|---:|---:|---:|---:|---:|\n"
                + "".join(f"| {n} | {n_pairs} | {P} | {P} | {P} | {P} | {P} |\n" for n in lm[:2])
                + f"| … up to {len(lm) - 2} further rows, one per model | | {P} | | | | |\n")
    s3 = V["plan.samples"]
    assert s3 == 3      # "at least 2 of the 3 answers" is written out here and in the text
    out["shape_paired.md"] = (
        paired(f"Table 9a. Right = target-right (primary); at least 2 of the {s3} answers. The "
               f"{V['corpus.twins.n_with_target']} pairs that have a target score.", V["corpus.twins.n_with_target"])
        + "\n"
        + paired(f"Table 9b. Right = task success (secondary); at least 2 of the {s3} answers. All "
                 f"{V['corpus.n_twin_pairs']} pairs.", V["corpus.n_twin_pairs"]))
    out["shape_robustness.md"] = (
        "| | Comparison | Tasks | Task success rate, first group | Task success rate, second group | Difference (95% interval) |\n"
        "|---:|:--------------------|---:|---:|---:|---:|\n"
        f"| 1 | Public split against held-back split (both tracks) | {V['corpus.public.n_tasks']} and {V['corpus.heldback.n_tasks']} | {P} | {P} | {P} |\n"
        f"| 2 | Full wording against terse wording | {V['corpus.n_requests_paraphrased']} requests ({V['corpus.n_tasks_paraphrased']} tasks) | {P} | {P} | {P} |\n"
        f"| 3 | Full wording against indirect wording | {V['corpus.n_requests_paraphrased']} requests ({V['corpus.n_tasks_paraphrased']} tasks) | {P} | {P} | {P} |\n"
        f"| 4 | Main against main + JSON mode (the models that offer it: {V['plan.n_json_mode_models']} of the {V['plan.n_core_models']} core models and each optional model that is run; 1 answer per task in JSON mode) | {V['corpus.n_tasks']} | {P} | {P} | {P} |\n"
        f"| 5 | Main against main + grounding pack (name-resolution and clinical categories, scene track) "
        f"| {V['corpus.mvs.resolve.n'] + V['corpus.mvs.clinical.n']} | {P} | {P} | {P} |\n"
        f"| 6 | Main against no format guide ({V['plan.n_bare_models']} models, scene track) "
        f"| {V['corpus.mvs.n']} | {P} | {P} | {P} |\n")
    out["shape_followup.md"] = (
        "| Group | Scene track: tasks | Scene track: task success rate | Call-list track: tasks | Call-list track: task success rate |\n"
        "|:----------|---:|---:|---:|---:|\n"
        f"| Follow-up turns that need a change | {V['corpus.mvs.followup.n'] - V['corpus.followup.mvs.noop']} | {P} "
        f"| {V['corpus.api.followup.n'] - V['corpus.followup.api.noop']} | {P} |\n"
        f"| Follow-up turns that need no change | {V['corpus.followup.mvs.noop']} | {P} | {V['corpus.followup.api.noop']} | {P} |\n"
        f"| Requests with several right answers | {V['corpus.mvs.accept_set.n']} | {P} | {V['corpus.api.accept_set.n']} | {P} |\n")
    return out


def si_models_table(models: list[dict]) -> str:
    rows = ["| Model identifier | Provider | Set | Weights | Hidden reasoning by default | JSON mode | List price, USD per million tokens (input / output) | Price read on |",
            "|:---------|:---|:---|:---|:---|:---|:---|:---|"]
    for x in models:
        if x["route"] == "baseline":
            rows.append("| Keyword script | – | core | not a model | – | – | 0 / 0 | – |")
            continue
        p = x["price"]
        provider = x["id"].split("/")[0] if "/" in x["id"] else x["route"].split(":")[0]
        rows.append(f"| `{x['id']}` | {provider} | {'optional' if x.get('optional') else 'core'} "
                    f"| {'open' if x['open_weights'] else 'closed'} | {'yes' if x.get('reasoning') else 'no'} "
                    f"| {'yes' if x.get('structured') not in (None, 'none') else 'no'} "
                    f"| {p['input']} / {p['output']} | {p['date']} |")
    return "\n".join(rows) + "\n"


def si_templates_table(orig: list[dict]) -> str:
    fams: dict = {}
    for t in orig:
        f = fams.setdefault((t["tier"], t["family"]), {"mvs": 0, "api": 0, "ex": None})
        f[t["track"]] += 1
        if f["ex"] is None or (t["track"] == "mvs" and f["ex"]["track"] != "mvs"):
            f["ex"] = t
    rows = ["| Category | Template | Scene tasks | Call-list tasks | Example request |", "|:----|:-----|--:|--:|:----------------|"]
    for tier in TIERS:
        for (tr, fam), f in sorted(fams.items()):
            if tr != tier:
                continue
            prompt = " ".join(f["ex"]["prompt"].split()).replace("|", "/")
            if len(prompt) > 170:
                prompt = prompt[:167].rstrip() + "…"
            rows.append(f"| {TIER_NAME[tier]} | `{fam}` | {f['mvs'] or '–'} | {f['api'] or '–'} | {prompt} |")
    return "\n".join(rows) + "\n"


# --------------------------------------------------------------------------- #
# The running example, graded by the benchmark's grader
# --------------------------------------------------------------------------- #
def example_values(V: dict, by_id: dict) -> dict:
    m, a = by_id[EXAMPLE + "-mvs"], by_id[EXAMPLE + "-api"]
    cl = m["provenance"]["clinical"]
    var = cl["variants"][0]
    res = var["residues"][0]
    assert len(var["residues"]) == 1 and len(cl["variants"]) == 1
    table = atoms.load_table(m["structures"][0])
    entry = m["structures"][0].upper()
    pos = var["uniprot_position"]
    V["ex.id_mvs"], V["ex.id_api"] = m["id"], a["id"]
    V["ex.prompt"] = m["prompt"]
    V["ex.entry"] = entry
    V["ex.gene"], V["ex.protein"], V["ex.accession"] = cl["gene"], cl["protein"], cl["accession"]
    V["ex.variant"], V["ex.hgvs"] = var["variant"], var["hgvs"]
    V["ex.name_in_prompt"] = var["name_in_prompt"]
    assert var["name_in_prompt"] in m["prompt"] and cl["accession"] in m["prompt"]
    from molbench import variants as variants_mod
    mature = variants_mod.mature_numbering(cl["accession"], var["uniprot_position"])
    assert mature and mature["number"] == res["auth_seq_id"], "the entry is not numbered along the mature protein"
    V["ex.mature_name"] = f"{var['variant'][0]}{mature['number']}{var['variant'][-1]}"
    V["ex.removed_what"] = mature["what"]
    V["ex.uniprot_position"] = pos
    V["ex.wild_type"] = res["comp_id"].capitalize()
    V["ex.auth_chain"], V["ex.auth_number"] = res["auth_asym_id"], res["auth_seq_id"]
    V["ex.label_chain"], V["ex.label_number"] = res["label_asym_id"], res["label_seq_id"]
    V["ex.offset"] = abs(cl["difficulty"]["author_minus_uniprot"][0])
    V["ex.clinvar_vcv"] = var["clinvar_vcv"][0]
    recs = jload(REPO / "data/panel/clinvar_records.json")["records"]
    V["ex.n_clinvar_records"] = len(var["clinvar_vcv"])
    V["ex.clinvar_records"] = "; ".join(f"{k}, {recs[k]['title']}" for k in var["clinvar_vcv"])
    V["ex.clinvar_first_title"] = recs[var["clinvar_vcv"][0]]["title"]      # the change as ClinVar writes it
    assert all(cl["gene"] in recs[k]["genes"] and f"({var['hgvs']})" in recs[k]["title"] for k in var["clinvar_vcv"])
    V["ex.clinvar_classification"] = var["clinvar_classification"][0].lower()
    assert len(set(var["clinvar_classification"])) == 1 and len(set(var["clinvar_review_status"])) == 1
    V["ex.clinvar_conditions"] = "; ".join(sorted({c for k in var["clinvar_vcv"] for c in recs[k]["conditions"]}))
    V["ex.clinvar_review_status"] = var["clinvar_review_status"][0]
    vfile = jload(REPO / f"data/panel/variants/{cl['accession']}.json")
    V["ex.disease"] = [v for v in vfile["variants"] if v["variant"] == var["variant"]][0]["diseases"][0]
    facts = jload(REPO / f"data/panel/facts/{m['structures'][0]}.json")
    V["ex.title"] = facts["title"]
    V["ex.resolution"] = facts["resolution"]
    mask = table.selector({"label_asym_id": res["label_asym_id"], "label_seq_id": res["label_seq_id"]})
    V["ex.n_target_atoms"] = bin(mask).count("1")
    V["ex.n_target_hydrogens"] = sum(1 for i in range(table.n)
                                     if mask >> i & 1 and table.columns["type_symbol"][i] in ("H", "D"))
    V["ex.n_target_heavy_atoms"] = V["ex.n_target_atoms"] - V["ex.n_target_hydrogens"]
    V["ex.n_atoms"] = table.n
    face = table.selector({"auth_asym_id": res["auth_asym_id"], "auth_seq_id": pos})
    row = (face & -face).bit_length() - 1
    V["ex.face_value_residue"] = table.columns["auth_comp_id"][row].capitalize()
    V["ex.face_value_n_atoms"] = bin(face).count("1")
    api_rep, rep_words = {"ball_and_stick": ("ball-and-stick", "ball-and-stick"),
                          "spacefill": ("spacefill", "spacefill spheres")}[cl["look"]["rep"]]
    V["ex.rep"], V["ex.color"] = rep_words, cl["look"]["color"]
    V["ex.rep_short"], V["ex.rep_scene"] = api_rep, cl["look"]["rep"]
    assert f"{V['ex.color']} {rep_words}" in m["prompt"], "the request does not state the look in these words"
    import re
    rng = re.search(r"UniProt (\d+)-(\d+) = auth (\d+)-(\d+)", m["grounding"]["text"])
    V["ex.map_uniprot_first"], V["ex.map_uniprot_last"] = int(rng.group(1)), int(rng.group(2))
    V["ex.map_auth_first"], V["ex.map_auth_last"] = int(rng.group(3)), int(rng.group(4))
    assert pos - V["ex.map_uniprot_first"] + V["ex.map_auth_first"] == res["auth_seq_id"]

    def scene(selector, color=None, context=False):
        s = copy.deepcopy(m["reference"])
        st = s["root"]["children"][0]["children"][0]["children"][0]
        comp = st["children"][0]
        comp["params"]["selector"] = selector
        if color:
            comp["children"][0]["children"][0]["params"]["color"] = color
        if context:
            st["children"].insert(0, {"kind": "component", "params": {"selector": "polymer"}, "children": [
                {"kind": "representation", "params": {"type": "cartoon"}, "children": [
                    {"kind": "color", "params": {"color": "gray"}}]}]})
        return s

    right = {"auth_asym_id": res["auth_asym_id"], "auth_seq_id": res["auth_seq_id"]}
    wrong = {"auth_asym_id": res["auth_asym_id"], "auth_seq_id": pos}
    def scene_plus(selector, rep_type, color):
        s = copy.deepcopy(m["reference"])
        st = s["root"]["children"][0]["children"][0]["children"][0]
        st["children"].append({"kind": "component", "params": {"selector": selector}, "children": [
            {"kind": "representation", "params": {"type": rep_type}, "children": [
                {"kind": "color", "params": {"color": color}}]}]})
        return s

    n0 = res["auth_seq_id"]
    around = {"auth_asym_id": res["auth_asym_id"], "beg_auth_seq_id": n0 - 1, "end_auth_seq_id": n0 + 1}
    V["ex.neighbours_first"], V["ex.neighbours_last"] = n0 - 1, n0 + 1
    V["ex.neighbours_n_atoms"] = bin(table.selector(around)).count("1")
    V["ex.chain_n_atoms"] = bin(table.selector({"auth_asym_id": res["auth_asym_id"]})).count("1")
    look_rep = cl["look"]["rep"]
    other_rep = "ball_and_stick" if look_rep != "ball_and_stick" else "spacefill"
    V["ex.other_rep"] = {"ball_and_stick": "ball-and-stick", "spacefill": "spacefill spheres"}[other_rep]
    mvs_answers = {
        "spill": scene(around),
        "spill_chain": scene({"auth_asym_id": res["auth_asym_id"]}),
        "extra": scene_plus(right_sel := {"auth_asym_id": res["auth_asym_id"], "auth_seq_id": n0}, other_rep, cl["look"]["color"]),
        "other_rep_around": scene_plus(around, other_rep, cl["look"]["color"]),
        "surface": scene_plus("polymer", "surface", "gray"),
        "right": scene(right),
        "label": scene({"label_asym_id": res["label_asym_id"], "label_seq_id": res["label_seq_id"]}),
        "face": scene(wrong),
        "context": scene(right, context=True),
        "colour": scene(right, color="red"),
        "face_context": scene(wrong, context=True),
    }

    def calls(sel, colour=cl["look"]["color"], cartoon="keep"):
        d = dict(sel)
        if cartoon == "keep":
            d["color"] = None
        d["representation"] = api_rep
        d["representationColor"] = colour
        return [{"action": "load", "molecule_id": m["structures"][0]}, {"action": "color", "data": [d]}]

    unp = {"uniprot_accession": cl["accession"], "uniprot_residue_number": pos}
    auth = {"auth_asym_id": res["auth_asym_id"], "auth_seq_id": res["auth_seq_id"]}
    api_answers = {
        "right": a["reference"],
        "author": calls(auth),
        "face": calls({"auth_asym_id": res["auth_asym_id"], "auth_seq_id": pos}),
        "colour": calls(unp, colour="red"),
        "default_colour": calls(unp, cartoon="default"),
        "bare": [{"action": "load", "molecule_id": m["structures"][0]}],
    }
    answers = {"mvs": mvs_answers, "api": api_answers}
    for track, task in (("mvs", m), ("api", a)):
        for name, ans in answers[track].items():
            r = runner.grade_parsed(task, ans)
            p = f"ex.{track}.{name}"
            V[f"{p}.f1"] = round(r["f1"], 3)
            V[f"{p}.precision"] = round(r["precision"], 3)
            V[f"{p}.recall"] = round(r["recall"], 3)
            V[f"{p}.target"] = round(r["target_f1"], 3)
            V[f"{p}.target_precision"] = round(r["target_precision"], 4)
            V[f"{p}.success"] = bool(r["success"])
    # The text describes these verdicts in words; stop if the grader no longer gives them.
    for track in ("mvs", "api"):
        assert V[f"ex.{track}.right.success"] and not V[f"ex.{track}.face.success"]
        assert V[f"ex.{track}.face.f1"] == 0 and V[f"ex.{track}.face.target"] == 0
        assert not V[f"ex.{track}.colour.success"] and 0 < V[f"ex.{track}.colour.target"] < 1
    assert V["ex.mvs.label.success"] and V["ex.api.author.success"]
    assert V["ex.mvs.context.target"] == 1 and not V["ex.mvs.context.success"] and V["ex.mvs.context.f1"] < 1
    assert V["ex.mvs.face_context.target"] == 0
    # Section 4.3 derives the precision of the cartoon answer in words (two facts: one half, none).
    assert V["ex.mvs.context.precision"] == 0.25 and V["ex.mvs.context.recall"] == 1
    assert V["ex.mvs.colour.f1"] == 0.5 and V["ex.mvs.face_context.f1"] == 0
    # Section 4.2 states the three rules for extra drawing in words; these are its examples.
    assert 0 < V["ex.mvs.spill.target"] < 1 and 0 < V["ex.mvs.spill_chain.target"] < V["ex.mvs.spill.target"]
    assert 0 < V["ex.mvs.extra.target"] < 1
    # The caption of Table 3 derives the two spill rows: target atoms over atoms drawn that way.
    assert V["ex.mvs.spill.target_precision"] == round(V["ex.n_target_atoms"] / V["ex.neighbours_n_atoms"], 4)
    assert V["ex.mvs.spill_chain.target_precision"] == round(V["ex.n_target_atoms"] / V["ex.chain_n_atoms"], 4)
    # Section 4.2 gives the red residue of the call-list track as the example of half credit.
    assert V["ex.api.colour.f1"] == 0.5 and V["ex.api.bare.f1"] == 0
    assert V["ex.mvs.other_rep_around.target"] == 1 and not V["ex.mvs.other_rep_around.success"]
    assert V["ex.mvs.surface.target"] == 1 and not V["ex.mvs.surface.success"]
    return {"mvs_task": m, "api_task": a, "answers": answers}


def example_table(V: dict) -> str:
    """Table 3. Rows are numbered S1... (scene track) and C1... (call-list track) so that the
    text can cite them."""
    e = V
    scene = [
        (f"Reference: author chain {e['ex.auth_chain']}, author residue {e['ex.auth_number']}, {e['ex.color']} {e['ex.rep']}", "ex.mvs.right"),
        (f"The same residue named by label numbering (label chain {e['ex.label_chain']}, residue {e['ex.label_number']})", "ex.mvs.label"),
        (f"Number copied from the variant name and used as the author number ({e['ex.face_value_residue']}{e['ex.uniprot_position']})", "ex.mvs.face"),
        ("Right residue, drawn red", "ex.mvs.colour"),
        ("Right residue, plus a grey cartoon of the protein that the request does not ask for: context", "ex.mvs.context"),
        ("Wrong residue, plus the grey cartoon", "ex.mvs.face_context"),
        (f"Right residue, and the same {e['ex.color']} {e['ex.rep']} on its two neighbours "
         f"(residues {e['ex.neighbours_first']} to {e['ex.neighbours_last']}): spill", "ex.mvs.spill"),
        (f"The whole chain as {e['ex.color']} {e['ex.rep']}: spill", "ex.mvs.spill_chain"),
        (f"Right residue, plus {e['ex.other_rep']} on the same residue alone: extra on the target", "ex.mvs.extra"),
        (f"Right residue, plus {e['ex.other_rep']} on residues {e['ex.neighbours_first']} to "
         f"{e['ex.neighbours_last']}: context", "ex.mvs.other_rep_around"),
    ]
    calls = [
        (f"Reference: UniProt {e['ex.accession']} position {e['ex.uniprot_position']}, resolved by the viewer; "
         "the cartoon of the default view is left as it is", "ex.api.right"),
        (f"The same residue named by author numbering (chain {e['ex.auth_chain']}, residue {e['ex.auth_number']})", "ex.api.author"),
        (f"Number copied from the variant name and used as the author number ({e['ex.face_value_residue']}{e['ex.uniprot_position']})", "ex.api.face"),
        ("Right residue, drawn red", "ex.api.colour"),
        ("Load only, no further call", "ex.api.bare"),
    ]
    rows = ["| Row | Answer | F1 | Task success | Target score |",
            "|:--|:------------------------------------------|--:|:--|--:|"]
    names = {}
    for label, letter, block in (("Scene track", "S", scene), ("Call-list track", "C", calls)):
        rows.append(f"| | **{label}** | | | |")
        for i, (what, key) in enumerate(block, 1):
            names[key] = f"{letter}{i}"
            rows.append(f"| {letter}{i} | {what} | {V[key + '.f1']:.2f} | {'yes' if V[key + '.success'] else 'no'} "
                        f"| {V[key + '.target']:.2f} |")
    for key, row in names.items():      # the text cites rows by these numbers
        V[key.replace("ex.", "ex.row.", 1)] = row
    return "\n".join(rows) + "\n"


def si_example(ex: dict) -> str:
    """The running example as stored: both references, the accepted alternative, the pack."""
    m, a = T.public_form(ex["mvs_task"]), T.public_form(ex["api_task"])
    fence = "`" * 3

    def block(obj, lang="json"):
        text = obj if isinstance(obj, str) else json.dumps(obj, indent=1, ensure_ascii=False)
        return f"{fence}{lang}\n{text}\n{fence}"

    return "\n\n".join([
        f"**Request (both tracks).** {m['prompt']}",
        f"**Scene track, task `{m['id']}`: reference answer.**", block(m["reference"]),
        f"**Call-list track, task `{a['id']}`: reference answer.**", block(a["reference"]),
        f"**Call-list track: accepted answers** ({len(a['accepted'])}; the residue's own segment of the cartoon is recoloured "
        "as well, in the residue's colour or in the viewer's selection colour).",
        *[block(x) for x in a["accepted"]],
        "**Target** (the atoms the request is about, stored in label numbering on both tasks).",
        block(m["target"]),
        "**Grounding pack** (appended to the request only in the grounding-pack condition).",
        block(m["grounding"]["text"], "text"),
    ]) + "\n"


def si_prompts() -> str:
    """The two system prompts as sent, with the long vendored references left as slots."""
    fence = "`" * 4
    out = []
    for name, title in (("system_mvs.md", "Scene track"), ("system_api.md", "Call-list track")):
        text = (REPO / "prompts" / name).read_text(encoding="utf-8").rstrip()
        text = re.sub(r"\{\{(\w+)\}\}", r"<<\1>>", text)   # a slot; not a marker of paper/build.py
        out.append(f"**{title}: system prompt.**\n\n{fence}text\n{text}\n{fence}")
    from molbench import schema
    long = "`" * 5
    for slot, title, text in (
            ("MVS_REFERENCE", "Scene track: the format guide", runner.MVS_REFERENCE.read_text(encoding="utf-8")),
            ("SCHEMA_TEXT", "Call-list track: the format guide, first part (the list of actions)", schema.schema_text()),
            ("API_REFERENCE", "Call-list track: the format guide, second part (the reference of the viewer's calls)",
             runner.API_REFERENCE.read_text(encoding="utf-8"))):
        # "{{distance}}" in a guide is literal text of the format, not a marker of paper/build.py:
        # a zero-width space between the braces keeps the build from reading it as one.
        shown = text.rstrip().replace("{{", "{\u200b{")
        out.append(f"**{title}** (slot `<<{slot}>>`), {len(text.split()):,} words.\n\n{long}text\n{shown}\n{long}")
    return "\n\n".join(out) + "\n"


# --------------------------------------------------------------------------- #
def build() -> tuple[dict, dict[str, str]]:
    V: dict = {}
    corpus = T.load_corpus()
    c = corpus_values(V, corpus)
    held = set(jload(REPO / "data/panel/heldback.json"))
    entries = panel_values(V, c["used"])
    s = controls_values(V)
    october_values(V)
    pilot_values(V)
    study_values(V)
    models = plan_values(V)
    ex = example_values(V, c["by_id"])
    assert V["controls.mvs.n_entries"] == V["corpus.n_structures"]   # caption of Table 4
    files = {
        "table_corpus.md": corpus_table(V),
        "table_october_regrade.md": october_table(V),
        "table_example.md": example_table(V),
        "table_variants.md": variants_table(V),
        "table_clinical_groupings.md": clinical_groupings_table(V),
        "si_panel.md": si_panel_table(entries, c["used"], held),
        "si_controls.md": si_controls_table(s),
        "si_models.md": si_models_table(models),
        "si_templates.md": si_templates_table(c["orig"]),
        "si_example.md": si_example(ex),
        "si_prompts.md": si_prompts(),
        "table_october_models.md": october_models_table(),
        "example_task.json": json.dumps(
            {"scene_task": T.public_form(ex["mvs_task"]), "call_list_task": T.public_form(ex["api_task"]),
             "graded_answers": ex["answers"]}, indent=1, ensure_ascii=False) + "\n",
    }
    files.update(shape_tables(V, models))
    files["corpus_values.json"] = json.dumps(dict(sorted(V.items())), indent=1, ensure_ascii=False) + "\n"
    return V, files


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if a file is stale")
    args = ap.parse_args(argv)
    V, files = build()
    stale = [n for n, text in files.items()
             if not (GEN / n).exists() or (GEN / n).read_text(encoding="utf-8") != text]
    if args.check:
        for n in stale:
            print(f"stale: paper/generated/{n}", file=sys.stderr)
        print(f"{len(files)} files checked, {len(stale)} stale")
        return 1 if stale else 0
    for n, text in files.items():
        (GEN / n).write_text(text, encoding="utf-8")
    print(f"wrote {len(files)} files to {GEN.relative_to(REPO)} ({len(V)} values; {len(stale)} changed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
