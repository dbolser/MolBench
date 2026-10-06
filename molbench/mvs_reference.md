# MolViewSpec (MVS) — scene-tree reference (vendored)

> **Frozen snapshot** of the MVS scene tree as implemented by Mol\* 5.9.0 (the
> version vendored in `molbench/static/molstar/`). This is both the context the
> model-under-test receives (the **Spec** condition) and the structure the grader
> trusts. It covers the structure-scene subset of MVS; volumes, trajectories,
> annotation files (`*_from_uri`/`*_from_source`) and multi-snapshot animation are
> left out.

MVS describes a 3D molecular scene as a **tree of nodes**. A scene is built by
nesting: you download data, parse it, derive a structure, carve out components,
and give each a representation and colour.

## State shape

```json
{
  "root": {
    "kind": "root",
    "children": [ <node>, ... ]
  }
}
```

Every node is `{"kind": <str>, "params": {<...>}, "children": [<node>, ...]}`
(`params`/`children` omitted when empty). Nesting encodes meaning — a `color` node
is a child of the `representation` it colours, which is a child of the `component`
it draws. A node may also carry `"custom": {...}`: viewer-specific extras (see
*Mol\* extensions* below).

## Node kinds

| kind | params | parent | meaning |
|---|---|---|---|
| `download` | `url` | root | fetch a structure file |
| `parse` | `format` (`mmcif`,`bcif`,`pdb`) | download | parse the data |
| `structure` | `type` (`model`,`assembly`,`symmetry`), `assembly_id`, `model_index` | parse | build a structure |
| `transform` | `rotation` (3×3, flat), `translation`, or `matrix` (4×4, flat) | structure | move it by a known matrix |
| `component` | `selector` | structure | select a subset to draw |
| `representation` | `type`, `size_factor` | component | how to draw it |
| `color` | `color`, optional `selector` | representation | colour it (or only the selected part) |
| `opacity` | `opacity` (0–1; 0.5 = 50% transparent) | representation | transparency |
| `label` | `text` | component | text label on the component |
| `tooltip` | `text` | component | hover text |
| `focus` | optional `radius` | component (or root) | aim the camera at it |
| `camera` | `target`, `position`, `up` | root | set the camera explicitly |
| `canvas` | `background_color` | root | background colour |
| `primitives` | optional `color`, `label_color`, `opacity` | structure | a group of drawn shapes |
| `primitive` | `kind` + params below | primitives | one shape |

**Component selectors** — a string for whole classes:
`all`, `polymer`, `protein`, `nucleic`, `ligand`, `ion`, `water`, `branched`.
Or a **ComponentExpression** object (or list of them) to pick specific atoms/residues:

| field | meaning |
|---|---|
| `auth_asym_id` | author chain id (e.g. `"A"`) |
| `auth_seq_id` | author residue number |
| `label_asym_id`, `label_seq_id` | label (mmCIF) chain / residue |
| `beg_auth_seq_id`, `end_auth_seq_id` | inclusive residue range (also `beg_/end_label_seq_id`) |
| `label_comp_id`, `auth_comp_id` | residue/ligand 3-letter code (`"HEM"`) |
| `label_atom_id`, `auth_atom_id` | atom name (`"FE"`, `"NE2"`) |
| `type_symbol` | element (`"FE"`) |
| `residue_index` | 0-based residue index in the file |

Fields in one expression are AND-ed; a list of expressions is OR-ed. A selection
that matches nothing draws nothing — it is not an error, so use real chain ids,
residue numbers and atom names.

**Representation types:** `cartoon`, `backbone`, `ball_and_stick`, `line`,
`spacefill`, `surface`, `putty`, `carbohydrate`.

**Colours:** lowercase CSS names (`"red"`, `"orange"`, `"steelblue"`) or hex
(`"#FF6699"`). A `color` node takes ONE colour.

## Worked example

Prompt: *"Load 1HHO; protein as grey cartoon, heme groups as orange ball-and-stick."*

```json
{"root": {"kind": "root", "children": [
  {"kind": "download", "params": {"url": "https://files.rcsb.org/download/1hho.cif"},
   "children": [
    {"kind": "parse", "params": {"format": "mmcif"}, "children": [
     {"kind": "structure", "params": {"type": "model"}, "children": [
       {"kind": "component", "params": {"selector": "polymer"}, "children": [
         {"kind": "representation", "params": {"type": "cartoon"}, "children": [
           {"kind": "color", "params": {"color": "gray"}}]}]},
       {"kind": "component", "params": {"selector": "ligand"}, "children": [
         {"kind": "representation", "params": {"type": "ball_and_stick"}, "children": [
           {"kind": "color", "params": {"color": "orange"}}]}]}
     ]}]}]}
]}}
```

To select specific residues, replace the selector string with an expression, e.g.
`"selector": {"auth_asym_id": "A", "auth_seq_id": 35}`.

**Transparency:** `{"kind": "opacity", "params": {"opacity": 0.5}}` as a child of
the `representation`, beside its `color`.

## Primitives: lines, distances, angles, 3D text

A primitive position (`start`, `end`, `position`, `a`/`b`/`c`) is either
`[x, y, z]` or a ComponentExpression naming **one atom**, e.g.
`{"auth_asym_id": "A", "auth_seq_id": 64, "label_atom_id": "NE2"}`
(if it matches several atoms, their centre is used).

| primitive `kind` | params | draws |
|---|---|---|
| `distance_measurement` | `start`, `end`, `color`, `radius`, `dash_length`, `label_template` | a dashed line labelled with its length (`"{{distance}}"` is replaced by it) |
| `tube` | `start`, `end`, `radius`, `dash_length` | a line, dashed if `dash_length` is set |
| `angle_measurement` | `a`, `b`, `c` | the angle at `b`, labelled |
| `arrow` | `start`, `end`, `tube_radius`, `color` | an arrow |
| `label` | `position`, `text`, `label_size` | 3D text |

Example — *"1A6M: show the distance from the distal His64 to the bound O2"*
(the ligand code is `OXY`). The `primitives` node is a child of `structure`, next
to its `component` nodes:

```json
{"kind": "primitives", "params": {"color": "yellow", "label_color": "yellow"}, "children": [
  {"kind": "primitive", "params": {"kind": "distance_measurement",
    "start": {"auth_asym_id": "A", "auth_seq_id": 64, "label_atom_id": "NE2"},
    "end": {"auth_asym_id": "A", "label_comp_id": "OXY", "label_atom_id": "O2"},
    "radius": 0.06, "dash_length": 0.15, "label_template": "{{distance}}"}}]}
```

## Mol\* extensions (`custom`)

Mol\* reads these `custom` keys; other MVS viewers ignore them.

* **Non-covalent interactions** (H-bonds, salt bridges, metal coordination, π
  stacking…), computed by Mol\*: on a `component`, set
  `"custom": {"molstar_show_non_covalent_interactions": true,
  "molstar_non_covalent_interactions_radius_ang": 5}`. Mol\* draws the residues
  within the radius as ball-and-stick plus dashed interaction lines coloured by
  type. The component needs no `representation` child for this.
* **Colour schemes** (rainbow, by chain, by secondary structure, by element): give
  the representation ONE `color` child carrying
  `"custom": {"molstar_color_theme_name": <theme>}` (its `color` param is a
  placeholder the theme overrides). Themes: `"sequence-id"`, `"chain-id"`,
  `"secondary-structure"`, `"element-symbol"`.
