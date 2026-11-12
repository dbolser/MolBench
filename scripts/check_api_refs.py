#!/usr/bin/env python3
"""
Check every API-track reference against the structure it talks about.

Default mode is offline and stdlib-only (it is what ``tests/test_api_refs.py`` runs).
For each task in ``tasks/api_calling`` it checks that

* the reference is schema-valid and replays with nothing ignored or unresolved;
* the structure has a frozen atom table (or the task is one of the two views that
  are compared by their settings: superposition, ligand view);
* every selection in the reference selects at least one atom;
* every selection listed under ``provenance.targets`` picks exactly the intended
  atoms. The intended atoms are written a second time, in author numbering *with the
  residue name* (``{"auth_asym_id": "A", "auth_seq_id": 57, "auth_comp_id": "HIS"}``),
  and resolved by ``molbench.atoms`` (the MVS resolver, itself checked against Mol*).
  So "His57" is checked to be a histidine, and a label/author mix-up cannot pass;
* every selection in the reference is covered by a target;
* every ``hide_*`` toggle hides a component the structure has;
* named colours are Mol* colour names;
* the reference and every ``accepted`` alternative grade as success, while a bare
  load and load + global style do not (unless the task has nothing else to do);
* the worked example in the prompt is not a benchmark task.

``--viewer`` adds the fidelity check: each reference (and each accepted alternative,
and the extra probes below) is run in the real pdbe-molstar 3.3.2 in headless
Chromium and the viewer's own answer is compared with the replay in
``molbench/pdbe_state.py``: the atoms of every selection, the default components
and which are hidden, the representation type and colour theme of each, the
overpaint colours, the added representations, the tooltips and the canvas colours.
Needs the ``execute`` extra, ``playwright install chromium``, the mmCIF files in
``data/cif`` (fetched from RCSB / AlphaFold DB if missing) and the pdbe-molstar
bundle (fetched from jsDelivr into ``molbench/static/molstar/pdbe-3.3.2`` if missing).

``--cif`` adds checks that need the mmCIF itself (gemmi): an ``assembly_id`` in a
reference names an assembly that exists and differs from the deposited model.

``--uniprot`` runs the fidelity check for ``uniprot_*`` selectors. The viewer maps
those with the SIFTS columns of the file it loaded, which only PDBe's "updated" mmCIF
carries, so these probes load that file (fetched into ``data/cif``) and compare the
viewer's atoms with the frozen SIFTS lookup behind
``pdbe_state.uniprot_residue_atoms``. Skipped, with a message, while that lookup is
not available.

    python scripts/check_api_refs.py            # offline checks
    python scripts/check_api_refs.py --viewer   # + real-viewer fidelity
    python scripts/check_api_refs.py --viewer --updated   # the same on PDBe's updated mmCIF
    python scripts/check_api_refs.py --uniprot  # + real-viewer fidelity of UniProt selectors
    python scripts/check_api_refs.py --cif      # + assembly checks
"""

from __future__ import annotations

import argparse
import copy
import http.server
import json
import pathlib
import re
import sys
import threading
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import pdbe_state as ps  # noqa: E402
from molbench import schema  # noqa: E402
from molbench.atoms import load_table  # noqa: E402

TASKS = REPO / "tasks" / "api_calling"
PROMPT = REPO / "prompts" / "system_api.md"
CIF_CACHE = REPO / "data" / "cif"
PDBE_VERSION = "3.3.2"
PDBE_DIR = REPO / "molbench" / "static" / "molstar" / f"pdbe-{PDBE_VERSION}"
PDBE_CDN = f"https://cdn.jsdelivr.net/npm/pdbe-molstar@{PDBE_VERSION}/build/"
PDBE_FILES = ("pdbe-molstar-plugin.js", "pdbe-molstar-light.css")
SELECTING = ("color", "focus", "highlight", "tooltips")


def load_api_tasks() -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(TASKS.glob("*.json"))]


def rows(mask: int) -> list[int]:
    out, i = [], 0
    while mask:
        if mask & 1:
            out.append(i)
        mask >>= 1
        i += 1
    return out


# --- offline checks ------------------------------------------------------------------

def check_task(task: dict) -> list[str]:
    """Problems with one task's reference (empty list = fine)."""
    bad: list[str] = []
    ref = task.get("reference")
    prov = task.get("provenance") or {}
    for key in ("derived", "checked_by", "structure"):
        if not prov.get(key):
            bad.append(f"provenance.{key} is missing")
    bad += [f"schema: {e}" for e in schema.validate_actions(ref)]
    if bad:
        return bad
    state = ps.replay(copy.deepcopy(ref))
    bad += [f"replay ignored: {m}" for m in state.log]
    bad += [f"unresolved: {m}" for m in state.unresolved]
    if not state.loaded:
        return bad + ["reference loads nothing"]
    if state.entry != prov.get("structure"):
        bad.append(f"provenance.structure {prov.get('structure')!r} != loaded {state.entry!r}")
    settings_only = state.options["superposition"] or state.ligand_view is not None
    if state.table is None and not settings_only:
        return bad + [f"no atom table for {state.entry}"]

    # selections: non-empty, and equal to the independently written intended atoms
    targets = {(t["action"], t["param"]): t for t in prov.get("targets", [])}
    table = state.table
    for ai, act in enumerate(ref):
        if act.get("action") not in SELECTING:
            continue
        for pi, param in enumerate(act["data"]):
            where = f"action[{ai}].data[{pi}]"
            if table is None:
                continue
            got = ps.resolve_param(table, param, state.entry)
            if not got:
                bad.append(f"{where}: selects no atoms")
            t = targets.pop((ai, pi), None)
            if t is None:
                bad.append(f"{where}: no provenance target says which atoms were meant")
                continue
            want = table.selector(t["atoms"])
            if want is None:
                bad.append(f"{where}: target atoms cannot be resolved")
            elif want != got:
                bad.append(f"{where}: selects {got.bit_count()} atoms, intended set "
                           f"({t.get('what')}) has {want.bit_count()}; "
                           f"{(want & got).bit_count()} in common")
            if t.get("n_atoms") != got.bit_count():
                bad.append(f"{where}: {got.bit_count()} atoms, provenance says {t.get('n_atoms')}")
    bad += [f"provenance target for missing selection action[{a}].data[{p}]" for a, p in targets]

    # hide toggles: the component must exist
    if table is not None and not settings_only:
        comps = state.components()
        for act in ref:
            if act.get("action") == "set_property" and act.get("name") in ps.HIDE_FLAGS \
                    and act.get("value"):
                if not any(c in comps for c in ps.HIDE_FLAGS[act["name"]]):
                    bad.append(f"{act['name']}: {state.entry} has no such component")

    # colour names must be ones the viewer knows
    for act in ref:
        for v in _colours(act):
            if isinstance(v, str) and not v.startswith("#") and v not in ps.COLOR_NAMES:
                bad.append(f"colour {v!r} is not a Mol* colour name")

    # grading: reference and alternatives succeed, trivial answers do not
    for i, alt in enumerate([ref] + list(task.get("accepted", []))):
        bad += [f"accepted[{i - 1}] schema: {e}" for e in schema.validate_actions(alt)] if i else []
        res = ps.grade_state(ref, alt)
        if not res["success"]:
            bad.append(f"{'reference' if not i else f'accepted[{i - 1}]'} does not grade as "
                       f"success (f1 {res['f1']})")
    n_facts = len(ps.grade_state(ref, ref)["reference_facts"])
    load = [a for a in ref if a.get("action") == "load"][:1]
    style = [a for a in ref if a.get("action") == "set_visual_style"][:1]
    if n_facts == 0:
        bad.append("the reference state is a bare load: the task asks for nothing the "
                   "viewer would show")
    bare = [{k: v for k, v in load[0].items() if k in ("action", "molecule_id", "custom_data")}]
    if ps.grade_state(ref, bare)["f1"] > 0:
        bad.append("a bare load scores above 0")
    has_selection = any(a.get("action") in SELECTING for a in ref)
    if has_selection and ps.grade_state(ref, load + style)["success"]:
        bad.append("load + style grades as success on a task with a selection")
    return bad


def _colours(act: dict):
    """Every colour value an action carries."""
    name = act.get("action")
    if name == "color" and act.get("non_selected_color") is not None:
        yield act["non_selected_color"]
    if name == "set_color":
        yield from (act[k] for k in ("highlight", "select") if act.get(k) is not None)
    if name == "highlight" and act.get("color") is not None:
        yield act["color"]
    if name == "set_property" and act.get("name") in ("highlight_color", "select_color"):
        yield act.get("value")
    for p in act.get("data") or []:
        yield from (p[k] for k in ("color", "representationColor") if p.get(k) is not None)


def check_prompt_example(tasks: list[dict]) -> list[str]:
    """The worked example in the system prompt must not be (the answer to) a task."""
    text = PROMPT.read_text()
    m = re.search(r"## Worked example.*?```json\s*(\[.*?\])\s*```", text, re.S)
    if not m:
        return ["system_api.md has no worked example to check"]
    example = json.loads(m.group(1))
    bad = [f"worked example schema: {e}" for e in schema.validate_actions(example)]
    state = ps.replay(copy.deepcopy(example))
    bad += [f"worked example: {m}" for m in state.log]
    if state.table is not None:     # the example's structure is reserved, so it may have no table
        for act in example:
            for p in act.get("data") or []:
                if not ps.resolve_param(state.table, p, state.entry):
                    bad.append(f"worked example: {json.dumps(p)} selects nothing")
    for task in tasks:
        res = ps.grade_state(task["reference"], example)
        if res["success"] or res.get("same_structure"):
            bad.append(f"{task['id']}: the prompt's worked example uses this task's structure"
                       + (" and solves it" if res["success"] else ""))
    return bad


# --- mmCIF checks (gemmi) ------------------------------------------------------------

def fetch_cif(entry: str, updated: bool = False) -> pathlib.Path:
    """The mmCIF of an entry, cached. ``updated``: PDBe's updated mmCIF (with SIFTS)."""
    CIF_CACHE.mkdir(parents=True, exist_ok=True)
    path = CIF_CACHE / (f"{entry}_updated.cif" if updated else f"{entry}.cif")
    if not path.exists():
        m = re.fullmatch(r"af-([a-z0-9]+)-f(\d+)", entry)
        url = (f"https://alphafold.ebi.ac.uk/files/AF-{m.group(1).upper()}-F{m.group(2)}-model_v6.cif"
               if m else f"https://www.ebi.ac.uk/pdbe/entry-files/download/{entry}_updated.cif"
               if updated else f"https://files.rcsb.org/download/{entry}.cif")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (generic-client)"})
        with urllib.request.urlopen(req, timeout=60) as r:
            path.write_bytes(r.read())
    return path


def check_assemblies(tasks: list[dict]) -> list[str]:
    import gemmi
    bad = []
    for task in tasks:
        state = ps.replay(copy.deepcopy(task["reference"]))
        if not state.assembly or state.table is None:
            continue
        st = gemmi.read_structure(str(fetch_cif(state.entry)))
        asm = next((a for a in st.assemblies if a.name == state.assembly), None)
        if asm is None:
            bad.append(f"{task['id']}: {state.entry} has no assembly {state.assembly!r}")
            continue
        n_ops = sum(len(g.operators) for g in asm.generators)
        label_chains = set(state.table.columns["label_asym_id"])
        covered = {c for g in asm.generators for c in g.subchains}
        if n_ops <= 1 and covered >= label_chains:
            bad.append(f"{task['id']}: assembly {state.assembly} of {state.entry} is the "
                       "deposited model, so asking for it tests nothing")
        if covered and not covered >= label_chains:
            bad.append(f"{task['id']}: assembly {state.assembly} leaves out chains "
                       f"{sorted(label_chains - covered)}; the replay does not model that")
    return bad


# --- the real viewer -----------------------------------------------------------------

_PAGE = b"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="/pdbe/pdbe-molstar-light.css">
<script src="/pdbe/pdbe-molstar-plugin.js"></script></head>
<body><div id="app" style="position:absolute;width:800px;height:600px"></div></body></html>"""

# Runs one action list in pdbe-molstar and reads the result back. The mapping from
# actions to viewer calls is the execution model documented in molbench/pdbe_state.py.
_RUN_JS = r"""
async ({ actions }) => {
  const f64 = new Float64Array(1), i32 = new Int32Array(f64.buffer);
  const each = (set, f) => {
    if (typeof set === 'number') { f64[0] = set; const a = i32[0], b = i32[1]; for (let i = a; i < b; i++) f(i); }
    else for (let i = 0; i < set.length; i++) f(set[i]);
  };
  const at = (set, i) => { if (typeof set === 'number') { f64[0] = set; return i32[0] + i; } return set[i]; };
  const uniq = (rows) => Array.from(new Set(rows)).sort((a, b) => a - b);
  const lociRows = (loci) => {
    const rows = [];
    if (!loci || loci.kind !== 'element-loci') return rows;
    for (const e of loci.elements) {
      const src = e.unit.model.atomicHierarchy.atomSourceIndex;
      each(e.indices, i => rows.push(src.value(at(e.unit.elements, i))));
    }
    return uniq(rows);
  };
  const structRows = (s) => {
    const rows = [];
    for (const unit of s.units) {
      const src = unit.model.atomicHierarchy.atomSourceIndex;
      each(unit.elements, el => rows.push(src.value(el)));
    }
    return uniq(rows);
  };
  const bundleRows = (s, bundle) => {
    const rows = [];
    for (const e of bundle.elements) {
      const idx = [];
      if (e.set) each(e.set, i => idx.push(i));
      if (e.ranges) for (let k = 0; k + 1 < e.ranges.length; k += 2) for (let i = e.ranges[k]; i <= e.ranges[k + 1]; i++) idx.push(i);
      for (const group of e.groupedUnits) each(group, uid => {
        const unit = s.unitMap.get(uid);
        const src = unit.model.atomicHierarchy.atomSourceIndex;
        for (const i of idx) rows.push(src.value(at(unit.elements, i)));
      });
    }
    return uniq(rows);
  };

  const v = new PDBeMolstarPlugin();
  const opts = { hideControls: true };
  const flags = {}; let spin; let loaded = false, spec = null;
  let highlightTrait = null, tooltipsTrait = null;
  const pending = [];
  const selections = [], notes = [];
  const HIDE = { hide_polymer: 'polymer', hide_water: 'water', hide_heteroatoms: 'het',
                 hide_carbs: 'carbs', hide_non_standard: 'nonStandard', hide_coarse: 'coarse' };
  const loadDone = () => new Promise(res => { const sub = v.events.loadComplete.subscribe(ok => { sub.unsubscribe(); res(ok); }); });
  const settle = async () => {
    const busy = v.plugin.behaviors.state.isBusy;
    for (let t = 0; busy.value && t < 400; t++) await new Promise(r => setTimeout(r, 50));
  };
  const reload = async () => {
    const done = loadDone();
    if (!loaded) { await v.render(document.getElementById('app'), opts); loaded = true; }
    else await v.visual.update({ ...opts }, true);
    const ok = await done;
    if (!ok) throw new Error('load failed');
    await settle();
    // what ipymolstar does on loadComplete
    for (const k in flags) await v.visual.visibility({ [HIDE[k]]: !flags[k] });
    if (spin !== undefined) await v.visual.toggleSpin(spin);
    if (highlightTrait) await v.visual.highlight(highlightTrait);
    if (tooltipsTrait) await v.visual.tooltips(tooltipsTrait);
    while (pending.length) await pending.shift()();
  };
  const record = (i, data) => selections.push({ action: i, params: data.map(p => lociRows(v.getLociForParams([p]))) });

  for (let i = 0; i < actions.length; i++) {
    const a = actions[i];
    const canvasCall = async (f) => { if (loaded) await f(); else pending.push(f); };
    if (a.action === 'load') {
      const next = JSON.stringify([a._url, a.assembly_id || '', a.preset || 'default']);
      if (next === spec) continue;
      spec = next;
      opts.customData = { url: a._url, format: 'cif', binary: false };
      opts.assemblyId = a.assembly_id || '';
      opts.defaultPreset = a.preset || 'default';
      await reload();
    } else if (a.action === 'set_visual_style') {
      if (opts.visualStyle === a.style) continue;
      opts.visualStyle = a.style;
      if (loaded) await reload();
    } else if (a.action === 'set_property') {
      if (a.name in HIDE) { flags[a.name] = !!a.value; if (loaded) await v.visual.visibility({ [HIDE[a.name]]: !a.value }); }
      else if (a.name === 'spin') { spin = !!a.value; if (loaded) await v.visual.toggleSpin(spin); }
      else if (a.name === 'bg_color') await canvasCall(() => v.canvas.setBgColor(a._rgb));
      else if (a.name === 'highlight_color') await canvasCall(() => v.visual.setColor({ highlight: a.value }));
      else if (a.name === 'select_color') await canvasCall(() => v.visual.setColor({ select: a.value }));
      else notes.push('not run in the viewer: set_property ' + a.name);
    } else if (a.action === 'set_color') {
      await canvasCall(() => v.visual.setColor({ highlight: a.highlight, select: a.select }));
    } else if (!loaded) {
      continue;
    } else if (a.action === 'color') {
      record(i, a.data);
      await v.visual.select({ data: a.data, nonSelectedColor: a.non_selected_color,
        keepColors: !!a.keep_colors, keepRepresentations: !!a.keep_representations });
    } else if (a.action === 'focus') { record(i, a.data); await v.visual.focus(a.data); }
    else if (a.action === 'highlight') {
      record(i, a.data);
      const p = { data: a.data, color: a.color, focus: a.focus };
      if (lociRows(v.getLociForParams(a.data)).length) highlightTrait = p;
      await v.visual.highlight(p);
    }
    else if (a.action === 'tooltips') { record(i, a.data); tooltipsTrait = { data: a.data }; await v.visual.tooltips(tooltipsTrait); }
    else if (a.action === 'reset') await v.visual.reset({ camera: a.camera, theme: a.theme, highlightColor: a.highlightColor, selectColor: a.selectColor });
    else if (a.action === 'clear_highlight') { highlightTrait = null; await v.visual.clearHighlight(); }
    else if (a.action === 'clear_selection') await v.visual.clearSelection();
    else if (a.action === 'clear_tooltips') { tooltipsTrait = null; await v.visual.clearTooltips(); }
    await settle();
  }
  if (!loaded) return { loaded: false, notes };

  const structs = v.plugin.managers.structure.hierarchy.current.structures;
  const s = structs[structs.length - 1];
  const root = s.cell.obj.data;
  const cells = Array.from(v.plugin.state.data.cells.values());
  const comps = s.components.map(c => ({
    tags: c.cell.transform.tags || [],
    hidden: !!c.cell.state.isHidden,
    rows: structRows(c.cell.obj.data),
    reprs: c.representations.map(r => {
      const ro = (r.cell.obj && r.cell.obj.data.repr.renderObjects) || [];
      let drawn = 0;
      for (const o of ro) drawn += (o.values.drawCount ? o.values.drawCount.ref.value : 0);
      const paint = [];
      for (const cell of cells) {
        if (cell.transform.parent !== r.cell.transform.ref) continue;
        if (!(cell.transform.tags || []).includes('overpaint-controls')) continue;
        for (const layer of cell.transform.params.layers) paint.push({ rows: bundleRows(root, layer.bundle), color: layer.color, clear: !!layer.clear });
      }
      return { type: r.cell.transform.params.type.name, theme: r.cell.transform.params.colorTheme.name,
               drawn: drawn > 0, hidden: !!r.cell.state.isHidden, paint };
    }),
  }));
  const tooltips = [];
  for (const cell of cells) {
    const props = cell.transform.params && cell.transform.params.properties;
    if (!props) continue;
    for (const key of Object.keys(props)) {
      const tips = props[key] && props[key].tooltips;
      if (Array.isArray(tips)) for (const t of tips) tooltips.push({ text: t.text, rows: bundleRows(root, t.selector.params) });
    }
  }
  const rp = v.plugin.canvas3d.props;
  return { loaded: true, atoms: structRows(root).length, units: root.units.length, comps, tooltips, selections, notes,
           canvas: { bg: rp.renderer.backgroundColor, highlight: rp.renderer.highlightColor,
                     select: rp.renderer.selectColor, spin: rp.trackball.animate.name === 'spin' } };
}
"""

_TAGS = {"structure-component-static-" + n: n for n in
         ("polymer", "ligand", "ion", "water", "branched", "non-standard", "coarse", "lipid")}


def _ensure_bundle() -> None:
    PDBE_DIR.mkdir(parents=True, exist_ok=True)
    for f in PDBE_FILES:
        if not (PDBE_DIR / f).exists():
            with urllib.request.urlopen(PDBE_CDN + f, timeout=120) as r:
                (PDBE_DIR / f).write_bytes(r.read())


class _Handler(http.server.BaseHTTPRequestHandler):
    roots = {"cif": CIF_CACHE, "pdbe": PDBE_DIR}

    def do_GET(self):  # noqa: N802
        parts = self.path.strip("/").split("/")
        if self.path == "/":
            body, ctype = _PAGE, "text/html"
        elif len(parts) == 2 and parts[0] in self.roots and (self.roots[parts[0]] / parts[1]).is_file():
            body = (self.roots[parts[0]] / parts[1]).read_bytes()
            ctype = {"js": "text/javascript", "css": "text/css"}.get(parts[1].rsplit(".", 1)[-1],
                                                                     "application/octet-stream")
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class Viewer:
    """Real pdbe-molstar in headless Chromium."""

    def __enter__(self):
        from playwright.sync_api import sync_playwright

        from molbench.render import _GL_ARGS
        _ensure_bundle()
        self._server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(args=_GL_ARGS)
        return self

    def __exit__(self, *exc):
        self._browser.close()
        self._pw.stop()
        self._server.shutdown()

    def run(self, actions: list[dict], updated: bool = False) -> dict:
        """Run the actions; returns the viewer's state dump (see _RUN_JS).
        ``updated``: load PDBe's updated mmCIF instead of the RCSB file."""
        acts = copy.deepcopy(actions)
        for a in acts:
            if a.get("action") == "load":
                entry = ps.canonical_entry(a.get("molecule_id"), a.get("custom_data"))
                a["_url"] = f"/cif/{fetch_cif(entry, updated).name}"
            if a.get("action") == "set_property" and a.get("name") == "bg_color":
                r, g, b = ps.css_color(a.get("value")) or (0, 0, 0)
                a["_rgb"] = {"r": r, "g": g, "b": b}
        page = self._browser.new_page()
        page.set_default_timeout(180000)
        try:
            page.goto(f"http://127.0.0.1:{self._server.server_address[1]}/")
            return page.evaluate(_RUN_JS, {"actions": acts})
        finally:
            page.close()


def _rgb(n: int) -> tuple:
    return ((n >> 16) & 255, (n >> 8) & 255, n & 255)


def _mask(rows_: list[int]) -> int:
    m = 0
    for r in rows_:
        m |= 1 << r
    return m


def compare_with_viewer(actions: list[dict], dump: dict) -> list[str]:
    """Differences between the real viewer's end state and the replay's."""
    bad: list[str] = []
    state = ps.replay(copy.deepcopy(actions))
    if not dump.get("loaded"):
        return [] if not state.loaded else ["viewer loaded nothing"]
    t = state.table
    if t is None:
        return ["no atom table to compare on"]
    if dump["atoms"] != t.n:
        bad.append(f"viewer structure has {dump['atoms']} distinct atoms, table {t.n}")

    # 1. every selection, atom for atom
    for sel in dump["selections"]:
        act = actions[sel["action"]]
        for pi, got_rows in enumerate(sel["params"]):
            want = ps.resolve_param(t, act["data"][pi], state.entry)
            if _mask(got_rows) != want:
                bad.append(f"selection action[{sel['action']}].data[{pi}] "
                           f"{json.dumps(ps._locator(act['data'][pi]))}: viewer "
                           f"{len(got_rows)} atoms, replay {want.bit_count()}")

    # 2. default components: which exist, their atoms, which are hidden, how drawn
    model_comps = state.components()
    hidden = {c for flag, cs in ps.HIDE_FLAGS.items() if state.hide[flag] for c in cs}
    seen = set()
    real_parts: list[tuple[int, str, object]] = []      # (atoms, type, colour) drawings
    for c in dump["comps"]:
        name = next((_TAGS[tg] for tg in c["tags"] if tg in _TAGS), None)
        added = "pdbe-molstar.added-component" in c["tags"]
        atoms = _mask(c["rows"])
        if not added:
            if name is None:
                bad.append(f"viewer component with unknown tags {c['tags']}")
                continue
            seen.add(name)
            if model_comps.get(name) != atoms:
                bad.append(f"component {name}: viewer {len(c['rows'])} atoms, replay "
                           f"{model_comps.get(name, 0).bit_count()}")
            if c["hidden"] != (name in hidden):
                bad.append(f"component {name}: viewer hidden={c['hidden']}, replay {name in hidden}")
        if c["hidden"]:
            continue
        for r in c["reprs"]:
            would_draw = state._drawn(r["type"], atoms)
            if bool(would_draw) != r["drawn"]:
                bad.append(f"{'added' if added else name} {r['type']}: viewer draws "
                           f"{'something' if r['drawn'] else 'nothing'}, replay says "
                           f"{'something' if would_draw else 'nothing'}")
            left = would_draw
            for layer in reversed(r["paint"]):
                hit = left & _mask(layer["rows"])
                if hit and not layer["clear"]:
                    real_parts.append((hit, r["type"], _rgb(layer["color"])))
                left &= ~hit
            if left:
                real_parts.append((left, r["type"], r["theme"]))
    for name in model_comps:
        if name not in seen:
            # a component with a visual style Mol* cannot draw is still there; one the
            # viewer never made is a modelling error
            bad.append(f"component {name}: replay has it, viewer does not")

    # 3. the display partition, built from the viewer's own representations
    real: dict[int, tuple] = {}
    per_atom: dict[int, set] = {}
    for atoms, rep, colour in real_parts:
        for row in rows(atoms):
            per_atom.setdefault(row, set()).add((rep, colour))
    by_val: dict[tuple, int] = {}
    for row in range(t.n):
        val = tuple(sorted(per_atom.get(row, ()), key=repr))
        by_val[val] = by_val.get(val, 0) | (1 << row)
    real = {m: v for v, m in by_val.items()}
    ours = state.display() if state.atomistic else {}
    if real != ours:
        for m, val in real.items():
            if ours.get(m) != val:
                bad.append(f"display: viewer draws {m.bit_count()} atoms as {val}; replay differs")
        for m, val in ours.items():
            if real.get(m) != val:
                bad.append(f"display: replay draws {m.bit_count()} atoms as {val}; viewer differs")

    # 4. tooltips
    real_tips = sorted((ps._norm_text(tp["text"]), _mask(tp["rows"])) for tp in dump["tooltips"])
    our_tips = sorted((ps._norm_text(p.get("tooltip")), state.select_one(p))
                      for p in (state.tooltip_params or []) if state.select_one(p))
    if real_tips != our_tips:
        bad.append(f"tooltips: viewer {[(x, m.bit_count()) for x, m in real_tips]}, "
                   f"replay {[(x, m.bit_count()) for x, m in our_tips]}")

    # 5. canvas
    cv = dump["canvas"]
    for label, got, want in (("background", _rgb(cv["bg"]), state.bg),
                             ("highlight colour", _rgb(cv["highlight"]), state.highlight_color),
                             ("select colour", _rgb(cv["select"]), state.select_color)):
        default_bg = label == "background" and state.bg == ps.DEFAULT_BG
        if got != want and not default_bg:     # the harness page does not set ipymolstar's default bg
            bad.append(f"{label}: viewer {got}, replay {want}")
    if cv["spin"] != state.spin:
        bad.append(f"spin: viewer {cv['spin']}, replay {state.spin}")
    return bad


# Action lists that exercise the semantics the tasks do not (run only with --viewer).
def probes() -> list[tuple[str, list[dict]]]:
    L = lambda e: {"action": "load", "molecule_id": e}  # noqa: E731
    C = lambda data, **kw: {"action": "color", "data": data, **kw}  # noqa: E731
    out = [
        ("3ptb label vs author numbering", [L("3ptb"), C([
            {"residue_number": 57, "color": "red"}, {"auth_seq_id": 57, "color": "blue"},
            {"auth_residue_number": 102, "color": "yellow"},
            {"struct_asym_id": "A", "start_residue_number": 10, "end_residue_number": 20, "color": "cyan"},
            {"auth_asym_id": "A", "start_auth_residue_number": 190, "end_auth_residue_number": 195,
             "color": "orange"}])]),
        ("precedence: comp id beats residue number; label chain beats author chain", [L("1tup"), C([
            {"label_comp_id": "ARG", "auth_seq_id": 248, "auth_asym_id": "B", "color": "red"},
            {"struct_asym_id": "A", "auth_asym_id": "B", "color": "blue"},
            {"entity_id": "1", "color": "yellow"},
            {"auth_asym_id": "A", "atoms": ["CA", "N"], "color": "magenta"},
            {"atom_id": [1, 2, 3], "atoms": ["CA"], "color": "cyan"}])]),
        ("odd values: strings for numbers, reversed range, lower-case comp id, residue 0", [L("3ptb"), C([
            {"auth_seq_id": "57", "color": "red"},
            {"start_residue_number": 30, "end_residue_number": 20, "auth_seq_id": 57, "color": "blue"},
            {"label_comp_id": "ben", "color": "yellow"}, {"residue_number": 0, "color": "cyan"},
            {"start_residue_number": 5, "end_residue_number": 5, "color": "orange"},
            {"entity_id": 1, "color": "white"}, {"color": "black", "auth_asym_id": "Z"}])]),
        ("select clears earlier colour and added representations", [L("3ptb"),
            C([{"auth_seq_id": 57, "color": "red", "representation": "ball-and-stick"}]),
            C([{"auth_seq_id": 102, "color": "blue"}])]),
        ("keep_colors and keep_representations", [L("3ptb"),
            C([{"auth_seq_id": 57, "color": "red", "sideChain": True}]),
            C([{"auth_seq_id": 102, "color": "blue", "representation": "spacefill",
                "representationColor": "#00ff00"}], keep_colors=True, keep_representations=True),
            C([{"auth_seq_id": 57, "color": {"r": 1, "g": 2, "b": 3}}], keep_colors=True)]),
        ("no colour key, null colour, non_selected_color, bad colour", [L("1hho"), C([
            {"label_comp_id": "HEM"}, {"auth_asym_id": "A", "auth_seq_id": 58, "color": None,
                                       "representation": "ball-and-stick"},
            {"auth_asym_id": "B", "auth_seq_id": 63, "color": "Red"},
            {"auth_asym_id": "B", "auth_seq_id": 92, "color": "#f00"}],
            non_selected_color={"r": 200, "g": 200, "b": 200})]),
        ("colour as a list, channel out of range, channel missing", [L("3ptb"), C([
            {"auth_seq_id": 57, "color": [255, 0, 0]},
            {"auth_seq_id": 102, "color": {"r": 300, "g": 0, "b": 0}},
            {"auth_seq_id": 195, "color": {"g": 128}}])]),
        ("style reload wipes colour; tooltips and hide flags survive", [L("3ptb"),
            C([{"auth_seq_id": 57, "color": "red", "representation": "ball-and-stick"}]),
            {"action": "tooltips", "data": [{"auth_seq_id": 195, "tooltip": "Ser195"}]},
            {"action": "set_property", "name": "hide_water", "value": True},
            {"action": "set_visual_style", "style": "ball-and-stick"}]),
        ("clear_selection, clear_tooltips, set_color formats, reset", [L("3ptb"),
            C([{"auth_seq_id": 57, "color": "red", "representation": "ball-and-stick"}]),
            {"action": "tooltips", "data": [{"auth_seq_id": 195, "tooltip": "x"}]},
            {"action": "set_color", "highlight": "yellow", "select": "#00ffff"},
            {"action": "clear_selection"}, {"action": "clear_tooltips"},
            {"action": "reset", "selectColor": True},
            {"action": "set_property", "name": "bg_color", "value": "black"},
            {"action": "set_property", "name": "spin", "value": True}]),
        ("highlight colour set by property, then clear_highlight resets it", [L("3ptb"),
            {"action": "set_property", "name": "highlight_color", "value": "#00ff00"},
            {"action": "set_property", "name": "select_color", "value": "blue"},
            {"action": "highlight", "data": [{"auth_seq_id": 57}]},
            {"action": "clear_highlight"}]),
        ("reset theme after a style", [L("3ptb"), C([{"auth_seq_id": 57, "color": "red"}]),
                                       {"action": "reset", "theme": True}]),
        ("hide every component", [L("1f88")] + [
            {"action": "set_property", "name": n, "value": True} for n in ps.HIDE_FLAGS]),
        ("non-standard residue in a polymer", [L("1ema"),
            {"action": "set_property", "name": "hide_non_standard", "value": True},
            C([{"label_comp_id": "CRO", "color": "orange"}])]),
        ("assembly", [{"action": "load", "molecule_id": "1hho", "assembly_id": "1"},
                      C([{"label_comp_id": "HEM", "color": "orange"}])]),
    ]
    for rep_type in ("ellipsoid", "carbohydrate", "cartoon", "putty", "bogus"):
        out.append((f"added {rep_type} on a residue, a ligand and a water", [L("3ptb"), C([
            {"auth_seq_id": 57, "representation": rep_type, "representationColor": "red"}]),
            C([{"label_comp_id": "BEN", "representation": rep_type}], keep_representations=True),
            C([{"label_comp_id": "HOH", "representation": rep_type}], keep_representations=True,
              keep_colors=True)]))
    for style in ps.REPRESENTATIONS:
        out.append((f"visual style {style}", [L("1f88"), {"action": "set_visual_style", "style": style},
                    C([{"label_comp_id": "RET", "representation": style, "representationColor": "red"}])]))
    for e in ("3eml", "1tup", "4ins", "af-p04637-f1"):
        load = L(e) if not e.startswith("af-") else {"action": "load", "custom_data": {
            "url": "https://alphafold.ebi.ac.uk/files/AF-P04637-F1-model_v6.cif", "format": "cif",
            "binary": False}}
        out.append((f"default components of {e}", [load]))
    return out


def uniprot_probes() -> list[tuple[str, list[dict]]]:
    """UniProt-numbered selections (run only with --uniprot, on PDBe's updated mmCIF)."""
    L = lambda e: {"action": "load", "molecule_id": e}  # noqa: E731
    C = lambda data: {"action": "color", "data": data}  # noqa: E731
    return [
        ("3ptb: UniProt P00760 63 is author His57 (offset); ranges; chain filter", [L("3ptb"), C([
            {"uniprot_accession": "P00760", "uniprot_residue_number": 63, "color": "red"},
            {"uniprot_accession": "P00760", "start_uniprot_residue_number": 100,
             "end_uniprot_residue_number": 110, "color": "blue"},
            {"uniprot_accession": "P00760", "uniprot_residue_number": 200, "auth_asym_id": "A",
             "atoms": ["CA"], "color": "yellow"}])]),
        ("3ptb: wrong accession, unmapped position, number as a string", [L("3ptb"), C([
            {"uniprot_accession": "P04637", "uniprot_residue_number": 63, "color": "red"},
            {"uniprot_accession": "P00760", "uniprot_residue_number": 5, "color": "blue"},
            {"uniprot_accession": "P00760", "uniprot_residue_number": "63", "color": "cyan"},
            {"uniprot_accession": "P00760", "uniprot_residue_number": 63, "label_comp_id": "SER",
             "color": "yellow"}])]),
        ("1tup: UniProt P04637 248 in three chains; a range; one chain", [L("1tup"), C([
            {"uniprot_accession": "P04637", "uniprot_residue_number": 248, "color": "red"},
            {"uniprot_accession": "P04637", "start_uniprot_residue_number": 270,
             "end_uniprot_residue_number": 282, "color": "blue"},
            {"uniprot_accession": "P04637", "uniprot_residue_number": 175, "auth_asym_id": "B",
             "color": "yellow"}])]),
    ]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--viewer", action="store_true", help="also compare with real pdbe-molstar")
    ap.add_argument("--cif", action="store_true", help="also run the mmCIF (gemmi) checks")
    ap.add_argument("--uniprot", action="store_true",
                    help="also compare UniProt-numbered selections with real pdbe-molstar")
    ap.add_argument("--updated", action="store_true",
                    help="with --viewer: load PDBe's updated mmCIF (the file a molecule_id "
                         "load really fetches) instead of the RCSB file the tables were built from")
    ap.add_argument("--only", nargs="*", help="task ids (or probe name fragments) to run")
    args = ap.parse_args()

    tasks = load_api_tasks()
    if args.only:
        picked = [t for t in tasks if t["id"] in args.only]
    else:
        picked = tasks
    n_bad = 0
    for task in picked:
        bad = check_task(task)
        n_bad += len(bad)
        state = ps.replay(copy.deepcopy(task["reference"]))
        n_sel = sum(len(a["data"]) for a in task["reference"] if a.get("action") in SELECTING)
        print(f"{task['id']}  {state.entry or '-':14} {n_sel} selection(s)  "
              f"{'ok' if not bad else 'PROBLEMS'}")
        for b in bad:
            print(f"    - {b}")
    if not args.only:
        bad = check_prompt_example(tasks)
        n_bad += len(bad)
        print(f"prompt worked example: {'not a task' if not bad else 'PROBLEMS'}")
        for b in bad:
            print(f"    - {b}")
    if args.cif:
        bad = check_assemblies(picked)
        n_bad += len(bad)
        print(f"assemblies: {'ok' if not bad else 'PROBLEMS'}")
        for b in bad:
            print(f"    - {b}")

    if args.viewer:
        runs: list[tuple[str, list[dict]]] = []
        for task in picked:
            for i, alt in enumerate([task["reference"]] + list(task.get("accepted", []))):
                runs.append((task["id"] + (f" accepted[{i - 1}]" if i else ""), alt))
        runs += [(n, a) for n, a in probes()
                 if not args.only or any(o in n for o in args.only)]
        n_sel = n_run = 0
        with Viewer() as viewer:
            for name, actions in runs:
                state = ps.replay(copy.deepcopy(actions))
                if state.table is None:
                    print(f"viewer  {name}: skipped (no atom table for {state.entry}; "
                          "this view is compared by its settings)")
                    continue
                try:
                    dump = viewer.run(actions, updated=args.updated)
                except Exception as e:  # report and carry on with the rest
                    n_bad += 1
                    print(f"viewer  {name}: FAILED TO RUN: {str(e).splitlines()[0][:200]}")
                    continue
                bad = compare_with_viewer(actions, dump)
                n_bad += len(bad)
                n_run += 1
                n_sel += sum(len(s["params"]) for s in dump.get("selections", []))
                print(f"viewer  {name}: {'agrees' if not bad else 'DIFFERS'}"
                      + (f"  (not run: {'; '.join(dump['notes'])})" if dump.get("notes") else ""))
                for b in bad:
                    print(f"    - {b}")
        print(f"viewer: {n_run} action lists run in pdbe-molstar {PDBE_VERSION}"
              f"{' on PDBe updated mmCIF' if args.updated else ''}, "
              f"{n_sel} selections compared atom for atom")
    if args.uniprot:
        todo = []
        for name, actions in uniprot_probes():
            state = ps.replay(copy.deepcopy(actions))
            if state.unresolved:
                print(f"uniprot {name}: skipped ({state.unresolved[0].rsplit('}: ', 1)[-1]})")
            else:
                todo.append((name, actions))
        n_sel = 0
        if todo:
            with Viewer() as viewer:
                for name, actions in todo:
                    try:
                        dump = viewer.run(actions, updated=True)
                    except Exception as e:
                        n_bad += 1
                        print(f"uniprot {name}: FAILED TO RUN: {str(e).splitlines()[0][:200]}")
                        continue
                    bad = compare_with_viewer(actions, dump)
                    n_bad += len(bad)
                    n_sel += sum(len(s["params"]) for s in dump.get("selections", []))
                    print(f"uniprot {name}: {'agrees' if not bad else 'DIFFERS'}")
                    for b in bad:
                        print(f"    - {b}")
        print(f"uniprot: {len(todo)} action lists run on PDBe's updated mmCIF, "
              f"{n_sel} selections compared atom for atom")
    if n_bad:
        raise SystemExit(f"{n_bad} problem(s)")
    print("all checks passed")


if __name__ == "__main__":
    main()
