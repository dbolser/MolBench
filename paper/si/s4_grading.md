## S4. Grading rules in full

### S4.1 Facts

The drawn state is cut into facts, each of weight 1.

- **Facts about atoms.** An atom's drawing is the set of its draws (representation type,
  colour, opacity). All atoms with the same set form one fact.
- **Facts about the scene**, when present: each label text with the atoms it is attached to; each
  tooltip text with its atoms; the camera target (the atoms it frames); each distance line or
  other drawn primitive; a request that the viewer compute and draw non-covalent interactions
  around some atoms; the structure type when it is not the deposited model (an assembly,
  another model); the background colour when it is not the default.

The structure is the frame in which facts are stated, not a fact. A file that an answer
downloads and never draws changes nothing on screen and is not counted. A second structure
that is drawn is unrequested drawing.

### S4.2 F1

Recall is the mean, over the reference's facts, of how much of each the answer has. Precision
is the mean, over the answer's facts, of how much of each the reference has. F1 is their
harmonic mean. How much of a fact the other side has:

- *Fact about atoms*: the mean over its atoms of the share of the atom's draws that the other side
  also has. A draw that the other side has with the same representation type and another
  colour or opacity counts half. An atom that the other side does not draw counts 0. Draws that
  the other side has in addition do not lower this number; they lower the number computed in
  the other direction.
- *Label, tooltip, interaction request*: the share of the atoms carrying it that carry the
  same on the other side.
- *Camera target*: the overlap (intersection over union) of the two targets, as whole
  residues.
- *Primitive, structure type, background*: 1 if the other side has the same, else 0.

An answer that draws nothing scores 0 on every score when the reference draws something.

### S4.3 Target score

The *target's drawing* is the set of the reference's draws that lie wholly inside the target
atoms (in the running example the {{ex.color}} {{ex.rep}} of the residue; a cartoon of the
whole chain that passes through the residue is not part of it). It is
cut into facts as above. For each fact, counting (atom, draw) items:

- *wanted*: the reference's items;
- *credit*: 1 for each item the answer has, ½ for each that the answer draws in the right
  representation with another colour or opacity;
- *attempted*: the items the answer drew at all;
- *spill*: items outside the target on which the answer repeats what it drew on the target,
  where the reference draws no such thing;
- *extra*: items on the target from an answer draw that is confined to the target, in a
  representation type that the reference does not draw there.

Target recall = credit / wanted. Target precision = credit / (attempted + spill + extra). The
target score is the harmonic mean of the two, each averaged over the target's facts and over
the facts about the scene that touch the target atoms. A draw of the answer that is not
confined to the target (a cartoon or a surface of the whole chain) is unrequested context and
is ignored, even if it would hide the target in a picture; F1 and task success count it. A task without a stored target
uses everything the reference draws.

### S4.4 Accepted answers and follow-up turns

A task may list further right answers. An answer is graded against the reference and each of
them, and the best result counts (a success first, then the highest F1). A name-resolution
task lists the entries that match the named protein; an answer on another listed entry is
graded against the reference's drawing resolved on that entry. A follow-up task gives a start
state and an edit request; the answer is the complete new scene or call list, and only the
drawn state it results in is graded. If the right answer is to change nothing, the reference is the start
state.

### S4.5 What the viewer draws (scene track, Mol\* 5.9.0)

Each rule was read back from the running viewer.

- Ball-and-stick, line, spacefill and surface representations draw every atom of their
  component. Cartoon, backbone and putty draw polymer residues, and only those whose trace atom
  (Cα of an amino acid, O3′ of a nucleotide) is in the component.
- A cartoon, backbone or putty requested on a component with no polymer atoms is drawn as
  ball-and-stick, and is graded as that.
- A component whose selector matches no atom is not created.
- A representation with no colour is white. Colour nodes apply in order, later over earlier.
  A colour value that is not a known name or a hexadecimal code makes Mol\* reject the scene.
- Two representations on overlapping components are both drawn; the atom carries both draws.
- Author and label numbering are different columns and are never pooled.
- A reference that colours "by chain" is matched by the same colour theme, or by an answer
  that gives every chain one colour of its own, all different.

Not graded on the scene track: metadata, the host of the structure file, the order of
children, representation size and surface kind, label and primitive styling, explicit camera
numbers.

### S4.6 What the viewer does (call-list track, PDBe Mol\* 3.3.2)

The grader replays the calls in order with a port of the viewer's own code paths (selection,
colouring, representation, visibility, reset). The facts of the drawn state that a call list
ends in are its differences from a bare load of the same structure (a load with no further
call):

| Fact | One per |
|:---|:---|
| atoms | each group of atoms whose drawing a colouring call changed, now drawn the same way |
| scene | the effect of the global style and the hide switches on all other atoms |
| focus, highlight, tooltip | the residues framed, the residues highlighted, each tooltip text with its atoms |
| assembly, preset, option, canvas | the assembly identifier, the load preset, each non-default option, each non-default canvas setting |

A bare load has no facts and scores 0, unless a bare load is the reference. Two details differ
from the scene track. A fact about atoms scores the share of its atoms that end up looking exactly
the same on the other side; atoms that both sides changed but that look different count half.
The target score is computed on the changes from a bare load on the target atoms. Selections in
UniProt numbering are resolved through the frozen SIFTS tables.

### S4.7 Outcomes

**Table S4. The outcome of an answer and how it is scored.** *As graded*: the answer receives
the scores that the grader computes. Strict averages count every answer with the score in the
last column; valid-only averages count the answers with outcome "valid". An answer with one of
the first three outcomes *cannot be shown*. An answer that was cut off at the token limit
is counted apart from a malformed one in the outcome tables.

| Track | Outcome | Meaning | Score |
|:---|:---|:---|:---|
| both | invalid JSON | the answer contains no parseable JSON of the right outer shape | 0 |
| scene | not a scene | JSON, but not a scene tree | 0 |
| scene | rejected by the viewer | a scene tree that the validation of Mol\* 5.9.0 rejects | 0 |
| scene | valid | Mol\* accepts the scene | as graded |
| call list | not valid | a JSON list that breaks the call schema (unknown call, wrong field type) | as graded: the replay ignores what the viewer would ignore |
| call list | valid | a call list that fits the schema | as graded |

### S4.8 Known limits of the grader

- **Assemblies.** Atom tables hold model 1 of the deposited unit. An assembly is a fact (its
  identifier), and atoms are compared on the deposited unit. Selections of single symmetry
  copies are not modelled.
- **Other models of a multi-model entry** are compared on the atoms of model 1, with the model
  index as a fact.
- **Entries outside the panel** have no atom table. An answer on such an entry (possible only
  in the name-resolution tier) is compared as written: two selections are equal only if
  spelled the same way.
- **Colour themes** other than colouring by chain or by entity are matched only by the same
  theme.
- **Distance lines.** The target score does not notice a missing distance line. Lines, labels
  and the camera target were not read back from Mol\*; they are compared as declared.
- **Lone ions.** An answer that draws a lone ion as ball-and-stick receives a target score of 0.
- **Call-list actions that one host ignores.** The call-list track grades what each call does
  in PDBe Mol\* 3.3.2. The notebook widget that hosts this viewer for Python users (ipymolstar
  0.1.0) has no handler for four of the actions (camera focus, setting the highlight colour,
  clearing the highlight and clearing the selection); there they do nothing.
- **Call-list track.** Options that need live services (superposition, ligand view,
  annotations, density maps, lighting) are compared as declared settings. Camera focus,
  highlight and UniProt-numbered selections were not read back from the viewer. Which atoms
  are polymer, ligand, ion or water comes from tables filled by Mol\* 5.9.0, whereas PDBe Mol\*
  3.3.2 carries an older Mol\*; a bare load of {{controls.viewer.api.bare_loads}} entries was
  compared with the viewer, and the two differences found are modelled as measured.
- **A second cartoon.** An answer that recolours a stretch by adding a second coloured cartoon
  over the first draws two cartoons there and fails task success.
