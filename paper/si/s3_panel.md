## S3. The structure panel and the variant list

### S3.1 The structure panel

**Methods.** Of the {{panel.n_pdb}} PDB entries, {{panel.n_xray}} were solved by X-ray
crystallography, {{panel.n_cryoem}} by cryo-electron microscopy and {{panel.n_nmr}} by nuclear
magnetic resonance.

**Selection rule.** The panel is the union of four groups. Every entry must be current in the
PDB archive and have at most {{panel.max_atoms:,}} atoms in its first coordinate set, so that
it renders quickly ({{panel.n_over_size_limit}} larger entries are kept because earlier tasks
used them). Every feature claimed for an entry (ligand, haem, metal, disulfide, nucleic acid,
glycan, membrane protein, assembly that differs from the deposited coordinates, insertion
codes, author chain identifiers that differ from label identifiers, a UniProt numbering
offset) must be found in the file by the build script, or the build fails.

1. *Entries used by earlier tasks.*
2. *Named entries*, chosen by hand to cover folds and features that the first group lacks.
   Well-known entries were preferred, solved by X-ray crystallography at 2.5 Å or better where
   one exists. The choice is by hand; the check of each claimed feature is by script.
3. *Disease proteins.* {{panel.n_disease_proteins}} human proteins in which germline missense
   variants cause Mendelian disease are listed by UniProt accession. The list was written by hand:
   familiar examples that have experimental structures. For each, candidate entries are all PDB entries that SIFTS maps to the accession.
   The script keeps X-ray entries at 2.5 Å or better that cover at least one variant position
   (failing that, X-ray or cryo-electron microscopy entries at 3.5 Å or better), drops entries
   above the size limit or with several coordinate sets, and then chooses by, in order: most
   variant positions covered, fewest engineered mutations, fewest polymer entities, best
   resolution. Whether the author numbering differs from UniProt was not a criterion. A
   variant may also be asked on any other panel structure of the same protein.
4. *{{panel.n_alphafold}} predicted structures* from the AlphaFold Protein Structure Database,
   which use UniProt numbering by construction: of {{panel.alphafold_proteins}}. The predicted
   structure of p53 was used by earlier tasks. Each of the others is a partner to an
   experimental structure of the same protein that is numbered differently, so that the same
   variant can be asked with and without an offset.

Counts of verified features in the panel: ligand {{panel.feature.ligand}}, metal
{{panel.feature.metal}}, disulfide {{panel.feature.disulfide}}, assembly differs
{{panel.feature.assembly-differs}}, author chain identifier differs from label identifier
{{panel.feature.auth-label-chain}}, glycan {{panel.feature.glycan}}, nucleic acid
{{panel.feature.nucleic}}, modified residue {{panel.feature.modified-residue}}, haem
{{panel.feature.heme}}, insertion codes {{panel.feature.insertion-codes}}, membrane protein
{{panel.feature.membrane}}. Structure files were retrieved on {{panel.retrieved:date}}; the
checksum of each file is stored with the panel.

**Atom tables and mapping tables.** The atom table of a structure lists every atom record of
the first coordinate set of its file. It keeps *alternate conformers*, the same atom recorded
at two or more positions where the experiment saw a residue in more than one pose
({{panel.n_with_alternate_conformers}} structures have them), and hydrogen atoms, which many
files omit ({{panel.n_with_hydrogens}} structures have them). A selection of a residue takes
all of its atom records, as the viewer does. An author residue number is used together with
its insertion code where there is one ({{panel.feature.insertion-codes}} entries have them).
The mapping table holds the SIFTS correspondence between each observed residue and its
UniProt position; it is read from the copy of the entry's file that PDBe distributes with the
SIFTS mapping added, whereas the atom table is built from the archive file.

**Table S3. The panel.** *Atoms*: atoms in the first coordinate set. *Author numbering differs
from UniProt*: at least one observed residue has an author number that is not its UniProt
position (a dash: no protein chain mapped to UniProt). *Split*: set aside (one of the {{corpus.heldback.n_structures}} structures of the set-aside
split; Section 3.6 of the paper), or other. *Tasks*: tasks of the
corpus on this structure, both tracks, without rephrasings.

{{include:generated/si_panel.md}}

### S3.2 The variant list, step by step

We use *missense* variants only: one amino acid replaced by another. Throughout, the
*classification* of a variant means ClinVar's aggregate germline classification on a variation
record, the record whose accession begins with VCV. ClinVar keeps germline classifications
(of variants present in every cell of a person, inherited or newly arisen) apart from somatic
ones (of variants that arise in a tumour); we use the germline one. A variation record
is usually about one change at the level of DNA, and different DNA changes can give the same
amino-acid change, so one amino-acid change can have several records.
{{variants.n_several_records}} of the variants that we keep have more than one qualifying
record.

**Table S4. The variant list in three steps.** Counts are of variants (amino-acid changes)
removed and left. The tests 3a to 3c are applied in this order. Section 3.1 of the paper
gives the same counts in one paragraph, with steps 3a to 3c taken together.

{{include:generated/table_variants.md}}

*The rule in one sentence.* A variant is kept if at least one ClinVar record that lists it is
classified as pathogenic or likely pathogenic, is of the gene that the request names,
describes that change alone, and states its assertion criteria.

*Step 1.* The candidates come from UniProt's variant annotation of the
{{panel.n_disease_proteins}} proteins. The position is that of the UniProt canonical sequence.

*Step 2.* We examined only the ClinVar records that UniProt cross-references for a variant;
we did not search ClinVar itself. UniProt's annotation can carry a pathogenic label where ClinVar's aggregate
classification does not; we observed this for {{variants.n_removed_by_clinvar}} candidates
({{variants.removed_share:.0%}}), most of which ClinVar classifies as "Conflicting
classifications of pathogenicity" or "Uncertain significance". A candidate is kept only if a
ClinVar record, reached through UniProt's cross-references to ClinVar, lists the same
amino-acid change at the same position among its protein changes and is classified
"Pathogenic", "Likely pathogenic" or "Pathogenic/Likely pathogenic". ClinVar lists the protein
change of a record once for each transcript of the gene. A record matches if any one of these
names equals our amino-acid change and position; we did not check which transcript that name
is counted on. We therefore rely on at least one reference protein of the record being numbered as
the UniProt canonical sequence is at that position. We also did not look for further records
of the same amino-acid change that carry another classification: one qualifying record is
enough, and ClinVar may hold a second record that disagrees with it.

*How the names in the requests relate to the HGVS nomenclature.* Names with "p." follow the
protein-level style of the HGVS nomenclature, the standard of the Human Genome Variation
Society for naming variants [@denDunnen2016hgvs; @hart2024hgvs], but they are not complete
HGVS descriptions. A complete description puts a reference sequence with its version number
before the "p."; for a protein change this is a protein accession of RefSeq or Ensembl
(beginning with NP_ or ENSP). A UniProt accession, which {{clin.n_accession_in_prompt}}
requests state, is not such a reference sequence. HGVS also prefers the three-letter form,
and it puts parentheses around a protein change that is predicted from the DNA change and
was not observed in the protein. Our requests write the protein change without parentheses
({{ex.name_in_prompt}} or {{ex.hgvs}}).

*How ClinVar names a record.* ClinVar states each change on a *transcript*, a reference
sequence of one messenger RNA of the gene. For the running example the title of the record
is {{ex.clinvar_first_title}}: nucleotide {{ex.clinvar_cdna_position}} of the coding sequence
of transcript {{ex.clinvar_transcript}}, counted from the A of the start codon ATG, changes
from {{ex.clinvar_cdna_from}} to {{ex.clinvar_cdna_to}}, and the protein change follows in
parentheses. This is the format of ClinVar's titles; we take the protein change in it to be
the consequence predicted from the DNA change. A gene can have several transcripts, and they
can number the protein differently, so a ClinVar record lists the protein change once for
each transcript. We accept a record if any one of these names equals our amino-acid change
and position (step 2). We did not check which transcript that name is counted on; we take
its position to be that of the UniProt canonical sequence (Section 9.2 of the paper).

*What a request says about the classification.* ClinVar classifies DNA-level records, each
for a stated condition. A request attaches the classification to the protein-level name and
names no condition: it means that at least one qualifying record of this amino-acid change
carries that classification. Where the qualifying records behind one request carry different
values, the request says "pathogenic or likely pathogenic" ({{clin.n_class_differs}}
requests); {{clin.n_class_both_word}} requests say "pathogenic/likely pathogenic", which is
ClinVar's own aggregate value on their records.

*Step 3.* A request says, in ClinVar's own word for the record, that the variant of a named
gene is classified as pathogenic, as likely pathogenic, or as pathogenic/likely pathogenic
("the *LYZ* variant p.W82R is classified as pathogenic in ClinVar"). The classification must
therefore rest on a record of that gene, about that one change, with stated criteria. In step
3a the other gene is nearly always one that encodes the same protein (*CALM2* or *CALM3* for
calmodulin, *HBA2* for alpha-globin). In step 3b the record describes two changes on one
chromosome and says nothing about either alone. In step 3c no submitter stated the criteria
behind the classification.

*Two variants were handled individually, outside these rules.* One variant removed in step 3c
is used all the same, in {{clin.n_tasks_kept_by_name}} task per track: lysozyme p.Ile74Thr
(I56T in the older literature), one of the first two variants reported to cause hereditary
lysozyme amyloidosis [@pepys1993lysozyme]. It is outside the {{variants.n_usable:,}}. Its
request says that the variant "is classified as {{clin.kept_by_name.classification}} in
ClinVar", which is what the record says; the record states no assertion criteria, and this
task is therefore an exception to the rule above. One variant inside the
{{variants.n_usable:,}} is never asked about: APOE p.Arg154Ser (R136S in the older literature,
the Christchurch variant). ClinVar's pathogenic record for it concerns a disorder of blood
lipids, while the variant is widely known for a reported protective effect in Alzheimer's
disease, so a request that calls it pathogenic would mislead.

*Well-known variants tried first.* Within the pool, the generator picks variants by seeded
random choice. For {{clin.n_featured_proteins}} proteins a list written by hand before
generation names well-known variants that are tried first, and used if they are in the pool
(or are the exception above) and observed in the structure: {{clin.featured_list}}. The list
decides which variant is asked about, never what the answer is.

*Traditional names.* A traditional name is used in {{clin.n_mature_name}} requests per
track. {{clin.n_traditional_init_met}} of these names differ from the UniProt number by the
initiator methionine alone (by 1), {{clin.n_traditional_signal}} by a signal peptide, and
{{clin.n_traditional_signal_propeptide}} by a signal peptide and a propeptide; each request
says which.

*Proteins without a task.* Tasks exist for {{clin.n_proteins}} of the
{{panel.n_disease_proteins}} proteins. The other {{panel.n_disease_proteins_without_task}}
are, by gene name, {{variants.proteins_without_task}}. For *TPI1* (triosephosphate isomerase)
the steps above left no variant. For *CA2* (carbonic anhydrase 2) they left one, at the first
residue of the sequence, which the panel structure does not contain; a task needs a residue
that is observed in the structure.

*Proteins and structures.* The {{clin.n_proteins}} proteins give tasks on
{{clin.n_structures}} structures. {{clin.n_proteins_several_structures}} proteins have tasks
on more than one structure, and {{clin.n_structures_two_proteins}} haemoglobin entries serve
two proteins each, because they hold both the alpha and the beta chain.

*Dates.* The variant lists and the classifications of step 2 were read from UniProt and
ClinVar on {{variants.clinvar_retrieved:date}}. The records were read again on
{{variants.records_retrieved:date}}, with their kind, gene, classification and review status; step
3 and the wording of the requests rest on that second reading.
