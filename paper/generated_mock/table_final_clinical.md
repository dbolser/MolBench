> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Clinical tier on the scene track, by what the request demands (21 models, 3 samples per task)**

| Clinical tasks (scene track) | Tasks | Task success | Target score | Task success with grounding pack |
|:---|---:|---:|---:|---:|
| Number in the variant name is the author residue number | 34 | 0.533 | 0.697 | 0.555 |
| Number in the variant name is **not** the author residue number | 48 | 0.537 | 0.708 | 0.535 |
| Target residue numbered as in UniProt | 23 | 0.517 | 0.677 | 0.546 |
| Target residue numbered differently from UniProt | 59 | 0.542 | 0.714 | 0.543 |
| Helix or strand requested (reported apart) | 10 | 0.538 | 0.771 | 0.584 |

Strict, mean over models. The grounding pack states the residue the variant maps to, so the last column is an upper bound: the lookup done and its result handed over.
