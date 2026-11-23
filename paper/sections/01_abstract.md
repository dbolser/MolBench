## Abstract

Language models now drive molecular viewers, and a wrong picture looks as polished as a
right one. MolBench grades by rule, without a judge model, what the Mol\* viewer would draw:
which atoms, in which representation (drawing style) and colour. The model sees only the
request and a format guide: no structure file, no lookup. Scripts compute references
from structure files, a residue-numbering table (SIFTS) and a variant archive (ClinVar). The {{corpus.n_tasks}} tasks on {{corpus.n_structures}} structures form eight
categories. One asks for the residue (amino acid) of a variant that ClinVar classifies as
pathogenic or likely pathogenic. The variant's name usually gives a position in the UniProt
sequence; the structure often numbers that residue differently. Do models convert the
number, or copy it? To separate content errors from format errors,
{{corpus.n_twin_pairs}} requests are answered in two formats: a scene description
(MolViewSpec) and a list of viewer calls (PDBe Mol\*). Three scores are given: task success
(drawing exactly right), a target score (requested atoms marked out exactly; background
ignored) and F1 (partial credit). The grader agrees with all {{controls.n:,}} control answers
used to develop it. A pilot run exposed two faults in our own references; both are corrected.
⟦PENDING: final run — main results on both tracks and the paired comparison, with the number of models, in two sentences, which replace the sentence on the pilot run so that the abstract stays within its limit⟧
