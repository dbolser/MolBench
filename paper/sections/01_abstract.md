## Abstract

Researchers increasingly ask computational intelligence (CI) assistants to drive molecular
viewers in plain language: "show the haem", "highlight the residue changed by this variant".
There is no agreed way to measure whether the result is right. We present MolBench, a benchmark
that grades a language model on **what the viewer would show**: which atoms are selected, and how
they are drawn and coloured. Every reference answer is built by script from the deposited
structure and tested against it. The same requests are posed in two output formats, a declarative
scene (MolViewSpec) and an imperative call list (the PDBe Mol\* viewer API), so that not knowing
the biology can be told apart from not being able to write the format. Difficulty rises from
translating a fully specified request, to requests that need facts about the structure, to
clinical-variant requests that need a mapping from UniProt numbering to the residues of a
structure. In a preliminary panel of {{mvs.spec.n_models}} models on {{mvs.n_tasks}} scene tasks,
strict scores ranged from {{mvs.spec.f1_min:.2f}} to {{mvs.spec.f1_max:.2f}}. Almost all of that
range came from whether the output was a valid scene at all (correlation between valid-scene rate
and score: r = {{mvs.spec.r_valid_f1:.3f}}). Over valid scenes only, models were close
({{mvs.spec.f1_valid_min:.2f}} to {{mvs.spec.f1_valid_max:.2f}}), and the hard tasks were the
clinical and name-lookup ones. Adding frozen facts about the structure to the request did not
help (mean change {{mvs.grounding.all.delta:+.3f}}). ⟦PENDING: replace the preliminary numbers
with the final run (both tracks, three samples per task) and add the paired-format result⟧
The tasks, references, graders, raw model outputs and the scripts that produce every number in
this paper are openly available.
