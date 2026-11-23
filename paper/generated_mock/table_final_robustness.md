> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Planned comparisons 1 to 6 (21 models, 3 samples per task)**

|  | Comparison | Tasks | Task success rate, first group | Task success rate, second group | Difference (95% interval) |
|---:|:---|---:|---:|---:|---:|
| 1 | Tasks on the other structures against the set-aside split (both tracks; all tasks) | 632 and 165 | 0.564 | 0.566 | +0.002 [-0.008, +0.011] |
| 2 | Full wording against terse wording (both tracks) | 30 requests (41 tasks) | 0.559 | 0.562 | +0.003 [-0.018, +0.022] |
| 3 | Full wording against indirect wording (both tracks) | 30 requests (41 tasks) | 0.559 | 0.550 | -0.009 [-0.034, +0.017] |
| 4 | Main against main + JSON mode (models that offer it; both tracks) | 797 | 0.565 | 0.563 | -0.001 [-0.009, +0.006] |
| 5 | Main against main + grounding pack (name-resolution and clinical categories, scene track) | 121 | 0.540 | 0.543 | +0.003 [-0.010, +0.017] |
| 6 | Main against no format guide (3 models, scene track) | 381 | 0.542 | 0.537 | -0.005 [-0.026, +0.015] |

The difference is the second group minus the first.
