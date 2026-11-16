## S1. The running example in full

The request, the two reference answers, the accepted alternative on the call-list track, the
stored target and the grounding pack, exactly as they are in the task files
`{{ex.id_mvs}}` and `{{ex.id_api}}`. The variant is {{ex.gene}} {{ex.variant}}
({{ex.hgvs}}; UniProt {{ex.accession}}; ClinVar {{ex.clinvar_vcv}}, "{{ex.disease}}",
classified {{ex.clinvar_classification}}, review status "{{ex.clinvar_review_status}}").

On the call-list track the reference sets `"color": null` on the residue. Without it, the
viewer also paints that stretch of the cartoon in its selection colour, which the request does
not ask for. An answer that paints the stretch green, as the residue is, is the accepted
alternative.

{{include:generated/si_example.md}}

**Table S1. Scores of the answers discussed in Section 4.3 of the paper.** *F1*: how much of
the drawn state is right (0 to 1). *Task success*: the drawn state is exactly right. *Target
score*: the requested atoms are drawn as asked, whatever else was drawn (0 to 1).

{{include:generated/table_example.md}}
