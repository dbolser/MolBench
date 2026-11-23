## 7. Errors in the first version and their corrections

The first version of MolBench (Section 6: the corpus and the two graders used up to the pilot
run of October 2026) was wrong in nine ways that we know of. Table 15 lists each error, how
we found out, and what replaced it in the present version, because each error is one that
another benchmark of this kind could make.

**Table 15. Nine errors in the first version of MolBench (the corpus and graders used up to
the October 2026 pilot run) and what replaced each in the benchmark of Sections 3 and 4.**
*Where*: the sections that give the numbers behind the row.

| Row | What was wrong | How we found out | What replaced it | Where |
|--:|:--------|:------|:--------|:----|
| 1 | Our clinical references drew a cartoon that no request asked for, and we read the low score that followed as a difficulty of finding the residue. | A breakdown of where valid answers lost their points (Section 6.6, Finding 2). | A reference holds only what the request states. If context is wanted, the request asks for it in words. Every task stores its target where it has one, and the target score is reported beside task success in Tables 6 to 10. | Sections 3.2, 4.2; 6.6, Finding 2 |
| 2 | The clinical category could not test the mapping: all its tasks sat on one protein whose structure uses UniProt numbering. | The same analysis. | {{clin.n}} tasks on {{clin.n_proteins}} proteins and {{clin.n_structures}} structures; in {{clin.n_offset}} tasks the target has an offset, and results are grouped by whether copying the number in the variant name is right (it is wrong in {{clin.n_face_value_wrong}}). | Section 3.3.1; 6.6, Finding 2 |
| 3 | "Pathogenic" was taken from a secondary source: we first took the variants that UniProt lists as pathogenic. | A check of each candidate against the ClinVar records that UniProt cross-references. For {{variants.removed_share:.0%}} of the candidates none of these records gives the same amino-acid change a pathogenic or likely pathogenic aggregate classification, and ClinVar's aggregate classification of some variants named in tasks of the first version is "conflicting classifications of pathogenicity". | A variant is used only if ClinVar holds a record of that gene and that one change with a pathogenic or likely pathogenic classification and stated criteria (one exception, SI Section S3.2). The dates are stored. | Section 3.1; SI Section S3.2 |
| 4 | Both graders compared text: scene trees path by path, call sequences field by field. They rejected correct answers that were merely written differently, both passed some wrong ones (the scene grader {{controls.mvs.old.false_pass_rate:.0%}}, the call-list grader {{controls.api.old.false_pass_rate:.0%}}), and on the call-list track a keyword script scored close to the models. | The control set. | Both tracks are graded on drawn state, and the control set is run as a test on every change. | Section 4.5, Table 4; 6.6, Finding 5 |
| 5 | Hand-written call-list tasks had errors: label numbers where author numbers were meant, and one task that was the worked example of the prompt. | A check of those references against the structures. | Every reference is generated; a sample of references is replayed in the viewer itself; and the entry used for the worked example of both system prompts is excluded from the corpus. | Sections 3.2, 3.7 |
| 6 | Some requests had no single answer. A request to highlight "all pathogenic residues" of one protein resolved to far more residues than any user means; "show me lysozyme" was graded against one arbitrary view. | Reading the references. | Clinical requests name each variant. Requests with a countable ambiguity have their own category, with every accepted answer listed. Open-ended requests are left out. | Sections 3.3, 9.1 |
| 7 | Raters could not see what they were rating. A single highlighted residue on a whole complex was a few pixels wide, and a volunteer flagged a reference as wrong when it was only unreadable. A volunteer also found references in which two cartoons overlapped. | The trial of the rating study. | Pictures are framed on the target atoms from one shared camera. The overlapping references were corrected. The next study completes two ratings of a picture comparison before it opens new ones. | Section 5.5; 6.6, Finding 6 |
| 8 | The pilot run collected one answer per task on {{mvs.n_structures}} structures, with a short limit on the length of an answer and no record of how often an answer was cut off. | Planning the final run. | {{plan.samples}} answers per task, {{corpus.n_structures}} structures, a limit of {{plan.max_tokens:,}} tokens, and the provider's reason for the end of each answer archived. | Sections 5.3, 5.4 |
| 9 | The prompts taught answers that the graders marked wrong, and other faults of the same kind (below). | Four reviews of the benchmark by language models before the final run. | Each finding was fixed in the generator or the grader and is now covered by an automated test and by a new kind of control. Both prompt examples are graded by the benchmark's own grader as a test. | Sections 3.1, 4.5; SI Section S5 |

Row 9 needs more words than a table cell holds. Before the final run, the benchmark was
reviewed four times by language-model reviewers, each given one role (structural biologist,
clinical geneticist, benchmark methodologist, tester of the grader). The reviewers wrote
natural answers by hand and graded them, and we reproduced each finding before acting on it.
The worked example of the scene prompt selected a named compound in a way that the references
did not. The worked example of the call-list prompt coloured a residue in a form that many
generated tasks did not accept. A residue named by UniProt number on a predicted structure was
scored as selecting nothing. A scene that named a file which the viewer cannot load was
graded as a success. The same reviews found
clinical requests whose "pathogenic" record belonged to another gene or to two variants taken
together (SI Section S3.2).
