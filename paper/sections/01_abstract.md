## Abstract

Language models drive molecular viewers from plain-language requests, and a wrong picture
looks as polished as a right one. MolBench grades what the Mol\* viewer would draw: which
atoms, in which representation and colour. The model sees only the request and a format guide:
no structure file, no lookup. References are computed by script from the structure file and,
for clinical variants, the SIFTS residue mapping and the ClinVar archive. The {{corpus.n_tasks}} tasks on
{{corpus.n_structures}} structures form eight categories, including clinical variants
whose UniProt positions must be mapped to a structure's numbering.
{{corpus.n_twin_pairs}} requests are posed in two answer formats, a MolViewSpec scene
(declarative) and a list of PDBe Mol\* calls (imperative), to separate content errors from
format errors. {{plan.n_core_models}} to {{plan.n_models_max}} models answer each request
{{plan.samples}} times. The grader agrees with all {{controls.n:,}} control answers, against
which it was developed; our two earlier, text-comparing graders rejected
{{controls.mvs.old.false_fail_rate:.0%}} and {{controls.api.old.false_fail_rate:.0%}} of the
correct ones. In a pilot, clinical tasks scored lowest although most answers drew the right
residue: our references also drew an unrequested background. References now contain only what
the request states, and a target score reports on the requested atoms alone.
⟦PENDING: final run — main results on both tracks and the paired comparison, two sentences, which replace the two sentences on the pilot run so that the abstract stays within its limit⟧
Tasks, graders and answers are open.
