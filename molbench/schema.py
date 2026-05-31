"""
Canonical action schema for MolBench.

The benchmark does NOT grade raw ipymolstar Python source. Instead, both the
reference answers and the model-under-test emit a *viewer-neutral intermediate
representation* (IR): an ordered list of "actions". Each action maps 1:1 onto a
real ipymolstar ``PDBeMolstar`` trait or method (see ``adapter.py``), but living
in a small JSON dialect makes three things possible:

  1. Grading without a browser (compare action lists structurally).
  2. Tolerant matching (a model may phrase a selection slightly differently).
  3. Re-targeting later to Mol* JS or PyMOL without rewriting the task corpus.

This module is the single source of truth: the action specs here drive both the
JSON Schema we hand to the model and the field-aware grader.
"""

from __future__ import annotations

from typing import Any

# --- The selection sub-language (a curated subset of ipymolstar's QueryParam) ----
#
# A "selection" answers *where* an operation applies. Locator fields identify the
# atoms/residues/chains; attribute fields decorate them (colour, representation...).
# We split them because the grader scores "did you point at the right residues"
# (locators) separately from "did you style them right" (attributes).

SELECTION_LOCATOR_FIELDS = [
    "entity_id",            # entity index, e.g. "1"
    "struct_asym_id",       # label asym (mmCIF) chain id
    "auth_asym_id",         # author chain id (the one users see, e.g. "A")
    "residue_number",       # label residue number
    "auth_seq_id",          # author residue number
    "start_residue_number",
    "end_residue_number",
    "label_comp_id",        # residue/ligand 3-letter code, e.g. "HEM", "HOH", "RTV"
    "atoms",                # list of atom names, e.g. ["NE2", "FE"]
    "uniprot_accession",
]

SELECTION_ATTR_FIELDS = [
    "color",                # {"r":int,"g":int,"b":int}
    "representation",       # one of REPRESENTATIONS (per-selection visual)
    "representationColor",
    "sideChain",            # bool
    "focus",                # bool
    "tooltip",              # str
]

# Per-selection / global visual styles supported by PDBeMolstar.visual_style and
# QueryParam.representation.
REPRESENTATIONS = [
    "cartoon",
    "ball-and-stick",
    "carbohydrate",
    "ellipsoid",
    "gaussian-surface",
    "molecular-surface",
    "point",
    "putty",
    "spacefill",
]

# Boolean / scalar widget traits a model may toggle via the "set_property" action.
# Maps canonical property name -> expected python type ("bool" | "str" | "color").
SETTABLE_PROPERTIES = {
    "hide_polymer": "bool",
    "hide_water": "bool",
    "hide_heteroatoms": "bool",
    "hide_carbs": "bool",
    "hide_non_standard": "bool",
    "hide_coarse": "bool",
    "spin": "bool",
    "superposition": "bool",   # PDBe superposition view (structural alignment)
    "load_maps": "bool",
    "validation_annotation": "bool",
    "domain_annotation": "bool",
    "symmetry_annotation": "bool",
    "alphafold_view": "bool",
    "bg_color": "str",
    "highlight_color": "str",
    "select_color": "str",
    "lighting": "str",   # flat | matte | glossy | metallic | plastic
}

RESET_FLAGS = ["camera", "theme", "highlightColor", "selectColor"]

LOAD_PRESETS = ["default", "unitcell", "all-models", "supercell"]


# --- Action specifications --------------------------------------------------------
#
# Each entry: required fields, optional fields, and a one-line doc. The grader and
# the JSON-Schema builder both read this table, so they can never drift apart.

ACTION_SPECS: dict[str, dict[str, Any]] = {
    "load": {
        "doc": "Load a structure into the viewer.",
        "required": [],   # one of molecule_id / custom_data must be present (checked below)
        "optional": ["molecule_id", "custom_data", "assembly_id", "preset", "alphafold"],
    },
    "set_visual_style": {
        "doc": "Set the global representation for the whole structure.",
        "required": ["style"],
        "optional": [],
    },
    "set_property": {
        "doc": "Toggle/assign a widget property (e.g. hide_water, spin, bg_color).",
        "required": ["name", "value"],
        "optional": [],
    },
    "color": {
        "doc": "Colour/select a set of residues (PDBeMolstar.color).",
        "required": ["data"],
        "optional": ["non_selected_color", "keep_colors", "keep_representations"],
    },
    "focus": {
        "doc": "Centre and zoom the camera on a selection (PDBeMolstar.focus).",
        "required": ["data"],
        "optional": [],
    },
    "highlight": {
        "doc": "Transiently highlight a selection (PDBeMolstar.highlight).",
        "required": ["data"],
        "optional": [],
    },
    "tooltips": {
        "doc": "Attach tooltips to a selection (PDBeMolstar.tooltips).",
        "required": ["data"],
        "optional": [],
    },
    "set_color": {
        "doc": "Set the highlight and/or select colours (PDBeMolstar.set_color).",
        "required": [],
        "optional": ["highlight", "select"],
    },
    "reset": {
        "doc": "Reset camera/theme/colours (PDBeMolstar.reset).",
        "required": [],
        "optional": RESET_FLAGS,
    },
    "clear_highlight": {"doc": "Clear current highlight.", "required": [], "optional": []},
    "clear_selection": {"doc": "Clear current selection.", "required": [], "optional": []},
    "clear_tooltips": {"doc": "Clear current tooltips.", "required": [], "optional": []},
}

ACTION_NAMES = list(ACTION_SPECS)


def build_json_schema() -> dict[str, Any]:
    """Return a JSON Schema (draft-07-ish) for a list of actions.

    We embed this in the model prompt and optionally validate against it with the
    ``jsonschema`` package when available. Validation is intentionally permissive:
    grading, not schema-rejection, is where nuance lives.
    """
    selection_schema = {
        "type": "object",
        "additionalProperties": True,
        "properties": {
            **{f: {} for f in SELECTION_LOCATOR_FIELDS},
            **{f: {} for f in SELECTION_ATTR_FIELDS},
        },
    }
    action_variants = []
    for name, spec in ACTION_SPECS.items():
        props: dict[str, Any] = {"action": {"const": name}}
        for f in spec["required"] + spec["optional"]:
            if f == "data":
                props[f] = {"type": "array", "items": selection_schema}
            elif f == "style":
                props[f] = {"enum": REPRESENTATIONS}
            elif f == "preset":
                props[f] = {"enum": LOAD_PRESETS}
            else:
                props[f] = {}
        action_variants.append(
            {
                "type": "object",
                "properties": props,
                "required": ["action"] + spec["required"],
                "additionalProperties": True,
            }
        )
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "array",
        "items": {"oneOf": action_variants},
    }


def validate_actions(actions: Any) -> list[str]:
    """Lightweight, dependency-free structural check. Returns a list of errors.

    Mirrors the JSON Schema's intent but runs without ``jsonschema`` installed so
    the harness works on a bare stdlib. An empty list means "structurally valid".
    """
    errors: list[str] = []
    if not isinstance(actions, list):
        return ["top-level value must be a list of action objects"]
    for i, act in enumerate(actions):
        where = f"action[{i}]"
        if not isinstance(act, dict):
            errors.append(f"{where}: not an object")
            continue
        name = act.get("action")
        if name not in ACTION_SPECS:
            errors.append(f"{where}: unknown action {name!r}")
            continue
        spec = ACTION_SPECS[name]
        for req in spec["required"]:
            if req not in act:
                errors.append(f"{where} ({name}): missing required field {req!r}")
        if name == "load" and not (act.get("molecule_id") or act.get("custom_data")):
            errors.append(f"{where} (load): needs molecule_id or custom_data")
        if name == "set_visual_style" and act.get("style") not in REPRESENTATIONS:
            errors.append(f"{where}: style {act.get('style')!r} not in {REPRESENTATIONS}")
        if name == "set_property":
            if act.get("name") not in SETTABLE_PROPERTIES:
                errors.append(f"{where}: property {act.get('name')!r} not settable")
        for sel_field in ("data",):
            if sel_field in act and not isinstance(act[sel_field], list):
                errors.append(f"{where}: {sel_field!r} must be a list of selections")
    return errors
