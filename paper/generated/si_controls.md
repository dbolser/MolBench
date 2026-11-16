**Scene track.**

| Verdict known from construction | Kind of control | Controls | Graded as success | Graded as success by the earlier grader |
|:---|:---|---:|---:|---:|
| must pass (equivalent) | selector 'all' instead of 'polymer' under a cartoon (a cartoon draws polymer only) | 20 | 20 | 1 |
| must pass (equivalent) | a chain's cartoon selected by author chain id, label chain id or entity id | 20 | 20 | 2 |
| must pass (equivalent) | reference colours by the chain-id theme; the answer gives each chain its own colour | 20 | 20 | 0 |
| must pass (equivalent) | components, and the keys inside nodes, in another order | 20 | 20 | 20 |
| must pass (equivalent) | a colour given as #rrggbb (lower or upper case) instead of its name | 20 | 20 | 0 |
| must pass (equivalent) | defaults stated explicitly: opacity 1, colour selector 'all', model_index 0, size_factor 1 | 20 | 20 | 0 |
| must pass (equivalent) | an extra component that selects no atoms (nothing is drawn for it) | 20 | 20 | 0 |
| must pass (equivalent) | a full state with metadata, and the same entry from another server or as BinaryCIF | 20 | 20 | 13 |
| must pass (equivalent) | the focus node on its own component with the same selector | 20 | 20 | 20 |
| must pass (equivalent) | 'grey' instead of 'gray' | 20 | 20 | 20 |
| must pass (equivalent) | a residue range in label numbering instead of author numbering | 20 | 20 | 20 |
| must pass (equivalent) | a residue addressed by label chain and number instead of author chain and number | 20 | 20 | 20 |
| must pass (equivalent) | a ligand selected by residue name, or each copy by author chain and number | 20 | 20 | 20 |
| must pass (equivalent) | one cartoon with a colour child for one chain, or one cartoon component per chain | 20 | 20 | 0 |
| must pass (equivalent) | three residues in one component (a selector list) or in three components | 20 | 20 | 20 |
| must pass (equivalent) | a colour that a later colour node replaces (the last one wins) | 20 | 20 | 0 |
| must pass (equivalent) | one residue range written as two adjacent ranges in two components | 20 | 20 | 20 |
| must pass (equivalent) | six residues listed one by one instead of an author-number range | 20 | 20 | 20 |
| must pass (equivalent) | a residue's ball-and-stick selected atom by atom instead of as a residue | 20 | 20 | 20 |
| must pass (equivalent) | a cartoon asked for on a ligand or ion: Mol* draws ball-and-stick instead | 20 | 20 | 0 |
| must pass (equivalent) | a cartoon on the C-alpha atoms of a range instead of on the residues | 20 | 20 | 0 |
| must pass (equivalent) | the request states no colour for the cartoon (the reference has no colour node there): the answer gives it a palette colour | 20 | 20 | 0 |
| must pass (equivalent) | a stretch of the cartoon is to be coloured and the rest has no stated colour: the answer colours the rest in another palette colour | 20 | 20 | 0 |
| must pass (equivalent) | another entry's file is downloaded and parsed as well, and nothing of it is drawn | 20 | 20 | 0 |
| must pass (identical) | the answer is the reference itself | 150 | 150 | 150 |
| must fail (wrong) | 'all' instead of 'polymer' under ball-and-stick (waters and ligands are drawn too) | 20 | 0 | 0 |
| must fail (wrong) | the biological assembly is loaded where the deposited model was asked for | 20 | 0 | 0 |
| must fail (wrong) | the author residue number written in the label-number field (structures where they differ) | 20 | 0 | 0 |
| must fail (wrong) | two chains' colours the wrong way round | 20 | 0 | 0 |
| must fail (wrong) | the structure is loaded and nothing is drawn | 20 | 0 | 0 |
| must fail (wrong) | something that was not asked for is drawn as well | 20 | 0 | 0 |
| must fail (wrong) | the right scene on a source Mol* cannot read: the mmCIF file parsed as BinaryCIF, the entry's web page instead of its file, or a bare file name (the viewer shows nothing) | 20 | 0 | 13 |
| must fail (wrong) | the camera focus is on another residue, or absent | 20 | 0 | 0 |
| must fail (wrong) | the label residue number written in the author-number field (structures where they differ) | 20 | 0 | 0 |
| must fail (wrong) | the residue label has another text | 20 | 0 | 0 |
| must fail (wrong) | one requested component is not drawn | 20 | 0 | 0 |
| must fail (wrong) | a neighbouring shade outside the tolerance (lightgray for gray, darkred for red, ...) | 20 | 0 | 0 |
| must fail (wrong) | reference colours by chain; the answer paints every chain the same colour | 20 | 0 | 0 |
| must fail (wrong) | a residue range that stops three residues early | 20 | 0 | 0 |
| must fail (wrong) | the neighbouring residue is highlighted | 20 | 0 | 0 |
| must fail (wrong) | only the side chain is drawn where the whole residue was asked for | 20 | 0 | 0 |
| must fail (wrong) | the UniProt residue number used as the author number (structures with an offset) | 20 | 0 | 0 |
| must fail (wrong) | a stretch of the cartoon is to be coloured and the rest has no stated colour: the answer colours the whole cartoon in the stated colour, so nothing stands out | 20 | 0 | 0 |
| must fail (wrong) | the same residue number in another chain | 20 | 0 | 0 |
| must fail (wrong) | the highlight in another palette colour | 20 | 0 | 0 |
| must fail (wrong) | the same scene on another structure | 20 | 0 | 0 |
| must fail (wrong) | another copy of the ligand than the one asked for | 20 | 0 | 0 |
| must fail (wrong) | a transparent surface with another opacity, or opaque | 20 | 0 | 0 |
| must fail (wrong) | the highlight in another representation type | 20 | 0 | 0 |

**Call-list track.**

| Verdict known from construction | Kind of control | Controls | Graded as success | Graded as success by the earlier grader |
|:---|:---|---:|---:|---:|
| must pass (equivalent) | struct_asym_id (label chain) instead of auth_asym_id for the same chain | 20 | 20 | 17 |
| must pass (equivalent) | auth_residue_number instead of auth_seq_id | 20 | 20 | 20 |
| must pass (equivalent) | a colour as #rrggbb or as an {r,g,b} object instead of its name | 20 | 20 | 0 |
| must pass (equivalent) | an entity id instead of the entity's only chain | 20 | 20 | 0 |
| must pass (equivalent) | the entry id in upper case, or the same entry loaded by URL | 20 | 20 | 7 |
| must pass (equivalent) | focus: true inside the color call, or a separate focus action | 20 | 20 | 0 |
| must pass (equivalent) | settings that do not interact, in another order | 20 | 20 | 20 |
| must pass (equivalent) | struct_asym_id + residue_number (label) instead of auth_asym_id + auth_seq_id | 20 | 20 | 10 |
| must pass (equivalent) | a ligand by residue name, or each copy by author chain and number | 20 | 20 | 0 |
| must pass (equivalent) | steps that change nothing are added | 20 | 20 | 0 |
| must pass (equivalent) | two residues in one color call, or in two calls with keep_colors | 20 | 20 | 0 |
| must pass (equivalent) | a wrong color call followed by the right one (only the final state counts) | 20 | 20 | 0 |
| must pass (equivalent) | six residues one by one instead of a start/end range (label or author numbers) | 20 | 20 | 0 |
| must pass (equivalent) | the selections of one call in another order | 20 | 20 | 20 |
| must pass (equivalent) | sideChain: true instead of representation: ball-and-stick | 20 | 20 | 0 |
| must pass (equivalent) | set_property visual_style instead of set_visual_style | 20 | 20 | 0 |
| must pass (equivalent) | tooltip text differing only in case and repeated spaces | 20 | 20 | 20 |
| must pass (equivalent) | on an AlphaFold DB model, a residue by UniProt accession and number instead of author numbering (the model file carries the SIFTS columns) | 5 | 5 | 0 |
| must pass (equivalent) | a residue by UniProt accession and number, or every mapped copy by author numbering | 20 | 20 | 0 |
| must pass (equivalent) | a grey cartoon and a coloured ligand are asked for: the answer leaves the cartoon to the viewer's default view and paints the ligand (water and other components stay on screen, which the request does not mention) | 20 | 20 | 0 |
| must pass (equivalent) | the same request answered on the default view with the waters hidden, which nobody asked for: the task accepts the cartoon style (no water drawn) and the default view (water drawn), so the state in between is right too (the task's free_hide) | 20 | 20 | 0 |
| must pass (equivalent) | a grey cartoon and a residue as coloured ball-and-stick are asked for: the answer colours the residue and adds the ball-and-stick in the same colour, the form the API prompt's own example teaches (the residue's stretch of cartoon takes the highlight colour) | 20 | 20 | 0 |
| must pass (identical) | the answer is the reference itself | 150 | 150 | 150 |
| must fail (wrong) | the author residue number given as residue_number, which is label numbering | 20 | 0 | 15 |
| must fail (wrong) | the structure is loaded and nothing else is done | 20 | 0 | 0 |
| must fail (wrong) | color given where representationColor was needed: the added sticks stay element-coloured | 20 | 0 | 20 |
| must fail (wrong) | a second color call without keep_colors wipes the first colour | 20 | 0 | 0 |
| must fail (wrong) | something that was not asked for is done as well | 20 | 0 | 0 |
| must fail (wrong) | the focus is on another residue, or absent | 20 | 0 | 0 |
| must fail (wrong) | the label residue number given as auth_seq_id | 20 | 0 | 0 |
| must fail (wrong) | one requested step is left out | 20 | 0 | 0 |
| must fail (wrong) | a residue range that stops three residues early | 20 | 0 | 20 |
| must fail (wrong) | the neighbouring residue is coloured | 20 | 0 | 0 |
| must fail (wrong) | the global style is set after colouring, which wipes it | 20 | 0 | 20 |
| must fail (wrong) | the UniProt residue number used as the author number (structures with an offset) | 20 | 0 | 0 |
| must fail (wrong) | a residue by UniProt accession and number on RCSB's mmCIF loaded by URL: that file has no SIFTS columns, so the viewer selects nothing | 20 | 0 | 0 |
| must fail (wrong) | the default-view answer to 'grey cartoon, ligand in <colour>' without the grey: the cartoon keeps the viewer's chain colours, and grey was stated | 20 | 0 | 0 |
| must fail (wrong) | the default-view answer to 'grey cartoon, ligand in <colour>' with the ligand in another palette colour: what the request states still has to match | 20 | 0 | 0 |
| must fail (wrong) | the default-view answer to 'grey cartoon, residue as coloured ball-and-stick' with the polymer hidden: a free hide toggle never covers what was asked for | 20 | 0 | 0 |
| must fail (wrong) | the same residue number in another chain | 20 | 0 | 0 |
| must fail (wrong) | another palette colour | 20 | 0 | 0 |
| must fail (wrong) | the same calls on another structure | 20 | 0 | 0 |
| must fail (wrong) | another copy of the ligand than the one asked for | 20 | 0 | 0 |
| must fail (wrong) | another representation type for the residue | 20 | 0 | 0 |
