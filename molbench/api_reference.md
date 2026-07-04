# ipymolstar `PDBeMolstar` — API reference (vendored)

> **Frozen snapshot** of the public surface of `ipymolstar.PDBeMolstar`
> (repo `molstar/ipymolstar`, file `src/ipymolstar/pdbemolstar.py`, `master`).
> This file is the *authority* for the benchmark: it is both the context shown to
> the model-under-test and the spec the grader trusts. Do not edit to "fix" a
> model's mistake — pin a new snapshot instead.

`PDBeMolstar` is an `anywidget` wrapping PDBe's Mol* plugin. You configure it by
setting **traits** (attributes synced to the JS view) and trigger one-shot
operations by calling **methods**.

## Construction / state traits

| Trait | Type | Notes |
|---|---|---|
| `molecule_id` | str | PDB id, e.g. `"1qyn"`. The primary way to load a structure. |
| `custom_data` | dict | `{"data": bytes, "format": "pdb"\|"cif"\|"bcif", "binary": bool}` to load a local/non-PDB structure. |
| `assembly_id` | str | Load a specific biological assembly. |
| `default_preset` | enum | `default` \| `unitcell` \| `all-models` \| `supercell`. |
| `alphafold_view` | bool | Load the AlphaFold model + pLDDT colouring. |
| `visual_style` | enum | Global representation, one of: `cartoon`, `ball-and-stick`, `carbohydrate`, `ellipsoid`, `gaussian-surface`, `molecular-surface`, `point`, `putty`, `spacefill`. |
| `hide_polymer` | bool | Hide protein/nucleic polymer. |
| `hide_water` | bool | Hide waters. |
| `hide_heteroatoms` | bool | Hide HETATM (ligands, ions). |
| `hide_carbs` | bool | Hide carbohydrates. |
| `hide_non_standard` | bool | Hide non-standard residues. |
| `hide_coarse` | bool | Hide coarse-grained parts. |
| `load_maps` | bool | Load electron-density maps. |
| `bg_color` | str | Background colour, hex e.g. `"#FFFFFF"`. |
| `highlight_color` | str | Hover-highlight colour (hex). |
| `select_color` | str | Selection colour (hex). |
| `lighting` | enum | `flat` \| `matte` \| `glossy` \| `metallic` \| `plastic`. |
| `spin` | bool | Spin the camera. |
| `superposition` | bool | Turn on the PDBe superposition view (structural alignment of the entry's chains/assemblies). |
| `validation_annotation` | bool | Overlay PDBe validation colours. |
| `domain_annotation` | bool | Overlay domain annotations. |
| `symmetry_annotation` | bool | Overlay symmetry annotations. |
| `granularity` | enum | Selection granularity, default `residue`. |

## Methods (one-shot operations)

```python
def color(data: list[QueryParam],
          non_selected_color=None,
          keep_colors=False,
          keep_representations=False) -> None
```
Colour and/or set a per-selection representation. Alias of Mol*'s `select`.

```python
def focus(data: list[QueryParam]) -> None   # centre + zoom camera on the selection
def highlight(data) -> None                 # (trait) transient highlight of a selection
def tooltips(data) -> None                  # (trait) attach tooltips to a selection
def set_color(highlight: Color = None, select: Color = None) -> None  # change UI colours
def reset(data: ResetParam) -> None         # ResetParam keys: camera, theme, highlightColor, selectColor (all bool)
def clear_highlight() -> None
def clear_selection(structure_number=None) -> None
def clear_tooltips() -> None
def update(data) -> None
```

## `QueryParam` — the selection language

A selection is a dict picking atoms/residues/chains. Common keys:

| Key | Meaning |
|---|---|
| `entity_id` | entity index (str) |
| `struct_asym_id` | label (mmCIF) chain id |
| `auth_asym_id` | **author chain id** — the chain letter users see, e.g. `"A"` |
| `residue_number` | label residue number |
| `auth_seq_id` | author residue number |
| `start_residue_number`, `end_residue_number` | inclusive residue range |
| `label_comp_id` | 3-letter residue/ligand code, e.g. `"HEM"`, `"HOH"`, `"RET"` |
| `atoms` | list of atom names, e.g. `["NE2", "FE"]` |
| `color` | `{"r": int, "g": int, "b": int}` |
| `representation` | per-selection style (same enum as `visual_style`) |
| `sideChain` | bool — include side-chain atoms |
| `focus` | bool — also focus this selection |
| `tooltip` | str — label text |
| `uniprot_accession`, `uniprot_residue_number` | map selection via UniProt |

Example — colour catalytic Asp25 on chains A and B red, and focus them:

```python
view.color(
    data=[
        {"auth_asym_id": "A", "residue_number": 25, "color": {"r": 255, "g": 0, "b": 0}},
        {"auth_asym_id": "B", "residue_number": 25, "color": {"r": 255, "g": 0, "b": 0}},
    ],
    non_selected_color={"r": 200, "g": 200, "b": 200},
)
view.focus(data=[
    {"auth_asym_id": "A", "residue_number": 25},
    {"auth_asym_id": "B", "residue_number": 25},
])
```
