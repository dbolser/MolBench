## Abstract

Language models now drive molecular viewers, and a wrong picture looks as polished as a
right one. MolBench grades by rule, without a judge model, what the Mol\* viewer would draw:
which atoms, which representation, which colour. The model sees only the request and a format
guide: no structure file, no lookup. Scripts compute references from structure files, a
residue-numbering table (SIFTS) and a clinical variant archive (ClinVar). The
{{corpus.n_tasks}} tasks on {{corpus.n_structures}} structures form eight categories. One
asks about variants that ClinVar classifies as pathogenic or likely pathogenic. The variant's
name usually gives its UniProt sequence position; the structure often numbers that residue
differently. Do models convert the number, or copy it? To separate content from format
errors, {{corpus.n_twin_pairs}} requests are posed twice: as a MolViewSpec scene and as
PDBe Mol\* viewer calls. The grader agrees with all {{controls.n:,}} control answers used to
develop it. In a pilot, clinical tasks scored lowest although most answers drew the right
residue. Our references drew an unrequested cartoon (a ribbon), and all clinical tasks used
one structure numbered as its UniProt sequence, which needs no conversion. Both are
corrected, and a target score now grades the requested atoms and ignores background.
⟦PENDING: final run — main results on both tracks and the paired comparison, with the number of models, in two sentences, which replace the four sentences on the pilot run so that the abstract stays within its limit⟧
