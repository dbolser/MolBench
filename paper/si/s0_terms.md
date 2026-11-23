## S0. Background terms of structural biology

For readers from outside structural biology. Box 1 of the paper defines the terms of
sequences and variants (UniProt, ClinVar, transcript, missense variant, mature protein) and
the terms of the corpus; Box 2 defines the terms of grading.

**Table S0. Background terms.**

| Term | Meaning |
|:---------|:------------------------------|
| Residue, chain | A protein is a chain of amino acids. One amino acid in the chain is a *residue*; residues are numbered along the chain. A structure file names each chain with a short identifier, often one letter. |
| C-alpha | The central carbon atom of an amino acid, to which its side chain is attached. One C-alpha per residue traces the course of the chain. |
| Polymer | The protein, DNA or RNA chains of a structure, as opposed to bound small molecules, ions and water. |
| Structure, entry | A set of atom coordinates. An *entry* is one deposition in the Protein Data Bank (PDB), with a four-character identifier such as {{ex.entry}}; where an entry holds several coordinate sets we use the first. A *predicted structure* is one computed from the sequence; ours come from the AlphaFold Protein Structure Database. |
| mmCIF | The file format of the PDB archive: tables of named columns, one row per atom in the table of atoms. |
| Ligand, het group | A *ligand* is a small molecule bound to the protein. *Het group* is the older file term for any molecule in an entry that is not part of a polymer chain (a ligand, an ion, a water); each kind has an identifier of up to three characters, such as HEM for haem. |
| Helix, strand | The two common local shapes of a protein chain. An entry records where each helix and each strand begins and ends. |
| Disulfide bond | A link between the sulfur atoms of two cysteine residues. |
| Representation | A way of drawing atoms: *cartoon* (a ribbon that traces the chain), *ball-and-stick*, *spacefill* (every atom as a full-size sphere), *surface*. |
| Selection | The expression in an answer that picks atoms, for example "chain {{ex.auth_chain}}, residue {{ex.auth_number}}". |
| Alternate positions | The same atom recorded at two or more positions, where the experiment saw a residue in more than one pose (the file calls these alternate conformers). |
