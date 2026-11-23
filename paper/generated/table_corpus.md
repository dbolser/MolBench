| Category | What is asked | Scene track (other + set-aside) | Call-list track (other + set-aside) | Pairs |
|:---------|:----------------|-----:|-----:|--:|
| ***Differ in what the model must know*** | | | | |
| Translation | Everything needed is in the request; write it in the format. | 73 (55 + 18) | 178 (138 + 40) | 62 |
| Structure-grounded | The request names a feature (the ligand, a bound small molecule; the disulfides, bonds between two cysteines); the model must know which atoms these are. | 63 (52 + 11) | 63 (52 + 11) | 63 |
| Name resolution | The structure is named by protein, not by identifier. | 39 (32 + 7) | – | – |
| Clinical variant | A variant is named in UniProt numbering or in mature-protein numbering; its residue must be found in the structure, where its number often differs. | 82 (63 + 19) | 82 (63 + 19) | 82 |
| ***Differ in the form of the task*** | | | | |
| Interactions | Named atoms and a measurement or contact between them. | 40 (32 + 8) | – | – |
| Follow-up turn | A start state plus an edit request; the full new state is returned. | 58 (50 + 8) | 44 (34 + 10) | 36 |
| Several right answers | The request leaves one countable thing open; several drawn states are right. | 26 (21 + 5) | 15 (11 + 4) | 15 |
| Viewer settings | A viewer setting that only the call-list format can express. | – | 34 (29 + 5) | – |
| **All** | | **381** (305 + 76) | **416** (327 + 89) | **258** |
