| Category | Template | Scene tasks | Call-list tasks | Example request |
|:----|:-----|--:|--:|:----------------|
| Translation | `api-assembly` | – | 6 | Load oxyhaemoglobin (1HHO) as its biological assembly (the tetramer, assembly 1) and show it as a molecular surface. |
| Translation | `api-atoms` | – | 5 | Open 1AAY in the ball-and-stick style; atoms CB and OD1 of Asp166 of chain A should be cyan. |
| Translation | `api-chain-colour` | – | 10 | Load insulin (4INS) as a cartoon. Colour the two A chains (author chains A and C) blue and the two B chains (author chains B and D) yellow, and show the zinc ions (ZN)… |
| Translation | `api-entity` | – | 5 | In 1AOI, colour by molecule: entity 3 (protein) cyan and entity 4 (protein) steel blue. Leave the other entities alone. |
| Translation | `api-hide` | – | 11 | Load the myoglobin structure 1A6M and hide all the water molecules. |
| Translation | `api-inscode` | – | 5 | Load 1IGT and colour Asn52A of chain D purple: the residue with insertion code A, not the other residue numbered 52. In the mmCIF label numbering it is residue 53 of l… |
| Translation | `api-keep-sticks` | – | 3 | Open 1D5R. Step one: Asp268 as ball-and-stick. Step two, on top of step one: Thr26 as spacefill. Element colours for both, and no other colour changes. |
| Translation | `api-label-chain` | – | 5 | In 1ATP, colour label chain B hot pink: B is the mmCIF label chain id, not the author chain id. |
| Translation | `api-layered-colour` | – | 7 | Open 1A3K; residues 197 to 204 in plum, but Val202 in hot pink. |
| Translation | `api-ligand` | – | 8 | Load streptavidin (1STP), hide the waters, and centre the view on the bound biotin (BTN). |
| Translation | `api-ligand-sticks` | – | 3 | Open haemoglobin (1HHO) and show the heme groups (HEM) in ball-and-stick coloured orange, with the rest as cartoon. |
| Translation | `api-range-colour` | – | 9 | Load ubiquitin (1UBQ) and colour the C-terminal tail, residues 71 to 76, red and the rest of the structure white. |
| Translation | `api-residue-colour` | – | 9 | Load 1AAY and colour Ser147, Ala164 and Glu177 of chain A khaki. |
| Translation | `api-residue-sticks` | – | 7 | Load hen egg-white lysozyme (1LYZ) as a cartoon, colour the two catalytic residues Glu35 and Asp52 red, and also show them as a red molecular surface. |
| Translation | `api-sticks-plain` | – | 3 | Open 1D5R and draw His61 as ball-and-stick on top of the default view; keep every colour at its default. |
| Translation | `api-style-colour` | – | 5 | Show 1CRN as putty and colour residues 14 to 20 purple. |
| Translation | `api-uniprot-range` | – | 6 | Load 1IGT and colour residues 108 to 121 of UniProt P01863 in both chains that have them orange. |
| Translation | `api-uniprot-residue` | – | 9 | Load 1AKI and colour His33 and Asn62 purple. The numbers are in UniProt numbering (P00698). |
| Translation | `tr-cartoon` | 4 | 4 | Open PDB entry 1C3W; draw the whole protein as a cartoon, coloured yellow. |
| Translation | `tr-chain-colour` | 4 | 4 | Load 1K4C as a grey cartoon and colour chain A blue. |
| Translation | `tr-chain-only` | 4 | 4 | Load 1AKE and show only chain A, as a teal cartoon. |
| Translation | `tr-chains-named` | 4 | 4 | Load 4INS as a cartoon and colour chain A magenta, chain B cyan, chain C plum and chain D red. |
| Translation | `tr-colour-by-chain` | 5 | – | Load 1AOI and show it as a cartoon coloured by chain. |
| Translation | `tr-glycans` | 4 | 4 | 1A3K: grey cartoon for the protein, hot pink ball-and-stick for the bound sugar. |
| Translation | `tr-het-code` | 4 | 4 | Show 1CBS as a grey cartoon with the REA residue in teal ball-and-stick. |
| Translation | `tr-ions` | 4 | 4 | Show 2P4E as a grey cartoon with the metal ions drawn as hot pink spheres. |
| Translation | `tr-ligands` | 4 | 4 | 1HVR: grey cartoon for the protein, magenta ball-and-stick for the ligand. |
| Translation | `tr-nucleic` | 5 | 5 | 1AAY, cartoon: DNA khaki, protein salmon. |
| Translation | `tr-range-labels` | 4 | – | Load 1A6M as a grey cartoon, then colour residues 5-12 of chain A yellow with the text label "patch B" and colour residues 68-79 of chain A red with the text label "si… |
| Translation | `tr-range-rows` | 4 | 4 | Load 1ATP as a grey cartoon and colour these segments: chain E 16-30 yellow; chain E 58-69 salmon. |
| Translation | `tr-range-sticks` | 5 | 5 | Load 1CRN as a grey cartoon and show residues 14-23 as brown ball-and-stick. |
| Translation | `tr-rep-word` | 4 | 2 | Load 1MBN and show the protein as brown space-filling spheres. |
| Translation | `tr-residue-focus` | 4 | 4 | 1EMA: grey cartoon, residue 196 as orange ball-and-stick, camera focused on the residue. |
| Translation | `tr-strands` | 3 | 3 | Load 1AAY and show the two DNA strands as cartoons: chain B in teal and chain C in blue. Nothing else. |
| Translation | `tr-surface` | 4 | 4 | Load 1AKI and show the protein as a steel blue molecular surface. |
| Translation | `tr-water` | 3 | 3 | Show 1IRO as a blue cartoon together with its waters as teal spheres. |
| Structure-grounded | `gr-all-but-chain` | 3 | 3 | 1LMB as an orange cartoon without chain 2: hide that chain and keep all the others. |
| Structure-grounded | `gr-attachment` | 4 | 4 | Show 1C3W as a grey cartoon with the retinal in steel blue ball-and-stick and the lysine that holds it covalently in lime green ball-and-stick. |
| Structure-grounded | `gr-catalytic` | 6 | 6 | 1AKI: grey cartoon, with the two catalytic residues drawn as green ball-and-stick. |
| Structure-grounded | `gr-disulfides` | 6 | 6 | 1CRN: grey cartoon, with every disulfide-bonded cysteine drawn in plum ball-and-stick. |
| Structure-grounded | `gr-entity` | 6 | 6 | Show 1AOI as a cartoon coloured by molecule: the two H3 histones orange, the two H4 histones brown, the two H2A histones red, the two H2B histones khaki and everything… |
| Structure-grounded | `gr-glyco-sites` | 5 | 5 | Show 1IGT as a grey cartoon and mark the glycosylation sites: the asparagines that carry a sugar, in brown ball-and-stick. Do not draw the sugars. |
| Structure-grounded | `gr-heme` | 4 | 4 | Load 1MBN; show the protein as a grey cartoon and the heme group as teal spheres. |
| Structure-grounded | `gr-heme-axial` | 4 | 4 | Load 1A6M; show the protein as a grey cartoon, the heme as teal ball-and-stick, and the protein residue bonded to the heme iron as hot pink ball-and-stick. |
| Structure-grounded | `gr-ligand` | 6 | 6 | In 1AKE, draw the protein as a grey cartoon and pick out the AP5A in lime green ball-and-stick. |
| Structure-grounded | `gr-longest-helix` | 4 | 4 | Load 1D5R as a grey cartoon and colour its longest helix lime green, going by the helix records of the entry. |
| Structure-grounded | `gr-metal-site` | 6 | 6 | 1IRO: grey cartoon; iron ion as a khaki sphere; every residue of the protein that coordinates the iron ion, as green ball-and-stick. |
| Structure-grounded | `gr-modres` | 5 | 5 | Show 1ATP as a grey cartoon and highlight the phosphorylated residues in lime green ball-and-stick. |
| Structure-grounded | `gr-secstruct` | 4 | 4 | Show 1A3K as a grey cartoon, then colour the helices blue and the beta strands lime green, following the helix and sheet records of the entry. |
| Interactions | `in-ca-distance` | 5 | – | Show 1AKE as a yellow cartoon. Add a distance measurement (dashed line with the value as label) from the CA atom of Ser183 to the CA atom of Lys200. Both residues are… |
| Interactions | `in-computed` | 5 | – | 1A6M: grey cartoon; heme as red ball-and-stick with its computed non-covalent interactions shown; camera on the heme. |
| Interactions | `in-disulfide` | 5 | – | In 1F88 (grey cartoon), measure the S-S bond of the disulfide between Cys110 and Cys187: the two cysteines in green ball-and-stick, a labelled dashed line between thei… |
| Interactions | `in-hbond` | 5 | – | 1A3K: grey cartoon; Asn174 and Arg224 as magenta ball-and-stick; measure the hydrogen bond between OD1 of Asn174 and NH1 of Arg224 with a labelled dashed line; focus t… |
| Interactions | `in-ligand-contact` | 5 | – | 1ATP: grey cartoon; ATP as teal ball-and-stick; Phe54 as cyan ball-and-stick; measure the contact between ATP atom O2B and N of Phe54 with a labelled dashed line; focu… |
| Interactions | `in-metal-contact` | 5 | – | 1HRC: grey cartoon; heme as plum ball-and-stick; His18 and Met80 as salmon ball-and-stick; measure the distance from the heme iron to NE2 of His18 and SD of Met80 with… |
| Interactions | `in-salt-bridge` | 5 | – | Load 1EMA as a grey cartoon. Show Lys3 and Glu90 as cyan ball-and-stick, draw the salt bridge between the NZ atom of Lys3 and the OE1 atom of Glu90 as a dashed line la… |
| Interactions | `in-transparent` | 5 | – | Show 1CTQ with a semi-transparent brown protein surface (opacity 0.5) so that the GppNHp, drawn in steel blue ball-and-stick, can be seen through it. |
| Name resolution | `res-complex` | 3 | – | Find a PDB entry of bovine trypsin in complex with bovine pancreatic trypsin inhibitor (BPTI) and show it as a plum cartoon. |
| Name resolution | `res-dna` | 3 | – | I want to see how the cI repressor of bacteriophage lambda sits on DNA. Any PDB structure of the complex will do: protein as a brown cartoon, DNA as a teal cartoon. |
| Name resolution | `res-gene` | 11 | – | I want to see a structure of human SOD1; a green cartoon will do. |
| Name resolution | `res-ligand` | 10 | – | Find a PDB entry of human phosphodiesterase 5A (PDE5A) in complex with sildenafil; draw the protein as a lime green cartoon and the sildenafil in purple ball-and-stick. |
| Name resolution | `res-name` | 12 | – | Find a PDB entry of horse heart cytochrome c and show it as a yellow cartoon. |
| Clinical variant | `clin-chain` | 8 | 8 | PDB entry 8EPH: the F9 (Coagulation factor IX, UniProt P00740) variant p.Gly412Glu is classified as pathogenic in ClinVar. Show the residue it replaces as magenta ball… |
| Clinical variant | `clin-hgvs-context` | 6 | 6 | PDB entry 8CE0: the APOE (Apolipoprotein E) variant p.Arg43Cys is classified as pathogenic/likely pathogenic in ClinVar. Show the whole structure as a white cartoon, w… |
| Clinical variant | `clin-hgvs-target` | 5 | 5 | In PDB entry 5CJ6, show the residue replaced by the likely pathogenic AR (Androgen receptor) variant p.Leu702Phe (ClinVar) as purple ball-and-stick. |
| Clinical variant | `clin-legacy-context` | 6 | 6 | In PDB entry 1HK0, show the whole structure as a gray cartoon and the residue replaced by the likely pathogenic CRYGD (Gamma-crystallin D, UniProt P07320) variant L44P… |
| Clinical variant | `clin-legacy-target` | 7 | 7 | In PDB entry 8CE0, show the residue replaced by the likely pathogenic APOE (Apolipoprotein E) variant R136L (ClinVar) as green ball-and-stick. The name R136L is in mat… |
| Clinical variant | `clin-multi-context` | 4 | 4 | In PDB entry 5CJ6, show the whole structure as a white cartoon and the residues replaced by the AR (Androgen receptor) variants p.P724S and p.M781I (each pathogenic or… |
| Clinical variant | `clin-multi-target` | 4 | 4 | Using PDB entry 6M7H, show as green spacefill spheres the wild-type residues at the positions of the CALM1 (Calmodulin-1) missense variants p.Thr30Pro, p.Glu105Lys and… |
| Clinical variant | `clin-pair-context` | 8 | 8 | PDB entry 1HK0: the CRYGD (Gamma-crystallin D, UniProt P07320) variant p.Arg37Pro is classified as likely pathogenic in ClinVar. Show the whole structure as a khaki ca… |
| Clinical variant | `clin-pair-target` | 10 | 10 | Using PDB entry 6M7H, show as cyan spacefill spheres the wild-type residue at the position of the CALM1 (Calmodulin-1, UniProt P0DP23) missense variant p.Phe142Leu (pa… |
| Clinical variant | `clin-short-context` | 5 | 5 | In PDB entry 5EDM, show the whole structure as a white cartoon and the residue replaced by the pathogenic/likely pathogenic F2 (Prothrombin) variant p.R461W (ClinVar)… |
| Clinical variant | `clin-short-target` | 9 | 9 | In PDB entry 5UAK, show the residue replaced by the pathogenic CFTR (Cystic fibrosis transmembrane conductance regulator) variant p.G551D (ClinVar) as magenta ball-and… |
| Clinical variant | `clin-sse-helix` | 5 | 5 | PDB entry 6M7H: the CALM1 (Calmodulin-1, UniProt P0DP23) variant p.E141V is classified as pathogenic in ClinVar. Show the helix (as annotated in the entry) that contai… |
| Clinical variant | `clin-sse-strand` | 5 | 5 | PDB entry 1HK0: the CRYGD (Gamma-crystallin D, UniProt P07320) variant p.Arg59His is classified as pathogenic in ClinVar. Show the beta strand (as annotated in the ent… |
| Follow-up turn | `fu-add-chain` | 2 | – | Also show chain 4 as a blue cartoon. |
| Follow-up turn | `fu-add-label` | 2 | – | Add a label reading "BTN" to the biotin (BTN). |
| Follow-up turn | `fu-add-ligand` | 2 | – | Now bring in the ligand HEM in plum ball-and-stick. |
| Follow-up turn | `fu-add-residue` | 4 | 4 | Now draw His122 of chain A as ball-and-stick too, in yellow; the cartoon keeps its colour. |
| Follow-up turn | `fu-also-colour-chain` | 2 | 2 | Now colour chain B as well, in brown. |
| Follow-up turn | `fu-api-clear-colours` | – | 1 | Go back to the default colours; the waters stay hidden. |
| Follow-up turn | `fu-api-show-water` | – | 2 | Bring the water molecules back. |
| Follow-up turn | `fu-api-stop-spin` | – | 1 | Stop the spinning. |
| Follow-up turn | `fu-api-style` | – | 2 | Switch the whole structure to the putty style and keep the two chain colours. |
| Follow-up turn | `fu-api-uncolour` | – | 2 | Put the retinal (RET) back to its default colours; the protein stays yellow. |
| Follow-up turn | `fu-background` | 2 | 2 | Black background, please. |
| Follow-up turn | `fu-focus-ligand` | 2 | 2 | Now focus the camera on the ligand GNP. |
| Follow-up turn | `fu-hide-water` | 2 | 2 | Get rid of the waters, please. |
| Follow-up turn | `fu-it-colour` | 2 | – | Colour it steel blue. |
| Follow-up turn | `fu-it-surface` | 1 | – | Make it a surface instead of a cartoon. |
| Follow-up turn | `fu-noop-colour` | 2 | 2 | Show the heme c (HEC) in cyan. |
| Follow-up turn | `fu-noop-hidden` | 2 | 2 | Hide the waters. |
| Follow-up turn | `fu-noop-ligand-rep` | 2 | 2 | Show the ligand HEM as ball-and-stick. |
| Follow-up turn | `fu-noop-shown` | 2 | 2 | Cartoon for the protein, please. |
| Follow-up turn | `fu-noop-spin` | 2 | – | Make the structure spin slowly, or leave the scene as it is if spinning is not possible here. |
| Follow-up turn | `fu-only-chain` | 2 | – | Only chain A, please. |
| Follow-up turn | `fu-opacity` | 2 | – | Can you make the surface of the protein 70% transparent? |
| Follow-up turn | `fu-other-chain` | 2 | 2 | Colour the other chain grey. |
| Follow-up turn | `fu-recolour-chain` | 2 | 2 | Change chain I to yellow. |
| Follow-up turn | `fu-recolour-ligand` | 3 | 3 | Could you turn the ligand XK2 blue? |
| Follow-up turn | `fu-referent-colour` | 3 | 3 | Change the teal chain to brown. |
| Follow-up turn | `fu-remove-label` | 1 | – | Take the label off. |
| Follow-up turn | `fu-remove-ligand` | 2 | – | Remove the ligand ATP from the view. |
| Follow-up turn | `fu-rep-ligand` | 2 | – | Show the ligand XK2 as spacefill instead of ball-and-stick. |
| Follow-up turn | `fu-rep-polymer` | 2 | – | Switch the protein from cartoon to surface. |
| Follow-up turn | `fu-same-colour-as` | 2 | 2 | Give the retinoic acid (REA) the same colour as the protein. |
| Follow-up turn | `fu-swap-colours` | 2 | 2 | Swap the colours of the two chains. |
| Follow-up turn | `fu-undo-grey` | 2 | 2 | Undo the magenta on the biotin (BTN): grey again, please. |
| Several right answers | `acc-chain-colours` | 3 | 3 | Load 1AAY and show it as a cartoon, with the three chains coloured green, magenta and cyan. |
| Several right answers | `acc-ligand-colours` | 3 | 3 | Show 1RX2 with the protein as a cartoon and the two ligands as ball-and-stick: one cyan, the other blue. |
| Several right answers | `acc-ligand-copy` | 3 | 3 | Open 1IEP with the protein as a cartoon and the ligand STI in purple ball-and-stick. |
| Several right answers | `acc-ligand-which` | 3 | 3 | Open 1RX2 with the protein as a cartoon and the ligand in cyan ball-and-stick. |
| Several right answers | `acc-metal-copy` | 3 | – | Show 1TUP with the protein and DNA as a cartoon and the zinc ion as a spacefill sphere, coloured magenta. |
| Several right answers | `acc-metal-which` | 2 | – | Open 1UDT with the protein as a cartoon and the metal ion in red spacefill. |
| Several right answers | `acc-representation-open` | 3 | – | Open 1MBN with the protein as a cartoon, and show the heme in blue. |
| Several right answers | `acc-residue-colour` | 3 | 3 | Show 1AOI with the protein and DNA as a cartoon. Colour Ile66 blue. |
| Several right answers | `acc-residue-copy` | 3 | – | Show 1TRN with the protein as a cartoon and Lys236 as ball-and-stick, coloured purple. |
| Viewer settings | `api-alphafold` | – | 3 | Load the AlphaFold DB model of human p53 (UniProt P04637) and colour it by the model's per-residue confidence (pLDDT). |
| Viewer settings | `api-canvas` | – | 4 | Show insulin (4INS), hide the waters and the heteroatoms, set glossy lighting, and make it slowly spin. |
| Viewer settings | `api-domain-overlay` | – | 3 | Load hen egg-white lysozyme (1AKI) as a cartoon, overlay the domain annotations, and attach a tooltip reading 'catalytic glutamate' to Glu35 on chain A. |
| Viewer settings | `api-highlight` | – | 3 | Load haemoglobin (1HHO), set the hover-highlight colour to yellow and the selection colour to cyan, and highlight the heme groups (HEM). |
| Viewer settings | `api-ligand-view` | – | 3 | I want the ligand view for the ligand XK2 of 1HVR: just that ligand with its environment, white background. |
| Viewer settings | `api-maps` | – | 2 | Load 3ERT with its electron-density maps, drawing the positive Fo-Fc difference map as a wireframe at opacity 0.7. |
| Viewer settings | `api-preset` | – | 2 | Load 1BNA showing the whole unit cell, on a black background. |
| Viewer settings | `api-superposition` | – | 3 | Open the PDBe-KB superposition view for human haemoglobin subunit alpha (UniProt P69905) on a white background. |
| Viewer settings | `api-symmetry-overlay` | – | 1 | Open 2OMF as assembly 1, the trimer, with the symmetry annotation turned on. |
| Viewer settings | `api-tooltips` | – | 3 | In 1C3W, switch off the water molecules and add hover tooltips reading 'Leu100' on Leu100 and 'Gly218' on Gly218. |
| Viewer settings | `api-undo` | – | 4 | Load 1F88 and hide the waters. Colour both copies of the retinal (RET) orange and highlight chain A; then clear the highlight again. |
| Viewer settings | `api-validation-overlay` | – | 3 | Load the A2A adenosine receptor (3EML) as a cartoon and overlay the PDBe geometry-validation colouring. |
