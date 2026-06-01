#!/usr/bin/env python3
"""
Merge model results from several scorecards into one.

Lets you run new models in a separate pass (e.g. a fresh set of OpenRouter models)
without re-spending on models you already scored, then combine everything into a
single leaderboard. Refuses to merge runs over a different corpus or sample count,
since blending those would make the comparison dishonest.

    python scripts/merge_scorecards.py BASE.json EXTRA1.json [EXTRA2.json ...] [-o OUT.json]
"""

from __future__ import annotations

import json
import pathlib
import sys


def merge(base_path: str, extra_paths: list[str], out: str | None = None) -> None:
    base = json.loads(pathlib.Path(base_path).read_text())
    for p in extra_paths:
        d = json.loads(pathlib.Path(p).read_text())
        if d.get("n_tasks") != base.get("n_tasks") or d.get("samples") != base.get("samples"):
            raise SystemExit(
                f"refusing to merge {p}: corpus/sample mismatch "
                f"({d.get('n_tasks')} tasks x{d.get('samples')} vs "
                f"{base.get('n_tasks')} x{base.get('samples')})")
        base.setdefault("models", {}).update(d.get("models", {}))
    out = out or base_path
    pathlib.Path(out).write_text(json.dumps(base, indent=2))
    print(f"merged -> {out}  ({len(base['models'])} models: {', '.join(base['models'])})")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "-o"]
    out = None
    if "-o" in sys.argv:
        i = sys.argv.index("-o")
        out = sys.argv[i + 1]
        args = [a for a in args if a != out]
    if len(args) < 2:
        raise SystemExit(__doc__)
    merge(args[0], args[1:], out)
