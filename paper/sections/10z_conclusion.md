## 10. Conclusion

MolBench grades how a language model drives a molecular viewer on the atoms,
representations and colours that the viewer would draw, without a judge model. References
are computed by script from the structure and, for clinical variants, from the SIFTS
mapping and ClinVar. The corpus has {{corpus.n_tasks}} tasks on {{corpus.n_structures}}
structures, and {{corpus.n_twin_pairs}} requests are posed in two answer formats, so that
an error of content can be told apart from an error of format. The grader agrees with every
known verdict of the {{controls.n:,}} control answers against which it was developed, and a
check by people is planned. A pilot run
taught two things: most points were lost to answers that the viewer could not show at all,
and in the clinical category most were lost to our own references, which drew a cartoon
that no request asked for. In the rebuilt category, copying the number from the variant
name gives the wrong residue in {{clin.n_face_value_wrong}} of {{clin.n}} tasks, and the
final run will show whether models copy it.
⟦PENDING: final run — two sentences on the results: how well the models drive the viewer on each track, and what the paired comparison shows⟧
