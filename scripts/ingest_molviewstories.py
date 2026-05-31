#!/usr/bin/env python3
"""
Ingest MolViewStories example scenes into MVS benchmark tasks.

Source: github.com/molstar/mol-view-stories  (webapp/public/examples/*/story.mvsj).
Each story is a "multiple"-state MVS file: an ordered list of snapshots, each with
its own scene tree (`root`) and an educational caption (`metadata.title` +
`metadata.description`). We emit one task per snapshot:

    prompt        <- cleaned title + description (the human narrative)
    reference_mvs <- the snapshot's scene tree
    categories    <- derived from the tree (molbench.mvs.categorize)

CAVEAT (printed in the summary): these captions are *educational narrative*, not
imperative visualization commands, so many are under-determined — a perfect model
need not reproduce the exact tree. They are valuable as (a) realistic curated
reference scenes and (b) category coverage for the leaderboard drill-down, but
prompt curation is a follow-up before they belong in a headline score.

    python scripts/ingest_molviewstories.py
"""

from __future__ import annotations

import json
import pathlib
import re
import urllib.request

from molbench.mvs import categorize, extract_root

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "molviewstories"
RAW = ("https://raw.githubusercontent.com/molstar/mol-view-stories/main/"
       "%40mol-view-stories/webapp/public/examples/{}/story.mvsj")

# Every story that ships a .mvsj. These are stored as (caption, scene) pairs for
# **Component 2** (VLM-judged), NOT as Component-1 tree-match tasks: experiment
# showed the captions are under-determined for exact-tree grading (a perfect model
# can't recover unspecified file variants, colours, labels, camera). They make
# excellent VLM rubrics once the render path is wired. See commit notes for the
# triage evidence.
STORIES = ["simple", "mvs-examples", "alphafind", "kinase", "tbp"]


def fetch_story(name: str) -> dict | None:
    try:
        with urllib.request.urlopen(RAW.format(name), timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001 - report and skip a story we can't fetch
        print(f"  ! {name}: fetch failed ({e})")
        return None


def clean_caption(title: str, desc: str) -> str:
    """Turn a markdown caption into a one-line prompt."""
    text = f"{title}. {desc}" if title else desc
    text = re.sub(r"[#*_`>\[\]]", "", text)          # strip markdown punctuation
    text = re.sub(r"\s+", " ", text).strip()
    # First two sentences keep it focused.
    parts = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(parts[:2])[:300].strip()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("story-*.json"):  # keep the dir in sync with STORIES
        stale.unlink()
    written = 0
    cat_counts: dict[str, int] = {}
    for story in STORIES:
        data = fetch_story(story)
        if not data:
            continue
        snapshots = data.get("snapshots") or []
        kept = 0
        for i, snap in enumerate(snapshots):
            root = extract_root(snap) or snap.get("root")
            if not isinstance(root, dict) or not (root.get("children")):
                continue
            md = snap.get("metadata", {}) or {}
            prompt = clean_caption(md.get("title", ""), md.get("description", ""))
            if not prompt:
                continue
            cats = categorize(root)
            for c in cats:
                cat_counts[c] = cat_counts.get(c, 0) + 1
            doc = {
                "id": f"story-{story}-{i:02d}",
                "kind": "scene",              # Component-2 data, not a graded C1 task
                "source": "molviewstories",
                "story": story,
                "title": md.get("title", ""),
                "caption": prompt,            # the rubric text for VLM judging
                "scene_mvs": root,            # the reference scene to render
                "categories": cats,
            }
            (OUT / f"{doc['id']}.json").write_text(json.dumps(doc, indent=2))
            kept += 1
            written += 1
        print(f"  {story}: {kept}/{len(snapshots)} snapshots -> tasks")

    print(f"\nwrote {written} tasks to {OUT.relative_to(REPO)}")
    print("category coverage:", dict(sorted(cat_counts.items(), key=lambda x: -x[1])))


if __name__ == "__main__":
    main()
