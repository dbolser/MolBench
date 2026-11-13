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
  representation with another colour or opacity; `attempted` = how many the answer
  drew at all; `spill` = items *outside* the target on which the answer repeats what it
  drew on the target, where the reference draws no such thing (the answer coloured the
  whole chain red when one residue was asked for).
- **Target recall** = credit / wanted. **Target precision** = credit / (attempted +
  spill). The target score (`target_f1`) is the harmonic mean of the two, each averaged
  over the target's classes and over the scene facts that touch the target atoms
  (labels, tooltips, focus, interaction request).
- A task without a `target` field uses everything the reference draws as the target.
  The target score then differs from F1 only in ignoring what the answer draws
  elsewhere in another style.

A task's `target` is `{"selector": <MVS selector>}` and/or `{"data": [<API
selection>, …]}` (either form works on either track; both are resolved on the same atom
table), optionally with `"facts": ["focus", …]` to include a scene fact that has no
atoms in the target.

### Accepted alternatives and follow-up turns

- A task may list further right answers under `accepted`. The answer is graded against
  the reference and each of them; the best result counts (a success first, then the
  highest F1), and `matched_reference` says which one it was.
- An MVS task that names a protein rather than an entry lists the right entries under
  `accepted_ids`. An answer on another accepted entry is graded against the reference's
  drawing re-resolved on that entry.
- A follow-up task gives a start scene (`context`) and an edit request. The answer is
  always the complete new scene or call list, and **only its final state is graded**,
  against the reference final state. An answer that rebuilds the scene from scratch and
  lands on the right state is right; one that loses an earlier choice is not. If the
  right answer is "change nothing", the reference is the start scene. The context is not
  graded, but it must load (`grader.check_task`).

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
- **Colour.** A representation with no colour node is white. Colour nodes apply in
  order, each to its selector (default: everything), later ones over earlier ones. A
  ribbon residue takes the colour of its trace atom. Colour names are Mol\*'s lower-case
  names; `#rrggbb` and `#rgb` are read in either case; anything else (`"RED"`,
  `"rgb(255,0,0)"`, a number) makes Mol\* reject the whole scene.
- **Opacity** is set per representation; the default is 1. Two opacities within 0.05
  are the same.
- **Overlap.** Two representations on overlapping components are both drawn; the atom
  carries both draws.
- **Selections** are resolved exactly as Mol\* resolves them (author and label
  numbering are different columns and are never pooled; a residue-number range, a list
  of the same residues, and one component per residue are the same atoms).
- **Colour themes.** A colour node that names a Mol\* colour theme
  (`custom.molstar_color_theme_name`) has no fixed colours, so it is compared as the
  theme: the same theme matches. One further match is allowed, in one direction only:
  when the *reference* uses the `chain-id` or `entity-id` theme ("colour by chain"), an
  answer that gives every chain (entity) one colour of its own, all different, matches
  it. Explicit colours in the reference are matched only by those colours.

Not graded on the MVS track: the envelope and metadata, the file's host and format
variant, the order of children, representation size and surface kind
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
scores 0. Two details differ from the MVS track and are stated here so that the two
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
| MVS | `load_failed` | (legacy render path only) Mol\* accepted the tree but could not load it | 0 |
| API | `invalid_api` | a JSON list that breaks the call schema (an unknown action, a wrong field type) | as graded: the replay ignores what the viewer would ignore |
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
  `grader.check_task` reports such a task; no benchmark task is one.
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
  ligand component. The two AlphaFold models and entries outside the panel were not
  compared.
- **UniProt-numbered API selections** resolve through the frozen SIFTS tables, which
  match PDBe's updated mmCIF (the file a `molecule_id` load fetches).
- **F1 arithmetic differs slightly between the tracks** (see "What the viewer does").
  Task success is the same idea on both: the final state is exactly right.

## How well the grader itself works

`scripts/grader_controls.py` builds a control set from the frozen structure panel
(75 entries; 1HSG, the API prompt's worked example, is left out): pairs of a reference
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

A **false pass** is a wrong answer graded as a success; a **false fail** is an identical
or equivalent answer graded as not a success. The numbers are in
`tests/controls/summary.json` (per track and per kind), and `tests/test_controls.py`
fails if the grader stops agreeing with any control.

| track | controls | kinds (equivalent / wrong) | false pass | false fail | graders before this work: false pass / false fail |
|---|---|---|---|---|---|
| MVS | 1,030 on 75 entries | 22 / 22 | 0 of 440 | 0 of 590 | 0 of 440 / 222 of 590 (October path grader, F1 = 1 as success) |
| API | 850 on 69 entries | 18 / 17 | 0 of 340 | 0 of 510 | 75 of 340 / 247 of 510 (July sequence grader, F1 = 1 as success) |

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
