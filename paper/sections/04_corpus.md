## 3. Building the benchmark

A task is a request on one track, a reference answer, a record of how the reference was made
and, for most tasks, the atoms that the request is about (the *target*; Section 4.2). No
reference is written by hand. This section follows
the running example from public data to a finished task, and then describes the corpus as a
whole.

### 3.1 Frozen public data

**Structures.** All tasks use a fixed *structure panel* of {{panel.n}} structures, namely
{{panel.n_pdb}} PDB entries [@wwpdb2019] and {{panel.n_alphafold}} predicted structures from
the AlphaFold Protein Structure Database [@varadi2024afdb]. One PDB entry is reserved as the
worked example in a prompt, so tasks use {{corpus.n_structures}}. The panel was chosen for
coverage, not at random: proteins alone, with bound small molecules or metal ions, with DNA or
RNA, with attached sugars, and membrane proteins. Of the PDB entries, {{panel.n_xray}} were solved by X-ray
crystallography, {{panel.n_cryoem}} by cryo-electron microscopy and {{panel.n_nmr}} by nuclear
magnetic resonance. The {{panel.n_alphafold}} predicted structures are of
{{panel.alphafold_proteins}}; each of these proteins also has an experimental structure in the
panel, and a predicted structure is numbered as UniProt is. In {{panel.n_offset}} of the
{{panel.n}} structures at least one residue has an offset: its author number differs from its
UniProt number. Every
feature that we claim for an entry is verified in its file by the build script, or the build
fails. The Supporting Information (SI, Section S3) lists the panel, its features and its
selection rule.

**Disease proteins and variants.** The panel includes structures of
{{panel.n_disease_proteins}} human proteins in which missense variants (one amino acid
replaced by another) cause inherited disease. We chose the proteins by hand, as familiar
examples that have experimental structures. For each protein, one PDB entry was then chosen
by a scripted rule that did not look at how the entry is numbered (SI Section S3). A protein
can still have tasks on more than one structure: on its chosen entry, on its predicted
structure where the panel has one, and on another panel entry that also contains it ({{clin.n_structures_two_proteins:word}}
haemoglobin entries hold both the alpha and the beta chain). This is so for
{{clin.n_proteins_several_structures}} proteins.

The pool of variants was built in three steps (SI Table S4; the SI uses the same step
numbers).

- *Step 1: candidates.* UniProt lists {{variants.n_candidates:,}} missense variants of these
  proteins as pathogenic or likely pathogenic.
- *Step 2: ClinVar agrees.* For {{variants.n_removed_by_clinvar}} of the candidates, none of
  the ClinVar records that UniProt cross-references lists the same amino-acid change with a
  pathogenic or likely pathogenic aggregate germline classification. They were removed. We
  did not search ClinVar beyond those cross-references.
- *Step 3: the record is about this gene and this change, with stated criteria.* A further
  {{variants.n_second_pass_removed}} have such a record only for another gene
  ({{variants.n_other_gene_only}}), only as one of two changes described together
  ({{variants.n_haplotype_only}}), or only without stated criteria for the classification
  ({{variants.n_no_criteria}}). They were removed as well.

The remaining {{variants.n_usable:,}} variants form the pool. Two exceptions were made by
hand. One well-known lysozyme variant, p.Ile74Thr, fails step 3 because its ClinVar record
states no criteria; we use it all the same, in {{clin.n_tasks_kept_by_name:word}} task per
track. One *APOE* variant that passed all three steps is never asked about, because it is
better known for a reported protective effect and a request that calls it pathogenic would
mislead. SI Section S3.2 gives the filter in full, with the dates on which the data were
read.

**From the pool to the clinical tasks.** A clinical task asks about one variant, or a few, on
a panel structure of its protein. The generator picks the variant by seeded random choice
among the pool variants whose residue is observed in the structure with the amino acid of the
reference sequence. For {{clin.n_featured_proteins}} proteins a well-known variant, named by
hand before generation, is tried first (for example the sickle-cell variant of haemoglobin
beta, p.Glu7Val; SI Section S3.2 has the list). The result is
{{clin.n}} tasks per track on {{clin.n_proteins}} proteins and {{clin.n_structures}}
structures ({{clin.n_pdb_structures}} PDB entries and the {{panel.n_alphafold}} predicted
structures), with at most {{clin.max_tasks_per_structure}} tasks per track on one structure.
The other {{panel.n_disease_proteins_without_task:word}} proteins have no task, because no
variant of the pool is observed in their panel structure (SI Section S3.2).

**Atom tables and residue mapping.** For each structure we freeze two tables. The *atom table*
is built from the entry's file in the PDB archive, in the archive's mmCIF format (for a
predicted structure, the file of the AlphaFold Protein Structure Database). It lists every
atom record of the first coordinate set, with its chain and residue in both author and label
numbering, and it keeps hydrogen atoms and alternate positions of an atom where the file has
them: a selection of a residue takes all of its atom records, as the viewer does. The
*mapping table* holds the SIFTS correspondence between each observed residue and its UniProt
position. Generators and graders read only these tables, and nothing is fetched while a task
is built from the tables, graded or loaded. The atom table is compared with what the viewer
itself selects in the same file (Section 3.7); SI Section S3.1 gives the details.

### 3.2 From data to a task: the running example

The clinical generator produced the running example in six steps.

1. **Variant.** From the pool it picks the *{{ex.gene}}* variant {{ex.name_in_prompt}}
   ({{ex.hgvs}}; UniProt {{ex.accession}}). ClinVar holds {{ex.n_clinvar_records}} records of
   this protein change, one for each DNA change that causes it ({{ex.clinvar_records}}). As
   read on {{variants.records_retrieved:date}}, both
   are classified as {{ex.clinvar_classification}}, with the review status
   "{{ex.clinvar_review_status}}": one laboratory submitted the classification and stated its
   criteria, and no second submitter or expert panel has confirmed it. The field of the
   record that names the condition reads "{{ex.clinvar_conditions}}".
2. **Structure.** The panel entry for {{ex.accession}} is {{ex.entry}}, human lysozyme.
3. **Mapping.** The mapping table says that UniProt positions
   {{ex.map_uniprot_first}}–{{ex.map_uniprot_last}} are author residues
   {{ex.map_auth_first}}–{{ex.map_auth_last}} of author chain {{ex.auth_chain}}: an offset of
   {{ex.offset}}, the length of the signal peptide. Position {{ex.uniprot_position}} is
   therefore author residue {{ex.auth_number}} (label chain {{ex.label_chain}}, label residue
   {{ex.label_number}}).
4. **Identity check.** The atom table must hold the amino acid of the reference sequence at
   that residue. It does: {{ex.wild_type}}{{ex.auth_number}}, {{ex.n_target_atoms}} atom
   records ({{ex.n_target_heavy_atoms}} non-hydrogen atoms and {{ex.n_target_hydrogens}}
   hydrogens; this entry, at {{ex.resolution}} Å resolution, includes hydrogens). Had
   the protein in the entry carried another amino acid there, the variant would not be offered
   for this entry.
5. **Wording.** A seeded random choice picks one of the template's three wordings, the colour
   ({{ex.color}}) and the representation ({{ex.rep}}). The request names the entry, the gene,
   the UniProt accession and the variant. It never says which residue of the entry is meant.
6. **Reference, twice.** The script writes the reference scene (author chain
   {{ex.auth_chain}}, author residue {{ex.auth_number}}, {{ex.color}} {{ex.rep}}) and the
   reference call list (load the entry; draw UniProt {{ex.accession}} position
   {{ex.uniprot_position}} as {{ex.color}} {{ex.rep}}). It then confirms that both resolve to
   the same {{ex.n_target_atoms}} atoms, and stores them as the target of both tasks.

One detail of the call-list viewer belongs here. It starts with the whole protein drawn as a
cartoon (the *default view*, Box 1), and a colouring call also recolours the residue's own segment of that
cartoon unless an option switches this off. The request says nothing about the cartoon, so the
call-list task accepts both results: the segment unchanged, or the segment recoloured (SI
Section S1).

The reference contains only what the request states: one residue, one representation, one
colour. It has no cartoon of the protein behind the residue, because the request does not ask
for one. Section 6.6 shows why this rule exists. SI Section S1 gives both tasks in full.

### 3.3 Eight categories of task

Tasks are grouped into eight *categories* by what a model must know beyond the request (Figure
2, Table 1). The categories are kinds of task, not steps on one scale of difficulty. Each
category has several *templates*: a template fixes what is asked, and a seeded generator fills
in the structure, the residues, the colours and the wording. The corpus has
{{corpus.n_templates}} templates. No template supplies more than
{{corpus.max_template_share_other:.0%}} of a category's tasks, except in name resolution (there
are only five ways to name a protein) and in the small call-list category of requests with
several right answers. SI Section S2 lists every template with an example.

![**Figure 2. The eight categories of task, with one request each.** Counts are tasks on the scene track / the call-list track; a dash means that the category has no task on that track (Table 1 gives the reasons). Requests are quoted from the corpus; a long one is cut short. Two words in them are file terms: a *het group* is a molecule in the entry that is not part of a polymer chain, such as a ligand, named by an identifier of up to three characters; *C-alpha* is the central carbon atom of an amino acid. Framed in blue: the two *lookup categories*, name resolution and clinical variant, in which the answer needs one fact that a person would look up in a database and that the model must recall.](generated/fig_tiers.svg)

- **Translation.** Everything needed is in the request: the entry, the chains, the residue
  numbers, the colours. The model only has to write it in the format.
- **Structure-grounded.** The request names a feature, such as the ligand, the disulfide bonds
  (links between two cysteine residues) or the residues that hold a metal ion. The model does
  not see the file. It must either use a generic selector of the format where one fits (for
  example "ligand") or recall what the entry contains, such as the identifier of the ligand
  or the numbers of the residues. The references are computed from the entry's own records.
- **Interactions.** The request names atoms and a measurement between them, such as a hydrogen
  bond drawn as a labelled line.
- **Name resolution.** The request names a protein, not an entry ("a structure of human p53
  bound to DNA"). Any entry on a frozen list of the PDB entries of that protein is accepted
  (SI Section S4.4 gives the rule and the date of the list). An answer on a panel entry is
  graded on drawn state. An answer on an accepted entry outside the panel is compared with
  the reference as written, because we hold no atom table for it; this is a limit (Sections
  4.1 and 9.3). The two kinds of answer are reported in separate rows (Section 6.2).
- **Clinical variant.** As in the running example: the request names a variant, and the model
  must find its residue in the structure, where its number often differs from the one in the
  name. Section 3.3.1 describes this category.
- **Follow-up turn.** The model receives a start state, written as a scene or a call list in
  the format of its answer, and an edit request ("make the magenta chain plum"). It returns
  the complete new state. Only the resulting drawn state is graded, so an answer that makes
  the edit but drops something from the start state, such as the colour of another chain,
  fails. In {{corpus.followup.mvs.noop}} scene tasks and {{corpus.followup.api.noop}}
  call-list tasks the right answer is the start state returned unchanged. In most of these
  the edit asks for something that the start state already shows ("{{corpus.followup.noop_example}}"
  when the start state has already hidden them); in 2 scene tasks it asks for a spin, which a
  scene cannot express, and says to change nothing in that case.
- **Several right answers.** The request leaves one countable thing open. "Colour Lys29
  yellow" in an insulin entry with two B chains can mean either copy or both. The script lists
  every *accepted answer* (a median of {{corpus.accept.mvs.median_states:.0f}} per task on the
  scene track), and an answer that matches any one of them is right.
- **Viewer settings.** Settings that only the call-list format can express, such as the
  background colour and spin.

Name resolution and clinical variant are the *lookup categories*. In both, what the request
leaves out is one fact that a person would look up in a database: which entry holds the
protein, or which residue number the variant has in the entry. The model cannot look it up and
must recall it. Only these two categories have a grounding pack, in which the lookup has been
done for the model (Section 5.2).

**Table 1. The corpus.** Tasks per category and track, written as total (public + held back;
Section 3.6). *Pairs*: requests posed on both tracks with the same target atoms. A dash means
that the category has no task on that track. For interactions (on the call-list track) and
viewer settings (on the scene track) the format cannot express what is asked. Name resolution
could be asked on the call-list track but is not: the call-list grader has no atom table for
an entry outside the panel (Section 3.4).

{{include:generated/table_corpus.md}}

The {{corpus.n_tasks}} tasks ({{corpus.mvs.n}} on the scene track, {{corpus.api.n}} on the
call-list track) use {{corpus.n_structures}} of the {{panel.n}} panel structures. No structure
appears in more than {{corpus.max_tasks_per_structure_tier_track}} tasks of one category and
track. The call-list track has more translation tasks than the scene track because its format
has many single-purpose calls and selectors. Calls that the scene templates have no
counterpart for are exercised by {{corpus.api.translation.n_call_only_templates}} templates
({{corpus.api.translation.n_call_only}} tasks); the other {{corpus.twins.translation}}
translation tasks are pairs.

#### 3.3.1 The clinical category

There are {{clin.n}} clinical tasks per track, on {{clin.n_proteins}} proteins and
{{clin.n_structures}} structures. Of these, {{clin.n_one_variant}} name one variant; the other
{{clin.n_multi}} name several, up to {{clin.max_variants_per_task}}. No target residue has an
insertion code.

*How variants are named.* The requests use three forms of name. Three-letter names
({{ex.hgvs}}) and one-letter names ({{ex.name_in_prompt}}) carry the prefix "p." and are in
UniProt numbering. *Traditional names* ({{ex.mature_name}}) carry no prefix and are counted
along the mature protein, as in older literature. The first two forms follow the protein-level
style of the HGVS nomenclature, the standard of the Human Genome Variation Society for naming
variants [@denDunnen2016hgvs], but they are not complete HGVS descriptions. HGVS requires a
reference sequence from RefSeq or Ensembl before the "p."; a UniProt accession, which
{{clin.n_accession_in_prompt}} requests state, is not one. HGVS also recommends the
three-letter form, and brackets around a protein change that was deduced from the DNA and not
observed in the protein.

ClinVar itself states each change on a *transcript*, a numbered reference copy of the gene's
messenger RNA (for the running example, {{ex.clinvar_first_title}}: DNA letter
{{ex.clinvar_cdna_position}} of transcript {{ex.clinvar_transcript}} changes from
{{ex.clinvar_cdna_from}} to {{ex.clinvar_cdna_to}}, which changes the protein as given in
brackets). A
gene can have several transcripts, and they can number the protein differently. We did not
check which transcript each matching name in ClinVar belongs to; we take its position to be
that of the UniProt canonical sequence (Section 9.2).

The request asks for the residue in one of three wordings: "the residue it replaces", "the
residue replaced by" the variant, or "the wild-type residue at the position of" the variant.
All three mean the amino acid of the reference sequence at that position.

*Traditional names.* A traditional name is used in {{clin.n_mature_name}} requests (for
example transthyretin V30M, which is p.Val50Met). Each of these requests says so, and says
what the traditional numbering leaves out. One of them in full:

> *"{{clin.mature_example.prompt}}"*

In UniProt numbering this variant is {{clin.mature_example.hgvs}}. Of the
{{clin.n_mature_name}} traditional names, {{clin.n_traditional_init_met}} differ from the
UniProt number by the initiator methionine alone (by 1), {{clin.n_traditional_signal}} by a
signal peptide, and {{clin.n_traditional_signal_propeptide}} by a signal peptide and a
propeptide.

*Two groupings.* Each clinical task has two yes-or-no properties that matter for the results.
They are not the same property (Table 2).

- **Copying the number** (the primary grouping). If an answer uses the number printed in the
  variant name as the author residue number, is it right? Copying is right in
  {{clin.n_face_value_right}} tasks and wrong in {{clin.n_face_value_wrong}}.
- **Offset** (a descriptive grouping). Does the author number of the target residue differ
  from its UniProt number? An offset is present in {{clin.n_offset}} tasks
  ({{clin.offset_share:.0%}}) and absent in {{clin.n_no_offset}}. Where there is one, the
  UniProt number is always the larger, by {{clin.offset_min}} to {{clin.offset_max}}
  residues.

A task with several target residues is assigned by rule. Copying counts as right only if the
answer with every number copied is exactly right, that is, if copying is right for every named
variant. The task has an offset if any of its target residues has one. In a task that asks for
a helix or strand, both properties are those of the variant's residue, not of the whole helix
or strand. As it turns out, all {{clin.n_multi}} tasks with several variants and all
{{clin.n_sse}} helix or strand tasks have an offset, and copying is wrong in all of them.

**Table 2. The two groupings of the {{clin.n}} clinical tasks, crossed.** *Copying the number*:
an answer that uses the number printed in the variant name as the author residue number is
right, or wrong. *Offset*: the author number of the target residue differs from its UniProt
number, or does not. A task with several target residues has an offset if any of them has
one, and copying is right in it only if it is right for all of them.

{{include:generated/table_clinical_groupings.md}}

With a name in UniProt numbering, copying is right exactly when there is no offset. The two
groupings differ only for the {{clin.n_mature_name}} traditional names. In
{{clin.n_face_right_offset}} of them the entry is numbered in the same traditional way, so the
number in the name is the author number although the UniProt number is not. The one
remaining traditional name ({{clin.traditional_on_predicted.name}} of haemoglobin beta, which
is {{clin.traditional_on_predicted.hgvs}}) is asked on a predicted structure, which is
numbered as UniProt is. There, copying the traditional number selects the wrong residue
although the target has no offset (the single task in the top-right cell of Table 2).

*Further properties.* The UniProt accession is stated in {{clin.n_accession_in_prompt}}
requests, as in the running example. The other {{clin.n_no_accession}} requests state none.
In {{clin.n_no_accession_uniprot}} of them the name carries "p." and is a position in the
UniProt canonical sequence; neither the request nor the system prompt says so, and the model
must assume it, as a reader of a protein-level name usually does. The other
{{clin.n_no_accession_traditional}} use a traditional name, and the request states how it is
numbered.

In {{clin.n_several_copies}} tasks the entry holds several copies of the protein, and the
request says which are meant. It says "in every chain that has it" in {{clin.n_every_chain}}
requests; the target is then the residue in all of those chains, and an answer that draws it
in one chain only is not target-right. It names one chain ("in chain B only") in the other
{{clin.n_one_chain}}. In {{clin.n_chain_differs}} tasks the author chain identifier differs from the
label chain identifier. A cartoon of the structure is also asked for, in words, in
{{clin.n_context_cartoon}} requests. A further {{clin.n_sse}} requests ask for the helix or
strand that contains the residue (the two common local shapes of a protein chain, as recorded
in the entry) together with the residue; they are reported apart.

*Matched tasks.* On each track, {{clin.n_in_pairs}} of the {{clin.n}} tasks form
{{clin.n_structure_pairs}} sets of two *matched tasks*, which ask about the same variant on
two structures of one protein. In {{clin.n_offset_pairs}} of these sets one structure has an
offset and the other, always a predicted structure, has none. Section 6.4 reports these
{{clin.n_offset_pairs}} sets. In the other 2 sets, both of p53, neither structure has an
offset (the PDB entry is numbered as UniProt is); they are not reported apart.

### 3.4 The same request in two formats

A wrong answer has two possible causes: the model did not know which atoms were meant, or it
knew and could not write them in the format. One format cannot separate the two. MolBench
therefore poses {{corpus.n_twin_pairs}} requests ({{corpus.twin_share_of_mvs:.0%}} of the scene
tasks) on both tracks, with identical wording and the same target atoms (Figure 3).

The two formats differ in kind. A MolViewSpec scene [@midlik2025mvs] is *declarative*: a tree
that states what to load, which atoms form a *component* (a named set of selected atoms), and
how each component is drawn.
Nothing is on screen unless the scene says so. A call list is *imperative*: an ordered list of
calls to the PDBe Mol\* viewer, version 3.3.2 [@pdbemolstar]. The viewer starts with the whole
structure drawn in a *default view*, and each call changes that state, so order matters. The
call list is written as a JSON list in a small notation of our own, which the format guide
documents (Section 5.2). Each item names one call or setting of the viewer and its arguments,
under the names that the viewer's Python notebook widget, ipymolstar 0.1.0 [@ipymolstar],
gives them. The model does not write JavaScript or Python, and the grader follows what PDBe
Mol\* 3.3.2 does with each call.

The formats also differ in what they demand for a clinical request, and we state this openly
because it shapes the comparison. The viewer behind the call-list track can select a residue by
UniProt accession and position and does the mapping itself. A scene has no such selector: the
model must produce author or label numbers. The running example's call-list reference uses the
UniProt selector; its scene reference uses author residue {{ex.auth_number}}. Any selection
that the format allows is accepted if it resolves to the right atoms: author or label
numbering on the scene track, and those two or the UniProt selector on the call-list track. On
the call-list side of a clinical pair, a model can thus be right without knowing any residue
number of the entry. When the request states the accession ({{clin.n_accession_in_prompt}} of
the {{clin.n}} clinical requests), it only has to pass the accession and the position on to
the right call; otherwise it must also know the accession.

The {{clin.n_mature_name}} requests with a traditional name are an exception. Their printed
number is not the UniProt position, so the UniProt selector gives the wrong residue if the
number is passed on as printed; the call-list reference uses the selector with the converted
position. In {{clin.n_face_right_offset}} of the {{clin.n_mature_name}} the printed number is
the entry's author number, so on either track an answer that selects by author number with
the printed number is right. In the remaining one, on a predicted structure, the model must
convert the number on either track. The format guide of the call-list track documents the UniProt selector, and the
guide of the scene track documents selection by author and by label numbering; neither says
which numbering a given entry uses (Section 5.2).

The grader resolves the UniProt selector through the frozen mapping table. The viewer reads
the same SIFTS mapping from the structure file that PDBe distributes. We did not replay
UniProt selections on PDB entries in the viewer (Section 3.7), so for these entries the
agreement between grader and viewer rests on both using SIFTS.

![**Figure 3. One request, two formats, the same target atoms.** The scene and the call list are shown in shortened form. Below: for each model, every pair falls into one of four cells by whether each side is right. The primary comparison counts a side as right when at least 2 of its {{plan.samples}} answers are *target-right*, that is, have a target score of exactly 1 (the requested atoms drawn as asked, whatever else was drawn). It uses the {{corpus.twins.n_with_target}} pairs that have a target score; it is repeated with task success in place of the target score, on all {{corpus.n_twin_pairs}} pairs (Section 5.4). McNemar's test compares the two shaded cells, in which the model was right in one format only.](generated/fig_twins.svg)

Pairs exist in five categories: translation ({{corpus.twins.translation}}), structure-grounded
({{corpus.twins.grounded}}), clinical ({{corpus.twins.clinical}}), follow-up
({{corpus.twins.followup}}) and several right answers ({{corpus.twins.accept_set}}). The
other {{corpus.n_mvs_without_twin}} scene tasks have no partner on the call-list track. Either the
call-list format cannot draw what they ask for (a distance line, a text label, a transparent
surface), or they are name-resolution tasks, in which the model chooses the entry and the
call-list grader has no atom table for an entry outside the panel.

Pairs are compared on the target score first, because task success is not the same test in
the two formats (Section 4.2 gives the reason, Section 5.4 the analysis).

In {{corpus.twins.need_hide_toggle}} pairs the reference call list contains an extra call
that switches off part of the default view, a call that a scene never needs. All of these
are first requests, not follow-up turns. In {{corpus.twins.hide_required}} of them the request
asks for something to be shown alone, or for part of the structure to be hidden
("{{corpus.twins.hide_example}}"), and the call list must contain the call. In the other
{{corpus.twins.hide_optional}} the request asks for the whole protein as a surface or as
spacefill spheres; the reference switches off the default cartoon, and a call list that leaves
the cartoon in place is accepted as well. The paired analysis is reported with and without
these {{corpus.twins.need_hide_toggle}} pairs.

### 3.5 What a request may leave open

Requests written by people leave things unsaid, and a benchmark must decide what silence
means. We use one rule: **an attribute that the request does not state is free; one that it
states must match.** If the request gives no colour for a ligand, the grader ignores the
colour, and any colour is accepted. If the request says
"green", only green is right. Where the open point is which atoms are meant, the task lists
every accepted answer (Section 3.3, several right answers).

The rule covers attributes of what was requested. Additions to the picture, such as a cartoon
that the request does not mention, are not covered by it; Section 4.2 says how they are
scored.

### 3.6 Public and held-back tasks; wording

MolBench tasks have been public since May 2026, so a model released later may have seen
earlier tasks. Two measures address this.

*Held-back split.* Before generation, {{corpus.heldback.n_structures}} structures were set
aside: no earlier MolBench release used them, and no task of the public split uses them.
The {{corpus.heldback.n_tasks}} tasks on them ({{corpus.heldback.share:.0%}} of the corpus) form
the *held-back split*; the other tasks form the *public split*. The name needs one warning: the
held-back tasks are themselves public. The corpus was developed in a public repository, so they
were online for some days before the final run, and the split is not a hidden test set. What
the split can show is limited. Nearly all tasks in both splits were generated for this version
and appear in no earlier release, so it does not compare seen tasks with unseen tasks. It
compares two sets of structures: the {{corpus.public.n_structures}} of the public split, of
which {{corpus.public.n_structures_used_earlier}} appeared in earlier MolBench tasks and
{{corpus.public.n_structures_not_used_earlier}} did not, and the
{{corpus.heldback.n_structures}} held-back ones, of which none did. Three held-back structures
share a protein with a public structure. What would be informative is a clearly lower score
on the held-back structures: it would suggest that scores on the public structures profit
from earlier tasks on them or from their being better known. A difference near zero would not
show the opposite. We report the difference between the splits with an interval and do not
test it, because the split is small (Section 9.4).

*Wording.* To measure sensitivity to wording, {{corpus.n_requests_paraphrased}} requests of
the public split have, beside their original (*full*) wording, two further phrasings each, a
*terse* one and an *indirect* one, with the same reference. For example, the request "{{corpus.paraphrase_example.full}}" also exists in
a terse form ("{{corpus.paraphrase_example.terse}}") and in an indirect form
("{{corpus.paraphrase_example.indirect}}"). Of the
{{corpus.n_requests_paraphrased}} requests, {{corpus.n_paraphrased_pairs}} are pairs, so they are
{{corpus.n_tasks_paraphrased}} tasks, and two further phrasings of each give
{{corpus.n_paraphrase_files}} additional task files. These are not counted in Table 1.

### 3.7 Checks on the corpus

Four checks involve no model (Figure 1).

- **Reference against structure.** Every reference must select at least one atom, must name the
  residue that the generator intended, and must grade as exactly right against itself. Every
  accepted answer must do the same.
- **Atom tables against the viewer.** Selections were read back from the running viewers. For
  the scene track, Mol\* 5.9.0 was run without a display and asked which atoms each
  representation holds. For the call-list track, a sample of {{controls.viewer.api.sample}}
  of the {{controls.viewer.api.n_at_check}} call-list controls that existed at the time
  ({{controls.viewer.api.sample_share:.0%}}; Section 4.5) was replayed in PDBe Mol\* 3.3.2.
  Each control has two call lists, its reference and its answer; {{controls.viewer.api.lists}}
  of the {{controls.viewer.api.sample_lists}} call lists were replayed, each selection was
  compared atom for atom, and all agreed. The default view after a
  load with no further call was compared in the same way for
  {{controls.viewer.api.bare_loads}} of the {{panel.n_pdb}} PDB entries of the panel (the entry
  reserved as a worked example was left out, as were the predicted structures). Both viewers
  were given the archive file from which the atom table was built. Selections by UniProt
  number were not part of this replay, and neither was the copy of the file that PDBe Mol\*
  fetches by default (SI Section S4.8).
- **Grader against a control set.** The grader is run on {{controls.n:,}} answers whose
  verdict is known (Section 4.5).
- **Format rules.** One script validates every task file against the written task format, and
  the run does not start unless every check passes.
