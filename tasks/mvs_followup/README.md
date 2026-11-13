# Follow-up turns, MVS track (generated; do not edit)

Written by `scripts/generate_followup_tasks.py` (seed 20261113); rerun it to rebuild these files byte for byte.
Each task is a start state (an MVS scene), an edit request, and the complete final state
as the reference. Start state and reference are built from the same component list,
from the frozen panel only. Only the final state is graded.

- **58 tasks** on 46 structures, at most 3 per structure; 9 held back (structures: 1f88, 1mbn, 1udt, 1y26, 2p4e, 3ave, 6tha, 8k7f).
- **10 need no change** (`context.noop`): the reference is the start state.
- **36 have a twin** on the API track (`twin_of`): same request, same structure, same target atoms.

| family | tasks | edit | how the reference is derived |
|---|---:|---|---|
| `fu-recolour-ligand` | 3 | recolour one existing component | start: polymer + main ligand, each one colour; the ligand's colour replaced |
| `fu-recolour-chain` | 2 | recolour one existing component | start: two chains, each one colour; the second chain's colour replaced |
| `fu-also-colour-chain` | 2 | also: colour a second component | start: first chain coloured, second not; a colour added to the second |
| `fu-other-chain` | 2 | ellipsis: colour the component not yet coloured | start: first of exactly two chains coloured, second not; a colour added to the second, which the request calls "the other chain" |
| `fu-referent-colour` | 3 | recolour a component named by its current colour | start: two chains in two colours; the chain that has the named colour is recoloured |
| `fu-same-colour-as` | 2 | recolour by reference to the scene | start: polymer + ligand; the ligand takes the polymer's colour, read from the start state |
| `fu-swap-colours` | 2 | recolour by reference to the scene | start: two chains in two colours (entries with exactly two polymer chains); colours exchanged |
| `fu-add-residue` | 4 | add a component (a residue), keeping the rest | start: polymer + ligand; one residue (author chain + number, checked to select exactly that residue) added as coloured ball-and-stick |
| `fu-hide-water` | 2 | remove / hide something | start: polymer (+ waters drawn, MVS); MVS drops the water component, API sets hide_water |
| `fu-undo-grey` | 2 | undo-like recolour | start: grey polymer, coloured ligand; the ligand set to grey |
| `fu-focus-ligand` | 2 | also: camera focus | start: polymer + ligand; a camera focus on the ligand added |
| `fu-background` | 2 | also: a scene setting | start: polymer + ligand; a black background added (MVS canvas node, API bg_color) |
| `fu-noop-colour` | 2 | no change: already true | the ligand already has the requested colour: reference = start state |
| `fu-noop-shown` | 2 | no change: already true | the polymer already is a cartoon: reference = start state |
| `fu-noop-hidden` | 2 | no change: already true | no water is drawn (MVS) / hide_water is already set (API): reference = start state |
| `fu-noop-question` | 2 | no change: a question | a question about the structure: reference = start state |
| `fu-noop-spin` | 2 | no change: the format cannot express the request (MVS only) | MVS cannot express motion: reference = start state |
| `fu-it-colour` | 2 | pronoun: recolour (MVS only) | start: the ligand alone (one copy); "it" recoloured |
| `fu-it-surface` | 1 | pronoun: change a representation (MVS only) | start: the polymer alone; "it" changed from cartoon to surface, colour kept |
| `fu-rep-ligand` | 2 | change a representation (MVS only) | start: polymer + ligand; the ligand's representation set to spacefill, colour kept |
| `fu-rep-polymer` | 2 | change a representation (MVS only) | start: polymer + ligand; the polymer's representation set to surface, colour kept |
| `fu-add-ligand` | 2 | add a component (the ligand), keeping the rest (MVS only) | start: polymer alone; the main ligand added as coloured ball-and-stick |
| `fu-add-chain` | 2 | add a component (a chain), keeping the rest (MVS only) | start: first chain alone; the second chain added as a coloured cartoon |
| `fu-remove-ligand` | 2 | remove / hide something (MVS only) | start: polymer + ligand; the ligand component dropped |
| `fu-only-chain` | 2 | narrow to one component (MVS only) | start: two chains; the second chain's component dropped |
| `fu-add-label` | 2 | also: a label (MVS only) | start: polymer + ligand; a label with the quoted text added to the ligand |
| `fu-remove-label` | 1 | remove / hide something (MVS only) | start: polymer + labelled ligand; the label dropped |
| `fu-opacity` | 2 | change one property of an existing component (opacity) (MVS only) | start: polymer surface + ligand; an opacity added to the surface |

## What each task records (`provenance`)

- `edit`: the edit kind; `noop_kind`: why no change is right (already true, a question,
  not expressible in the format); `referent`: why a pronoun or description ("it", "the
  red chain") names one thing only in the start state.
- `preserved`: the parts of the start state the edit must leave alone, in the form of
  `target` parts. Handing one part to the grader as the task's target gives a
  *preserved* score for it; the reference and the start state both score 1 on every
  part (checked). An answer that rebuilds the scene and loses an earlier choice scores
  below 1 there. `null` when the edit touches everything that was set.
- `removed`: what the edit takes away. On the MVS track the reference draws nothing
  there, so it cannot be a target; such tasks have `target: null`.
- `difficulty`: whether the residue's author number differs from its label number,
  whether the entry's author chain ids differ from its label chain ids, whether the
  request leans on the start state for a referent. Requests give the ligand's code and
  use author numbering, so no ligand identity or UniProt mapping has to be looked up.
- `checks`: what the generator verified before writing the file, with the controls it
  graded (other ways of writing the same final state must succeed; the edit made on an
  empty viewer, and known slips, must not).

## Left out, and why

- **Switch to another structure** ("now show 4HHB instead"): the task format refuses a
  start state that loads a structure the reference does not (`molbench/tasks.py`), so
  such a task cannot be written yet.
- **A component the user named earlier** (issue #5): the vendored MVS reference and the
  API have no component names to refer back to.
- **"It" on the API track**: a bare load already draws everything, so no start state
  has a single thing "it" could mean. The API twins of the pronoun tasks are the ones
  that name a component by its colour or as "the other chain".
- **Requests the format cannot express**, other than spinning on the MVS track: for a
  distance-based selection or a superposition the unchanged state is not the only
  defensible answer, so they are not tasks here.
- **A target for something removed, on the MVS track**: see `removed` above.

Held-back structures are the fifth of the panel with the smallest SHA-256 of
`"molbench-heldback-v1:<id>"` (a rule on the structure alone), unless the generator was
given a list.
