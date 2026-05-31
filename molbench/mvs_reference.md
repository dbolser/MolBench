# MolViewSpec (MVS) — scene-tree reference (vendored)

> **Frozen snapshot** targeting the `molviewspec` package (v1.8.x) and the MVS
> state format rendered by `ipymolstar.MolViewSpec`. This is both the context the
> model-under-test receives and the structure the grader trusts.

MVS describes a 3D molecular scene as a **tree of nodes**, independent of any
specific viewer. A scene is built by nesting: you download data, parse it, derive
a structure, carve out components, and give each a representation and colour.

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
it draws.

## Node kinds (the ones this benchmark uses)

| kind | params | typical parent | meaning |
|---|---|---|---|
| `download` | `url` | root | fetch a structure file |
| `parse` | `format` (`mmcif`,`bcif`,`pdb`) | download | parse the data |
| `structure` | `type` (`model`,`assembly`) | parse | build a structure |
| `component` | `selector` | structure | select a subset to draw |
| `representation` | `type` | component | how to draw it |
| `color` | `color` | representation | colour it |
| `focus` | *(none)* | component | aim the camera at it |
| `label` | `text` | component | attach a text label |

**Component selectors** — a string for whole classes:
`all`, `polymer`, `protein`, `nucleic`, `ligand`, `ion`, `water`, `branched`.
Or a **ComponentExpression** object (or list of them) to pick specific atoms/residues:

| field | meaning |
|---|---|
| `auth_asym_id` | author chain id (e.g. `"A"`) |
| `auth_seq_id` | author residue number |
| `label_asym_id`, `label_seq_id` | label (mmCIF) chain / residue |
| `beg_auth_seq_id`, `end_auth_seq_id` | inclusive residue range |
| `label_comp_id` | residue/ligand 3-letter code (`"HEM"`) |
| `label_atom_id` | atom name (`"FE"`) |

**Representation types:** `cartoon`, `ball_and_stick`, `spacefill`, `surface`,
`carbohydrate`, `isosurface`.

**Colours:** CSS names (`"red"`, `"orange"`, `"steelblue"`) or hex (`"#FF6699"`).

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
