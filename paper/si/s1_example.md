## S1. The running example in full

The request, the two reference answers, the further accepted answers on the call-list track,
the stored target and the grounding pack, exactly as they are in the task files
`{{ex.id_mvs}}` (scene track) and `{{ex.id_api}}` (call-list track). The variant is
{{ex.gene}} {{ex.variant}} ({{ex.hgvs}}; UniProt {{ex.accession}}). UniProt names the disease
as "{{ex.disease}}". ClinVar holds {{ex.n_clinvar_records}} records of this protein change, one
for each DNA change that causes it: {{ex.clinvar_records}}. Both carry the aggregate
classification "{{ex.clinvar_classification}}" and the review status
"{{ex.clinvar_review_status}}"; ClinVar's own field for the condition reads
"{{ex.clinvar_conditions}}" on both. The entry {{ex.entry}} is human lysozyme at
{{ex.resolution}} Å resolution; the target residue has {{ex.n_target_atoms}} atoms
({{ex.n_target_heavy_atoms}} heavy atoms and {{ex.n_target_hydrogens}} hydrogens, which this
entry contains).

On the call-list track the viewer starts with the protein drawn as a cartoon. The reference
sets `"color": null` on the residue, which leaves that cartoon as it was. Without that field
the viewer also recolours the residue's own segment of the cartoon, in its selection colour.
The request says nothing about the cartoon, so an answer that recolours the segment, in the
selection colour or in {{ex.color}} as the residue is, is accepted as well.

{{include:generated/si_example.md}}

**Table S1. Scores of the answers discussed in Sections 4.2 and 4.3 of the paper** (the same as Table 3 of the paper). *F1*: how much of
the drawn state is right (0 to 1). *Task success*: the drawn state is exactly right. *Target
score*: the requested atoms are drawn as asked, whatever else was drawn (0 to 1). *Spill*, *extra on the target* and *context* are the three rules for extra
drawing of Section S4.3.

{{include:generated/table_example.md}}
