## 10. Conclusion

MolBench shows that control of a molecular viewer by a language model can be graded exactly
and without a judge model. References are computed by script from the structure, the SIFTS
mapping and ClinVar, and answers are compared on the atoms, representations and colours that
a viewer would draw. Three things hold before any final result. Graders that compare text
failed {{controls.mvs.old.false_fail_rate:.0%}} and
{{controls.api.old.false_fail_rate:.0%}} of the correct control answers that the drawn-state
grader accepts. One score is not enough: we report the task success rate, the target score
and F1, each strict and valid-only. And in the pilot run the largest source of error was our
own references, which drew more than the requests asked for.
⟦PENDING: final run — two sentences on the results: how well the models control the viewer on each track, and what the paired comparison shows⟧
