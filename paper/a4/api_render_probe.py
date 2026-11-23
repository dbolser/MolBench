#!/usr/bin/env python3
"""
Probe: can an API-track answer be pictured for a rater? (Not part of rating set a4-v2.)

Replays a task's reference call list and a model's call list in the real pdbe-molstar
3.3.2 (the headless viewer of scripts/check_api_refs.py), takes the reference's picture
from the viewer's own camera and the answer's picture from that same camera.

    uv run python paper/a4/api_render_probe.py results/pilot-v1/samples/spec/<model>.jsonl \\
        OUT_DIR tr-range-rows-3k34-api gr-attachment-1hrc-hec-api

What it showed on 2026-11-16 (two answers of the pilot run, software GL): both
references and both answers load and are drawn; the same camera works. What it does not
do: frame on the target atoms, set the white background of the scene-track pictures,
or cover calls the headless harness skips (it lists them under "notes"). It reaches
into check_api_refs.py's page script, so treat it as a probe, not a tool.
"""

from __future__ import annotations

import base64
import copy
import importlib.util
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(REPO / "scripts")]

_SHOT = """async (camera) => {
  const p = window.__v.plugin, cam = p.canvas3d.camera;
  if (camera) { cam.setState(camera, 0); await new Promise(r => setTimeout(r, 500)); }
  const s = cam.getSnapshot();
  const used = { mode: s.mode, fov: s.fov, position: Array.from(s.position), up: Array.from(s.up),
                 target: Array.from(s.target), radius: s.radius, radiusMax: s.radiusMax, fog: s.fog,
                 clipFar: s.clipFar, minNear: s.minNear, minFar: s.minFar };
  return { png: await p.helpers.viewportScreenshot.getImageDataUri(), camera: used };
}"""


def main(argv: list[str]) -> None:
    samples, out, wanted = pathlib.Path(argv[0]), pathlib.Path(argv[1]), argv[2:]
    spec = importlib.util.spec_from_file_location("check_api_refs", REPO / "scripts" / "check_api_refs.py")
    car = importlib.util.module_from_spec(spec)
    sys.modules["check_api_refs"] = car
    spec.loader.exec_module(car)
    from molbench import tasks

    hook = "const v = new PDBeMolstarPlugin();"
    if hook not in car._RUN_JS:
        raise SystemExit("check_api_refs.py's page script has changed; this probe needs updating")
    js = car._RUN_JS.replace(hook, hook + " window.__v = v;")
    corpus = {t["id"]: t for t in tasks.load_corpus()}
    rows = {r["task_id"]: r for r in map(json.loads, samples.read_text().splitlines()) if r["track"] != "mvs"}
    out.mkdir(parents=True, exist_ok=True)

    def shot(viewer, actions, path, camera=None):
        acts = copy.deepcopy(actions)
        for a in acts:
            if a.get("action") == "load":
                entry = car.ps.canonical_entry(a.get("molecule_id"), a.get("custom_data"))
                a["_url"] = f"/cif/{car.fetch_cif(entry, False).name}"
        page = viewer._browser.new_page(viewport={"width": 800, "height": 600})
        page.set_default_timeout(180000)
        try:
            page.goto(f"http://127.0.0.1:{viewer._server.server_address[1]}/")
            dump = page.evaluate(js, {"actions": acts})
            r = page.evaluate(_SHOT, camera)
            path.write_bytes(base64.b64decode(r["png"].split(",", 1)[1]))
            return r["camera"], dump
        finally:
            page.close()

    with car.Viewer() as viewer:
        for tid in wanted:
            s, task = rows[tid], corpus[tid]
            camera, ref = shot(viewer, task["reference"], out / f"{tid}-ref.png")
            _, ans = shot(viewer, s["predicted"], out / f"{tid}-out.png", camera)
            print(f"{tid}: success {s['success']}, target score {s['target_f1']}; reference loaded "
                  f"{ref.get('loaded')}, answer loaded {ans.get('loaded')}; calls not run in the viewer: "
                  f"{(ref.get('notes') or []) + (ans.get('notes') or []) or 'none'}")


if __name__ == "__main__":
    main(sys.argv[1:])
