# ipymolstar `PDBeMolstar` — API reference (vendored)

> **Frozen snapshot** of the public surface of `ipymolstar.PDBeMolstar` **0.1.0**, which
> drives PDBe's Mol* viewer, **pdbe-molstar 3.3.2**. Behaviour notes below were read from
> that release's source and checked in the running viewer. This file is the *authority*
> for the benchmark: it is the context shown to the model-under-test and the spec the
> grader follows. Do not edit to "fix" a model's mistake — pin a new snapshot instead.

You configure the viewer by setting **traits** and trigger one-shot operations by
calling **methods**.

## Traits

| Trait | Type | Notes |
|---|---|---|
| `molecule_id` | str | PDB id, e.g. `"1cbs"`. With `superposition=True` it is a **UniProt accession** instead. |
| `custom_data` | dict | `{"url": str, "format": "cif"\|"bcif"\|"pdb", "binary": bool}` — load any structure file by URL instead of a PDB id. An AlphaFold DB model is `https://alphafold.ebi.ac.uk/files/AF-<accession>-F1-model_v6.cif`. |
| `assembly_id` | str | Biological assembly to build, e.g. `"1"`; `"preferred"` = the first. Default: the deposited model. |
| `default_preset` | enum | `default` \| `unitcell` \| `all-models` \| `supercell`. |
| `ligand_view` | dict | PDBe ligand page view: only that ligand and its surroundings. `{"label_comp_id": "REA"}` and/or `auth_asym_id` + `auth_seq_id`. |
| `alphafold_view` | bool | Colour by AlphaFold confidence (pLDDT). It does **not** load a model: load one with `custom_data`. |
| `superposition` | bool | PDBe-KB superposition view: the superposed PDB entries of one protein, addressed by UniProt accession in `molecule_id`. |
| `superposition_params` | dict | `{"matrixAccession": str, "segment": int, "cluster": [int], "superposeCompleteCluster": bool, "ligandView": bool, "superposeAll": bool, "ligandColor": color}`. |
| `visual_style` | enum | One representation for every component: `cartoon`, `ball-and-stick`, `carbohydrate`, `ellipsoid`, `gaussian-surface`, `molecular-surface`, `point`, `putty`, `spacefill`. Unset = the default view: polymer as cartoon; ligands, ions, waters and non-standard residues as ball-and-stick. `cartoon` and `putty` draw polymer only (ligands, ions and waters disappear). |
| `hide_polymer`, `hide_water`, `hide_heteroatoms`, `hide_carbs`, `hide_non_standard`, `hide_coarse` | bool | Hide the polymer / waters / ligands and ions / carbohydrates / non-standard residues / coarse parts. |
| `load_maps` | bool | Load electron-density (or EM) maps. |
| `map_settings` | dict | Map style, e.g. `{"2fo-fc": {"opacity": 0.5, "wireframe": True}}` (also `"fo-fc(+ve)"`, `"fo-fc(-ve)"`, `"em"`). |
| `validation_annotation`, `domain_annotation`, `symmetry_annotation` | bool | PDBe validation / domain / assembly-symmetry overlays. |
| `bg_color` | str | Background, a CSS colour, e.g. `"#FFFFFF"`. |
| `highlight_color`, `select_color` | str | Hover-highlight and selection-mode colours (`"#rrggbb"` or a colour name). |
| `lighting` | enum | `flat` \| `matte` \| `glossy` \| `metallic` \| `plastic`. |
| `spin` | bool | Spin the camera. |
| `sequence_panel` | bool | Show the sequence panel. |

Setting `molecule_id`, `custom_data` or `visual_style` **reloads the structure**: colouring,
added representations and the camera focus made before it are lost. Set them first.

## Methods

```python
def color(data: list[QueryParam], non_selected_color=None,
          keep_colors=False, keep_representations=False) -> None
```
pdbe-molstar's `select`. For each item of `data`:

* `color` paints the selected atoms in the representations the structure **already has**
  (not in ones this call adds). Left out, they are painted the default orange
  (255,112,3); `"color": None` leaves them as they are.
* `representation` (or `sideChain=True`, meaning ball-and-stick) **adds** a representation
  for the selected residues, in element or chain colours unless `representationColor` is
  given.
* `focus=True` also zooms on the item.

`non_selected_color` paints everything else. Each call first **removes** the colouring and
the added representations of earlier calls, unless `keep_colors` / `keep_representations`.

```python
def focus(data: list[QueryParam]) -> None    # centre and zoom the camera on the selection
highlight = {"data": [...], "color": ..., "focus": bool}   # (trait) hover-style highlight; color and focus optional
tooltips = {"data": [{..., "tooltip": "text"}]}            # (trait) replaces earlier tooltips
def set_color(highlight=None, select=None) -> None         # same as the highlight_color / select_color traits
def reset(data) -> None     # keys: camera, theme, highlightColor, selectColor (bool)
def clear_highlight() -> None
def clear_selection() -> None                # removes colouring and added representations
def clear_tooltips() -> None
```

## `QueryParam` — the selection language

A dict; its tests are AND-ed, a list of dicts is the union. `{}` selects everything.

| Key | Meaning |
|---|---|
| `entity_id` | mmCIF entity id (str, e.g. `"1"`) |
| `struct_asym_id` | **label** chain id (mmCIF `label_asym_id`); wins if both chain keys are given |
| `auth_asym_id` | **author** chain id — the chain letter in the paper and the PDB file |
| `label_comp_id` | residue/ligand code, e.g. `"HEM"`, `"HOH"` (upper case). **Overrides** every residue-number key |
| `residue_number` | **label** residue number (mmCIF `label_seq_id`: 1-based position in the deposited sequence) |
| `start_residue_number`, `end_residue_number` | inclusive **label** range |
| `auth_seq_id` (alias `auth_residue_number`) | **author** residue number — the number used in the literature (His57, Asp25) |
| `start_auth_residue_number`, `end_auth_residue_number` | inclusive **author** range |
| `uniprot_accession` + `uniprot_residue_number` | residue by UniProt numbering (the viewer maps it with SIFTS) |
| `uniprot_accession` + `start_uniprot_residue_number`, `end_uniprot_residue_number` | UniProt range |
| `atoms` | list of atom names, e.g. `["CA", "CB"]` |
| `color`, `representation`, `representationColor`, `sideChain`, `focus` | see `color()` |
| `tooltip` | str — text for `tooltips` |

Label and author numbers often differ; a residue named the way papers name it needs the
**author** keys. Numbers are ints, not strings. Colours are `{"r": int, "g": int, "b": int}`,
`"#rrggbb"`, or a lower-case CSS colour name (`"red"`, `"orange"`).

Example — HIV-1 protease 1HSG: colour the catalytic Asp25 of both chains red and add red
ball-and-stick for them, leave the rest white, then centre on the inhibitor (MK1):

```python
view.color(
    data=[
        {"auth_asym_id": "A", "auth_seq_id": 25, "color": "red",
         "representation": "ball-and-stick", "representationColor": "red"},
        {"auth_asym_id": "B", "auth_seq_id": 25, "color": "red",
         "representation": "ball-and-stick", "representationColor": "red"},
    ],
    non_selected_color="white",
)
view.focus(data=[{"label_comp_id": "MK1"}])
```
