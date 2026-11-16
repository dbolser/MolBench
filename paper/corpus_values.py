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
    "grounded": "The request names a feature (the ligand, the disulfides); its atoms must be found in the structure.",
    "interactions": "Named atoms and a measurement or contact between them.",
    "resolve": "The structure is named by protein, not by identifier.",
    "clinical": "A variant in UniProt numbering must be mapped to the residues of the structure.",
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
    return {"orig": orig, "para": para, "by_id": by_id, "used": used}


def corpus_table(V: dict) -> str:
    rows = ["| Tier | What is asked | Scene track (public + held back) | Call-list track (public + held back) | Pairs |",
            "|:---|:---|---:|---:|---:|"]
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
    return entries


def variants_table(V: dict) -> str:
    """The variant list step by step (Section 3.1)."""
    rows = ["| Step | Rule | Removed | Left |", "|:---|:---|---:|---:|",
            f"| 1 | Single-residue missense variants of the {V['panel.n_disease_proteins']} proteins that UniProt reports as "
            f"pathogenic or likely pathogenic, with ClinVar as a source | | {V['variants.n_candidates']:,} |",
            f"| 2 | Keep if a ClinVar variation record lists the same amino-acid change and its aggregate classification is "
            f"pathogenic, likely pathogenic or both | {V['variants.n_removed_by_clinvar']:,} | {V['variants.n_confirmed']:,} |",
            f"| 3a | Remove if the only such record belongs to another gene | {V['variants.n_other_gene_only']} | |",
            f"| 3b | Remove if the only such record is a haplotype (two changes on one chromosome) | {V['variants.n_haplotype_only']} | |",
            f"| 3c | Remove if every such record has the review status \"no assertion criteria provided\" "
            f"| {V['variants.n_no_criteria']} | {V['variants.n_usable']:,} |"]
    return "\n".join(rows) + "\n"


def si_panel_table(entries, used, held) -> str:
    rows = ["| Entry | Title (as deposited) | Method | Deposited | Atoms | Author numbering differs from UniProt | Split | Tasks |",
            "|:---|:---|:---|:---|---:|:---|:---|---:|"]
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
    V["controls.viewer.api.agree"] = a["agree"]
    V["controls.viewer.api.bare_loads"] = a["bare_loads"]["entries"]
    V["controls.viewer.api.bare_agree"] = a["bare_loads"]["agree"]
    c = jload(REPO / "tests/controls/colour_evidence.json")
    V["colour.tolerance"] = c["tolerance"]
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
                "|:---|:---|---:|---:|---:|"]
        for k in s["tracks"][track]["kinds"]:
            verdict = {"identical": "must pass (identical)", "equivalent": "must pass (equivalent)",
                       "wrong": "must fail (wrong)"}.get(k["group"], k["group"])
            out.append(f"| {verdict} | {k['what'].replace('|', '/')} | {k['n']} | {k['graded_success']} "
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
    rows = ["| Model | Weights | Valid answers | F1 (strict) | Task success (strict) | F1, valid-only | Task success, valid-only |",
            "|:---|:---|---:|---:|---:|---:|---:|"]
    for k, m in sorted(by_model.items(), key=lambda kv: (-kv[1]["success"], -kv[1]["new_f1"], kv[0])):
        name = alias.get(k, k).split("/")[-1]
        rows.append(f"| {name} | {weights.get(name, '?')} | {m['valid']} of {m['n']} | {m['new_f1']:.3f} "
                    f"| {m['success']:.1%} | {m['valid_only']['new_f1']:.3f} | {m['valid_only']['success']:.1%} |")
    return "\n".join(rows) + "\n"


def october_table(V: dict) -> str:
    rows = ["| Tier (October corpus) | Answers | Valid | F1, earlier grader | F1 | Task success | Requested part exactly right |",
            "|:---|---:|---:|---:|---:|---:|---:|"]
    for key, name in (("translation", "Translation"), ("grounded", "Structure-grounded, name resolution and interactions"),
                      ("clinical", "Clinical variant")):
        q = f"oct.spec.{key}"
        rows.append(f"| {name} | {V[q + '.n']} | {V[q + '.n_valid']} | {V[q + '.old_f1']:.3f} | {V[q + '.f1']:.3f} "
                    f"| {V[q + '.success']:.1%} | {V[q + '.highlight_exact']:.1%} of {V[q + '.highlight_n']} |")
    rows.append(f"| **All** | {V['oct.spec.n']} | {V['oct.spec.n_valid']} | {V['oct.spec.old_f1']:.3f} "
                f"| {V['oct.spec.f1']:.3f} | {V['oct.spec.success']:.1%} | |")
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
    return models


def shape_tables(V: dict, models: list[dict]) -> dict[str, str]:
    """The result tables in their final shape, every result cell pending."""
    P = PENDING
    names = [("Keyword script (no model)" if x["route"] == "baseline" else x["id"].split("/")[-1])
             + (" †" if x.get("optional") else "") for x in models]
    weights = ["–" if x["route"] == "baseline" else ("open" if x["open_weights"] else "closed") for x in models]
    out = {}
    head = ("| Model | Weights | Valid answers | F1 (strict) | Task success (strict) | Target score (strict) "
            "| F1, valid-only | Tasks with all 3 samples right | Cost (USD) |\n"
            "|:---|:---|---:|---:|---:|---:|---:|---:|---:|\n")
    # The review draft shows the first rows; the final table has one row per model (SI Table S6).
    shown = 3
    body = "".join(f"| {n} | {w} | {P} | {P} | {P} | {P} | {P} | {P} | {P} |\n"
                   for n, w in list(zip(names, weights))[:shown])
    body += f"| … {len(names) - shown} further rows, one per model of SI Table S6 | | {P} | | | | | | |\n"
    out["shape_leaderboard.md"] = head + body
    tiers = "| Tier | Tasks | Structures | F1 (strict) | Task success (strict) | Target score (strict) | Task success, valid-only |\n|:---|---:|---:|---:|---:|---:|---:|\n"
    for track, label in (("mvs", "Scene track"), ("api", "Call-list track")):
        for tier in TIERS:
            n = V[f"corpus.{track}.{tier}.n"]
            if n:
                tiers += f"| {label}: {TIER_NAME[tier]} | {n} | {P} | {P} | {P} | {P} | {P} |\n"
    out["shape_tiers.md"] = tiers
    out["shape_clinical.md"] = (
        "| Clinical tasks (scene track) | Tasks | Task success | Target score | Task success with grounding pack |\n"
        "|:---|---:|---:|---:|---:|\n"
        f"| **Split A** (primary): the number in the variant name is the author residue number | {V['clin.n_face_value_right']} | {P} | {P} | {P} |\n"
        f"| **Split A**: the number in the variant name is **not** the author residue number | {V['clin.n_face_value_wrong']} | {P} | {P} | {P} |\n"
        f"| **Split B**: target residue numbered as in UniProt | {V['clin.n_no_offset']} | {P} | {P} | {P} |\n"
        f"| **Split B**: target residue numbered differently from UniProt | {V['clin.n_offset']} | {P} | {P} | {P} |\n"
        f"| Helix or strand requested (a subset, reported apart) | {V['clin.n_sse']} | {P} | {P} | {P} |\n")
    lm = [n for n, x in zip(names, models) if x["route"] != "baseline"]
    out["shape_paired.md"] = (
        "| Model | Pairs | Target-right: both | Target-right: scene only | Target-right: call list only "
        "| Target-right: neither | McNemar p | Task success: both | Task success: scene only "
        "| Task success: call list only | Task success: neither | McNemar p |\n"
        "|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n"
        + "".join(f"| {n} | {V['corpus.n_twin_pairs']} | {P} | {P} | {P} | {P} | {P} | {P} | {P} | {P} | {P} | {P} |\n"
                  for n in lm[:2])
        + f"| … {len(lm) - 2} further rows, one per model | | {P} | | | | | | | | | |\n")
    out["shape_robustness.md"] = (
        "| Comparison | Tasks | Task success, first group | Task success, second group | Difference (95% interval) |\n"
        "|:---|---:|---:|---:|---:|\n"
        f"| Public split against held-back split (both tracks) | {V['corpus.public.n_tasks']} and {V['corpus.heldback.n_tasks']} | {P} | {P} | {P} |\n"
        f"| Full wording against terse wording | {V['corpus.n_requests_paraphrased']} requests ({V['corpus.n_tasks_paraphrased']} tasks) | {P} | {P} | {P} |\n"
        f"| Full wording against indirect wording | {V['corpus.n_requests_paraphrased']} requests ({V['corpus.n_tasks_paraphrased']} tasks) | {P} | {P} | {P} |\n"
        f"| Format reference against format reference plus JSON mode (the {V['plan.n_json_mode_models']} models that offer it; 1 sample in JSON mode) | {V['corpus.n_tasks']} | {P} | {P} | {P} |\n"
        f"| Format reference against format reference plus grounding pack (name-resolution and clinical tiers, scene track) "
        f"| {V['corpus.mvs.resolve.n'] + V['corpus.mvs.clinical.n']} | {P} | {P} | {P} |\n"
        f"| Format reference against no format reference ({V['plan.n_bare_models']} models, scene track) "
        f"| {V['corpus.mvs.n']} | {P} | {P} | {P} |\n")
    out["shape_followup.md"] = (
        "| Group | Scene track: tasks | Scene track: task success | Call-list track: tasks | Call-list track: task success |\n"
        "|:---|---:|---:|---:|---:|\n"
        f"| Follow-up turns that need a change | {V['corpus.mvs.followup.n'] - V['corpus.followup.mvs.noop']} | {P} "
        f"| {V['corpus.api.followup.n'] - V['corpus.followup.api.noop']} | {P} |\n"
        f"| Follow-up turns that need no change | {V['corpus.followup.mvs.noop']} | {P} | {V['corpus.followup.api.noop']} | {P} |\n"
        f"| Requests with several right answers | {V['corpus.mvs.accept_set.n']} | {P} | {V['corpus.api.accept_set.n']} | {P} |\n")
    return out


def si_models_table(models: list[dict]) -> str:
    rows = ["| Model identifier | Panel | Weights | Hidden reasoning by default | JSON mode | List price, USD per million tokens (input / output) | Price read on |",
            "|:---|:---|:---|:---|:---|:---|:---|"]
    for x in models:
        if x["route"] == "baseline":
            rows.append("| Keyword script | core | not a model | – | – | 0 / 0 | – |")
            continue
        p = x["price"]
        rows.append(f"| `{x['id']}` | {'optional' if x.get('optional') else 'core'} "
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
    rows = ["| Tier | Template | Scene tasks | Call-list tasks | Example request |", "|:---|:---|---:|---:|:---|"]
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
    assert all(cl["gene"] in recs[k]["genes"] and f"({var['hgvs']})" in recs[k]["title"] for k in var["clinvar_vcv"])
    V["ex.clinvar_classification"] = var["clinvar_classification"][0].lower()
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
    mvs_answers = {
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
    return {"mvs_task": m, "api_task": a, "answers": answers}


def example_table(V: dict) -> str:
    def row(what, key):
        return (f"| {what} | {V[key + '.f1']:.2f} | {'yes' if V[key + '.success'] else 'no'} "
                f"| {V[key + '.target']:.2f} |")
    e = V
    rows = ["| Answer | F1 | Task success | Target score |", "|:---|---:|:---|---:|",
            "| **Scene track** | | | |",
            row(f"Reference: author chain {e['ex.auth_chain']}, author residue {e['ex.auth_number']}, {e['ex.color']} {e['ex.rep']}", "ex.mvs.right"),
            row(f"The same residue named by label numbering (label chain {e['ex.label_chain']}, residue {e['ex.label_number']})", "ex.mvs.label"),
            row(f"Number in the variant name used as the author number ({e['ex.face_value_residue']}{e['ex.uniprot_position']})", "ex.mvs.face"),
            row("Right residue, drawn red", "ex.mvs.colour"),
            row("Right residue, plus a grey cartoon of the protein that the request does not ask for", "ex.mvs.context"),
            row("Wrong residue, plus the grey cartoon", "ex.mvs.face_context"),
            "| **Call-list track** | | | |",
            row(f"Reference: UniProt {e['ex.accession']} position {e['ex.uniprot_position']}, resolved by the viewer", "ex.api.right"),
            row(f"The same residue named by author numbering (chain {e['ex.auth_chain']}, residue {e['ex.auth_number']})", "ex.api.author"),
            row(f"Number in the variant name used as the author number ({e['ex.face_value_residue']}{e['ex.uniprot_position']})", "ex.api.face"),
            row("Right residue, drawn red", "ex.api.colour"),
            row("Load only, no further call", "ex.api.bare")]
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
        f"**Call-list track: accepted answers** ({len(a['accepted'])}; the residue's own stretch of cartoon is painted "
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
    files = {
        "table_corpus.md": corpus_table(V),
        "table_october_regrade.md": october_table(V),
        "table_example.md": example_table(V),
        "table_variants.md": variants_table(V),
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
