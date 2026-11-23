## Abstract

Language models now drive molecular viewers, and a wrong picture looks as polished as a right
one. MolBench grades by rule, without a judge model, what the Mol\* viewer would draw: which
atoms, in which representation and colour. The model sees only the plain-language request and
a format guide: no structure file, no lookup. References are computed by script from
structure files, SIFTS and ClinVar. The {{corpus.n_tasks}} tasks on
{{corpus.n_structures}} structures form eight categories. In one, a disease-linked variant is
named by its UniProt position, which often differs from the structure's residue number:
do models convert the number or copy it? To separate content from format errors,
{{corpus.n_twin_pairs}} requests are posed both as a MolViewSpec scene and as a list of PDBe
Mol\* calls, whose viewer can do that conversion itself. Each task is answered
{{plan.samples}} times by {{plan.n_core_models}} core models and up to
{{plan.n_optional_models}} larger ones. The grader agrees with all {{controls.n:,}} control
answers, against which it was developed. In a pilot, clinical tasks scored lowest although
most answers drew the right residue: our references drew an unrequested background, since
removed, and the single structure needed no renumbering. A target score now reports on
the requested atoms alone.
⟦PENDING: final run — main results on both tracks and the paired comparison, two sentences, which replace the two sentences on the pilot run so that the abstract stays within its limit⟧
