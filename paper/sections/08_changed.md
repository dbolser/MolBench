## 7. Errors in the first version and their corrections

The first version of MolBench was wrong in nine ways that we know of. Table 13 names each
error and what replaced it, because each is one that another benchmark of this kind could
make. SI Section S13.2 says how each was found.

**Table 13. Nine errors in the first version of MolBench and what replaced each.**

| | What was wrong | What replaced it |
|--:|:----------------|:----------------|
| 1 | Clinical references drew a cartoon that no request asked for, and we read the low score that followed as a difficulty of finding the residue. | A reference holds only what the request states. Every task stores its target where it has one, and the target score is reported beside task success. |
| 2 | The clinical category could not test the mapping: all its tasks sat on one structure that uses UniProt numbering. | {{clin.n}} tasks on {{clin.n_structures}} structures; copying the number is wrong in {{clin.n_face_value_wrong}} of them, and results are grouped by that property. |
| 3 | "Pathogenic" was taken from a secondary source, UniProt's variant annotation. | A variant is used only if a ClinVar variation record of that gene and that one change has the aggregate germline classification pathogenic, likely pathogenic or pathogenic/likely pathogenic, with a review status other than "no assertion criteria provided" (one exception, lysozyme p.Ile74Thr; Section 3.1). |
| 4 | Both graders compared text. They rejected correct answers that were written differently ({{controls.mvs.old.false_fail_rate:.0%}} and {{controls.api.old.false_fail_rate:.0%}} of them on the control set) and passed some wrong ones. | Both tracks are graded on drawn state, and the control set is run as a test on every change. |
| 5 | Hand-written call-list references had errors, such as label numbers where author numbers were meant. | Every reference is generated and checked against the structure. |
| 6 | Some requests had no single answer ("show me lysozyme"). | Requests with a countable ambiguity list every accepted answer; open-ended requests are left out. |
| 7 | Raters could not see what they were rating: one highlighted residue on a whole complex is a few pixels wide. | Pictures are also framed on the target atoms, from one shared camera. |
| 8 | One answer per task, on {{mvs.n_structures}} structures, with no record of answers that were cut off. | {{plan.samples}} answers per task, {{corpus.n_structures}} structures, and the reason for the end of each answer archived. |
| 9 | The prompts taught answers that the graders marked wrong. | Both prompt examples are graded by the benchmark's own grader as a test. |
