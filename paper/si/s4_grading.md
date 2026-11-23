## S4. Grading rules in full

### S4.1 Facts

The drawn state is cut into facts, each of weight 1.

- **Facts about atoms.** An atom's drawing is the set of its styles (a style is a
  representation type with a colour and an opacity). All atoms with the same set form one fact.
- **Facts about the scene**, when present: each label text with the atoms it is attached to; each
  tooltip text with its atoms; the camera target (the atoms it frames); each distance line or
  other drawn primitive; a request that the viewer compute and draw non-covalent interactions
  around some atoms; the structure type when it is not the first deposited coordinate set (an
  assembly, or another coordinate set of the entry); the background colour when it is not the default.

The structure is the frame in which facts are stated, not a fact. A file that an answer
downloads and never draws changes nothing on screen and is not counted. A second structure
that is drawn is unrequested drawing.

### S4.2 F1

Recall is the mean, over the reference's facts, of how much of each the answer has. Precision
is the mean, over the answer's facts, of how much of each the reference has. F1 is their
harmonic mean. Two drawn states are compared, that of the reference and that of the answer;
*the other* below means the other of these two. How much of a fact the other drawn state has:

- *Fact about atoms*: the mean over its atoms of the share of the atom's styles that the
  other also has. A style that the other has with the same representation type and another
  colour or opacity counts half. An atom that the other does not draw counts 0. Styles that
  the other has in addition do not lower this number; they lower the number computed in the
  other direction.
- *Label, tooltip, interaction request*: the share of the atoms carrying it that carry the
  same in the other.
- *Camera target*: the overlap (intersection over union) of the two targets, as whole
  residues.
- *Primitive, structure type, background*: 1 if the other has the same, else 0.

An answer that draws nothing scores 0 on every score when the reference draws something.

### S4.3 Target score

The *target's drawing* is the set of the reference's styles that lie wholly inside the target
atoms (in the running example the {{ex.color}} {{ex.rep}} of the residue; a cartoon of the
whole chain that passes through the residue is not part of it). It is
cut into facts as above. For each fact, counting items (one item is one style on one atom):

- *wanted*: the reference's items;
- *credit*: 1 for each wanted item that the answer has, ½ for each that the answer draws in
  the right representation with another colour or opacity;
- *attempted*: the wanted items that the answer drew in the right representation, in any
  colour or opacity;
- *spill*: items outside the target that belong to a style of the answer (one representation
  in one colour and opacity) which also earned credit on the target, where the reference
  draws no such thing. The style is the answer's own: if it drew the target in red where
  yellow was asked, its red items outside the target are spill. The requested representation
  drawn outside the target in a separate style of another colour is not spill but
  unrequested context;
- *extra*: items on the target from a style of the answer that is confined to the target, in
  a representation type that the reference does not draw there.

Target recall = credit / wanted. Target precision = credit / (attempted + spill + extra). The
target score is the harmonic mean of the two, each averaged over the target's facts and over
the facts about the scene that touch the target atoms (a label on the target, for example).
A target with one fact, as in the running example, needs no averaging. The three rules for extra drawing follow from these counts. *Spill*: the answer repeats, on
atoms outside the target, the style that it drew on the target in the requested
representation, whatever its colour (red spacefill on the whole chain, where yellow spacefill
on one residue was asked for, is spill); the items count against target precision. *Extra
on the target*: a style of the answer in another representation that is confined to the
target; its items count against target precision. *Unrequested context*: any other style of
the answer that is not confined to the target (a cartoon or a surface of the chain, of the
whole chain or of part of it) is ignored, even if it would hide the target in a picture; F1
and task success count it. Table S1 gives the score of one example of each rule. The line
between the second and the third rule is whether the style is confined to the target. It is a
convention: a second representation on the target alone is read as part of the answer to "how
should these atoms be drawn?", and a style that also covers other atoms is read as background.
Rows S9 and S10 of Table S1 show the two cases. Row S9 by hand: the target has
{{ex.n_target_atoms}} atoms and one requested style, so wanted, credit and attempted are each
{{ex.n_target_atoms}}; the added {{ex.other_rep}} is confined to the target, so extra is
{{ex.n_target_atoms}}; target precision is {{ex.n_target_atoms}}/{{ex.n_target_atoms_twice}}
= {{ex.mvs.extra.target_precision:.2f}}, target recall is 1, and the target score is
{{ex.mvs.extra.target:.2f}}. In row S10 the {{ex.other_rep}} also covers the two neighbours,
is not confined to the target, and enters no count.

Tasks without a stored target are of two kinds (Section 4.2 of the paper). A single request
without one, such as a change of the background colour, uses everything the reference draws or
changes as its target. A follow-up task without one, in which the edit takes something away,
changes or restores a setting of the whole view, or needs no change, has no target score, and averages leave it out: there are no atoms
"drawn as asked", and to use everything the reference draws would give full marks to the
start state returned unchanged.

### S4.4 Accepted answers and follow-up turns

A task may list further right answers. An answer is graded against the reference and each of
them, and the best result counts (a success first, then the highest F1). A name-resolution
task lists the entries that match the named protein. The list was frozen on
{{resolve.retrieved:date}} from the web services of the RCSB PDB (the US member site of the
Protein Data Bank): it holds every current PDB entry
in which a chain is aligned to the UniProt accession of the named protein over at least
{{resolve.min_residues}} residues in total, or over at least half of the UniProt sequence if
that is shorter. Where the request names several proteins, a ligand or bound DNA, the entry
must hold all of them. The references of this category select by kind (the polymer, the
protein, the nucleic acid) or by the identifier of a compound, never by chain identifier or
residue number, so the same selections can be evaluated on any entry. An answer on another
listed entry that is in the structure panel ({{resolve.n_other_panel_entries}} such entries
exist) is graded on drawn state: the reference's selections and the answer's are both
resolved on the atom table of that entry. Where the entry is outside the structure panel,
selections are compared as written (Section S4.8), and F1, task success and the target score
all come from that comparison. A follow-up task gives a start
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
- Two representations on overlapping components are both drawn; the atom carries both styles.
- Author and label numbering are different columns and are never pooled.
- A reference that colours "by chain" is matched by the same colour theme, or by an answer
  that gives every chain one colour of its own, all different.

Colour. Two colours count as the same if their red, green and blue values (0 to 255) each
differ by at most {{colour.tolerance}}; the distance between two colours is the largest of
these three differences. Requests use a palette of {{colour.palette_n}} named colours. Its
two closest colours ({{colour.closest_pair}}) are {{colour.closest_pair_distance}} apart. In
the pilot run, {{colour.oct.n_comparable:,}} colour values in answers could be compared with
a requested colour. Of these, {{colour.oct.exact:,}} were exactly the requested colour, and
each of the other {{colour.oct.inexact}} was at least {{colour.oct.closest_inexact}} away
from it, so the tolerance decided no case.

Not graded on the scene track: metadata, the host of the structure file, the order of
children, representation size and surface kind, the appearance of labels and primitives, explicit camera
numbers.

### S4.6 What the viewer does (call-list track, PDBe Mol\* 3.3.2)

The grader replays the calls in order with a port of the viewer's own code paths (selection,
colouring, representation, visibility, reset). The facts of the drawn state that a call list
ends in are its differences from the default view of the same structure, that is, from a
*bare load*, a load with no further call:

| Fact | One per |
|:---|:---|
| atoms | each group of atoms whose drawing a colouring call changed, now drawn the same way |
| scene | the effect of the viewer's global representation setting and of the hide switches on all other atoms |
| focus, highlight, tooltip | the residues framed, the residues highlighted, each tooltip text with its atoms |
| assembly, preset, option, canvas | the assembly identifier, the load preset, each non-default option, each non-default canvas setting |

A bare load has no facts and scores 0, unless a bare load is the reference. Two details differ
from the scene track. A fact about atoms scores the share of its atoms that end up looking
exactly the same in the other drawn state; atoms that reference and answer both changed but
that look different count half. The target score is computed on the changes from a bare load
on the target atoms (a style added, or a default style removed), with the same counts of
wanted, credit, attempted, spill and extra as on the scene track. Selections in
UniProt numbering are resolved through the frozen SIFTS tables; the viewer reads the same
mapping from the structure file that PDBe distributes.

### S4.7 Outcomes

**Table S5. The outcome of an answer and how it is scored.** *As graded*: the answer receives
the scores that the grader computes. Strict averages count every answer with the score in the
last column; valid-only averages count the answers with outcome "valid". *Class*: the three
classes of Section 4.4 of the paper. An answer that was cut off at the token limit gets the
outcome of the text that arrived and is counted apart from other invalid answers in the outcome
tables.

| Track | Outcome | Class | Meaning | Score |
|:---|:---|:---|:---|:---|
| both | invalid JSON | unshowable | the answer contains no parseable JSON of the right outer shape | 0 |
| scene | not a scene | unshowable | JSON, but not a scene tree | 0 |
| scene | rejected by the viewer | unshowable | a scene tree that the validation of Mol\* 5.9.0 rejects | 0 |
| scene | structure failed to load | unshowable | a well-formed scene that names a file which Mol\* cannot load: a web page in place of a structure file, a file on an unknown host, or a file read in the wrong format | 0 |
| scene | valid | valid | Mol\* accepts the scene and can load its file | as graded (0 on every score if the entry is not one that the task accepts) |
| call list | not valid | schema-breaking | a JSON list that breaks the call schema (unknown call, wrong field type) | as graded: the replay ignores what the viewer would ignore |
| call list | valid | valid | a call list that fits the schema | as graded |

### S4.8 Known limits of the grader

- **Assemblies.** Atom tables hold the first coordinate set of the deposited unit. An assembly is a fact (its
  identifier), and atoms are compared on the deposited unit. Selections of single symmetry
  copies are not modelled.
- **Other coordinate sets of an entry that has several** are compared on the atoms of the
  first set, and the index of the coordinate set is a fact.
- **Entries outside the structure panel** have no atom table. An answer on such an entry (possible only
  in the name-resolution category) is compared as written: two selections are equal only if
  spelled the same way.
- **Colour themes** other than colouring by chain or by entity are matched only by the same
  theme.
- **Distance lines.** The target score does not notice a missing distance line. Lines, labels
  and the camera target were not read back from Mol\*; they are compared as declared.
- **Lone ions.** {{corpus.n_ion_sphere_tasks}} tasks, half of them on each track, ask for a
  metal ion as a sphere, and the reference draws it as spacefill. An answer that draws the ion as ball-and-stick uses another
  representation and, by the general rule, receives a target score of 0, although a single
  atom looks much the same in both.
- **The file that PDBe Mol\* fetches.** The atom tables are built from the archive file of
  each entry, and the replay in PDBe Mol\* loaded that file. Left to itself, the viewer
  fetches PDBe's own copy of the entry, which also carries the SIFTS mapping; the mapping
  tables are read from that copy. The atom records of the two copies were not compared.
- **Call-list actions that one host ignores.** The call-list track grades what each call does
  in PDBe Mol\* 3.3.2. The notebook widget that hosts this viewer for Python users (ipymolstar
  0.1.0) has no handler for four of the actions (camera focus, setting the highlight colour,
  clearing the highlight and clearing the selection); there they do nothing.
- **Call-list track.** Four options fetch data from live services (superposition of related
  structures, the close-up view of one ligand, annotations from databases, experimental
  density maps). They are compared as declared settings, and so is lighting. Camera focus,
  highlight and UniProt-numbered selections were not read back from the viewer. Which atoms
  are polymer, ligand, ion or water comes from tables filled by Mol\* 5.9.0, whereas PDBe Mol\*
  3.3.2 carries an older Mol\*; a bare load of {{controls.viewer.api.bare_loads}} entries was
  compared with the viewer, and the two differences found are modelled as measured.
- **A second cartoon.** An answer that recolours a stretch by adding a second coloured cartoon
  over the first draws two cartoons there and fails task success.
