## 10. Conclusion

MolBench grades how a language model drives a molecular viewer on the atoms, representations
and colours that the viewer would draw, without a judge model. References are computed by
script from the structure and, for clinical variants, from the SIFTS mapping and ClinVar.
Three things hold before any final result. On a control set of {{controls.n:,}} answers the
grader agrees with every known verdict, where our earlier graders, which compared text, rejected
{{controls.mvs.old.false_fail_rate:.0%}} and {{controls.api.old.false_fail_rate:.0%}} of the
correct answers; the control set is the one against which the grader was developed, and a
check by people is planned. One score is not enough: we report the task success rate, the
target score and F1. And in the clinical category of the pilot run the largest source of lost
points was our own references, which drew more than the requests asked for; over the whole
pilot it was answers that could not be shown. That clinical category did not yet test the
mapping of residue numbers, which the final run is built to test.
⟦PENDING: final run — two sentences on the results: how well the models drive the viewer on each track, and what the paired comparison shows⟧
