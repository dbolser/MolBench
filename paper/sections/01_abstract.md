## Abstract

Scientists ask language models to drive molecular viewers in plain words: "show the residue
changed by this variant". A wrong picture looks as polished as a right one. MolBench grades a
model on what the viewer would draw: which atoms, in which representation and colour. Each
reference answer is computed by script from the deposited structure, the SIFTS residue mapping
to UniProt, and ClinVar. The corpus has {{corpus.n_tasks}} tasks on {{corpus.n_structures}}
structures in eight tiers, from fully specified requests to clinical variants whose UniProt
positions must be mapped to the residues of a structure. {{corpus.n_twin_pairs}} requests are
posed in two answer formats, a declarative scene and an imperative call list, to separate
errors of content from errors of format. The grader agrees with all {{controls.n:,}} control
answers of known verdict, against which it was developed; two earlier text-comparing graders
rejected {{controls.mvs.old.false_fail_rate:.0%}} and
{{controls.api.old.false_fail_rate:.0%}} of the correct ones. In a pilot run, clinical tasks
scored lowest although most answers drew the right residue: our references also drew a
background that no request had asked for. References now contain only what the request
states, and a target score reports on the requested atoms alone.
⟦PENDING: final run — main results on both tracks and the paired comparison, two sentences, which replace the two sentences on the pilot run so that the abstract stays within its limit⟧
Tasks, graders and model answers are open.
