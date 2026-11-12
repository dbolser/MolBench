"""
Canonical actions  ->  real ipymolstar calls.

This module proves the IR is not made-up: every canonical action maps onto a
concrete ``PDBeMolstar`` trait assignment or method call. Two uses:

* Documentation / sanity — read it to see the exact mapping.
* Execution — ``apply_actions(view, actions)`` drives a live widget, which is the
  first half of the Component-2 (visual-rubric) pipeline: build the scene, then
  snapshot it for a VLM judge. Importing this module does NOT require ipymolstar;
  only calling ``apply_actions`` with a real widget does.

The function is intentionally total over the schema in ``schema.py``; if you add an
action there, add its mapping here.

Known gaps in ipymolstar 0.1.0 itself (its ``static/pdbemolstar.js`` has no handler
for these, so on a live widget they do nothing): ``focus``, ``set_color``,
``clear_highlight``, ``clear_selection``, ``update``, and changes after the first
render to ``select_color``, ``lighting``, ``assembly_id``, ``default_preset``,
``superposition``, ``alphafold_view`` and the annotation flags (they are read once,
when the viewer is created; ``domain_annotation`` and ``highlight_color`` are not
passed even then). The benchmark grades the pdbe-molstar call each action stands
for (``molbench/pdbe_state.py``), not these gaps.
"""

from __future__ import annotations

from typing import Any


def apply_actions(view: Any, actions: list[dict[str, Any]]) -> None:
    """Apply a list of canonical actions to a live PDBeMolstar ``view``."""
    for act in actions:
        name = act.get("action")

        if name == "load":
            # A load action is the whole load spec: fields it leaves out go back to
            # their defaults. The traits that only take effect at (re)load are set
            # first, because ipymolstar reloads on molecule_id / custom_data alone.
            view.assembly_id = str(act.get("assembly_id") or "")
            view.default_preset = act.get("preset") or "default"
            view.ligand_view = act.get("ligand_view")
            if act.get("alphafold"):
                view.alphafold_view = True
            if act.get("custom_data"):
                view.custom_data = act["custom_data"]
            elif act.get("molecule_id"):
                view.custom_data = None
                view.molecule_id = act["molecule_id"]

        elif name == "set_visual_style":
            view.visual_style = act["style"]

        elif name == "set_property":
            setattr(view, act["name"], act["value"])

        elif name == "color":
            view.color(
                data=act["data"],
                non_selected_color=act.get("non_selected_color"),
                keep_colors=act.get("keep_colors", False),
                keep_representations=act.get("keep_representations", False),
            )

        elif name == "focus":
            view.focus(data=act["data"])

        elif name == "highlight":
            view.highlight = {"data": act["data"],
                              **{k: act[k] for k in ("color", "focus") if k in act}}

        elif name == "tooltips":
            view.tooltips = {"data": act["data"]}

        elif name == "set_color":
            view.set_color(highlight=act.get("highlight"), select=act.get("select"))

        elif name == "reset":
            view.reset({k: act[k] for k in ("camera", "theme", "highlightColor", "selectColor")
                        if k in act})

        elif name == "clear_highlight":
            view.clear_highlight()
        elif name == "clear_selection":
            view.clear_selection()
        elif name == "clear_tooltips":
            view.clear_tooltips()

        else:  # pragma: no cover - guarded by schema validation upstream
            raise ValueError(f"no ipymolstar mapping for action {name!r}")
