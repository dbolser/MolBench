#!/usr/bin/env python3
"""
Drill into an archived run — the forensic companion to the leaderboard.

Filters the per-sample raw outputs stored in a `runs/run_*.json` archive so you can
read exactly what a model emitted, e.g. to diagnose why it scored low or whether a
failure was a capability gap vs a formatting slip.

    python scripts/inspect_run.py                         # latest run, summary
    python scripts/inspect_run.py --model qwen --max-f1 0.5 --show raw
    python scripts/inspect_run.py runs/run_2026...Z.json --task clinvar --show predicted
"""

from __future__ import annotations

import argparse
import glob
import json
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
RUNS = REPO / "runs"


def latest_archive() -> str:
    files = sorted(glob.glob(str(RUNS / "run_*.json")))
    if not files:
        raise SystemExit("no archives in runs/ — run the harness first (archiving is on by default)")
    return files[-1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("archive", nargs="?", help="run archive (default: latest in runs/)")
    ap.add_argument("--model", default="", help="substring filter on model name")
    ap.add_argument("--task", default="", help="substring filter on task id")
    ap.add_argument("--min-f1", type=float, default=0.0)
    ap.add_argument("--max-f1", type=float, default=1.0)
    ap.add_argument("--show", choices=["none", "raw", "predicted"], default="none",
                    help="also print each sample's raw text or parsed prediction")
    args = ap.parse_args()

    path = args.archive or latest_archive()
    data = json.loads(pathlib.Path(path).read_text())
    meta = data.get("meta", {})
    print(f"# {path}\n# {meta.get('started_at')}  commit {(meta.get('git_commit') or '?')[:8]}  "
          f"models={meta.get('models')}\n")

    for model, tasks in data.get("raw_samples", {}).items():
        if args.model.lower() not in model.lower():
            continue
        shown_model = False
        for tid, samples in tasks.items():
            if args.task.lower() not in tid.lower():
                continue
            for i, s in enumerate(samples):
                f1 = s.get("f1")
                if f1 is None or not (args.min_f1 <= f1 <= args.max_f1):
                    continue
                if not shown_model:
                    print(f"=== {model} ===")
                    shown_model = True
                err = f"  ERROR={s['error']}" if s.get("error") else ""
                print(f"  {tid:<26} sample {i}  f1={f1:.2f}{err}")
                if args.show == "raw" and s.get("raw"):
                    print("    raw:", s["raw"][:600].replace("\n", "\n    "))
                elif args.show == "predicted" and s.get("predicted") is not None:
                    print("    predicted:", json.dumps(s["predicted"])[:600])


if __name__ == "__main__":
    main()
