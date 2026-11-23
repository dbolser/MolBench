## Abstract

Language models drive molecular viewers, and a wrong picture looks as polished as a right
one. MolBench grades by rule, without a judge model, what the Mol\* viewer would draw: which
atoms, which representation, which colour. The model sees only the request and a format
guide: no structure file, no lookup. References are computed by script from structure files,
the SIFTS residue-number mapping and the ClinVar variant archive. The {{corpus.n_tasks}}
tasks on {{corpus.n_structures}} structures form eight categories. One names a variant that
ClinVar classifies as pathogenic or likely pathogenic, usually by its UniProt sequence
position, which often differs from the structure's numbering: do models convert the
number or copy it? To separate content from format errors, {{corpus.n_twin_pairs}}
requests are posed in two formats: a MolViewSpec scene, and a list of calls to the PDBe
Mol\* viewer, which can convert the number itself. The grader agrees with all
{{controls.n:,}} control answers used to develop it. In a pilot, clinical tasks scored
lowest, yet most answers drew the right residue. The fault was ours: references drew an
unrequested cartoon, and every clinical task used one structure numbered as UniProt is. Both
are corrected; a second score grades the requested atoms alone.
⟦PENDING: final run — main results on both tracks and the paired comparison, with the number of models, in two sentences, which replace the four sentences on the pilot run so that the abstract stays within its limit⟧
