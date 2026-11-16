## Abstract

Scientists now ask language models to drive molecular viewers in plain words: "show the residue
changed by this variant". A wrong picture looks as polished as a right one. MolBench grades a model on what the viewer
would draw: which atoms, in which representation and colour. Every reference answer is
computed by script from the deposited structure, a residue-level mapping to UniProt, and ClinVar,
and is checked against the structure. The corpus has {{corpus.n_tasks}} tasks on
{{corpus.n_structures}} structures in eight tiers, from fully specified requests to clinical
variants that must be mapped from UniProt numbering to the residues of a structure.
{{corpus.n_twin_pairs}} requests are posed in two output formats, a declarative scene and an
imperative call list, to separate not knowing the answer from not being able to write it. On
{{controls.n:,}} control answers with known verdicts the grader made no error; the two graders it
replaces failed {{controls.mvs.old.false_fail_rate:.0%}} and
{{controls.api.old.false_fail_rate:.0%}} of the correct ones. In a pilot run, clinical tasks
scored lowest although most answers drew the right residue: they lost points on context that
nobody had requested. References now hold only what the request states.
⟦PENDING: final run — headline results on both tracks and the paired comparison, two sentences⟧
Tasks, graders and model outputs are open.
