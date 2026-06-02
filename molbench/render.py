"""
Component-2 renderer — MVS scene tree -> PNG, via headless Mol* (Playwright).

Drives a local HTML page that loads the pinned prebuilt Mol* viewer bundle, feeds
it the MVS state, waits for the structure to load, and captures Mol*'s own
viewport screenshot (which avoids the WebGL preserve-drawing-buffer pitfall).

Requires the `execute` extra and one-time setup:
    pip install -e ".[execute]"
    python scripts/fetch_molstar.py        # fetch the Mol* bundle
    playwright install chromium            # fetch the browser

This is deliberately outside the core/CI path (which stays browser-free).
"""

from __future__ import annotations

import base64
import json
import pathlib

from .mvs import extract_root

STATIC = pathlib.Path(__file__).resolve().parent / "static"
RENDER_HTML = STATIC / "render.html"

# Headless WebGL needs a software GL backend; these flags enable SwiftShader.
_GL_ARGS = [
    "--use-gl=angle",
    "--use-angle=swiftshader",
    "--enable-unsafe-swiftshader",
    "--ignore-gpu-blocklist",
    "--enable-webgl",
]


def to_mvs_state(scene: dict) -> str:
    """Wrap a scene (root node or {'root':...} or full state) into an .mvsj string."""
    root = extract_root(scene) or scene
    state = {
        "kind": "single",
        "root": root,
        "metadata": {"version": "1", "timestamp": "1970-01-01T00:00:00.000Z"},
    }
    return json.dumps(state)


def render_scene(scene: dict, out_png: str | pathlib.Path,
                 width: int = 800, height: int = 600,
                 timeout_ms: int = 40000) -> pathlib.Path:
    """Render an MVS scene to a PNG. Raises RuntimeError if Mol* reports a failure."""
    from playwright.sync_api import sync_playwright

    if not (STATIC / "molstar" / "molstar.js").exists():
        raise RuntimeError("Mol* bundle missing — run scripts/fetch_molstar.py")

    mvs = to_mvs_state(scene)
    out_png = pathlib.Path(out_png)
    with sync_playwright() as p:
        browser = p.chromium.launch(args=_GL_ARGS)
        page = browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(timeout_ms)
        page.goto(RENDER_HTML.as_uri())
        result = page.evaluate("(mvs) => window.renderMvs(mvs)", mvs)
        browser.close()

    if not result or not result.get("ok"):
        raise RuntimeError(f"render failed: {result and result.get('error')}")
    data_uri = result["png"]
    b64 = data_uri.split(",", 1)[1]
    out_png.write_bytes(base64.b64decode(b64))
    return out_png
