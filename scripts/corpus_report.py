#!/usr/bin/env python3
"""
Write CORPUS.md: what the corpus in ``tasks/`` holds, counted from the task files.

    uv run python scripts/corpus_report.py            # write CORPUS.md
    uv run python scripts/corpus_report.py --check    # fail if CORPUS.md is out of date
    uv run python scripts/corpus_report.py --json     # the numbers alone, as JSON

Every number in CORPUS.md comes from here: the files are read through
``molbench.tasks.load_corpus`` and counted. The prose that no script can count (the
rulings applied, the checks that were run and their results, known weaknesses) is kept
in ``data/corpus/corpus_notes.md`` and appended word for word. No network.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import Counter, defaultdict

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import grounding, manifest, tasks as T  # noqa: E402

OUT = REPO / "CORPUS.md"
NOTES = REPO / "data" / "corpus" / "corpus_notes.md"
HELDBACK = REPO / "data" / "panel" / "heldback.json"
TIER_NAMES = {"translation": "translation", "grounded": "grounded", "interactions": "interactions",
              "resolve": "resolve", "clinical": "clinical", "followup": "follow-up",
              "accept_set": "accept-set", "tool_only": "tool-only"}
DIRECTORIES = [
    ("tasks/mvs_generated", "MVS translation", "scripts/generate_mvs_tasks.py"),
    ("tasks/mvs_grounded", "MVS grounded", "scripts/generate_grounded_tasks.py"),
    ("tasks/mvs_interactions", "MVS interactions", "scripts/author_interaction_tasks.py"),
    ("tasks/mvs_resolve", "MVS resolve", "scripts/generate_resolve_tasks.py"),
    ("tasks/mvs_clinical`, `tasks/api_clinical", "clinical, both tracks", "scripts/generate_clinical_tasks.py"),
    ("tasks/mvs_followup`, `tasks/api_followup", "follow-up turns", "scripts/generate_followup_tasks.py"),
    ("tasks/mvs_accept`, `tasks/api_accept", "accept-set", "scripts/generate_accept_set_tasks.py"),
    ("tasks/api_calling`, `tasks/api_generated", "API translation and tool-only", "scripts/generate_api_tasks.py"),
    ("tasks/api_twins", "API twins of MVS translation and grounded tasks", "scripts/translate_mvs_to_api.py"),
    ("tasks/paraphrases", "terse and indirect phrasings", "scripts/generate_paraphrases.py"),
]


def call_forms(t: dict) -> list[str]:
    p = t["provenance"]
    forms = p.get("call_forms") or (p.get("twin") or {}).get("call_forms") or []
    # a form made of two rewrites is labelled "first; second": count each rewrite once
    return sorted({part for f in forms for part in f.split("; ")})


def numbers() -> dict:
    """Everything CORPUS.md states as a number, from the task files."""
    corpus = T.load_corpus()
    originals = [t for t in corpus if not t["paraphrase_of"]]
    paraphrases = [t for t in corpus if t["paraphrase_of"]]
    by_id = {t["id"]: t for t in corpus}
    held = sorted(json.loads(HELDBACK.read_text(encoding="utf-8")))
    panel = [e["id"] for e in grounding.panel()["entries"]]
    n: dict = {"files": len(corpus), "originals": len(originals), "paraphrases": len(paraphrases),
               "hash": manifest.corpus_hash(T.TASKS_DIR)}

    size: dict = {}
    for t in originals:
        size.setdefault(t["tier"], Counter())[(t["track"], t["split"])] += 1
    n["size"] = {tier: {f"{track}_{split}": c[(track, split)] for track in T.TRACKS
                        for split in ("public", "heldback")} for tier, c in size.items()}
    n["by_track"] = dict(Counter(t["track"] for t in originals))
    n["heldback_tasks"] = sum(t["split"] == "heldback" for t in originals)

    # templates
    fam = defaultdict(Counter)
    for t in originals:
        fam[(t["track"], t["tier"])][t["family"]] += 1
    n["families"] = len({t["family"] for t in originals})
    n["largest_family_share"] = {
        f"{track} {tier}": {"family": c.most_common(1)[0][0], "tasks": c.most_common(1)[0][1],
                            "of": sum(c.values()),
                            "share": round(c.most_common(1)[0][1] / sum(c.values()), 3)}
        for (track, tier), c in sorted(fam.items())}
    api_tr = [t for t in originals if t["track"] == "api" and t["tier"] == "translation"]
    n["api_translation"] = {
        "curated": sum("api_calling" in t["_path"] for t in api_tr),
        "generated": sum("api_generated" in t["_path"] for t in api_tr),
        "twins": sum(bool(t["twin_of"]) for t in api_tr)}

    # structures
    used = Counter()
    per_tier = Counter()
    for t in originals:
        for s in t["structures"][:1]:
            used[s] += 1
            per_tier[(t["track"], t["tier"], s)] += 1
    n["structures_used"] = len(used)
    n["panel"] = len(panel)
    n["panel_not_used"] = sorted(set(panel) - set(used))
    n["no_structure"] = sorted(t["id"] for t in originals if not t["structures"])
    top = max(per_tier.values())
    n["max_per_structure_tier_track"] = {"tasks": top, "where": sorted(
        f"{track} {tier} {s.upper()}" for (track, tier, s), c in per_tier.items() if c == top)}
    hi, lo = max(used.values()), min(used.values())
    n["most_used"] = {"tasks": hi, "structures": sorted(s.upper() for s, c in used.items() if c == hi)}
    n["least_used"] = {"tasks": lo, "structures": sorted(s.upper() for s, c in used.items() if c == lo)}
    n["heldback_structures"] = [s.upper() for s in held]
    n["heldback_structure_in_public_task"] = sorted(
        t["id"] for t in corpus if t["split"] == "public" and set(t["structures"]) & set(held))
    n["heldback_share_of_tasks"] = round(n["heldback_tasks"] / len(originals), 3)

    # twins
    mvs = [t for t in originals if t["track"] == "mvs"]
    twinned = [t for t in mvs if t["twin_of"]]
    n["twins"] = {"mvs_tasks": len(mvs), "with_twin": len(twinned),
                  "by_tier": dict(Counter(t["tier"] for t in twinned))}
    translator = [t for t in originals if "api_twins" in t["_path"]]
    need_hide = [t for t in translator if t["provenance"]["difficulty"].get("context_switched_off")]
    n["twins"]["by_translator"] = len(translator)
    n["twins"]["translator_twins_with_a_hide_toggle"] = len(need_hide)
    n["twins"]["of_those_accepting_a_list_without_the_toggle"] = sum(bool(call_forms(t)) for t in need_hide)
    n["twins"]["no_twin_by_tier"] = dict(Counter(t["tier"] for t in mvs if not t["twin_of"]))

    # unstated attributes: accepted call forms on the API track
    forms = Counter()
    with_forms = 0
    for t in originals:
        if t["track"] == "api" and t["tier"] != "accept_set" and call_forms(t):
            with_forms += 1
            forms.update(call_forms(t))
    n["api_call_forms"] = {"tasks": with_forms, "forms": dict(forms)}
    n["mvs_single_turn_with_an_unstated_colour"] = sum(
        1 for t in mvs if not t["context"] and '"kind": "representation"' in json.dumps(t["reference"])
        and _uncoloured(t["reference"]))

    # paraphrases
    requests = {tuple(sorted(filter(None, [t["paraphrase_of"], by_id[t["paraphrase_of"]]["twin_of"]])))
                for t in paraphrases}
    n["paraphrase"] = {
        "requests": len(requests), "originals": len({t["paraphrase_of"] for t in paraphrases}),
        "by_track_tier": {f"{track} {tier}": c for (track, tier), c in sorted(
            Counter((t["track"], t["tier"]) for t in paraphrases).items())},
        "of_accept_set": sum(t["tier"] == "accept_set" for t in paraphrases),
        "heldback": sum(t["split"] == "heldback" for t in paraphrases)}

    # follow-ups
    fu = [t for t in originals if t["context"]]
    n["followup"] = {track: {"tasks": sum(t["track"] == track for t in fu),
                             "no_change": sum(t["track"] == track and t["context"]["noop"] for t in fu)}
                     for track in T.TRACKS}
    n["followup"]["twinned"] = sum(t["track"] == "mvs" and bool(t["twin_of"]) for t in fu)
    n["followup"]["no_change_kinds"] = dict(Counter(
        t["provenance"]["noop_kind"] for t in fu if t["context"]["noop"]))

    # accept-set
    acc = [t for t in originals if t["tier"] == "accept_set"]
    n["accept_set"] = {track: sum(t["track"] == track for t in acc) for track in T.TRACKS}
    n["accept_set"]["readings"] = {
        # an API state label is "<reading>; <call form>": a reading is counted once
        track: sum(len({str(x).split(";")[0] for x in t["provenance"]["accepted_states"]})
                   for t in acc if t["track"] == track)
        for track in T.TRACKS}
    n["accept_set"]["final_states"] = {
        track: sum(1 + len(t["accepted"]) for t in acc if t["track"] == track) for track in T.TRACKS}
    others = [t for t in originals if t["tier"] != "accept_set" and t["accepted"]]
    why = Counter()
    for t in others:
        why["resolve: other namings of the same drawing" if t["tier"] == "resolve"
            else "API clinical twins: the residue's own stretch of cartoon" if t["tier"] == "clinical"
            else "API call forms (unstated attributes)" if call_forms(t)
            else "other equivalents an API generator lists"] += 1
    n["accept_set"]["other_tasks_with_accepted"] = {"tasks": len(others), "why": dict(why)}

    # clinical
    clin = [t for t in originals if t["tier"] == "clinical" and t["track"] == "mvs"]
    c = [t["provenance"]["clinical"] for t in clin]
    d = [x["difficulty"] for x in c]
    pairs = [x for x in c if x["pair"]]
    offset_pairs = Counter(x["gene"] for x in pairs
                           if x["pair"]["this_structure"] == "author numbers differ from UniProt numbers")
    mature_pairs = Counter(x["gene"] for x in pairs
                           if x["pair"]["this_structure"] == "author numbers are the mature-protein numbers")
    control_pairs = Counter(x["gene"] for x in pairs
                            if x["pair"]["this_structure"].startswith("author numbers are UniProt numbers; three"))
    by_clin_id = {t["id"]: t for t in clin}
    n["clinical"] = {
        "tasks_per_track": len(clin),
        "proteins": len({x["accession"] for x in c}),
        "structures": len({t["structures"][0] for t in clin}),
        "heldback_structures": len({t["structures"][0] for t in clin if t["split"] == "heldback"}),
        "difficulty": {k: dict(Counter(str(x.get(k)) for x in d)) for k in sorted({k for x in d for k in x})},
        "mature_numbering_names": sum(x["naming"] == "legacy" for x in c),
        "offset_pairs": dict(offset_pairs), "mature_numbering_pairs": dict(mature_pairs),
        "no_offset_control_pairs": dict(control_pairs),
        "pairs_across_the_split": sorted(
            t["id"] for t in clin if t["provenance"]["clinical"]["pair"]
            and by_clin_id[t["provenance"]["clinical"]["pair"]["with"]]["split"] != t["split"]),
        "reported_apart": sum(bool(x["report_apart"]) for x in c),
        "reported_apart_families": sorted({t["family"] for t in clin
                                           if t["provenance"]["clinical"]["report_apart"]}),
    }

    # two examples per tier (the first two ids of the tier's two largest MVS templates,
    # or API templates where the tier has no MVS task)
    examples = {}
    for tier in T.TIERS:
        pool = [t for t in originals if t["tier"] == tier and t["split"] == "public"]
        track = "mvs" if any(t["track"] == "mvs" for t in pool) else "api"
        pool = sorted((t for t in pool if t["track"] == track), key=lambda t: t["id"])
        fams = [f for f, _ in Counter(t["family"] for t in pool).most_common()]
        picked = [next(t for t in pool if t["family"] == f) for f in fams[:2]]
        examples[tier] = [{"id": t["id"], "prompt": t["prompt"],
                           "start": bool(t["context"]), "accepted": len(t["accepted"])} for t in picked]
    n["examples"] = examples
    return n


def _uncoloured(tree) -> bool:
    """True if some representation node of an MVS reference has no colour child."""
    if isinstance(tree, dict):
        if tree.get("kind") == "representation" and not any(
                c.get("kind") == "color" for c in tree.get("children", [])):
            return True
        return any(_uncoloured(v) for v in tree.values())
    if isinstance(tree, list):
        return any(_uncoloured(v) for v in tree)
    return False


def _count(counter: dict, key: str) -> int:
    return int(counter.get(key, 0))


def render(n: dict) -> str:
    L: list[str] = []
    add = L.append
    add("# The MolBench corpus")
    add("")
    add("Written by `scripts/corpus_report.py`; do not edit. Every number below is counted from "
        "the task files through `molbench.tasks.load_corpus()`; the sections after \"Rulings "
        "applied\" are `data/corpus/corpus_notes.md`, word for word. Format: `TASK_FORMAT.md`. "
        "Grading: `GRADING.md`. Each tier directory has its own generated `README.md` with "
        "templates and how each reference is derived.")
    add("")
    add("**Not frozen yet.** The manifest names the corpus version and pins the hash at the freeze. "
        f"Hash of `tasks/` on disk now: `{n['hash']}`.")
    add("")
    add("## Size")
    add("")
    add(f"{n['files']} task files: **{n['originals']} original tasks** ({n['by_track']['mvs']} MVS, "
        f"{n['by_track']['api']} API) and **{n['paraphrases']} paraphrases** of "
        f"{n['paraphrase']['originals']} of them.")
    add("")
    add("Original tasks by track, tier and split (public / held back):")
    add("")
    add("| tier | MVS public | MVS held back | MVS total | API public | API held back | API total |")
    add("|---|---:|---:|---:|---:|---:|---:|")
    tot = Counter()
    for tier in T.TIERS:
        s = n["size"].get(tier)
        if not s:
            continue
        cells = []
        for track in T.TRACKS:
            pub, hb = s[f"{track}_public"], s[f"{track}_heldback"]
            tot[f"{track}_public"] += pub
            tot[f"{track}_heldback"] += hb
            cells += ["–"] * 3 if pub + hb == 0 else [str(pub), str(hb), str(pub + hb)]
        add(f"| {TIER_NAMES[tier]} | " + " | ".join(cells) + " |")
    add("| **all** | " + " | ".join(
        f"**{v}**" for track in T.TRACKS for v in (tot[f"{track}_public"], tot[f"{track}_heldback"],
                                                    tot[f"{track}_public"] + tot[f"{track}_heldback"])) + " |")
    add("")
    a = n["api_translation"]
    add(f"- The API translation tier is {a['curated'] + a['generated']} tasks written for the API "
        f"({a['curated']} curated, {a['generated']} generated) plus {a['twins']} twins of MVS "
        "translation tasks. The API grounded tier is twins only.")
    add("- Paraphrases (all public): " + "; ".join(f"{k} {v}" for k, v in n["paraphrase"]["by_track_tier"].items()) + ".")
    add(f"- {n['families']} templates (\"families\"). Largest template share per track and tier: " + "; ".join(
        f"{k} `{v['family']}` {v['tasks']} of {v['of']} ({v['share']:.0%})"
        for k, v in n["largest_family_share"].items()) + ".")
    add("")
    add("Where the files are:")
    add("")
    add("| directory | what | written by |")
    add("|---|---|---|")
    for d, what, script in DIRECTORIES:
        add(f"| `{d}` | {what} | `{script}` |")
    add("")
    add("## Structures")
    add("")
    add(f"- **{n['structures_used']} structures** are used, of the frozen panel of {n['panel']} "
        f"(`data/panel`). Not used: {', '.join(s.upper() for s in n['panel_not_used']) or 'none'} "
        "(1HSG is the API prompt's worked example).")
    m = n["max_per_structure_tier_track"]
    add(f"- **Reuse.** Within one tier of one track no structure is in more than {m['tasks']} tasks "
        f"(reached by {', '.join(m['where'])}). Over the whole corpus (both tracks, all tiers, "
        f"paraphrases not counted) the most used are {', '.join(n['most_used']['structures'])} with "
        f"{n['most_used']['tasks']} tasks each; the least used are "
        f"{', '.join(n['least_used']['structures'])} with {n['least_used']['tasks']}.")
    add(f"- {len(n['no_structure'])} API tasks name no single structure "
        f"({', '.join('`' + i + '`' for i in n['no_structure'])}).")
    add(f"- **Held back: {len(n['heldback_structures'])} structures**, one list for the whole corpus "
        f"(`data/panel/heldback.json`): {', '.join(n['heldback_structures'])}. "
        f"Public tasks on a held-back structure: {len(n['heldback_structure_in_public_task'])}. "
        f"{n['heldback_tasks']} original tasks are held back ({n['heldback_share_of_tasks']:.0%}).")
    add("")
    add("## Special kinds")
    add("")
    t = n["twins"]
    add(f"- **Twins.** {t['with_twin']} of the {t['mvs_tasks']} MVS tasks "
        f"({t['with_twin'] / t['mvs_tasks']:.0%}) have an API twin with the same prompt and the same "
        "target atoms: " + ", ".join(f"{TIER_NAMES[k]} {v}" for k, v in sorted(t["by_tier"].items())) +
        f". {t['by_translator']} of them were written by the translator; "
        f"{t['translator_twins_with_a_hide_toggle']} of those set a hide toggle "
        "(`provenance.difficulty.context_switched_off`), and "
        f"{t['of_those_accepting_a_list_without_the_toggle']} of these also accept the list without "
        "it, because the request never asks for anything to be hidden. MVS tasks without a twin: " +
        ", ".join(f"{TIER_NAMES[k]} {v}" for k, v in sorted(t["no_twin_by_tier"].items())) + ".")
    f = n["api_call_forms"]
    add(f"- **Unstated attributes.** {f['tasks']} API tasks outside the accept-set tier list accepted "
        "call forms for what their request leaves open (`scripts/api_forms.py`): " +
        "; ".join(f"{k}: {v}" for k, v in sorted(f["forms"].items())) +
        f". On the MVS track the grader does it: {n['mvs_single_turn_with_an_unstated_colour']} "
        "single-turn references draw something with no colour node, and there any colour is right.")
    p = n["paraphrase"]
    add(f"- **Paraphrases.** {p['requests']} requests (a twin pair is one request), seeded, public "
        f"split only ({p['heldback']} held back), none of an accept-set task ({p['of_accept_set']}); "
        "each has the full, a terse and an indirect phrasing, written by hand and checked by rule. "
        f"{n['paraphrases']} new task files.")
    fu = n["followup"]
    add(f"- **Follow-ups.** {fu['mvs']['tasks']} MVS and {fu['api']['tasks']} API two-turn tasks "
        f"({fu['twinned']} twinned). {fu['mvs']['no_change']} MVS and {fu['api']['no_change']} API are "
        "\"no change\" tasks, where the start state returned unchanged is the right answer (" +
        ", ".join(f"{k}: {v}" for k, v in sorted(fu["no_change_kinds"].items())) + "; none is a question).")
    ac = n["accept_set"]
    o = ac["other_tasks_with_accepted"]
    add(f"- **Accept-set.** {ac['mvs']} MVS and {ac['api']} API tasks where the request leaves one "
        f"countable thing open. They hold {ac['readings']['mvs']} MVS and {ac['readings']['api']} API "
        f"*readings* (`provenance.accepted_states`); as final states, counting API call forms, "
        f"{ac['final_states']['mvs']} and {ac['final_states']['api']}. The paper counts readings. "
        f"Besides these, {o['tasks']} other tasks list accepted alternatives and are not accept-set "
        "tasks: " + "; ".join(f"{k}: {v}" for k, v in sorted(o["why"].items())) + ".")
    c = n["clinical"]
    dd = c["difficulty"]
    add(f"- **Clinical tier** ({c['tasks_per_track']} tasks per track, {c['proteins']} proteins, "
        f"{c['structures']} structures, {c['heldback_structures']} of them held back):")
    for key, words in (("needs_numbering_offset", "target residue's author number differs from its UniProt number"),
                       ("author_chain_differs_from_label_chain", "target's author chain id differs from its label chain id"),
                       ("insertion_code", "a target has an insertion code"),
                       ("number_in_name_as_author_number_is_right",
                        "an answer that uses the number in the variant name as the author residue number is right")):
        if key in dd:
            yes = _count(dd[key], "True")
            add(f"  - {words}: **{yes} of {c['tasks_per_track']}** ({yes / c['tasks_per_track']:.0%});")
    add(f"  - {c['mature_numbering_names']} names are in mature-protein numbering;")
    add("  - offset pairs (the same variant on a structure whose author numbers differ from UniProt "
        "and on one numbered as UniProt): " +
        ", ".join(f"{g} {k}" for g, k in sorted(c["offset_pairs"].items())) +
        f" ({len(c['offset_pairs'])} proteins); mature-numbering pair: " +
        (", ".join(f"{g} {k}" for g, k in sorted(c["mature_numbering_pairs"].items())) or "none") +
        "; no-offset control pairs: " +
        (", ".join(f"{g} {k}" for g, k in sorted(c["no_offset_control_pairs"].items())) or "none") +
        f"; pairs with one side held back: {len(c['pairs_across_the_split'])};")
    add(f"  - {c['reported_apart']} tasks per track ({', '.join('`' + x + '`' for x in c['reported_apart_families'])}) "
        "are flagged `provenance.clinical.report_apart`: they need the entry's own helix or strand "
        "records, which only the grounding pack states, and are reported apart from the tier.")
    add("")
    add("## Two example tasks per tier")
    add("")
    for tier in T.TIERS:
        ex = n["examples"].get(tier)
        if not ex:
            continue
        add(f"**{TIER_NAMES[tier].capitalize()}**")
        for e in ex:
            extra = ("; with a start state" if e["start"] else "") + \
                    (f"; {e['accepted']} accepted alternative(s)" if e["accepted"] else "")
            add(f"- `{e['id']}`: \"{e['prompt']}\"{extra}")
        add("")
    add(NOTES.read_text(encoding="utf-8").rstrip("\n"))
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="write nothing; fail if CORPUS.md would change")
    ap.add_argument("--json", action="store_true", help="print the numbers as JSON and stop")
    a = ap.parse_args(argv)
    n = numbers()
    if a.json:
        print(json.dumps(n, indent=1))
        return 0
    text = render(n)
    if a.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print("CORPUS.md is out of date: run scripts/corpus_report.py")
            return 1
        print("CORPUS.md is up to date")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} ({n['files']} task files, {n['originals']} originals)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
