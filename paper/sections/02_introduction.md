## 1. Introduction

Molecular viewers are how structural biologists look at their data. They are also hard to drive.
To show one residue in one chain, a user must know the viewer's selection language, the chain
identifier, and which of two residue numbering schemes the viewer expects. Language models
promise to remove that barrier: the user says what they want and the model writes the commands.
Several viewers now ship such assistants, or expose themselves to one through a tool protocol
[@chimeraxmcp; @molstarprism; @navarro2026speak; @sun2024chatmol].

Whether these assistants are right is rarely measured. A wrong scene looks as polished as a
correct one. A model that colours residue 175 of the wrong chain, or residue 175 by the wrong
numbering scheme, still produces a clean picture. For a clinical variant, that picture points a
reader at the wrong amino acid. The problem is not rare: a survey of the Protein Data Bank found
that more than a third of entries contain proteins that are not numbered as their UniProt sequences
are (38.6% of the 176,507 entries examined) [@faezov2021pdbrenum].

We built MolBench to measure this. It rests on four choices.

**Grade what the viewer would show.** A model's answer is resolved to the set of atoms it selects
in the real structure, and to how those atoms are drawn and coloured. Two answers that name the
same atoms in different ways score the same. An answer that selects nothing scores nothing. The
grader never compares text with text.

**Build every reference by script.** No reference answer is written from memory. Each one is
produced by a script from the deposited structure and public annotation, records how it was
made, and is tested against the structure.

**Ask the same question in two formats.** Each request is posed once for a declarative scene
description, MolViewSpec [@midlik2025mvs; @bittrich2024mvs], and once for an imperative call list
against the PDBe Mol\* viewer [@pdbemolstar; @ipymolstar]. If a model picks the right atoms in one
format and not in the other, the fault lies in writing the format, not in the biology.

**Raise the difficulty in known steps.** Tasks range from translating a fully specified request,
through requests that need facts about the structure (which ligand, which disulfide bonds), to
requests about clinical variants. A variant is reported in UniProt numbering [@uniprot2025;
@landrum2018clinvar]. To show it, a model must find the matching residue in the structure, which
needs the residue-level mapping kept by SIFTS [@dana2019sifts].

This paper makes three contributions.

1. A benchmark of ⟦PENDING: final task count (target: about 300 across both tracks)⟧ tasks on
   ⟦PENDING: final structure count (target: at least 50 PDB entries)⟧ structures, with references
   that are correct by construction, in two output formats, with follow-up turns and a small set
   of requests that have more than one right answer.
2. A grader based on resolved atoms and final viewer state, with an explicit account of invalid
   output. We report a strict score, a score over valid outputs only, and what an offline repair
   of broken JSON would have changed.
3. Findings from a panel of current models, including two null results that we report as
   findings: frozen grounding facts did not raise scores, and without a copy of the format
   reference no model produced a valid scene.

We use "computational intelligence (CI)" for what is often called artificial intelligence.
