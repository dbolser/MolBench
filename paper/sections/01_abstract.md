## Abstract

Language models now drive molecular viewers, and a wrong picture looks as polished as a
right one. MolBench grades by rule, without a judge model, what the Mol\* viewer would draw:
which atoms, which representation, which colour. The model sees only the request and a format
guide: no structure file, no lookup. References are computed by script from structure files,
the SIFTS residue mapping and ClinVar. The {{corpus.n_tasks}} tasks on
{{corpus.n_structures}} structures fall into eight categories. In one, the request names a
variant that ClinVar classifies as pathogenic or likely pathogenic. Its name usually gives
the UniProt position; the structure often numbers that residue differently. Do models convert
the number, or copy it? To separate content from format errors, {{corpus.n_twin_pairs}}
requests are posed in two formats: a MolViewSpec scene and a list of PDBe Mol\* viewer calls.
The grader agrees with all {{controls.n:,}} control answers used to develop it. In a pilot,
clinical tasks scored lowest although most answers drew the right residue. Two faults were
ours: references drew an unrequested cartoon (a protein ribbon), and every clinical
task used one structure numbered as UniProt, needing no conversion. Both are
corrected; a second score grades the requested atoms alone.
⟦PENDING: final run — main results on both tracks and the paired comparison, with the number of models, in two sentences, which replace the four sentences on the pilot run so that the abstract stays within its limit⟧
