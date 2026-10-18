#!/usr/bin/env python3
"""
Freeze the per-structure atom tables the MVS grader resolves selections against.

For every structure a task's ``reference_mvs`` downloads, write
``data/atom_tables/<id>.json.gz``: the ``_atom_site`` columns a ComponentExpression can
test (model 1, asymmetric unit, file order, read with gemmi), plus the atoms Mol*
5.9.0 puts in each static selector (``polymer``, ``ligand``, ...). Those depend on
entity types and on bonds (``ligand`` pulls in covalently and metal-bonded
neighbours), so we ask Mol* itself: each structure is loaded in the pinned headless
viewer and each component's atoms are read back as ``_atom_site`` row indices.

Then every expression in the task references, plus edge-case probes, is resolved
both by Mol* and by ``molbench.atoms``; any disagreement fails the build. ``--check``
adds more selectors to that comparison (a JSON list of ``{"pdb", "selector"}``).

Needs the ``authoring`` and ``execute`` extras, ``scripts/fetch_molstar.py`` and
``playwright install chromium``. Grading itself needs none of it.

    python scripts/build_atom_tables.py              # all referenced structures
    python scripts/build_atom_tables.py 1tup 4ins    # just these
"""

from __future__ import annotations

import argparse
import functools
import gzip
import http.server
import json
import pathlib
import sys
import threading
import urllib.request

import gemmi

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from molbench import atoms  # noqa: E402
from molbench.mvs import _param_signature, extract_root  # noqa: E402
from molbench.render import _GL_ARGS, RENDER_HTML, STATIC  # noqa: E402
from molbench.runner import load_tasks  # noqa: E402

CACHE = REPO / "data" / "cif"
CIF = "https://files.rcsb.org/download/{}.cif"
MOLSTAR_VERSION = (STATIC / "molstar" / "VERSION").read_text().strip() \
    if (STATIC / "molstar" / "VERSION").exists() else None

_STR_COLUMNS = ("label_asym_id", "auth_asym_id", "label_entity_id", "pdbx_PDB_ins_code",
                "label_comp_id", "auth_comp_id", "label_atom_id", "auth_atom_id",
                "type_symbol", "label_alt_id")
_INT_COLUMNS = ("label_seq_id", "auth_seq_id", "id")


# --- the atom table (gemmi) -------------------------------------------------------

def fetch_cif(pdb: str) -> pathlib.Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{pdb}.cif"
    if not path.exists():
        with urllib.request.urlopen(CIF.format(pdb), timeout=60) as r:
            path.write_bytes(r.read())
    return path


def read_atom_site(path: pathlib.Path) -> dict[str, list]:
    """Model 1's ``_atom_site`` rows, with values as Mol* reads them."""
    block = gemmi.cif.read(str(path)).sole_block()
    table = block.find("_atom_site.", list(_STR_COLUMNS + _INT_COLUMNS) + ["pdbx_PDB_model_num"])
    models = table.find_column("_atom_site.pdbx_PDB_model_num")
    first = models[0]
    cols: dict[str, list] = {c: [] for c in _STR_COLUMNS + _INT_COLUMNS}
    for i in range(len(table)):
        if models[i] != first:
            break  # mmCIF lists models in order; Mol*'s 'model' structure is the first
        row = table[i]
        for j, c in enumerate(_STR_COLUMNS + _INT_COLUMNS):
            raw = row[j]
            missing = raw in (".", "?")
            if c in _INT_COLUMNS:
                cols[c].append(0 if missing else int(raw))  # Mol*: an absent int reads as 0
            else:
                v = "" if missing else gemmi.cif.as_string(raw)
                cols[c].append(v.upper() if c == "type_symbol" else v)
    cols["atom_id"] = cols.pop("id")
    # residue_index: 0-based order of residues by their first atom (Mol*'s residueSourceIndex).
    res, prev = [], None
    for i in range(len(cols["atom_id"])):
        key = (cols["label_asym_id"][i], cols["auth_seq_id"][i], cols["pdbx_PDB_ins_code"][i],
               cols["label_seq_id"][i], cols["label_comp_id"][i])
        if key != prev:
            res.append(len(res))
            prev = key
        cols.setdefault("residue_index", []).append(len(res) - 1)
    return cols


def _ranges(rows: list[int]) -> list[list[int]]:
    """Sorted row indices -> half-open [start, end) runs (static sets are mostly contiguous)."""
    out: list[list[int]] = []
    for r in sorted(rows):
        if out and out[-1][1] == r:
            out[-1][1] = r + 1
        else:
            out.append([r, r + 1])
    return out


# --- the Mol* oracle (headless viewer) --------------------------------------------

_SELECT_JS = """
async ({ mvs }) => {
  const viewer = await molstar.Viewer.create('app', { layoutIsExpanded: false,
    layoutShowControls: false, layoutShowSequence: false, layoutShowLog: false });
  const plugin = viewer.plugin;
  await viewer.loadMvsData(mvs, 'mvsj', { replaceExisting: true });
  const busy = plugin.behaviors.state.isBusy;
  for (let t = 0; busy.value && t < 400; t++) await new Promise(r => setTimeout(r, 150));
  const out = {};
  for (const cell of plugin.state.data.cells.values()) {
    const tag = (cell.transform.tags || []).find(t => t.startsWith('mvs-ref:sel'));
    if (!tag) continue;
    const rows = [];
    const s = cell.obj && cell.obj.data;
    if (s && s.units) {
      for (const unit of s.units) {
        const src = unit.model.atomicHierarchy.atomSourceIndex;
        for (let i = 0; i < unit.elements.length; i++) rows.push(src.value(unit.elements[i]));
      }
    }
    out[tag.slice('mvs-ref:sel'.length)] = rows;
  }
  return out;
}
"""


class MolstarOracle:
    """Load a structure in headless Mol* and read back the atoms each selector picks."""

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        handler = functools.partial(_QuietHandler, directory=str(CACHE))
        self._server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(args=_GL_ARGS)
        return self

    def __exit__(self, *exc):
        self._browser.close()
        self._pw.stop()
        self._server.shutdown()

    def select(self, pdb: str, selectors: list) -> list[list[int]]:
        """Sorted ``_atom_site`` row indices selected by each selector (one component each)."""
        url = f"http://127.0.0.1:{self._server.server_address[1]}/{pdb}.cif"
        comps = [{"kind": "component", "ref": f"sel{i}", "params": {"selector": s}}
                 for i, s in enumerate(selectors)]
        mvs = {"kind": "single", "metadata": {"version": "1", "timestamp": "1970-01-01T00:00:00Z"},
               "root": {"kind": "root", "children": [
                   {"kind": "download", "params": {"url": url}, "children": [
                       {"kind": "parse", "params": {"format": "mmcif"}, "children": [
                           {"kind": "structure", "params": {"type": "model"},
                            "children": comps}]}]}]}}
        page = self._browser.new_page()
        page.set_default_timeout(120000)
        page.goto(RENDER_HTML.as_uri())
        got = page.evaluate(_SELECT_JS, {"mvs": json.dumps(mvs)})
        page.close()
        # A component that selects nothing is not created, so it has no cell.
        return [sorted(got.get(str(i), [])) for i in range(len(selectors))]


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    """Serve the CIF cache to the viewer page (a file:// origin, hence the CORS header)."""

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, *args):
        pass


# --- which structures and selectors -----------------------------------------------

def referenced_selectors() -> dict[str, list]:
    """structure id -> every expression selector (and primitive endpoint) in the references."""
    out: dict[str, list] = {}

    def walk(node: dict, pdb: str | None) -> None:
        params = node.get("params") or {}
        if node.get("kind") == "download":
            pdb = _param_signature("download", params)[1]
            out.setdefault(pdb, [])
        if node.get("kind") == "component" and not isinstance(params.get("selector"), str):
            out[pdb].append(params["selector"])
        if node.get("kind") == "primitive":
            out[pdb].extend(params[k] for k in ("start", "end", "position", "a", "b", "c")
                            if isinstance(params.get(k), dict))
        for c in node.get("children") or []:
            walk(c, pdb)

    for task in load_tasks(["mvs"]):
        walk(extract_root(task["reference_mvs"]), None)
    return out


def probes(cols: dict[str, list]) -> list:
    """Edge cases whose Mol* semantics we rely on, built from this structure's own atoms."""
    chain, seq, comp = cols["auth_asym_id"][0], cols["auth_seq_id"][0], cols["label_comp_id"][0]
    het = next((i for i, v in enumerate(cols["label_seq_id"]) if v == 0), 0)
    return [
        {"auth_asym_id": chain, "auth_seq_id": seq},
        {"label_asym_id": cols["label_asym_id"][0], "label_seq_id": cols["label_seq_id"][0]},
        {"label_comp_id": comp},
        {"label_comp_id": comp.lower()},                       # case-sensitive
        {"type_symbol": cols["type_symbol"][0].lower()},       # upper-cased first
        {"auth_asym_id": chain, "beg_auth_seq_id": seq, "end_auth_seq_id": seq + 9},
        {"end_label_seq_id": 5},                               # non-polymer reads as 0
        {"label_seq_id": 0},
        {"beg_label_seq_id": 3},
        {"pdbx_PDB_ins_code": ""},
        {"label_entity_id": cols["label_entity_id"][-1]},
        {"auth_comp_id": cols["auth_comp_id"][het], "auth_atom_id": cols["auth_atom_id"][het]},
        {"atom_id": cols["atom_id"][10]},
        {"atom_index": 10},
        {"residue_index": 3},
        {"residue_index": cols["residue_index"][-1]},
        {"auth_asym_id": chain, "chain": "ignored", "residue": 1},  # unknown keys add no test
        [{"auth_seq_id": seq}, {"label_comp_id": comp}],
        {},
    ]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*", help="structure ids (default: every referenced one)")
    ap.add_argument("--check", help="JSON list of {pdb, selector} to compare as well")
    args = ap.parse_args()

    by_pdb = referenced_selectors()
    extra: dict[str, list] = {}
    if args.check:
        for item in json.loads(pathlib.Path(args.check).read_text()):
            extra.setdefault(item["pdb"], []).append(item["selector"])
    ids = args.ids or sorted(by_pdb)
    atoms.TABLES.mkdir(parents=True, exist_ok=True)
    bad = 0
    with MolstarOracle() as oracle:
        for pdb in ids:
            cols = read_atom_site(fetch_cif(pdb))
            n = len(cols["atom_id"])
            static = oracle.select(pdb, list(atoms.STATIC_SELECTORS))
            for name, rows in zip(atoms.STATIC_SELECTORS, static):
                if rows and rows[-1] >= n:
                    raise SystemExit(f"{pdb}: Mol* selected '{name}' atoms outside model 1")
            data = {"id": pdb, "source": CIF.format(pdb), "molstar": MOLSTAR_VERSION,
                    "model": 1, "columns": cols,
                    "static": {name: _ranges(rows)
                               for name, rows in zip(atoms.STATIC_SELECTORS, static)}}
            table = atoms.AtomTable(json.loads(json.dumps(data)))
            ids_seen = {table.identity(i) for i in range(n)}
            if len(ids_seen) != n:
                raise SystemExit(f"{pdb}: atom identities are not unique")
            if table.selector("all") != (1 << n) - 1:
                raise SystemExit(f"{pdb}: Mol*'s 'all' is not the whole table")

            check = by_pdb.get(pdb, []) + probes(cols) + extra.get(pdb, [])
            uniq = list({json.dumps(s, sort_keys=True): s for s in check}.values())
            want = oracle.select(pdb, uniq)
            for sel, rows in zip(uniq, want):
                mask = table.selector(sel)
                if mask is None:
                    continue
                if mask != atoms._mask(rows, n):
                    bad += 1
                    print(f"  MISMATCH {pdb} {json.dumps(sel)}: Mol* {len(rows)} atoms, "
                          f"ours {mask.bit_count()}")
            out = atoms.TABLES / f"{pdb}.json.gz"
            text = json.dumps(data, separators=(",", ":")).encode()
            out.write_bytes(gzip.compress(text, compresslevel=9, mtime=0))  # reproducible bytes
            sizes = {k: sum(b - a for a, b in v) for k, v in data["static"].items() if v}
            print(f"{pdb}: {n} atoms, {len(uniq)} selectors agree with Mol*, "
                  f"{out.stat().st_size // 1024} KB  {sizes}")
    if bad:
        raise SystemExit(f"{bad} selector(s) disagree with Mol* {MOLSTAR_VERSION}")


if __name__ == "__main__":
    main()
