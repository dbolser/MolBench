## Abstract

Language models now drive molecular viewers, and a wrong picture looks as polished as a
right one. MolBench grades what the Mol\* viewer would draw, by rule, without a judge model:
which atoms, in which representation and colour. The model sees only the
request and a format guide: no structure file, no lookup. Scripts compute references
from structure files, residue mapping (SIFTS) and ClinVar. Of eight task categories
({{corpus.n_tasks}} tasks, {{corpus.n_structures}} structures), one asks for the residue
replaced by a variant that ClinVar classifies as pathogenic or likely
pathogenic. The variant's name usually gives a position in UniProt's canonical
sequence; the structure often numbers that residue differently. Do models map the
number, or copy it? To separate content from format errors,
{{corpus.n_twin_pairs}} requests are posed in two formats: a scene description
(MolViewSpec) and a list of viewer calls (PDBe Mol\*). The three scores are task success
(drawing exactly right), a target score (requested atoms marked exactly; background
ignored) and F1 (partial credit). The grader agrees with all {{controls.n:,}} control answers
used to develop it. A pilot run found that our first clinical references drew an unrequested
cartoon and its clinical tasks could not test the mapping; both are fixed.
⟦PENDING: final run — main results on both tracks and the paired comparison, with the number of models, in two sentences, which replace the sentence on the pilot run so that the abstract stays within its limit⟧
