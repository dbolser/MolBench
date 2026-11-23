> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Clinical tasks on the scene track, grouped by whether copying the number is right (21 models, 3 samples per task)**

| Clinical tasks (scene track) | Tasks | Target score (the primary score here) | Task success rate | Target score with grounding pack | Task success rate with grounding pack |
|:---|---:|---:|---:|---:|---:|
| **Copying the number**: copying is right | 34 | 0.697 | 0.533 | 0.711 | 0.555 |
| **Copying the number**: copying is wrong | 48 | 0.708 | 0.537 | 0.693 | 0.535 |
| Difference between these two rows (95% interval) |  | -0.011 [-0.039, +0.020] | -0.004 [-0.029, +0.024] | +0.017 [-0.017, +0.051] | +0.020 [-0.006, +0.047] |
| **Offset** (for description only): no offset | 23 | 0.677 | 0.517 | 0.701 | 0.546 |
| **Offset**: offset | 59 | 0.714 | 0.542 | 0.700 | 0.543 |
| Matched tasks named in UniProt numbering, structure with an offset (copying is wrong) | 7 | 0.711 | 0.562 | 0.700 | 0.531 |
| The same variants on the predicted structure, without an offset (copying is right) | 7 | 0.692 | 0.531 | 0.739 | 0.565 |
| Helix or strand requested (a subset, reported apart) | 10 | 0.771 | 0.538 | 0.775 | 0.584 |
