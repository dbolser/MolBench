## 3. Building the benchmark

A task is a request, a reference answer, the atoms the request is about (the *target*), and a
record of how the reference was made. No reference is written by hand. This section follows
the running example from public data to a finished task, and then describes the corpus as a
whole.

### 3.1 Frozen public data

**Structures.** All tasks use a fixed panel of {{panel.n}} structures: {{panel.n_pdb}} PDB
entries [@wwpdb2019] and {{panel.n_alphafold}} predicted models from the AlphaFold Protein
Structure Database [@varadi2024afdb]. The panel was chosen for coverage, not at random: small
and large folds, protein–ligand complexes, haem and metal sites, disulfide-rich proteins,
nucleic acids, glycans, membrane proteins, and biological assemblies that differ from the
deposited model. {{panel.n_xray}} entries were solved by X-ray crystallography,
{{panel.n_cryoem}} by cryo-electron microscopy and {{panel.n_nmr}} by nuclear magnetic
resonance. Every feature we claim for an entry is verified in its file by the build script, or
the build fails. In {{panel.n_offset}} structures at least one residue has an author number
that differs from its UniProt number. Entries are limited to {{panel.max_atoms:,}} atoms so that
they render quickly ({{panel.n_over_size_limit}} larger entries are kept from earlier tasks).
The Supporting Information (SI, Section S3) lists the panel and its selection rule.

**Disease proteins and variants.** {{panel.n_disease_proteins}} human disease proteins are
listed by UniProt accession, and one structure per protein is chosen by a scripted rule
(coverage of variant positions, then resolution; SI Section S3). Whether a structure is
numbered differently from UniProt played no part in the choice. For each protein we took every
single-residue missense variant that UniProt reports as pathogenic or likely pathogenic with
ClinVar as a source: {{variants.n_candidates:,}} candidates. We then asked ClinVar itself.
UniProt lists a variant as pathogenic when any one submission to ClinVar says so, whereas
ClinVar's own classification aggregates all submitters. We kept a candidate only if its ClinVar
variant record names the same protein change and carries the aggregate classification
"Pathogenic", "Likely pathogenic" or "Pathogenic/Likely pathogenic". This removed
{{variants.n_removed_by_clinvar}} candidates ({{variants.removed_share:.0%}}), most of them
classified as conflicting or of uncertain significance, and left {{variants.n_confirmed:,}}.
ClinVar was read on {{variants.clinvar_retrieved}}.

**Atom tables and residue mapping.** For each structure we store two frozen tables. The *atom
table* lists every atom with its chain and residue in both author and label numbering; it is
built from the deposited file and compared with what the viewer itself selects (Section 3.7).
The *mapping table* holds the SIFTS correspondence between each observed residue and its
UniProt position. Generators and graders read only these tables. Nothing is fetched while a
task is built from the tables, graded or loaded.

### 3.2 From data to a task: the running example

The clinical generator produced the running example in six steps.

1. **Variant.** From the confirmed list it draws {{ex.gene}} {{ex.variant}} (UniProt
   {{ex.accession}}, {{ex.hgvs}}; ClinVar record {{ex.clinvar_vcv}}, "{{ex.disease}}",
   classified {{ex.clinvar_classification}}). The record's review status is
   "{{ex.clinvar_review_status}}"; we return to what that means in Section 9.
2. **Structure.** The panel structure for {{ex.accession}} is {{ex.entry}}, human lysozyme at
   {{ex.resolution}} Å resolution.
3. **Mapping.** The mapping table says that UniProt positions
   {{ex.map_uniprot_first}}–{{ex.map_uniprot_last}} are author residues
   {{ex.map_auth_first}}–{{ex.map_auth_last}} of author chain {{ex.auth_chain}}. Position {{ex.uniprot_position}} is therefore author
   residue {{ex.auth_number}} (label chain {{ex.label_chain}}, label residue
   {{ex.label_number}}).
4. **Identity check.** The atom table must hold the wild-type amino acid at that residue. It
   does: {{ex.wild_type}}{{ex.auth_number}}, {{ex.n_target_atoms}} atoms. Had the structure
   carried an engineered substitution there, the variant would not be offered for this entry.
5. **Wording.** A seeded random choice picks one of the template's three wordings, the colour
   ({{ex.color}}) and the representation ({{ex.rep}}). The request names the structure and the
   variant. It never says which residue of the structure is meant.
6. **Reference, twice.** The script writes the reference scene (author chain
   {{ex.auth_chain}}, author residue {{ex.auth_number}}, {{ex.color}} {{ex.rep}}) and the
   reference call list (load the entry; draw UniProt {{ex.accession}} position
   {{ex.uniprot_position}} as {{ex.color}} {{ex.rep}}). It then confirms that both resolve to
   the same {{ex.n_target_atoms}} atoms, and stores them as the target of both tasks.

The reference holds only what the request states: one residue, one representation, one colour.
It has no cartoon of the protein behind the residue, because the request does not ask for one.
Section 6.6 shows why this rule exists. SI Section S1 gives both tasks in full.

### 3.3 Eight tiers

Tasks are grouped into eight tiers by what a model must know beyond the request (Figure 2,
Table 1). Each tier has several *templates*: a template fixes what is asked, and a seeded
generator fills in the structure, the residues, the colours and the wording.
The corpus has {{corpus.n_templates}} templates; outside two small tiers no template supplies
more than {{corpus.max_template_share_other:.0%}} of a tier's tasks. SI Section S2 lists every
template with an example.

![**Figure 2. The eight tiers, with one request each.** Counts are tasks on the scene track / the call-list track; a dash means that the format cannot express the tier. Requests are quoted from the corpus.](generated/fig_tiers.svg)

- **Translation.** Everything needed is in the request: the entry, the chains, the residue
  numbers, the colours. The model only has to write it in the format.
- **Structure-grounded.** The request names a feature, such as the ligand, the disulfide bonds
  or the residues that hold a metal ion. Its atoms must be known from the structure. References
  are read from the entry's own records.
- **Interactions.** The request names atoms and a measurement between them, such as a hydrogen
  bond drawn as a labelled line.
- **Name resolution.** The request names a protein, not an entry ("a structure of human p53
  bound to DNA"). Any entry on a frozen list of matching entries is accepted, and the drawing
  is compared on the entry the model chose.
- **Clinical variant.** As in the running example. Of the {{clin.n}} tasks per track,
  {{clin.n_offset}} ({{clin.offset_share:.0%}}) have a target whose author number differs from
  its UniProt number, by {{clin.offset_min}} to {{clin.offset_max}} residues, and in
  {{clin.n_chain_differs}} the author chain identifier differs from the label chain identifier.
  {{clin.n_mature_name}} requests use a traditional name counted along the mature protein
  (the form found in older literature, such as transthyretin V30M) and say so. An answer that takes
  the number in the variant name as the author residue number is right in
  {{clin.n_face_value_right}} tasks and wrong in {{clin.n_face_value_wrong}}; results are
  reported for the two groups apart. {{clin.n_in_pairs}} tasks ask the same variant on two
  structures of one protein, and {{clin.n_sse}} also ask for the helix or strand around the
  residue.
- **Follow-up turn.** The model receives a start state and an edit request ("make the magenta
  chain plum") and returns the complete new state. Only the final state is graded, so an answer
  that loses an earlier choice fails. In {{corpus.followup.mvs.noop}} scene tasks and
  {{corpus.followup.api.noop}} call-list tasks the right answer is to change nothing.
- **Several right answers.** The request leaves one countable thing open. "Colour Lys29
  yellow" in an insulin entry with two B chains can mean either copy or both. The script lists
  every accepted final state (a median of {{corpus.accept.mvs.median_readings:.0f}} readings per
  task), and an answer that matches any of them is right.
- **Viewer settings.** Settings that only the call-list format can express, such as electron
  density maps, background and spin.

**Table 1. The corpus.** Tasks per tier and track, written as total (public + held back; Section
3.6). *Pairs*: requests posed on both tracks with the same target atoms. A dash means that the
format cannot express the tier.

{{include:generated/table_corpus.md}}

The {{corpus.n_tasks}} tasks ({{corpus.mvs.n}} scene, {{corpus.api.n}} call-list) use
{{corpus.n_structures}} of the {{panel.n}} panel structures. The one unused entry is the worked
example in the call-list prompt, which must not also be a task. No structure appears in more
than {{corpus.max_tasks_per_structure_tier_track}} tasks of one tier and track.

### 3.4 The same request in two formats

A wrong answer has two possible causes: the model did not know which atoms were meant, or it
knew and could not write them in the format. One format cannot separate the two. MolBench
therefore poses {{corpus.n_twin_pairs}} requests ({{corpus.twin_share_of_mvs:.0%}} of the scene
tasks) on both tracks, with identical wording and the same target atoms (Figure 3).

The two formats differ in kind. A MolViewSpec scene [@midlik2025mvs] is *declarative*: a tree
that states what to load, which atoms form a component, and how each component is drawn.
Nothing is on screen unless the scene says so. A call list is *imperative*: an ordered list of
calls to the PDBe Mol\* viewer, version 3.3.2 [@pdbemolstar]. The viewer starts with the whole
structure drawn in a default style, and each call changes that state, so order matters.

The formats also differ in what they demand for a clinical request, and we state this openly
because it shapes the comparison. The viewer behind the call-list track can select a residue by
UniProt accession and position and does the mapping itself. A scene has no such selector: the
model must produce author or label numbers. The running example's call-list reference uses the
UniProt selector; its scene reference uses author residue {{ex.auth_number}}. Either numbering
is accepted on either track if it resolves to the right atoms.

![**Figure 3. One request, two formats, the same target atoms.** The scene and the call list are shown in shortened form. Below: for each model, every pair falls into one of four cells by task success on each side. McNemar's test compares the two shaded cells, in which the model was right in one format only.](generated/fig_twins.svg)

Pairs exist in five tiers: translation ({{corpus.twins.translation}}), structure-grounded
({{corpus.twins.grounded}}), clinical ({{corpus.twins.clinical}}), follow-up
({{corpus.twins.followup}}) and several right answers ({{corpus.twins.accept_set}}).
{{corpus.n_mvs_without_twin}} scene tasks have no partner, because the call-list format cannot
draw a distance line, a text label or a transparent surface, or cannot be graded on an entry
outside the panel. {{corpus.twins.need_hide_toggle}} call-list partners need an extra step that
the request does not state: switching off parts of the viewer's default drawing. The paired
analysis is reported with and without them.

### 3.5 What a request may leave open

Requests written by people leave things unsaid, and a benchmark must decide what silence
means. We use one rule: **an attribute that the request does not state is free; one that it
states must match.** If the request gives no colour for a ligand, any colour is accepted, by
listing the alternatives in the task or by a rule of the grader. If it says "green", only green
is right. The same holds for the representation. Context works the other way round, because
context is drawing: an answer that adds a cartoon nobody asked for has drawn something
unrequested, and loses precision and task success (Section 4.2), while its target score is
unaffected.

### 3.6 Public and held-back tasks; wording

MolBench tasks have been public since May 2026, so a model released later may have seen
earlier tasks. Two measures address this. First, generators are seeded, and
{{corpus.heldback.n_structures}} structures were set aside before generation. The
{{corpus.heldback.n_tasks}} tasks on them ({{corpus.heldback.share:.0%}} of the corpus) form a
*held-back split*: no public task uses those structures, and the split is not published before
the final run. Results are reported for both splits and compared. Second, to measure
sensitivity to wording, {{corpus.n_requests_paraphrased}} requests of the public split have two
further phrasings each, a terse one and an indirect one, with the same reference
({{corpus.n_paraphrase_files}} additional task files, not counted in Table 1).

### 3.7 Checks on the corpus

Four checks involve no model (Figure 1, bottom row).

- **Reference against structure.** Every reference must select at least one atom, must name the
  residue that the generator intended, and must grade as exactly right against itself. Every
  accepted alternative must do the same.
- **Atom tables against the viewer.** Selections were read back from the real viewers. For the
  scene track, Mol\* 5.9.0 was run without a display and asked which atoms each representation
  holds. For the call-list track, call lists were replayed in PDBe Mol\* 3.3.2 and each
  selection compared atom for atom ({{controls.viewer.api.lists}} lists, all in agreement). A
  bare load of {{controls.viewer.api.bare_loads}} panel entries was compared in the same way.
- **Grader against a control set.** Section 4.5.
- **Format rules.** One script validates every task file against the written task format and
  refuses a corpus in which any check fails. The run refuses to start on such a corpus.
