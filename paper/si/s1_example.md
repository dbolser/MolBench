## S1. The running example in full

The request, the two reference answers, the further accepted answers on the call-list track,
the stored target and the grounding pack, exactly as they are in the task files
`{{ex.id_mvs}}` (scene track) and `{{ex.id_api}}` (call-list track). The variant is
{{ex.gene}} {{ex.variant}} ({{ex.hgvs}}; UniProt {{ex.accession}}; "{{ex.disease}}";
classified {{ex.clinvar_classification}}, review status "{{ex.clinvar_review_status}}").
ClinVar records of this protein change: {{ex.clinvar_records}}.

On the call-list track the reference sets `"color": null` on the residue, which leaves the
cartoon as it was. Without that field the viewer also paints the residue's stretch of the
cartoon in its selection colour. The request says nothing about that stretch, so an answer
that paints it, in the selection colour or in {{ex.color}} as the residue is, is accepted as
well.

{{include:generated/si_example.md}}

**Table S1. Scores of the answers discussed in Section 4.3 of the paper.** *F1*: how much of
the drawn state is right (0 to 1). *Task success*: the drawn state is exactly right. *Target
score*: the requested atoms are drawn as asked, whatever else was drawn (0 to 1).

{{include:generated/table_example.md}}
