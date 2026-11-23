# How MolBench answers are graded

This is the full definition of every score. It is written to be lifted into the paper.
The code is `molbench/grader.py` (entry point), `molbench/mvs.py` (MVS track),
`molbench/pdbe_state.py` (API track) and `molbench/drawn.py` (what the two share).
Every rule below is pinned by a test in `tests/test_grading_semantics.py`; the grader's
own error rate is measured on a control set (`tests/controls/`, last section).

## The idea

An answer is graded by **what the viewer would show**, not by how the answer is
written. Both the reference answer and the model's answer are turned into a *final
state*: for every atom of the structure, how it is drawn; plus a few facts about the
scene as a whole. Two answers that give the same final state get the same score,
whatever their wording. Nothing is fetched and no browser runs while grading: atoms
are looked up in frozen per-structure tables (`molbench/atom_tables/`, built from the
deposited mmCIF and checked against the viewer).

One call grades one answer on either track:

```python
from molbench.grader import grade_task
result = grade_task(task, answer)   # answer: parsed JSON (MVS scene tree, or list of API calls)
result["f1"], result["success"], result["target_f1"], result["outcome"]
```

The result has the same keys on both tracks (`molbench.drawn.RESULT_KEYS`).

## The three scores

| score | question it answers | range |
|---|---|---|
| **F1** | How much of the final state is right? | 0–1, graded |
| **Task success** | Is the final state exactly right: nothing missing, nothing extra? | yes / no |
| **Target score** | Are the atoms the request is about drawn as asked, whatever else the answer did? | 0–1, graded |

### The final state and its facts

The final state is cut into **facts**, each worth the same (weight 1):

- **Display classes.** The atoms are grouped by how they are drawn. An atom's drawing
  is the set of its *draws*; a draw is a representation type, a colour and an opacity
  (for example: grey cartoon, opaque). All atoms with the same set of draws form one
  class, and each class is one fact. "The whole protein as a grey cartoon, with
  Arg248 also as red ball-and-stick" is two classes: the atoms of Arg248 (grey cartoon
  and red ball-and-stick) and all other polymer atoms (grey cartoon only).
- **Scene facts**, when present: each label text with the atoms it is attached to;
  each tooltip text with its atoms; the camera focus (the atoms it frames); each
  drawn primitive (a distance line between two atoms, an arrow, a 3D label); a request
  to have the viewer compute and draw non-covalent interactions around some atoms; the
  structure type when it is not the deposited model (an assembly, another model, a
  symmetry-built structure); the background colour when it is not the default.

The structure itself is the frame the facts are stated in, not a fact. Loading the
right entry earns nothing by itself; on the wrong entry there is nothing to compare,
and the score is 0. A file that an answer downloads and never draws, labels or focuses
changes nothing on screen and is not counted; a second structure that is drawn is
unrequested drawing.

### F1

- **Recall** = mean, over the reference's facts, of how much of each the answer has.
- **Precision** = mean, over the answer's facts, of how much of each the reference has.
- **F1** = their harmonic mean.

How much of a fact the other side has:

- *Display class*: the mean over its atoms of the share of the atom's draws that the
  other side also has. A draw the other side has with the same representation type but
  another colour or opacity counts **half** (right atoms, right representation, wrong
  colour). An atom the other side does not draw counts 0. Draws the other side has *in
  addition* do not lower this number; they lower the number computed in the other
  direction. So **missing drawing costs recall, and unrequested drawing costs
  precision.**
- *Label, tooltip, interaction request*: the share of the atoms carrying it that carry
  the same on the other side.
- *Focus*: the overlap (intersection over union) of the two focus targets, as whole
  residues.
- *Primitive, structure type, background*: 1 if the other side has the same, else 0.

An answer that draws nothing scores 0 on every score when the reference draws
something.

### Task success

Success means precision = 1 and recall = 1 on the same structure: every fact of the
reference is fully present and the answer has no other fact. Any missing drawing, any
unrequested drawing, a wrong colour, a wrong residue, a wrong structure type: not a
success.

For a model on a task, success is the **mean over its samples** (the share of its
answers that are right). The share of tasks on which **all** samples are right is
reported next to it.

### Target score

Many requests are about a few atoms ("show Arg248 as red sticks"). A task can name
them in a `target` field. The target score asks only: *are those atoms drawn as the
reference draws them, and only those?* Context the request did not mention (a grey
cartoon around the residue) is ignored, in either direction.

- The **target's drawing** is the set of the reference's draws that lie wholly inside
  the target atoms (the red sticks of the residue; not a grey cartoon that merely
  passes through it). If no draw is confined to the target, it is everything the
  reference draws on those atoms. It is cut into classes as above.
- For each class, counting (atom, draw) items: `wanted` = the reference's items;
  `credit` = 1 for each the answer has, ½ for each the answer draws in the right
  representation with another colour or opacity **in a drawing confined to the
  target** (the right residue as blue sticks where red were asked for). The right
  representation in another colour in a drawing that runs on beyond the target (the
  grey cartoon of the whole chain; the white that an API call paints "everything
  else") is backdrop: the target is not singled out by it, so it earns no credit and
  is not counted as an attempt or as spill either. `attempted` = how many the answer
  drew at all; `spill` = items *outside* the target on which the answer repeats what it
  drew on the target, where the reference draws no such thing (the answer coloured the
  whole chain red when one residue was asked for); `extra` = items on the target from
  an answer draw that is confined to the target, in a representation type the
  reference does not draw there (a surface wrapped around the residue that was to be
  shown as sticks). A draw that is not confined to the target (a cartoon of the whole
  chain passing through the residue) is context, and is ignored.
- **Target recall** = credit / wanted. **Target precision** = credit / (attempted +
  spill + extra). The target score (`target_f1`) is the harmonic mean of the two, each averaged
  over the target's classes and over the scene facts that touch the target atoms
  (labels, tooltips, focus, interaction request).
- A single-turn task without a `target` field uses everything the reference draws as
  the target. The target score then differs from F1 only in ignoring what the answer
  draws elsewhere in another style.
- **A follow-up task without a `target` has no target score** (`target_f1` is `None`, and
  averages leave the sample out). Such an edit takes something away or resets a setting
  (hide the waters, remove the label, stop the spin, a new background): there are no
  atoms "drawn as asked", and "everything the reference draws" would give the start
  state returned unchanged full marks. Where an edit has a target (recolour chain B),
  the unchanged start state scores below 1 on it: 0 on the API track (nothing was
  changed on those atoms); on the MVS track one half where the start scene already
  draws exactly those atoms in a colour of their own (chain B magenta, to be made
  plum: right atoms, right representation, wrong colour), and 0 where they are part of
  a larger drawing in one colour.

A task's `target` is `{"selector": <MVS selector>}` and/or `{"data": [<API
selection>, …]}` (either form works on either track; both are resolved on the same atom
table), optionally with `"facts": ["focus", …]` to include a scene fact that has no
atoms in the target.

### Accepted alternatives and follow-up turns

- A task may list further right answers under `accepted`. The answer is graded against
  the reference and each of them; the best result counts (a success first, then the
  highest F1), and `matched_reference` says which one it was. **The target score is
  the best over the reference and all alternatives**, whichever of them has the best
  F1: the alternatives differ only in what the request leaves open, so whether the
  requested atoms are drawn as asked does not depend on which of them the rest of the
  picture resembles (`drawn.best_of`). An alternative may be
  about other atoms than the reference (an ambiguous request with several right
  residues), so its target score uses, in this order: its own entry in
  `accepted_targets` (a list parallel to `accepted`), if the task gives one; the
  task's `target`, if the alternative scores 1 on it against itself; otherwise
  everything the alternative draws. An answer that is exactly an accepted alternative
  therefore has target score 1.
- An MVS task that names a protein rather than an entry lists the right entries under
  `accepted_ids`. An answer on another accepted entry is graded against the reference's
  drawing re-resolved on that entry.
- A follow-up task gives a start scene (`context`) and an edit request. The answer is
  always the complete new scene or call list, and **only its final state is graded**,
  against the reference final state. An answer that rebuilds the scene from scratch and
  lands on the right state is right; one that loses an earlier choice is not. If the
  right answer is "change nothing", the reference is the start scene. The context is not
  graded, but it must load (`grader.check_task`).

## Unstated attributes are free

A request that states no colour, or no representation, for something leaves that
attribute open: any value is right. What it does state must match. (Ruling of
2026-11-15, `FINAL_PLAN.md`.)

- **MVS track, colour: a grader rule.** A single-turn reference holds only what the
  request states, so where it draws something with **no colour node**, no colour was
  asked for. The answer may give those atoms any colour, a colour theme included. One
  limit: not a colour the reference *states* for other atoms in the same representation
  type. "Show the protein as a cartoon and colour Ile66 blue" is not answered by a
  cartoon that is blue all over, because Ile66 has to stand out; it is answered by a
  white, grey or chain-coloured cartoon with Ile66 blue. A blue cartoon with blue
  sticks on a residue is fine: the sticks are another representation type.
  The rule applies to single-turn tasks only. In a follow-up the start scene is on
  screen, an uncoloured drawing there *is* white, and the edit must keep it.
  Code: `drawn.unstated_colour`, `mvs.resolve_scene(unstated_colour_free=True)`, set by
  `mvs.grade_mvs_task`. A plain scene comparison (`mvs.grade_mvs`) keeps Mol\*'s own
  rule, no colour node is white.
- **MVS track, representation: the accepted list.** A scene cannot leave a
  representation out, so a request that states none ("show the heme in green") lists
  each representation type as an accepted scene (`acc-representation-open`).
- **API track: the accepted list.** A bare load already draws everything, so the same
  words can be answered by call lists that end in different states. Each API task
  lists, under `accepted`, the end states that differ from the reference only in
  something the request does not state. The forms are built by one module
  (`scripts/api_forms.py`) and each is checked to draw the requested atoms as the
  reference does (target recall 1 against the reference: nothing asked for is missing
  or drawn another way):
  - *cartoon by default.* Where the request asks for a cartoon and the reference sets
    the cartoon style, the same colouring on the default view is accepted, and the
    other way round: the viewer already draws the polymer as a cartoon. What the
    request does not name (other ligands, ions, water) may then be absent (cartoon
    style), drawn as the viewer draws it, or painted in the backdrop colour.
  - *the drawing under an added representation.* "Show Arg248 as magenta
    ball-and-stick" does not say what colour the residue's own stretch of cartoon
    should be. It may stay as it was (`"color": null`), take the highlight colour, or
    take the viewer's select colour (no `color` key). If the request states a colour
    for the cartoon ("a grey cartoon, with ..."), the stretch is grey or the highlight
    colour. The second is the form the API prompt's own example teaches
    (`"color": "red", "representationColor": "red"`), and every task accepts it
    (`tests/test_audit_fixes.py`).
  - *chains by either id.* On the default view a chain named by its author id also
    selects the ligands, ions and waters filed under that chain; named by its label id
    it selects the polymer alone. "Colour chain A brown" says nothing of those, so both
    are accepted.
  - *the viewer's drawing under spheres or a surface.* On the default view a ligand
    asked for as spheres keeps the viewer's own ball-and-stick inside them, where it
    cannot be seen; it may be painted in the requested colour, left alone or left to
    the select colour.
  - *nothing hidden.* Where the request asks for the protein in one representation
    ("as a surface") and the reference hides water or ligands only to match the MVS
    scene, the same list without those toggles is accepted.
  A request that names the viewer's style itself ("in the cartoon style") states it.
  A request that **excludes** something in words ("no sugars", "only the DNA, no
  water") states that too: every default-view form of such a task carries the matching
  hide toggle, and no accepted form draws the excluded component
  (`provenance.excludes`).
- **API track: hide toggles nobody asked for (`free_hide`), a grader rule.** Where a
  task accepts both the cartoon style (ligands, ions and water are gone) and the
  default view (they are all drawn), the request evidently leaves open whether they are
  on screen, so every state in between is right as well: the default view with the
  waters hidden, say. The task file lists the toggles this holds for (`free_hide`, from
  `hide_water`, `hide_heteroatoms`, `hide_carbs`, `hide_non_standard`): those that no
  accepted list sets, and that leave the requested atoms drawn as they were on every
  accepted list. When an answer sets one of them, it is compared with each right list
  plus that toggle. `hide_polymer` is never free, and a toggle that would hide what the
  request names (the heme of "the heme in teal spheres") is not listed. A task whose
  only right form is the default view (a clinical request for the residue alone) has no
  `free_hide`: there an unrequested hide toggle is an unrequested change, and wrong.
  Accept-set tasks follow the same rule, applied to the call forms of each reading: a
  toggle is free when it is free in all of them (14 of the 15 API accept-set tasks).
  A call list that changes something the request does not mention in any other way
  (another global style, a second colour) is still wrong, as an unrequested extra
  component is on the MVS track.

## What the viewer draws (MVS track)

The MVS grader resolves a scene tree to its final state with the rules of Mol\* 5.9.0's
MolViewSpec extension. Each rule was read back from the headless viewer (which atoms
each representation object holds, and in which colour), not taken from documentation.

- **A representation draws atoms of its component.** `ball_and_stick`, `line`,
  `spacefill` and `surface` draw every atom of the component. `cartoon`, `backbone` and
  `putty` draw polymer residues, and only those whose *trace atom* is in the component
  (Cα of an amino-acid residue, O3′ of a nucleotide). So under a cartoon the selectors
  `all` and `polymer` give the same drawing, and so do a residue and its Cα atom.
  `carbohydrate` draws the sugar residues of the component and the polymer residues
  they are bonded to.
- **A type that does not apply is replaced by the viewer.** A cartoon, backbone or
  putty asked for on a component with no polymer atoms (a ligand, an ion, water) is
  drawn as ball-and-stick. `carbohydrate` in a structure with no sugars is drawn as a
  cartoon (or ball-and-stick). These answers are graded as what is drawn.
- **Nothing selected, nothing drawn.** A component whose selector matches no atom is
  not created.
- **Colour.** A representation with no colour node is white (in an answer; in a
  single-turn reference it means no colour was stated, see "Unstated attributes are
  free"). Colour nodes apply in
  order, each to its selector (default: everything), later ones over earlier ones. A
  ribbon residue takes the colour of its trace atom. Colour names are Mol\*'s lower-case
  names; `#rrggbb` and `#rgb` are read in either case; anything else (`"RED"`,
  `"rgb(255,0,0)"`, a number) makes Mol\* reject the whole scene.
- **Opacity** is set per representation; the default is 1. Two opacities within 0.05
  are the same.
- **Overlap.** Two representations of *different* types on overlapping components are
  both drawn; the atom carries both draws.
- **Coincident representations: only one is seen.** Two opaque representations of the
  *same* type on the same atoms have the same geometry there, and the viewer shows the
  one listed first; the later one is not seen at all. With different `size_factor`s
  the larger one is seen, whatever the order. So "a grey cartoon of the polymer, then
  residues 84-95 again as a green cartoon in a component of their own" is a cartoon
  that is grey all over, and is graded as that; the same two components in the other
  order, or one cartoon with a `color` child that has a selector, show the green. A
  surface is the exception (the surface of a part is not part of the surface of the
  whole, so both are seen), and so is a representation with opacity below 1. Measured
  by counting pixels in headless Mol\* 5.9.0 for every representation type
  (`scripts/check_overlap.py`, `tests/controls/overlap_evidence.json`); the rule is
  `mvs.DrawnStructure.settle`. This is the one place where the order of sibling nodes
  changes the picture. The MVS reference shown to the models states the rule. Each MVS
  sample records whether its answer has such a hidden drawing (`hidden_overlay`), so
  failures of this kind can be counted; no reference, accepted scene or start scene
  of the corpus has one (`grader.check_task` refuses it).
- **Selections** are resolved exactly as Mol\* resolves them (author and label
  numbering are different columns and are never pooled; a residue-number range, a list
  of the same residues, and one component per residue are the same atoms).
- **Colour themes.** A colour node that names a Mol\* colour theme
  (`custom.molstar_color_theme_name`) has no fixed colours, so it is compared as the
  theme: the same theme matches. One further match is allowed, in one direction only:
  when the *reference* uses the `chain-id` or `entity-id` theme ("colour by chain"), an
  answer that gives every chain (entity) one colour of its own, all different, matches
  it. Explicit colours in the reference are matched only by those colours. The
  allowance needs at least two chains (entities) under the theme: on a single chain
  "one colour per chain" would be any colour at all, so there only the theme itself
  matches, and `grader.check_task` reports a reference that uses the theme that way.

**The file must load.** A scene Mol\* accepts can still show nothing: the download URL
is the entry's web page, a bare file name or a file on an unknown host, or the `parse`
format is not the file's (an mmCIF text parsed as `bcif` gives 0 atoms; read back in
headless Mol\* 5.9.0). Such an answer has outcome `load_failed` and scores 0
(`mvs.load_problem`). Accepted sources: an http(s) URL on a wwPDB site or mirror
(`rcsb.org`, `ebi.ac.uk`, `wwpdb.org`, `pdbj.org`, `pdbe.org`, which covers AlphaFold
DB; also `alphafold.com`) that ends in `.cif`, `.bcif`, `.pdb` or `.ent` (optionally
`.gz`) or is a model-server query, with the matching `parse` format. Which of those
hosts and which file variant (`1cbs`, `1cbs_updated`, `pdb1cbs`) is not graded.

**An AlphaFold DB model has one address**,
`https://alphafold.ebi.ac.uk/files/AF-<accession>-F<n>-model_v<version>.cif` (also
`.bcif`, `.pdb`). The same file name on RCSB's host, the name without
`-model_v<version>`, the name in lower case and a version the database no longer
serves all answer 404 (checked 2026-11-16), so the viewer shows an empty canvas: the
answer is `load_failed` on the MVS track and loads nothing on the API track
(`drawn.alphafold_problem`). The version must be the one frozen in the panel (6).
Both references shown to the models give the address. (Found on the pilot: an answer
on `files.rcsb.org/download/AF-P68871-F1.cif` had passed.)

**A PDB id on the API track is written in lower case.** pdbe-molstar puts `molecule_id`
into PDBe's file address as written (`.../entry-files/download/<id>.bcif`), PDBe names
its files in lower case and tells the cases apart, so `"3K34"` asks for a file that is
not there and the canvas stays empty. Run in headless pdbe-molstar 3.3.2 against PDBe
on 2026-11-23: 0 structures for `"3K34"` and `"1LMB"`, 2,387 atoms for `"3k34"`. Such
an answer loads nothing and scores 0 (`pdbe_state.canonical_entry`); the same holds for
a PDBe entry-file URL with the id in upper case, on either track
(`drawn.pdbe_file_problem`). RCSB's download host serves either case, so
`files.rcsb.org/download/3K34.cif` is graded as the entry. The API reference shown to
the models says so. (Found on the pilot: the free model copied the id as the request
writes it; two such answers had passed, and until then a control kind expected them to.)

A state's own `root` is the scene: `{"root": {...}, "kind": "root"}` (a stray
top-level `kind`) loads in Mol\* as the tree under `root`, and is graded as that.

Not graded on the MVS track: the envelope and metadata, the file's host and name
variant (within the rule above), the order of children (except where two coincident
representations make it visible, above), representation size and surface kind
(`size_factor`, `surface_type`), label and primitive styling, and explicit camera
numbers (below).

## What the viewer does (API track)

The API track is graded as **pdbe-molstar 3.3.2 calls**. The answer is a list of
calls; the grader replays it, in order, with the semantics of that release, and
compares the end state with the reference's end state. The replay is a port of the
viewer's own code paths (selection, colouring, representation, visibility, reset) and
was compared with the real viewer, atom for atom (`scripts/check_api_refs.py
--viewer`). The module docstring of `molbench/pdbe_state.py` lists every modelled rule.

Because a bare load already draws the structure, the facts of an API end state are its
**differences from a bare load** of the same structure:

| fact | one per … |
|---|---|
| display | each class of atoms whose drawing a `color` call changed, now drawn the same way |
| scene | the effect of the global style and the hide toggles on all other atoms |
| focus, highlight, tooltip | the residues framed, the residues highlighted, each tooltip text with its atoms |
| assembly, preset, option, canvas | the assembly id, the load preset, each non-default option, each non-default canvas setting |

F1, success and the accepted alternatives work as above. A bare load has no facts and
scores 0 (unless a bare load is what the reference is: then it is right on every
score). Two details differ from the MVS track and are stated here so that the two
are not taken to be identical arithmetic:

- A display class scores the share of its atoms that end up looking *exactly* the same
  on the other side; atoms that both sides changed (classes that overlap by half or
  more) but that look different count half.
- The target score is computed on the *changes from a bare load* on the target atoms
  (a draw added, or a default draw removed), with the same credit / attempted / spill
  arithmetic as on the MVS track.

Order matters on this track because the viewer is stateful: a `color` call without
`keep_colors` removes earlier colouring, and a style set after colouring wipes it. Such
answers reach a different end state and are graded as that state.

## The camera

Camera numbers are never graded. What is graded is **which atoms the focus frames**,
compared as whole residues:

- If the reference has a focus, the answer must frame the same residues. An answer with
  no focus frames everything it draws, and is compared as that. On the MVS track
  several `focus` nodes frame their union (checked in the viewer).
- If the reference has no focus, the answer's focus is **not counted**: zooming in on
  the residue one was asked to highlight is not an error. (The camera is where one looks
  from, not what is drawn, and the human rating study pictures both answers from the
  same camera.) A request to see the whole molecule is expressed by a reference focus on
  the whole structure.
- An explicit MVS `camera` node (position, target, up) is ignored.

`molbench.drawn.GRADE_UNREQUESTED_FOCUS = True` switches to the stricter reading (any
focus is a fact on both sides). On the October predictions the choice moves mean task
success from 0.494 (strict) to 0.499.

## Colour

One rule on both tracks: two colours are the same if **every channel (0–255) differs
by at most 32**. One table of colour names on both tracks (Mol\*'s, in
`molbench/drawn.py`); `gray` and `grey` are the same colour.

Evidence for 32 (`tests/controls/colour_evidence.json`):

- Tasks ask for colours from a fixed palette of 19 names (`drawn.TASK_PALETTE`). The
  two closest palette colours are 55 apart (plum and hotpink), so no palette colour can
  pass for another. A test fails if a task uses a colour outside the palette.
- Models write the named colour exactly. Of 2,303 colour values in valid October
  scenes that could be compared with a reference colour, 2,227 were exactly a reference
  colour; none of the other 76 was closer than 58 to one (the commonest: `lightgray`
  where `gray` was asked, 83 away). Any tolerance between 0 and 54 gives the same
  verdicts on that evidence. 32 leaves room for a hand-mixed shade of a named colour
  and keeps every palette colour distinct.

A lighter or darker named shade (`lightgray` for gray, `darkred` for red, `lime` for
green) is a different colour.

## Pictures for the human rating study

Pictures are not graded; they are what human raters see. `molbench.render.render_pair`
makes four pictures of a (reference, answer) pair in headless Mol\* 5.9.0: each scene
whole, and each scene **framed on the target atoms** (the task's `target`; without
one, the atoms of the reference's draws that cover less than half of what it draws).
The camera is worked out once, on the reference: it looks at the centre of the target
atoms from outside the molecule, with a radius of the target's extent plus 4 Å (at
least 8 Å). That exact camera is then applied to the answer, so the two pictures of a
pair are always taken from the same place; a `focus` or `camera` node in either scene
is overridden. The structure file is read from the frozen panel, not downloaded.

## Validity outcomes, and the three ways a score is averaged

Every sample has an **outcome**:

| track | outcome | meaning | score |
|---|---|---|---|
| both | `invalid_json` | the reply contains no parseable JSON of the right outer shape | 0 |
| MVS | `not_mvs` | JSON, but not a scene tree | 0 |
| MVS | `invalid_mvs` | a scene tree that Mol\* 5.9.0's own validation rejects (it would load nothing) | 0 |
| MVS | `valid` | Mol\* accepts the scene | as graded |
| MVS | `unchecked` | a scene tree graded without running Mol\*'s validation (no browser available) | as graded; no validity is claimed |
| MVS | `load_failed` | the scene names a source Mol\* cannot load (see "The file must load"); also set by the legacy render path | 0 |
| API | `invalid_api` | a JSON list that breaks the call schema (an unknown action, a wrong field type, a representation name outside the viewer's list) | as graded: the replay ignores what the viewer would ignore, and falls back as the viewer does |
| API | `valid` | a schema-valid call list | as graded |

`grade_task` sets `not_mvs` / `unchecked` and `valid` / `invalid_api`; whoever parses the
raw reply sets `invalid_json`, and Mol\*'s validation (`render.molstar_issues`, one
headless browser for a whole batch) turns `unchecked` into `valid` or `invalid_mvs`.

Scores are averaged in three ways, always named:

- **Strict** (primary): every sample counts; an invalid one counts 0 on F1, success and
  target score.
- **Valid-only**: the mean over the samples with outcome `valid`. This separates "wrote
  a loadable answer" from "the answer is right".
- **Repaired** (a counterfactual, never the headline): an `invalid_json` reply is passed
  through the offline `json-repair` library and graded again; the strict score is
  unchanged, and the repaired score is reported beside it.

## Known limits

- **Assemblies.** Atom tables hold model 1 of the deposited (asymmetric) unit. An
  assembly is a fact (its id), and atoms are compared on the deposited unit. An assembly
  that contains only some of the chains, and selections of single symmetry copies
  (`instance_id`), are not modelled; a scene that uses the latter is compared as
  written, not as drawn.
- **Other models of an NMR entry** are compared on model 1's atoms, with the model
  index as a fact.
- **Structures with no atom table** (an entry outside the panel, a PDB-format file) are
  compared as written: two selections are equal only if spelled the same way, and the
  equivalences above (all vs polymer under a cartoon, and so on) do not apply.
  `grader.check_task` reports such a task; no benchmark task's reference is one.
- **Resolve tier: an answer on another accepted entry is graded as written.** A resolve
  task names a protein and accepts any PDB entry of it (5,739 accepted entries over the
  39 tasks). Three of those entries have a frozen atom table; on every other one the
  answer's selections are compared with the reference's as text. The usual namings pass
  (the accepted scenes list `polymer`, `all`, `protein`, `nucleic` and the component
  code), but a correct selection by chain id on such an entry scores 0, where the same
  answer on the reference entry passes. The runner records which kind of entry each
  answer used (`entry_outcome`) and, for an accepted entry, whether it is the reference
  entry (`entry_is_reference`); resolve success is reported apart for the two.
- **Reply parsing.** The answer is the outermost JSON array (API) or object (MVS) in the
  reply; if that span is not JSON because the prose around it has a bracket of its own,
  the first balanced array that parses as a list of objects is taken. A reply no JSON
  parser can read (a number of thousands of digits, nesting thousands deep) is
  `invalid_json`.
- **Themes** other than `chain-id` and `entity-id` are matched only by the same theme.
- **Carbohydrate** representations: which sugar residues are drawn is modelled; the
  colour of a sugar when a colour node selects only some of its atoms is not checked
  against the viewer.
- **`ignore_hydrogens`** is honoured as documented (hydrogens are not drawn); this was
  not read back from the viewer.
- **Not drawn, so not graded:** representation size, surface kind, label and primitive
  styling, camera numbers. An MVS node kind with no rule here (a volume, an annotation
  from a URL, a transform) is compared as written: it must be present, with the same
  parameters, on both sides.
- **API track vs ipymolstar.** The track grades the pdbe-molstar 3.3.2 call that each
  action stands for. ipymolstar 0.1.0, one host of that viewer, has no handler for
  `focus`, `set_color`, `clear_highlight` and `clear_selection`: there those actions do
  nothing. Options that need live PDBe services (`superposition`, `ligand_view`,
  annotations, maps, lighting) are compared as declared settings; the atoms those views
  draw are not modelled. Camera focus and highlight are compared by the atoms their
  selections resolve to; they were not read back from the viewer.
- **Default components on the API track.** Which atoms are polymer, ligand, ion or
  water comes from the atom tables, which Mol\* 5.9.0 filled; pdbe-molstar 3.3.2
  carries an older Mol\*. A bare load of 73 panel entries was compared with the viewer.
  Two differences were found and are now modelled as measured: the acetyl cap of 1HRC
  is not in the viewer's "non-standard" component, and Arg167 of 1AKE is not in its
  ligand component. The AlphaFold models and entries outside the panel were not
  compared.
- **UniProt-numbered API selections** resolve through the frozen SIFTS tables, which
  match PDBe's updated mmCIF (the file a `molecule_id` load fetches) and, for an
  AlphaFold model, the model file itself (read back in pdbe-molstar 3.3.2). On any other
  file loaded by URL (RCSB's mmCIF, a PDB-format file) the viewer has no SIFTS columns
  and selects nothing, and so does the replay. PDBe's `.bcif` and model-server URLs are
  taken to carry the columns; that was not read back.
- **A cartoon needs a trace atom** on both tracks: a polymer residue with no CA (O3′ for
  a nucleotide) has no ribbon in the viewer (Pro552 of 3ERT, the acetyl cap of 1HRC),
  and none in the replay.
- **F1 arithmetic differs slightly between the tracks** (see "What the viewer does").
  Task success is the same idea on both: the final state is exactly right.

## How well the grader itself works

`scripts/grader_controls.py` builds a control set from the frozen structure panel
(78 entries; 1HSG, the API prompt's worked example, is left out): pairs of a reference
and an answer whose verdict is known from how the pair was made.

- **Identical**: the answer is the reference. Must pass.
- **Equivalent**: the answer is rewritten so that the viewer shows the same (a residue
  range as a list; label instead of author numbering, on residues where the two name
  the same atoms; `all` for `polymer` under a cartoon; a colour as hex; one component
  or several; a nested colour node or flat components; a cartoon asked for on an ion;
  on the API track also UniProt numbering instead of author numbering, a wrong step
  that a later step undoes, …). Must pass.
- **Wrong**: the viewer shows something else (the neighbouring residue; the other
  chain; the label number in the author-number field on structures where they differ;
  the UniProt number used as the author number on structures with an offset; another
  colour; a nearby shade; another representation; a missing or an extra component;
  another copy of the ligand; another entry; …). Must fail.

Six kinds were added after the audits of 2026-11-16, each for a fault an auditor
found: the API prompt's example form (residue and its stretch of cartoon in one colour)
and an unrequested `hide_water` on the default view (must pass); the polymer hidden,
and UniProt keys on a file without SIFTS columns (must fail); UniProt keys on an
AlphaFold model (must pass; five controls, one per model in the panel); and, on the MVS
track, a scene whose file cannot load (must fail).

Four kinds were added after the pilot of 2026-11-16 (`PILOT.md`): on the MVS track a
stretch drawn a second time in the same representation type over the whole (must fail:
it is hidden) and the same two components in the other order (must pass); and on both
tracks the right answer on an AlphaFold file address that does not exist (must fail;
five controls each, one per model in the panel).

Five kinds are about unstated attributes: on the MVS track a reference with no colour
node answered in a palette colour (must pass) and answered with the stated colour all
over (must fail); on the API track "a grey cartoon and the ligand in a colour" answered
on the viewer's default view (must pass; these controls carry the task's accepted call
forms), with another ligand colour, and without the grey (must fail). The viewer shows
two different pictures for the must-pass pairs by construction, so their verdict is the
ruling's, not the viewer's.

A **false pass** is a wrong answer graded as a success; a **false fail** is an identical
or equivalent answer graded as not a success. The numbers are in
`tests/controls/summary.json` (per track and per kind), and `tests/test_controls.py`
fails if the grader stops agreeing with any control.

| track | controls | kinds (equivalent / wrong) | false pass | false fail | graders before this work: false pass / false fail |
|---|---|---|---|---|---|
| MVS | 1,155 on 78 entries | 25 / 26 | 0 of 505 | 0 of 650 | 16 of 505 / 284 of 650 (October path grader, F1 = 1 as success) |
| API | 1,020 on 74 entries | 22 / 23 | 0 of 445 | 0 of 575 | 95 of 445 / 319 of 575 (July sequence grader, F1 = 1 as success) |

Read these zeros with care: the grader was corrected until it agreed with every
control, so they show that the rules above are implemented, not how often an unforeseen
way of writing an answer is misjudged. What keeps them honest is that the verdicts do
not come from the grader:

- **MVS.** `scripts/grader_controls.py --viewer` loads both scenes of a pair in headless
  Mol\* 5.9.0, reads back which atoms each representation object draws and in what
  colour and opacity, and confirms that the viewer draws the same for a must-pass pair
  and something different for a must-fail pair. The same run confirms, scene by scene,
  that the grader's resolved state equals the viewer's, and probes every representation
  type on several kinds of component in every panel entry. Seven kinds cannot be read
  back this way and are not viewer-checked (camera focus, label text, the chain-id
  theme, assembly, another entry).
- **API.** `--viewer-api N` replays a sample of the call lists in real pdbe-molstar
  3.3.2 and compares the end state with the grader's replay (selections atom for atom,
  components, representations, colouring), and does the same for a bare load of every
  panel entry. Focus, highlight and UniProt-numbered selections are not read back, so
  for those kinds the verdict rests on the construction of the pair alone.

The result of both runs is `tests/controls/viewer_check.json`.
