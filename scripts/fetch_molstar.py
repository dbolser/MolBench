#!/usr/bin/env python3
"""
Fetch the prebuilt Mol* viewer bundle for the Component-2 renderer.

We do NOT vendor Mol*'s source (a submodule would force an npm build) — we fetch
its prebuilt, MVS-capable viewer bundle at a pinned version into a local static
dir, so rendering is reproducible and offline after one fetch, with no Node
toolchain. The bundle (MIT, Mol* contributors) is fetched, not rehosted.

    python scripts/fetch_molstar.py        # -> molbench/static/molstar/

Pin bump: change MOLSTAR_VERSION, re-fetch, and note it in the methods/run record.
"""

from __future__ import annotations

import pathlib
import urllib.request

MOLSTAR_VERSION = "5.9.0"
REPO = pathlib.Path(__file__).resolve().parent.parent
DEST = REPO / "molbench" / "static" / "molstar"
BASE = f"https://cdn.jsdelivr.net/npm/molstar@{MOLSTAR_VERSION}/build/viewer/"
FILES = ["molstar.js", "molstar.css"]


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for f in FILES:
        url = BASE + f
        out = DEST / f
        with urllib.request.urlopen(url, timeout=60) as r:
            out.write_bytes(r.read())
        print(f"  {f}: {out.stat().st_size // 1024} KB")
    (DEST / "VERSION").write_text(MOLSTAR_VERSION + "\n")
    print(f"fetched Mol* {MOLSTAR_VERSION} -> {DEST.relative_to(REPO)}")


if __name__ == "__main__":
    main()
