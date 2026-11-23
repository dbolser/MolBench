## 10. Conclusion

MolBench grades, without a judge model, the atoms, representations and colours that a
molecular viewer would draw from a language model's answer. Its {{corpus.n_tasks}} tasks on
{{corpus.n_structures}} structures have references computed by script, and
{{corpus.n_twin_pairs}} requests are posed in two answer formats. The grader agrees with all
{{controls.n:,}} control answers against which it was developed; a check by people is
planned. A pilot run
taught two things: most points were lost to answers that the viewer could not show,
and in the clinical category most were lost to our own references, which drew an
unrequested cartoon. In the rebuilt category, copying the number from the variant
name gives the wrong residue in {{clin.n_face_value_wrong}} of {{clin.n}} tasks, and the
final run will show whether models copy it.
⟦PENDING: final run — two sentences on the results: how well the models drive the viewer on each track, and what the paired comparison shows⟧
