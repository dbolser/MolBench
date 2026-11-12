"""
MVS scene tree -> PNG via headless Mol* (Playwright), and Mol*'s own validity check.

``render_scene`` renders a scene as it is. ``render_framed`` / ``render_pair`` render
with a stated camera, so a reference and an answer can be pictured from the same
place, whole and framed on the target atoms (decision 24). ``molstar_issues`` asks
Mol* whether it would load a scene at all.

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


# --- renders framed on the target (decision 24) -----------------------------------
#
# Raters could not see a one-residue target in a whole-molecule view. So a pair of
# scenes (reference, answer) is rendered twice with **the same camera for both**:
# once showing everything, once framed on the target atoms. The camera is worked out
# once, on the reference, by Mol* itself from the coordinates of the target atoms
# (their bounding sphere, seen from outside the molecule: along the line from the
# structure's centre through the target), and that exact camera snapshot is then
# applied to the answer. Any ``focus`` or ``camera`` node in either scene is
# overridden, on purpose: the pictures are to be compared, so they must be taken from
# the same place.

_FRAMED_JS = r"""
async ({ mvs, rows, camera, extraRadius, minRadius }) => {
  try {
    const viewer = await molstar.Viewer.create('app', { layoutIsExpanded: false,
      layoutShowControls: false, layoutShowSequence: false, layoutShowLog: false,
      viewportShowExpand: false, viewportShowControls: false });
    const plugin = viewer.plugin;
    await viewer.loadMvsData(mvs, 'mvsj', { replaceExisting: true });
    const busy = plugin.behaviors.state.isBusy;
    const deadline = Date.now() + 60000;
    while (busy.value && Date.now() < deadline) await new Promise(r => setTimeout(r, 100));
    await new Promise(r => setTimeout(r, 600));
    const cam = plugin.canvas3d.camera;
    let framed = null;
    if (rows) {
      // the root structure: the one with the most atoms
      let root = null;
      for (const cell of plugin.state.data.cells.values()) {
        const s = cell.obj && cell.obj.data;
        if (s && s.units && s.elementCount !== undefined && (!root || s.elementCount > root.elementCount)) root = s;
      }
      if (!root) return { ok: false, error: 'no structure to frame on' };
      const want = new Set(rows);
      const p = [0, 0, 0];
      const pts = [];
      let cx = 0, cy = 0, cz = 0, n = 0;
      for (const unit of root.units) {
        if (!unit.model || !unit.model.atomicHierarchy) continue;
        const src = unit.model.atomicHierarchy.atomSourceIndex;
        for (let i = 0; i < unit.elements.length; i++) {
          const el = unit.elements[i];
          unit.conformation.position(el, p);
          cx += p[0]; cy += p[1]; cz += p[2]; n++;
          if (want.has(src.value(el))) pts.push([p[0], p[1], p[2]]);
        }
      }
      if (!pts.length) return { ok: false, error: 'none of the target atoms is in the structure' };
      const centre = [cx / n, cy / n, cz / n];
      const t = [0, 0, 0];
      for (const q of pts) { t[0] += q[0]; t[1] += q[1]; t[2] += q[2]; }
      t[0] /= pts.length; t[1] /= pts.length; t[2] /= pts.length;
      let radius = 0;
      for (const q of pts) radius = Math.max(radius, Math.hypot(q[0] - t[0], q[1] - t[1], q[2] - t[2]));
      radius = Math.max(radius + extraRadius, minRadius);
      // look at the target from outside: the view direction runs from the camera,
      // through the target, towards the structure's centre
      let dir = [centre[0] - t[0], centre[1] - t[1], centre[2] - t[2]];
      let len = Math.hypot(dir[0], dir[1], dir[2]);
      if (len < 1e-3) { dir = [0, 0, -1]; len = 1; }
      dir = dir.map(v => v / len);
      let up = Math.abs(dir[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0];
      const d = up[0] * dir[0] + up[1] * dir[1] + up[2] * dir[2];
      up = up.map((v, i) => v - d * dir[i]);
      const ul = Math.hypot(up[0], up[1], up[2]);
      up = up.map(v => v / ul);
      const focus = cam.getFocus(t, radius, up, dir);
      cam.setState(focus, 0);
      framed = { target: t, radius, n_atoms: pts.length, structure_centre: centre };
    } else if (camera) {
      cam.setState(camera, 0);
    }
    await new Promise(r => setTimeout(r, 400));
    const snap = cam.getSnapshot();
    const used = { mode: snap.mode, fov: snap.fov, position: Array.from(snap.position),
                   up: Array.from(snap.up), target: Array.from(snap.target), radius: snap.radius,
                   radiusMax: snap.radiusMax, fog: snap.fog, clipFar: snap.clipFar,
                   minNear: snap.minNear, minFar: snap.minFar };
    const png = await plugin.helpers.viewportScreenshot.getImageDataUri();
    return { ok: true, png, camera: used, framed };
  } catch (e) {
    return { ok: false, error: String(e && e.stack || e) };
  }
}
"""


def render_framed(scene: dict, out_png: str | pathlib.Path, *, rows: list[int] | None = None,
                  camera: dict | None = None, width: int = 800, height: int = 600,
                  extra_radius: float = 4.0, min_radius: float = 8.0,
                  timeout_ms: int = 120000) -> dict:
    """Render a scene with a stated camera and return what was used.

    ``rows``: atoms to frame on, as ``_atom_site`` row indices (the rows of the frozen
    atom table; ``rows_of`` turns a grader bitmask into them). Mol* works the camera out
    from their coordinates. ``camera``: a camera snapshot returned by an earlier call,
    applied as it is. With neither, the scene's own view is kept. Returns ``{"camera":
    the snapshot used, "framed": {target, radius, n_atoms} or None}``; pass ``camera``
    to the next call to take the second picture from the same place.
    """
    from playwright.sync_api import sync_playwright

    if not (STATIC / "molstar" / "molstar.js").exists():
        raise RuntimeError("Mol* bundle missing — run scripts/fetch_molstar.py")
    out_png = pathlib.Path(out_png)
    with sync_playwright() as p, p.chromium.launch(args=_GL_ARGS) as browser:
        page = browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(timeout_ms)
        page.goto(RENDER_HTML.as_uri())
        result = page.evaluate(_FRAMED_JS, {"mvs": to_mvs_state(scene), "rows": rows,
                                            "camera": camera, "extraRadius": extra_radius,
                                            "minRadius": min_radius})
    if not result or not result.get("ok"):
        raise RuntimeError(f"render failed: {result and result.get('error')}")
    out_png.write_bytes(base64.b64decode(result["png"].split(",", 1)[1]))
    return {"camera": result["camera"], "framed": result["framed"], "png": out_png}


def rows_of(mask: int) -> list[int]:
    """Atom-table row indices of a grader bitmask."""
    out, i = [], 0
    while mask:
        if mask & 1:
            out.append(i)
        mask >>= 1
        i += 1
    return out


def target_rows(task: dict) -> list[int] | None:
    """The rows to frame a task's renders on: its ``target`` atoms, or without a
    ``target`` every atom the reference draws in a way confined to part of the
    structure (falling back to everything it draws). MVS tasks only. None if the
    reference cannot be resolved on a frozen atom table."""
    from . import mvs
    scene = mvs.resolve_scene(task.get("reference_mvs"))
    if scene is None:
        return None
    for st in scene.structures.values():
        if st.table is None:
            continue
        atoms = mvs._target_atoms(task.get("target"), st)
        if atoms is None:
            everything = st.drawn_atoms()
            atoms = 0
            for m in st.draws.values():
                if m.bit_count() * 2 < everything.bit_count():   # a highlight, not the context
                    atoms |= m
            atoms = atoms or everything
        if atoms:
            return rows_of(atoms)
    return None


def render_pair(reference: dict, answer: dict, out_dir: str | pathlib.Path,
                rows: list[int] | None, width: int = 800, height: int = 600) -> dict:
    """The four pictures of a rating item, reference and answer **from the same
    camera**: ``ref_whole.png`` / ``answer_whole.png`` (the reference's whole-scene
    view) and, when ``rows`` is given, ``ref_target.png`` / ``answer_target.png`` (framed
    on those atoms), plus ``panel.png`` (whole view and target view side by side for
    both, if Pillow is installed). Returns the paths and the two cameras.

    An answer that fails to render leaves its pictures out and is reported under
    ``answer_error``; a failing reference raises.
    """
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    report: dict = {"files": {}}
    whole = render_framed(reference, out / "ref_whole.png", width=width, height=height)
    report["whole_camera"] = whole["camera"]
    report["files"]["ref_whole"] = str(out / "ref_whole.png")
    target = None
    if rows:
        target = render_framed(reference, out / "ref_target.png", rows=rows, width=width, height=height)
        report["target_camera"], report["framed"] = target["camera"], target["framed"]
        report["files"]["ref_target"] = str(out / "ref_target.png")
    try:
        render_framed(answer, out / "answer_whole.png", camera=whole["camera"], width=width, height=height)
        report["files"]["answer_whole"] = str(out / "answer_whole.png")
        if target is not None:
            render_framed(answer, out / "answer_target.png", camera=target["camera"],
                          width=width, height=height)
            report["files"]["answer_target"] = str(out / "answer_target.png")
    except Exception as e:  # noqa: BLE001 - the answer is a model's; say why it has no picture
        report["answer_error"] = str(e)
    try:
        from PIL import Image
    except ImportError:
        return report
    order = ["ref_whole", "ref_target", "answer_whole", "answer_target"]
    if all(k in report["files"] for k in order):
        tiles = [Image.open(report["files"][k]).convert("RGB") for k in order]
        w, h = tiles[0].size
        panel = Image.new("RGB", (2 * w + 6, 2 * h + 6), "white")
        for i, tile in enumerate(tiles):
            panel.paste(tile, ((i % 2) * (w + 6), (i // 2) * (h + 6)))
        panel.save(out / "panel.png")
        report["files"]["panel"] = str(out / "panel.png")
    return report


# Validity per Mol* itself: the tree rules (allowed parents, required and typed
# params) that decide whether Mol* will load a scene at all. The molviewspec
# library's validator is looser; on the 2026-10 runs it missed 37 of 39 scenes
# that Mol* rejected.
_ISSUES_JS = """(scenes) => scenes.map((s) => {
  try {
    const mvs = molstar.PluginExtensions.mvs.MVSData;
    return mvs.validationIssues(mvs.fromMVSJ(s)) || [];
  } catch (e) {
    return [String(e)];
  }
})"""


def molstar_issues(scenes: list[dict], timeout_ms: int = 60000) -> list[list[str]]:
    """Mol*'s validation messages for each scene (empty list = valid). No rendering,
    one browser for the whole batch."""
    from playwright.sync_api import sync_playwright

    if not scenes:
        return []
    if not (STATIC / "molstar" / "molstar.js").exists():
        raise RuntimeError("Mol* bundle missing — run scripts/fetch_molstar.py")
    with sync_playwright() as p, p.chromium.launch(args=_GL_ARGS) as browser:
        page = browser.new_page()
        page.set_default_timeout(timeout_ms)
        page.goto(RENDER_HTML.as_uri())
        return page.evaluate(_ISSUES_JS, [to_mvs_state(s) for s in scenes])
