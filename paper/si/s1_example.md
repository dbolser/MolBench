## S1. The running example in full

The request, the two reference answers, the further accepted answers on the call-list track,
the stored target and the grounding pack, exactly as they are in the task files
`{{ex.id_mvs}}` (scene track) and `{{ex.id_api}}` (call-list track). The variant is
*{{ex.gene}}* {{ex.name_in_prompt}} ({{ex.hgvs}}; UniProt {{ex.accession}}). UniProt names the disease
as "{{ex.disease}}". Through UniProt's cross-references we found {{ex.n_clinvar_records}}
ClinVar records of this protein change, one for each of the two single-nucleotide changes
that turn the codon of this tryptophan into a codon of arginine: {{ex.clinvar_records}}. Both carry the aggregate
classification "{{ex.clinvar_classification}}" and the review status
"{{ex.clinvar_review_status}}"; ClinVar's own field for the condition reads
"{{ex.clinvar_conditions}}" on both. The entry {{ex.entry}} is human lysozyme at
{{ex.resolution}} Å resolution; the target residue has {{ex.n_target_atoms}} atom records
({{ex.n_target_heavy_atoms}} non-hydrogen atoms and {{ex.n_target_hydrogens}} hydrogens, which
this entry contains).

On the call-list track the viewer starts with the protein drawn as a cartoon. The reference
sets `"color": null` on the residue, which leaves that cartoon as it was. Without that field
the viewer also recolours the residue's own segment of the cartoon, in its selection colour.
The request says nothing about the cartoon, so an answer that recolours the segment, in the
selection colour or in {{ex.color}} as the residue is, is accepted as well.

{{include:generated/si_example.md}}

**Table S1. Scores of the answers discussed in Sections 4.2 and 4.3 of the paper** (the same as Table 3 of the paper). *F1*: how much of
the drawn state is right (0 to 1). *Task success*: the drawn state is exactly right. *Target
score* (0 to 1): how exactly the answer marks out the requested atoms. It is 1 (*target-right*) when three things hold: the target atoms carry the requested style; no other atom carries that style; and no second representation is drawn on target atoms alone. Any other drawing, such as a cartoon of the protein, is ignored. Rows S1 to S10 are scenes, rows C1 to C7 call lists. *Spill*, *extra on the target* and *context* are the three rules for extra
drawing of Section S4.3.

{{include:generated/table_example.md}}
