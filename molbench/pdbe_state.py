"""
Replay a list of canonical API actions into the final viewer state, and compare states.

The API track used to compare action lists step by step, so an answer that named the
same atoms differently lost points and an answer that named different atoms the same
way did not. Here both the reference and the answer are *replayed* into the state the
viewer would end in, and the two states are compared. Nothing is fetched and no
browser runs at grade time: selections are resolved against the frozen atom tables
(``molbench/atom_tables``), the same ones the MVS grader uses.

What is modelled, and from where
--------------------------------
pdbe-molstar **3.3.2** (the bundle ipymolstar 0.1.0 loads). File and line references
are to that release's ``src/app``.

* **Selections** are a port of ``QueryHelper.getQueryObject`` (helpers.ts:225-300).
  Each ``QueryParam`` is entity AND chain AND residue AND atom test; a list is the
  union. Precedence inside one param, exactly as in the source:

  - chain: ``struct_asym_id`` (label chain) wins over ``auth_asym_id``; the two are
    different columns and are never pooled;
  - residue: ``label_comp_id`` > ``uniprot_accession`` + ``uniprot_residue_number`` >
    UniProt range > ``residue_number`` (**label_seq_id**) > ``start/end_residue_number``
    (label; used only when end >= start) > ``auth_seq_id`` > ``auth_residue_number``
    > ``start/end_auth_residue_number``. Only the first that applies is tested, so
    ``label_comp_id`` plus a residue number selects every residue with that name;
  - atoms: ``atoms`` (label_atom_id in list), overridden by ``atom_id``
    (``_atom_site.id`` in list).

  Comparisons are JavaScript ``===``: a residue number given as the string ``"57"``
  matches nothing, ``label_comp_id`` is case-sensitive. A non-polymer residue's
  label_seq_id reads as 0. ``auth_ins_code_id`` is accepted and ignored (3.3.2 never
  tests it).
* **color** is ``visual.select`` (viewer.ts:724-799). It first removes earlier
  colouring and earlier added representations unless ``keep_colors`` /
  ``keep_representations`` is set. Colour is an overpaint on the *default*
  components only; a param with no ``color`` key is painted the default select
  colour (255,112,3), ``"color": null`` paints nothing. ``representation`` (or
  ``sideChain``, which means ball-and-stick for the whole residue) adds a separate
  component for the union of the params that ask for that type; it is coloured only
  by ``representationColor``. ``focus: true`` zooms on those params.
* **Colours** go through ``normalizeColor`` (helpers.ts:429-440): an ``{r,g,b}``
  object, a ``#rrggbb`` string, or a lower-case Mol* colour name; anything else is
  grey (170,170,170). ``bg_color`` is the exception: ipymolstar parses that trait as
  a CSS colour before the viewer sees it.
* **visual_style** replaces the representation of every default component with one
  type (viewer.ts:469-500). Checked in the real viewer: cartoon and putty draw
  polymer residues only (water and ion representations are deleted, ligand ones are
  empty), ``carbohydrate`` draws branched entities only, ``ellipsoid`` draws nothing
  without anisotropic B-factors (the tables do not carry them, so it is treated as
  drawing nothing). With a style set every component is coloured by chain.
* **hide_*** toggles act on the default components that exist (polymer, het =
  ligand + ion, water, carbs = branched, nonStandard, coarse). Hiding a component
  the structure does not have changes nothing, and so states nothing.
* **focus / highlight / tooltips / set_color / reset / clear_*** follow
  viewer.ts:692-923. ``clear_highlight`` also resets the highlight colour.
* **When the scene is rebuilt.** A ``load`` and a ``set_visual_style`` that change
  their value reload the structure (ipymolstar calls ``visual.update(options, true)``
  for ``molecule_id``, ``custom_data`` and ``visual_style``). A reload discards
  colouring, added representations and focus; tooltips and the highlight are traits
  that ipymolstar re-applies after the reload. Every other option (assembly,
  annotations, lighting, superposition, ...) is declarative: its final value counts.
  Calls made before anything is loaded do nothing.
* ``superposition`` takes a UniProt accession as ``molecule_id`` and shows PDBe-KB's
  superposed entries; ``alphafold_view`` only switches the colouring to pLDDT, it
  does not load a model (spec.ts:103,115). An AlphaFold model is loaded with
  ``custom_data`` pointing at the AlphaFold DB file.

Known simplifications (stated so nobody has to discover them)
-------------------------------------------------------------
* Tables hold model 1 of the asymmetric unit. An assembly is recorded as a fact
  (its id) and atoms are compared on the asymmetric unit; an assembly that contains
  only some chains is not modelled.
* ``ligand_view`` and ``superposition`` scenes are compared by their settings; the
  atoms drawn in those views (surroundings, superposed entries) are not modelled.
* ``uniprot_*`` selectors need a frozen SIFTS table. ``uniprot_residue_atoms`` below
  is the single hook (``uniprot_range_atoms`` answers a range through it, or in one
  call to the frozen lookup, so a huge range in an answer costs nothing): it uses ``molbench.sifts.uniprot_atoms`` when that exists, and
  otherwise (or for an entry with no frozen table) raises ``NotImplementedError``;
  the selection is then reported as unresolved and selects nothing. In the viewer the
  mapping comes from the ``_atom_site.pdbx_sifts_xref_db_*`` columns of the file it
  loaded: PDBe's updated mmCIF has them (checked: P00760 position 63 selects author
  His57 of 3PTB; P04637 position 248 selects Arg248 of all three chains of 1TUP), an
  RCSB mmCIF does not, and there the same selectors select nothing.
* A structure with no atom table (or an unknown id) is compared symbolically: its
  selections are equal only if they are written the same way.

The score
---------
A state is reduced to **facts** (``facts()``): the ways it differs from a bare load of
the same structure. The structure itself is the frame the facts are stated in, not a
fact: loading the right entry earns nothing by itself, and on the wrong entry nothing
can be compared, so the score is 0. Each fact has weight 1 (``WEIGHTS``):

=============  ======================================================================
facet          one fact per ...
=============  ======================================================================
assembly       assembly id, when not the deposited model
preset         load preset, when not ``default``
option:<name>  each non-default option (superposition, alphafold_view, annotations,
               lighting, load_maps, ligand_view, ...)
canvas:<name>  background, spin, highlight colour, select colour (non-default)
display        each *display class*: a set of atoms whose look a ``color`` call
               changed and that are now drawn the same way (representation types
               and colours), differently from a bare load
scene          one fact for everything else that is drawn differently from a bare
               load: the effect of the global style and the hide toggles
focus          the residues the camera is focused on
highlight      the residues highlighted
tooltip        each distinct tooltip text, with the atoms that carry it
=============  ======================================================================

``recall`` is the weighted share of the reference's facts that the answer has,
``precision`` the share of the answer's facts that the reference has, ``f1`` their
harmonic mean. An answer with no facts (a bare load) has precision 0. Atom-set facts
earn graded credit, always judged on how each atom finally looks, so two routes to the
same picture score the same: a display class, the scene fact or a tooltip class scores
the fraction of its atoms that look the same on the other side; if the other side
changed essentially the same atoms as a display class (Jaccard >= 0.5) but drew them
differently, those atoms count ``PARTIAL`` (right place, wrong look). Focus and
highlight score the Jaccard overlap of residues.

``success`` is strict: the same structure and every fact matched in full, with no
extra facts. The only tolerances are ``COLOR_TOLERANCE`` per colour channel, tooltip
text compared ignoring case and repeated spaces, and focus/highlight compared as
whole residues (the camera and the default residue granularity do not tell atoms of
one residue apart).
"""

from __future__ import annotations

import copy
import json
import re
from typing import Any, Callable

from .atoms import AtomTable, load_table

# --- colours ----------------------------------------------------------------------

# The colour-name table and the tolerance are shared with the MVS grader (drawn.py):
# Mol*'s ColorNames, the same in the pdbe-molstar 3.3.2 bundle and in Mol* 5.9.0.
from .drawn import COLOR_NAMES, COLOR_TOLERANCE, color_eq  # noqa: E402,F401

RGB = tuple  # (r, g, b)
GREY = (170, 170, 170)            # normalizeColor's fallback
DEFAULT_SELECT_PAINT = (255, 112, 3)   # viewer.ts:740, a param with no colour
DEFAULT_HIGHLIGHT = (255, 102, 153)    # ipymolstar trait default #FF6699 (= Mol*'s)
DEFAULT_SELECT = (51, 255, 25)         # ipymolstar trait default #33FF19 (= Mol*'s)
DEFAULT_BG = (247, 247, 247)           # ipymolstar's light theme, #F7F7F7


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _whole(v: Any) -> bool:
    """A number equal to an integer (5 and 5.0; not 5.5, NaN, Infinity or "5")."""
    if isinstance(v, int) and not isinstance(v, bool):
        return True
    return isinstance(v, float) and v.is_integer()


def _truthy(v: Any) -> bool:
    """JavaScript truthiness for JSON values."""
    if v is None or v is False or v == "":
        return False
    if _is_num(v):
        return v != 0 and v == v
    return True


def _channel(v: Any) -> int:
    """A channel as JavaScript's ``<<`` and ``|`` read it: truncated, NaN/Infinity = 0."""
    return int(v) if _is_num(v) and v == v and abs(v) != float("inf") else 0


def normalize_color(v: Any, default: RGB = GREY) -> RGB:
    """``normalizeColor`` (helpers.ts:429-440)."""
    if v is None:
        return default
    if _is_num(v):
        if v != v or v in (float("inf"), float("-inf")):
            return (0, 0, 0)     # NaN and Infinity are 0 under JavaScript's bit operators
        n = int(v) & 0xFFFFFF
        return (n >> 16, (n >> 8) & 255, n & 255)
    if isinstance(v, str) and v[:1] == "#":
        try:
            n = int(v[1:], 16)   # Number('0x...'): '#fff' is 0x000fff, not white
        except ValueError:
            return default       # NaN in the viewer; treated as the fallback here
        n &= 0xFFFFFF
        return (n >> 16, (n >> 8) & 255, n & 255)
    if isinstance(v, str) and v in COLOR_NAMES:
        return COLOR_NAMES[v]
    if isinstance(v, dict):
        # Color.fromRgb is (r << 16) | (g << 8) | b with no clamping: a channel above
        # 255 spills into its neighbour (checked in the viewer: r 300 is drawn as r 44)
        n = ((_channel(v.get("r")) << 16) | (_channel(v.get("g")) << 8) | _channel(v.get("b"))) & 0xFFFFFF
        return (n >> 16, (n >> 8) & 255, n & 255)
    if isinstance(v, list):
        return (0, 0, 0)         # typeof [] is 'object': r, g and b are undefined, read as 0
    return default


def css_color(v: Any) -> RGB | None:
    """A CSS colour as ipymolstar's ``toRgb`` reads the ``bg_color`` trait, or None if
    it is not one the canvas would accept (the canvas then keeps black)."""
    if isinstance(v, dict):
        return normalize_color(v)
    if not isinstance(v, str):
        return None
    s = v.strip().lower()
    if re.fullmatch(r"#[0-9a-f]{6}([0-9a-f]{2})?", s):
        return (int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))
    if re.fullmatch(r"#[0-9a-f]{3}", s):
        return tuple(int(c * 2, 16) for c in s[1:])
    m = re.fullmatch(r"rgba?\(\s*(\d+)\s*[, ]\s*(\d+)\s*[, ]\s*(\d+)\s*(?:[,/]\s*[\d.]+%?\s*)?\)", s)
    if m:
        return tuple(min(255, int(g)) for g in m.groups())
    return COLOR_NAMES.get(s)


# --- UniProt numbering: the one hook the frozen SIFTS data plugs into ---------------

def uniprot_residue_atoms(entry: str, accession: str, uniprot_resnum: int) -> int:
    """Atoms of ``entry`` (a bitmask over its atom table rows) that SIFTS maps to
    position ``uniprot_resnum`` of UniProt ``accession``.

    This is the one hook for the frozen SIFTS tables. It forwards to
    ``molbench.sifts.uniprot_atoms(entry, accession, unp_num)`` as soon as that function
    exists (it arrives with the frozen tables in ``molbench/sifts_tables``); nothing
    else has to change. Until then, and for an entry with no frozen table, it raises
    ``NotImplementedError`` and the selection is reported as unresolved. Another
    mapping can be plugged in with one assignment::

        pdbe_state.uniprot_residue_atoms = my_mapping

    pdbe-molstar tests ``accession === siftMappings.accession[residue]`` and
    ``resnum === +siftMappings.num[residue]`` (helpers.ts:247-264), so the function
    must return every atom of every residue (any chain) mapped to that position, and
    0 when nothing maps there.
    """
    from . import sifts
    frozen = getattr(sifts, "uniprot_atoms", None)
    if frozen is None:
        raise NotImplementedError("frozen SIFTS mapping is not wired in yet "
                                  "(molbench.sifts.uniprot_atoms is missing)")
    atoms = frozen(entry, accession, uniprot_resnum)
    if atoms is None:
        raise NotImplementedError(f"no frozen SIFTS table for {entry!r}")
    return atoms


_frozen_uniprot_residue_atoms = uniprot_residue_atoms
#: Longest UniProt range walked position by position when another mapping is plugged
#: in (the longest UniProt sequence, titin, has about 36,000 residues).
MAX_UNIPROT_POSITION = 50_000


def uniprot_range_atoms(entry: str, accession: str, lo: float, hi: float) -> int:
    """Atoms mapped to UniProt positions ``lo..hi`` (inclusive). The numbers come from
    a model's answer, so the cost must not grow with the width of the range: the
    frozen lookup takes the range in one call; a plugged-in per-position mapping is
    walked over at most ``MAX_UNIPROT_POSITION`` positions."""
    if not (lo == lo and hi == hi) or hi < lo:       # NaN, or an empty range
        return 0
    if uniprot_residue_atoms is _frozen_uniprot_residue_atoms:
        from . import sifts
        frozen = getattr(sifts, "uniprot_atoms", None)
        if frozen is None:
            return uniprot_residue_atoms(entry, accession, 0)     # raises: not wired in
        atoms = frozen(entry, accession, lo, hi)
        if atoms is None:
            raise NotImplementedError(f"no frozen SIFTS table for {entry!r}")
        return atoms
    first = int(-(-max(lo, 1) // 1))
    last = int(min(hi, MAX_UNIPROT_POSITION) // 1)
    out = 0
    for n in range(first, last + 1):
        out |= uniprot_residue_atoms(entry, accession, n)
    return out


# --- selection resolution (getQueryObject) -------------------------------------------

LOCATOR_KEYS = (
    "entity_id", "struct_asym_id", "auth_asym_id", "label_comp_id",
    "uniprot_accession", "uniprot_residue_number", "start_uniprot_residue_number",
    "end_uniprot_residue_number", "residue_number", "start_residue_number",
    "end_residue_number", "auth_seq_id", "auth_residue_number", "auth_ins_code_id",
    "start_auth_residue_number", "end_auth_residue_number", "start_auth_ins_code_id",
    "end_auth_ins_code_id", "atoms", "atom_id",
)


def _eq(table: AtomTable, column: str, value: Any) -> int:
    try:
        return table.index(column).get(value, 0)
    except TypeError:        # unhashable value: equal to nothing
        return 0


def _between(table: AtomTable, column: str, lo: Any, hi: Any) -> int:
    out = 0
    for v, m in table.index(column).items():
        if lo <= v <= hi:
            out |= m
    return out


def resolve_param(table: AtomTable, param: dict[str, Any], entry: str = "") -> int:
    """Atoms one QueryParam selects, as a bitmask over the table's rows."""
    p = param
    sel = (1 << table.n) - 1

    # entity (helpers.ts:234)
    if _truthy(p.get("entity_id")):
        sel &= _eq(table, "label_entity_id", p["entity_id"]) if isinstance(p["entity_id"], str) else 0

    # chain (helpers.ts:237-241): label chain wins; never pooled with the author chain
    if _truthy(p.get("struct_asym_id")):
        sel &= _eq(table, "label_asym_id", p["struct_asym_id"]) if isinstance(p["struct_asym_id"], str) else 0
    elif _truthy(p.get("auth_asym_id")):
        sel &= _eq(table, "auth_asym_id", p["auth_asym_id"]) if isinstance(p["auth_asym_id"], str) else 0

    # residue (helpers.ts:244-282): first branch that applies
    def defined(k: str) -> bool:
        return k in p

    def num_eq(column: str, v: Any) -> int:
        return _eq(table, column, int(v)) if _whole(v) else 0

    def num_range(column: str, lo: Any, hi: Any) -> int:
        return _between(table, column, lo, hi)

    def ordered(a: str, b: str) -> str | None:
        """'range', 'single' or None for a start/end pair, as the source tests it."""
        if not (defined(a) and defined(b)):
            return None
        lo, hi = p[a], p[b]
        if not (_is_num(lo) and _is_num(hi)):
            # null === null selects nothing; other non-numbers are not modelled
            return "nothing" if lo == hi else None
        return "range" if hi > lo else "single" if hi == lo else None

    if _truthy(p.get("label_comp_id")):
        sel &= _eq(table, "label_comp_id", p["label_comp_id"]) if isinstance(p["label_comp_id"], str) else 0
    elif _truthy(p.get("uniprot_accession")) and defined("uniprot_residue_number"):
        n = p["uniprot_residue_number"]
        sel &= uniprot_residue_atoms(entry, p["uniprot_accession"], int(n)) if _whole(n) else 0
    elif (_truthy(p.get("uniprot_accession")) and defined("start_uniprot_residue_number")
          and defined("end_uniprot_residue_number")):
        lo, hi = p["start_uniprot_residue_number"], p["end_uniprot_residue_number"]
        sel &= uniprot_range_atoms(entry, p["uniprot_accession"], lo, hi) \
            if _is_num(lo) and _is_num(hi) else 0
    elif defined("residue_number"):
        sel &= num_eq("label_seq_id", p["residue_number"])
    elif ordered("start_residue_number", "end_residue_number"):
        kind = ordered("start_residue_number", "end_residue_number")
        lo, hi = p["start_residue_number"], p["end_residue_number"]
        sel &= (num_range("label_seq_id", lo, hi) if kind == "range"
                else num_eq("label_seq_id", lo) if kind == "single" else 0)
    elif defined("auth_seq_id"):
        sel &= num_eq("auth_seq_id", p["auth_seq_id"])
    elif defined("auth_residue_number"):
        sel &= num_eq("auth_seq_id", p["auth_residue_number"])
    elif ordered("start_auth_residue_number", "end_auth_residue_number"):
        kind = ordered("start_auth_residue_number", "end_auth_residue_number")
        lo, hi = p["start_auth_residue_number"], p["end_auth_residue_number"]
        sel &= (num_range("auth_seq_id", lo, hi) if kind == "range"
                else num_eq("auth_seq_id", lo) if kind == "single" else 0)

    # atoms (helpers.ts:285-291); atom_id overrides atoms
    if _truthy(p.get("atom_id")) or isinstance(p.get("atom_id"), list):
        ids = p["atom_id"] if isinstance(p["atom_id"], list) else []
        m = 0
        for i in ids:
            m |= num_eq("atom_id", i)
        sel &= m
    elif _truthy(p.get("atoms")) or isinstance(p.get("atoms"), list):
        names = p["atoms"]
        m = 0
        if isinstance(names, list):
            for a in names:
                m |= _eq(table, "label_atom_id", a) if isinstance(a, str) else 0
        elif isinstance(names, str):      # String.prototype.includes: a substring test
            for a, am in table.index("label_atom_id").items():
                if a in names:
                    m |= am
        sel &= m
    return sel


def residues_of(table: AtomTable, mask: int) -> int:
    """The mask grown to whole residues."""
    if not mask:
        return 0
    out = 0
    for m in table.index("residue_index").values():
        if m & mask:
            out |= m
    return out


# --- the viewer state ----------------------------------------------------------------

# trait -> default component(s) it hides (helpers.ts:476-484; 'het' is ligand + ion)
HIDE_FLAGS = {
    "hide_polymer": ("polymer",),
    "hide_water": ("water",),
    "hide_heteroatoms": ("ligand", "ion"),
    "hide_carbs": ("branched",),
    "hide_non_standard": ("non-standard",),
    "hide_coarse": ("coarse",),
}
# default component -> its representations as (type, colour theme) under the default
# preset (read back from the real viewer; see scripts/check_api_refs.py --viewer)
DEFAULT_REPRS = {
    "polymer": (("cartoon", "chain-id"),),
    "ligand": (("ball-and-stick", "element-symbol"),),
    "ion": (("ball-and-stick", "element-symbol"),),
    "water": (("ball-and-stick", "element-symbol"),),
    "branched": (("ball-and-stick", "element-symbol"), ("carbohydrate", "carbohydrate-symbol")),
    "non-standard": (("ball-and-stick", "element-symbol"),),
    "coarse": (("spacefill", "chain-id"),),
}
STYLE_THEME = "chain-id"      # colour theme of every component once visual_style is set
# Colour theme of a representation added by `color`, by the type that was asked for
# (read back from the viewer). Anything else, including an unknown type, is chain-id.
ADDED_ELEMENT_THEMED = ("ball-and-stick", "ellipsoid", "point", "spacefill")
REPRESENTATIONS = ("cartoon", "ball-and-stick", "carbohydrate", "ellipsoid", "gaussian-surface",
                   "molecular-surface", "point", "putty", "spacefill")

# Options whose final value is a fact (name -> default). Everything here is declarative.
OPTION_DEFAULTS: dict[str, Any] = {
    "alphafold_view": False, "superposition": False, "superposition_params": None,
    "load_maps": False, "map_settings": None, "validation_annotation": False,
    "domain_annotation": False, "symmetry_annotation": False, "lighting": None,
    "sequence_panel": False, "expanded": False, "granularity": "residue",
}
STANDARD_COMPS = frozenset(
    "ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL "
    "SEC PYL ASX GLX UNK A C G U I DA DC DG DT DI DU N DN".split())

_PDB_ID = re.compile(r"(?:pdb_0000)?[0-9][a-z0-9]{3}")
_AF_URL = re.compile(r"AF-([A-Za-z0-9]+)-F(\d+)")
_PDB_URL = re.compile(r"/(?:pdb)?([0-9][A-Za-z0-9]{3})(?:_updated|-assembly\d+)?\.(?:b?cif|pdb|ent)(?:\.gz)?(?:[?#].*)?$")


def canonical_entry(molecule_id: Any, custom_data: Any) -> str | None:
    """What is loaded, written one way: a lower-case PDB id, ``af-<accession>-f<n>``
    for an AlphaFold DB file (any model version), else the URL; ``id:<text>`` for a
    molecule_id that is not a PDB id. ``custom_data`` wins, as in ``getMoleculeSrcUrl``
    (viewer.ts:297-325)."""
    if isinstance(custom_data, dict) and custom_data.get("url"):
        url = str(custom_data["url"])
        if not custom_data.get("format"):
            return None            # "Provide all custom data parameters": nothing loads
        m = _AF_URL.search(url)
        if m:
            return f"af-{m.group(1).lower()}-f{m.group(2)}"
        m = _PDB_URL.search(url)
        return m.group(1).lower() if m else url
    if isinstance(molecule_id, str) and molecule_id.strip():
        m = molecule_id.strip().lower()
        # moleculeId is a PDB id (or, in the superposition view, a UniProt accession).
        # Anything else is asked of PDBe's model server as if it were a PDB id and
        # fails; the "id:" prefix keeps it apart from a file loaded by URL.
        return m if _PDB_ID.fullmatch(m) else "id:" + m
    return None


class ViewerState:
    """Where the viewer ends up. Atom sets are bitmasks over ``table`` rows."""

    def __init__(self) -> None:
        self.entry: str | None = None          # canonical_entry of what is loaded
        self.table: AtomTable | None = None
        self.assembly: str = ""                # "" = deposited model
        self.preset: str = "default"
        self.ligand_view: Any = None
        self.visual_style: str | None = None
        self.options: dict[str, Any] = dict(OPTION_DEFAULTS)
        self.hide: dict[str, bool] = {k: False for k in HIDE_FLAGS}
        self.bg: RGB = DEFAULT_BG
        self.spin: bool = False
        self.highlight_color: RGB = DEFAULT_HIGHLIGHT
        self.select_color: RGB = DEFAULT_SELECT
        # scene decorations (lost on reload)
        self.paint: list[tuple[Any, RGB]] = []               # overpaint layers, in order
        self.added: list[tuple[Any, str, list[tuple[Any, RGB]]]] = []  # (atoms, type, paint)
        self.focus: Any = None                               # None = whole scene
        # traits ipymolstar re-applies after a reload: kept as given, resolved on demand
        self.highlight_params: list | None = None
        self.tooltip_params: list | None = None
        self.log: list[str] = []                             # things that did nothing, and why
        self.unresolved: list[str] = []                      # selections that could not be resolved

    # -- selections ------------------------------------------------------------------

    @property
    def loaded(self) -> bool:
        return self.entry is not None

    @property
    def atomistic(self) -> bool:
        """True when atoms can be resolved and the default components are on screen."""
        return (self.table is not None and not self.options["superposition"]
                and self.ligand_view is None)

    def select_one(self, param: Any) -> Any:
        """Atoms of one param: a bitmask, or (without a table) a symbolic signature."""
        if not isinstance(param, dict):
            return 0
        if self.table is None:
            return _symbol(param)
        try:
            return resolve_param(self.table, param, self.entry or "")
        except NotImplementedError as e:
            self.unresolved.append(f"{json.dumps(_locator(param), sort_keys=True)}: {e}")
            return 0

    def select(self, params: list) -> Any:
        """Union of the params (``getLociForParams``)."""
        parts = [self.select_one(p) for p in params]
        if self.table is None:
            return frozenset().union(*parts) if parts else frozenset()
        out = 0
        for m in parts:
            out |= m
        return out

    def everything(self) -> Any:
        return (1 << self.table.n) - 1 if self.table is not None else frozenset(["*"])

    # -- derived views of the scene --------------------------------------------------

    def components(self) -> dict[str, int]:
        """Default components this structure has (name -> atoms). Needs a table."""
        t = self.table
        out = {name: t.static.get(name, 0) for name in ("polymer", "ligand", "ion", "water",
                                                         "branched", "coarse")}
        out["non-standard"] = nonstandard_atoms(t)
        return {k: v for k, v in out.items() if v}

    def _drawn(self, rep: str, atoms: int) -> int:
        """The atoms of a component that a representation type actually draws."""
        t = self.table
        if rep in ("cartoon", "putty"):
            return atoms & t.static.get("polymer", 0)
        if rep == "carbohydrate":
            return atoms & t.static.get("branched", 0) & ~t.static.get("polymer", 0)
        if rep == "ellipsoid" or rep not in REPRESENTATIONS:
            return 0
        return atoms

    def added_type(self, rep: str, atoms: int) -> str:
        """The type an added representation really gets. Mol* only offers the types
        that are applicable to the component; asking for another one silently gives
        the first applicable type instead (cartoon if the component has polymer
        residues, else ball-and-stick). Checked in the viewer: ``representation:
        "cartoon"`` on a ligand draws ball-and-stick."""
        t = self.table
        has_polymer = bool(atoms & t.static.get("polymer", 0))
        if rep in ("cartoon", "putty"):
            ok = has_polymer
        elif rep == "carbohydrate":
            ok = bool(t.static.get("branched", 0))     # Mol* asks the model, not the component
        elif rep == "ellipsoid":
            ok = False                                 # needs anisotropic B-factors
        else:
            ok = rep in REPRESENTATIONS
        return rep if ok else "cartoon" if has_polymer else "ball-and-stick"

    def display(self) -> dict[int, tuple]:
        """Partition of the atoms by how they are drawn: mask -> sorted tuple of
        (representation, colour). An atom nothing draws has the empty tuple."""
        t = self.table
        parts: dict[int, tuple] = {(1 << t.n) - 1: ()}

        def draw(mask: int, entry: tuple) -> None:
            if not mask:
                return
            nxt: dict[int, tuple] = {}
            for m, val in parts.items():
                hit = m & mask
                if hit:
                    new = val if entry in val else tuple(sorted(val + (entry,), key=repr))
                    nxt[hit] = new
                    rest = m & ~mask
                    if rest:
                        nxt[rest] = val
                else:
                    nxt[m] = val
            parts.clear()
            # two masks can end with the same value; merge them
            merged: dict[tuple, int] = {}
            for m, val in nxt.items():
                merged[val] = merged.get(val, 0) | m
            parts.update({m: val for val, m in merged.items()})

        def paint_regions(atoms: int, layers: list, base: Any) -> list[tuple[int, Any]]:
            """Split ``atoms`` by the last overpaint layer covering each."""
            regions, left = [], atoms
            for mask, rgb in reversed(layers):
                hit = left & mask
                if hit:
                    regions.append((hit, rgb))
                    left &= ~mask
            if left:
                regions.append((left, base))
            return regions

        hidden = {c for flag, comps in HIDE_FLAGS.items() if self.hide[flag] for c in comps}
        for name, atoms in self.components().items():
            if name in hidden:
                continue
            reprs = ((self.visual_style, STYLE_THEME),) if self.visual_style else DEFAULT_REPRS[name]
            for rep, theme in reprs:
                for mask, colour in paint_regions(self._drawn(rep, atoms), self.paint, theme):
                    draw(mask, (rep, colour))
        for atoms, rep, layers in self.added:
            has_carbs = bool(t.static.get("branched", 0))
            theme = ("element-symbol" if rep in ADDED_ELEMENT_THEMED
                     else "carbohydrate-symbol" if rep == "carbohydrate" and has_carbs
                     else "chain-id")       # the theme follows the type asked for ...
            rep = self.added_type(rep, atoms)   # ... even when another type is drawn
            for mask, colour in paint_regions(self._drawn(rep, atoms), layers, theme):
                draw(mask, (rep, colour))
        return parts


def nonstandard_atoms(table: AtomTable) -> int:
    """Mol*'s 'non-standard' component: polymer residues that are not one of the
    standard amino acids or nucleotides."""
    poly = table.static.get("polymer", 0)
    out = 0
    for comp, m in table.index("label_comp_id").items():
        if comp not in STANDARD_COMPS:
            out |= m & poly
    return out


def _locator(param: dict) -> dict:
    return {k: param[k] for k in LOCATOR_KEYS if k in param}


def _symbol(param: dict) -> frozenset:
    """Without a table a selection is its own description."""
    return frozenset([json.dumps(_locator(param), sort_keys=True)])


# --- replay --------------------------------------------------------------------------

def replay(actions: Any, tables: Callable[[str | None], AtomTable | None] = load_table) -> ViewerState:
    """Run a list of canonical actions and return the state the viewer ends in.

    Never raises on bad input: an action the viewer would ignore or reject is logged
    in ``state.log`` and changes nothing.
    """
    s = ViewerState()
    if not isinstance(actions, list):
        s.log.append("not a list of actions")
        return s
    for i, act in enumerate(actions):
        if not isinstance(act, dict):
            s.log.append(f"action[{i}]: not an object")
            continue
        try:
            _apply(s, act, tables)
        except Exception as e:  # a malformed action must not sink the grade
            s.log.append(f"action[{i}] {act.get('action')!r}: ignored ({type(e).__name__}: {e})")
    return s


def _table_for(entry: str, tables) -> AtomTable | None:
    """The atom table of an entry. An AlphaFold model is compared whatever its file
    version, so when there is no table under the version-free name ``af-<acc>-f<n>``
    the table of a versioned file (``af-<acc>-f<n>-model_v6``, the newest) is used."""
    table = tables(entry)
    if table is None and entry.startswith("af-"):
        from .atoms import TABLES
        versioned = sorted(TABLES.glob(f"{entry}-model_v*.json.gz"),
                           key=lambda q: int(re.sub(r"\D", "", q.name.rsplit("_v", 1)[-1]) or 0))
        if versioned:
            table = tables(versioned[-1].name[:-len(".json.gz")])
    return table


def _reload(s: ViewerState, tables) -> None:
    s.paint, s.added, s.focus = [], [], None
    s.table = _table_for(s.entry, tables) if s.entry and re.fullmatch(r"[a-z0-9_-]+", s.entry) else None


def _data(act: dict) -> list | None:
    d = act.get("data")
    return d if isinstance(d, list) and all(isinstance(p, dict) for p in d) else None


def _apply(s: ViewerState, act: dict, tables) -> None:
    name = act.get("action")

    if name == "load":
        entry = canonical_entry(act.get("molecule_id"), act.get("custom_data"))
        if entry is None:
            s.log.append("load: needs molecule_id or custom_data {url, format}")
            return
        spec = (entry, str(act.get("assembly_id") or ""), act.get("preset") or "default",
                act.get("ligand_view"))
        if act.get("alphafold"):
            s.options["alphafold_view"] = True
        if spec == (s.entry, s.assembly, s.preset, s.ligand_view):
            return                      # same trait values: no change event, no reload
        s.entry, s.assembly, s.preset, s.ligand_view = spec
        _reload(s, tables)
        return

    if name == "set_visual_style":
        style = act.get("style")
        if style not in REPRESENTATIONS:
            s.log.append(f"set_visual_style: {style!r} is not a style")   # traitlets rejects it
            return
        if style != s.visual_style:
            s.visual_style = style
            if s.loaded:
                _reload(s, tables)
        return

    if name == "set_property":
        _set_property(s, act.get("name"), act.get("value"), tables)
        return

    if name == "set_color":             # visual.setColor: canvas-level, survives reloads
        if _truthy(act.get("highlight")):
            s.highlight_color = normalize_color(act["highlight"])
        if _truthy(act.get("select")):
            s.select_color = normalize_color(act["select"])
        return

    # Everything below acts on the loaded structure.
    if not s.loaded:
        s.log.append(f"{name}: nothing is loaded yet")
        return

    if name == "color":
        data = _data(act)
        if data is None:
            s.log.append("color: data must be a list of selections")
            return
        if not act.get("keep_colors"):
            s.paint = []
        if not act.get("keep_representations"):
            s.added = []
        picked = [(p, s.select_one(p)) for p in data]
        picked = [(p, m) for p, m in picked if m]          # empty selections are skipped
        layers = [(m, normalize_color(p["color"]) if _truthy(p.get("color")) else DEFAULT_SELECT_PAINT)
                  for p, m in picked if not ("color" in p and p["color"] is None)]
        if _truthy(act.get("non_selected_color")):
            layers.insert(0, (s.everything(), normalize_color(act["non_selected_color"])))
        s.paint = s.paint + layers
        by_type: dict[str, list] = {}
        for p in data:
            rep = p.get("representation") or ("ball-and-stick" if p.get("sideChain") else None)
            if rep:
                by_type.setdefault(str(rep), []).append(p)
        rep_layers = [(m, normalize_color(p["representationColor"]))
                      for p, m in picked if _truthy(p.get("representationColor"))]
        for rep, params in by_type.items():
            atoms = s.select(params)
            if atoms:
                s.added.append((atoms, rep, list(rep_layers)))
        focus = [p for p in data if _truthy(p.get("focus"))]
        if focus and s.select(focus):
            s.focus = s.select(focus)
        return

    if name == "focus":
        data = _data(act)
        atoms = s.select(data) if data is not None else 0
        if atoms:                        # focusLoci on an empty loci leaves the camera alone
            s.focus = atoms
        return

    if name == "highlight":
        data = _data(act)
        if data is None or not s.select(data):
            return                       # viewer.ts:703: empty loci, nothing happens
        if _truthy(act.get("color")):
            s.highlight_color = normalize_color(act["color"])
        s.highlight_params = data
        if act.get("focus"):
            s.focus = s.select(data)
        return

    if name == "tooltips":
        data = _data(act)
        if data is not None:
            s.select(data)               # resolve now, so a malformed selection is ignored here
            s.tooltip_params = data
        return

    if name == "reset":
        if act.get("camera"):
            s.focus = None
        # reset({theme}) re-applies each representation's default colour theme, which is
        # what it already has; overpaint and added representations stay (checked in the viewer)
        if act.get("highlightColor"):
            s.highlight_color = DEFAULT_HIGHLIGHT
        if act.get("selectColor"):
            s.select_color = DEFAULT_SELECT
        return

    if name == "clear_highlight":        # viewer.ts:712-717: also resets the colour
        s.highlight_params = None
        s.highlight_color = DEFAULT_HIGHLIGHT
        return
    if name == "clear_selection":
        s.paint, s.added = [], []
        return
    if name == "clear_tooltips":
        s.tooltip_params = None
        return

    s.log.append(f"unknown action {name!r}")


def _set_property(s: ViewerState, name: Any, value: Any, tables) -> None:
    if (name in HIDE_FLAGS or name == "spin" or isinstance(OPTION_DEFAULTS.get(name), bool)) \
            and not (isinstance(value, bool) or (isinstance(value, int) and value in (0, 1))):
        # traitlets.Bool takes true, false, 1 or 0: anything else ("false", "yes", 2)
        # raises and changes nothing
        s.log.append(f"set_property {name}: {value!r} is not true or false")
    elif name in HIDE_FLAGS:
        s.hide[name] = bool(value)
    elif name == "spin":
        s.spin = bool(value)
    elif name == "bg_color":
        s.bg = css_color(value) or (0, 0, 0)
    elif name == "highlight_color":
        if _truthy(value):
            s.highlight_color = normalize_color(value)
    elif name == "select_color":
        if _truthy(value):
            s.select_color = normalize_color(value)
    elif name == "visual_style":
        _apply(s, {"action": "set_visual_style", "style": value}, tables)
    elif name in ("assembly_id", "default_preset", "ligand_view"):
        # load-time traits with no change handler: they take effect at the next reload,
        # which a list that sets them after `load` never causes
        s.log.append(f"set_property {name}: only read when a structure is loaded; "
                     "give it in the load action")
    elif name in OPTION_DEFAULTS:
        s.options[name] = value
    else:
        s.log.append(f"set_property: {name!r} is not a property")


# --- facts ---------------------------------------------------------------------------

#: Weight of one fact of each facet. One number per facet so they are easy to tune.
WEIGHTS = {"assembly": 1.0, "preset": 1.0, "option": 1.0, "canvas": 1.0,
           "display": 1.0, "scene": 1.0, "focus": 1.0, "highlight": 1.0, "tooltip": 1.0}
#: Credit for an atom that both sides changed but that does not look the same, given
#: when the two sides changed essentially the same set of atoms (PARTIAL_OVERLAP).
PARTIAL = 0.5
PARTIAL_OVERLAP = 0.5


def _norm_text(t: Any) -> str:
    return " ".join(str(t if t is not None else "").split()).casefold()


def _freeze(v: Any) -> Any:
    """A hashable, order-insensitive form of a JSON value, for comparing option values."""
    if isinstance(v, dict):
        return tuple(sorted((k, _freeze(x)) for k, x in v.items() if x is not None))
    if isinstance(v, list):
        return tuple(_freeze(x) for x in v)
    if isinstance(v, str):
        return v.strip().casefold()
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def _bare(s: ViewerState) -> ViewerState:
    """A bare load of the same structure: the baseline that facts are measured against."""
    b = ViewerState()
    b.entry, b.table, b.assembly, b.preset, b.ligand_view = (s.entry, s.table, s.assembly,
                                                               s.preset, s.ligand_view)
    return b


def _ligand_view_key(s: ViewerState) -> Any:
    lv = s.ligand_view
    if not isinstance(lv, dict):
        return _freeze(lv)
    if s.table is None or lv.get("label_comp_id_list"):
        return _freeze(lv)
    t, sel = s.table, (1 << s.table.n) - 1
    if "auth_seq_id" in lv and lv["auth_seq_id"] is not None:
        sel &= _eq(t, "auth_seq_id", lv["auth_seq_id"])
    elif _truthy(lv.get("label_comp_id")):
        sel &= _eq(t, "label_comp_id", lv["label_comp_id"])
    if _truthy(lv.get("auth_asym_id")):
        sel &= _eq(t, "auth_asym_id", lv["auth_asym_id"])
    elif _truthy(lv.get("struct_asym_id")):
        sel &= _eq(t, "label_asym_id", lv["struct_asym_id"])
    if sel and not lv.get("show_all"):       # MS.struct.filter.first: the first residue
        first = (sel & -sel).bit_length() - 1
        sel &= t.index("residue_index")[t.columns["residue_index"][first]]
    return ("atoms", sel)


def facts(s: ViewerState) -> dict[str, Any]:
    """The state as comparable facts. Keys are ``facet`` or ``facet:name``; display and
    tooltip facts are dicts ``value -> atoms`` (one fact per value). The structure is
    not in here: it is ``state.entry``."""
    out: dict[str, Any] = {}
    if not s.loaded:
        return out
    asm = "1" if s.assembly == "preferred" else s.assembly
    if asm:
        out["assembly"] = asm
    if s.preset != "default":
        out["preset"] = s.preset
    if s.ligand_view is not None:
        out["option:ligand_view"] = _ligand_view_key(s)
    for name, default in OPTION_DEFAULTS.items():
        v = s.options.get(name)
        if isinstance(default, bool):
            v = bool(v)
        if _freeze(v) != _freeze(default):
            out[f"option:{name}"] = _freeze(v)
    if s.bg != DEFAULT_BG:
        out["canvas:bg_color"] = s.bg
    if s.spin:
        out["canvas:spin"] = True
    if s.highlight_color != DEFAULT_HIGHLIGHT:
        out["canvas:highlight_color"] = s.highlight_color
    if s.select_color != DEFAULT_SELECT:
        out["canvas:select_color"] = s.select_color

    t = s.table
    if s.atomistic:
        base, now = _bare(s).display(), s.display()
        changed: dict[tuple, int] = {}       # value -> atoms drawn differently from a bare load
        whole_scene: dict[tuple, int] = {}   # value -> atoms, for the whole structure
        for m, val in now.items():
            whole_scene[val] = whole_scene.get(val, 0) | m
            for bm, bval in base.items():
                hit = m & bm
                if hit and val != bval:
                    changed[val] = changed.get(val, 0) | hit
        # atoms whose look a color call changed: those drawn differently once the
        # paint and the added representations are taken away
        plain = _bare(s)
        plain.visual_style, plain.hide = s.visual_style, s.hide
        touched = 0
        for pm, pval in plain.display().items():
            for m, val in now.items():
                if val != pval:
                    touched |= m & pm
        classes = {val: m & touched for val, m in changed.items() if m & touched}
        scene = 0
        for m in changed.values():
            scene |= m & ~touched
        if classes:
            out["display"] = classes
        if scene:
            out["scene"] = scene
        out["_changed"], out["_all"] = changed, whole_scene
    else:
        # no atoms to draw on (no table, or a view whose content is not modelled):
        # record the calls that would have painted something
        sym: dict[Any, Any] = {}
        none = 0 if t is not None else frozenset()

        def key_of(m: Any) -> Any:
            return m if isinstance(m, int) else tuple(sorted(m))

        if s.visual_style:
            sym[("style", s.visual_style)] = s.everything()
        for flag, on in s.hide.items():
            if on:
                sym[("hidden", flag)] = s.everything()
        for mask, rgb in s.paint:
            sym[("paint", rgb)] = sym.get(("paint", rgb), none) | mask
        for mask, rep, layers in s.added:
            key = ("added", rep, tuple(sorted(((key_of(m), c) for m, c in layers), key=repr)))
            sym[key] = sym.get(key, none) | mask
        if sym:
            out["display"] = sym
        out["_changed"] = out["_all"] = sym

    def whole(mask: Any) -> Any:
        return residues_of(t, mask) if t is not None else mask

    if s.focus:
        out["focus"] = whole(s.focus)
    if s.highlight_params:
        hl = s.select(s.highlight_params)
        if hl:
            out["highlight"] = whole(hl)
    if s.tooltip_params:
        tips: dict[str, Any] = {}
        for p in s.tooltip_params:
            m = s.select_one(p)
            if m:
                text = _norm_text(p.get("tooltip"))
                tips[text] = tips.get(text, 0 if t is not None else frozenset()) | m
        if tips:
            out["tooltip"] = tips
    return out


def changes(s: ViewerState) -> dict[tuple, int]:
    """The drawing as it differs from a bare load of the same structure: a draw
    ``(type, colour)`` -> the atoms that now carry it and would not after a bare load,
    and ``("-" + type, colour)`` -> the atoms that have lost a draw a bare load gives
    them (something hidden, restyled or painted over). This is what the target score is
    computed on (``drawn.target_display``): on the API track a bare load already draws
    everything, so only the changes say what an answer did. Needs an atom table."""
    out: dict[tuple, int] = {}
    if not s.atomistic:
        return out
    base, now = _bare(s).display(), s.display()
    for m, val in now.items():
        for bm, bval in base.items():
            hit = m & bm
            if not hit or val == bval:
                continue
            for d in val:
                if d not in bval:
                    out[d] = out.get(d, 0) | hit
            for d in bval:
                if d not in val:
                    key = ("-" + d[0], d[1])
                    out[key] = out.get(key, 0) | hit
    return out


def target_atoms(target: Any, s: ViewerState) -> int | None:
    """The atoms a task's ``target`` names (``{"data": [QueryParam, ...]}`` in this
    track's selection language and/or ``{"selector": <MVS selector>}``), or None when
    the task has no usable target or the structure has no atom table."""
    if not isinstance(target, dict) or s.table is None:
        return None
    if target.get("entry") and str(target["entry"]).lower() != s.entry:
        return 0
    out = 0
    for prm in target.get("data") if isinstance(target.get("data"), list) else []:
        if isinstance(prm, dict):
            try:
                out |= resolve_param(s.table, prm, s.entry or "")
            except NotImplementedError:
                pass
    if "selector" in target:
        out |= s.table.selector(target["selector"]) or 0
    return out


def _target_parts(reference: ViewerState, predicted: ViewerState, ref: dict, r_trace: list,
                  target: Any) -> list[dict]:
    """The facts of the target score (see ``drawn.target_display``). Without a task
    ``target`` the target is everything the reference changed; with one, it is the
    reference's drawing of those atoms plus the focus, highlight and tooltips that
    touch them, plus any fact the target lists under ``facts``."""
    from . import drawn
    t_atoms = target_atoms(target, reference)
    whole = t_atoms is None
    wanted = set(target.get("facts") or []) if isinstance(target, dict) else set()
    parts: list[dict] = []
    atom_facts = ("display", "scene", "focus", "highlight", "tooltip")
    if reference.atomistic and predicted.atomistic:
        ref_changes = changes(reference)
        if whole:
            t_atoms = 0
            for m in ref_changes.values():
                t_atoms |= m
        parts += drawn.target_display(ref_changes, changes(predicted), t_atoms)
    else:
        whole = True                          # nothing to restrict: use the fact scores
        parts += [{"fact": r["fact"], "recall": r["score"], "precision": r["score"]}
                  for r in r_trace if r["fact"] in ("display", "scene")]
    pred = facts(predicted)
    for key in ("focus", "highlight"):
        if key in ref and (whole or key in wanted or (isinstance(ref[key], int)
                                                       and ref[key] & t_atoms)):
            sc = _jaccard(ref[key], pred[key]) if key in pred else 0.0
            parts.append({"fact": key, "recall": sc, "precision": sc})
    if isinstance(ref.get("tooltip"), dict):
        theirs = pred.get("tooltip") if isinstance(pred.get("tooltip"), dict) else {}
        for text, atoms in ref["tooltip"].items():
            if whole or "tooltip" in wanted or (isinstance(atoms, int) and atoms & t_atoms):
                sc = _jaccard(atoms, theirs[text]) if text in theirs else 0.0
                parts.append({"fact": "tooltip", "value": text, "recall": sc, "precision": sc})
    for r in r_trace:
        name = r["fact"]
        if name.split(":")[0] in atom_facts:
            continue
        if whole and not wanted or name in wanted or name.split(":")[0] in wanted:
            parts.append({"fact": name, "recall": r["score"], "precision": r["score"]})
    return parts


# --- comparison ----------------------------------------------------------------------

def _size(m: Any) -> int:
    return m.bit_count() if isinstance(m, int) else len(m)


def _display_eq(a: Any, b: Any) -> bool:
    """Two display values: the same representations with colours within tolerance."""
    if a == b:
        return True
    if not (isinstance(a, tuple) and isinstance(b, tuple)) or len(a) != len(b):
        return False
    if not all(isinstance(x, tuple) and len(x) == 2 for x in a + b):
        return False
    left = list(b)
    for rep, col in a:
        hit = next((x for x in left if x[0] == rep and color_eq(col, x[1])), None)
        if hit is None:
            return False
        left.remove(hit)
    return True


def _same_share(mask: Any, val: Any, theirs: dict, same: Callable[[Any, Any], bool]) -> float:
    """Number of atoms of ``mask`` (drawn as ``val``) that the other side draws the same way."""
    return float(sum(_size(mask & omask) for oval, omask in theirs.items() if same(val, oval)))


def _class_scores(mine: dict, their_all: dict, their_changed: dict,
                  same: Callable[[Any, Any], bool]) -> dict[Any, float]:
    """For each of my classes: the share of its atoms that the other side draws the same
    way, plus PARTIAL for atoms in a changed class of theirs that covers essentially the
    same atoms but is drawn differently."""
    scores = {}
    for val, mask in mine.items():
        n = _size(mask)
        got = _same_share(mask, val, their_all, same)
        for oval, omask in their_changed.items():
            hit = _size(mask & omask)
            if hit and not same(val, oval) and hit / _size(mask | omask) >= PARTIAL_OVERLAP:
                got += hit * PARTIAL
        scores[val] = got / n if n else 0.0
    return scores


def _jaccard(a: Any, b: Any) -> float:
    union = _size(a | b)
    return _size(a & b) / union if union else 1.0


def _value_eq(key: str, a: Any, b: Any) -> bool:
    if key.startswith("canvas:") and isinstance(a, tuple):
        return color_eq(a, b)
    return a == b


def compare(reference: ViewerState, predicted: ViewerState, target: Any = None) -> dict[str, Any]:
    """Score ``predicted`` against ``reference``: precision, recall, f1, success, the
    target score (``target`` is the task's ``target``; see ``_target_parts``), and a
    per-fact trace."""
    from . import drawn
    ref, pred = facts(reference), facts(predicted)
    n_ref_facts = sum(1 for k in ref if not k.startswith("_"))
    n_pred_facts = sum(1 for k in pred if not k.startswith("_"))
    same_structure = reference.loaded and reference.entry == predicted.entry
    base = {"same_structure": same_structure, "structure": [reference.entry, predicted.entry],
            "ignored": list(predicted.log),
            "unresolved": sorted(set(predicted.unresolved))}
    if not same_structure:
        # facts are differences from a bare load of *this* structure: on another one
        # (or none) there is nothing to compare them with
        return drawn.zero(**base)

    def side(mine: dict, theirs: dict) -> tuple[float, float, list]:
        total = got = 0.0
        trace = []
        for key, val in mine.items():
            if key.startswith("_"):
                continue
            facet = key.split(":")[0]
            w = WEIGHTS[facet]
            other = theirs.get(key)
            if facet in ("display", "tooltip"):
                if facet == "display":
                    scores = _class_scores(val, theirs.get("_all", {}), theirs.get("_changed", {}),
                                           _display_eq)
                elif isinstance(other, dict):
                    scores = _class_scores(val, other, other, lambda a, b: a == b)
                else:
                    scores = {v: 0.0 for v in val}
                for v, sc in scores.items():
                    total += w
                    got += w * sc
                    trace.append({"fact": key, "value": _show(v), "atoms": _size(val[v]),
                                  "score": round(sc, 3)})
                continue
            if facet == "scene":
                # every atom the global settings changed, judged on how it finally looks
                same_n = sum(_same_share(val & m, v, theirs.get("_all", {}), _display_eq)
                             for v, m in mine["_all"].items() if val & m)
                sc = same_n / _size(val)
                total += w
                got += w * sc
                trace.append({"fact": key, "atoms": _size(val), "score": round(sc, 3)})
                continue
            if facet in ("focus", "highlight"):
                sc = _jaccard(val, other) if other is not None else 0.0
                shown: Any = f"{_size(val)} atoms"
            else:
                sc = 1.0 if other is not None and _value_eq(key, val, other) else 0.0
                shown = _show(val)
            total += w
            got += w * sc
            trace.append({"fact": key, "value": shown, "score": round(sc, 3)})
        return got, total, trace

    r_got, r_total, r_trace = side(ref, pred)
    p_got, p_total, p_trace = side(pred, ref)
    if not n_ref_facts and not n_pred_facts:
        precision = recall = 1.0          # a bare load was asked for and given
    else:
        recall = r_got / r_total if r_total else 0.0
        precision = p_got / p_total if p_total else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    success = bool(precision > 1 - 1e-9 and recall > 1 - 1e-9)
    return {
        "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4),
        "success": success,
        **drawn.target_summary(_target_parts(reference, predicted, ref, r_trace, target)),
        "n_ref": len(r_trace), "n_pred": len(p_trace),
        "reference_facts": r_trace, "predicted_facts": p_trace, **base,
    }


def _show(v: Any) -> Any:
    """A fact value for the trace (JSON-friendly, masks as atom counts)."""
    if isinstance(v, frozenset):
        return sorted(map(str, v))
    if isinstance(v, tuple):
        return [_show(x) for x in v]
    return v


def gradable(reference: Any, tables: Callable = load_table) -> bool:
    """True if the reference loads a structure this module can resolve atoms on, or one
    of the views that are compared by their settings."""
    s = replay(reference, tables)
    return s.loaded and (s.table is not None or s.options["superposition"]
                         or s.ligand_view is not None)


def grade_state(reference: list, predicted: Any, accepted: list[list] | None = None,
                tables: Callable = load_table, target: Any = None) -> dict[str, Any]:
    """Grade an answer by the final viewer state. ``accepted`` lists further action
    lists that are also right; the answer is scored against the one it matches best.
    ``target`` is the task's ``target`` (the atoms the request is about). The result
    has the same keys as the MVS grader's (``drawn.RESULT_KEYS``)."""
    from . import drawn
    if not isinstance(predicted, list):
        return drawn.zero(error="prediction is not a list", grader="state")
    pred = replay(copy.deepcopy(predicted), tables)
    best = None
    for i, ref in enumerate([reference] + list(accepted or [])):
        try:
            res = compare(replay(copy.deepcopy(ref), tables), pred, target)
        except Exception as e:  # an answer must never be able to crash the grader
            res = drawn.zero(error=f"could not compare states ({type(e).__name__}: {e})")
        res["matched_reference"] = i
        if best is None or (res["success"], res["f1"]) > (best["success"], best["f1"]):
            best = res
    best["grader"] = "state"
    return best
