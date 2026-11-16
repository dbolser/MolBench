## 8. Discussion

⟦PENDING: final run — discussion of the results: which tiers separate models, what the paired comparison shows, whether the held-back split differs from the public one⟧

Three points can be made before the final run, because they concern the instrument and not
the models.

**Exactness is measurable for this task.** A viewer scene has a definite content: these atoms,
drawn this way. Once references are computed from the structure and answers are resolved to
atoms, "is it right?" has a yes-or-no answer that needs no judge model and no rubric. The
control set shows that the answer is stable under rewriting ({{controls.n:,}} controls, no
error) and that graders which compare text are not ({{controls.mvs.old.false_fail_rate:.0%}}
and {{controls.api.old.false_fail_rate:.0%}} of correct answers failed).

**One score is not enough.** The pilot run gave three different pictures of the same answers.
Strict scores mostly measured whether a model can close its braces. F1 on the clinical tier
mostly measured whether a model reproduced a background. Only a score restricted to the
requested atoms showed that the residue was usually right. We therefore report task success
as the headline, F1 for partial credit, the target score to separate substance from scenery,
and each of them strict and over valid outputs only.

**A benchmark's references need the same scrutiny as the models.** The most important
finding so far concerns our own references (Section 7). It was found by asking where valid
answers lost their points, and not by looking at totals. We recommend that analysis to anyone
who builds a benchmark with partial credit.
