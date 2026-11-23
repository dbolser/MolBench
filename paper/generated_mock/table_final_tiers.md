> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Scores by tier and track, mean over models (21 models, 3 samples per task)**

| Tier | Tasks | Structures | F1 (strict) | Task success (strict) | Target score (strict) | Task success, valid outputs only |
|:---|---:|---:|---:|---:|---:|---:|
| Scene track: Translation | 73 | 67 | 0.694 | 0.551 | 0.720 | 0.727 |
| Scene track: Structure-grounded | 63 | 55 | 0.687 | 0.534 | 0.743 | 0.710 |
| Scene track: Interactions | 40 | 38 | 0.725 | 0.560 | 0.733 | 0.736 |
| Scene track: Name resolution | 39 | 39 | 0.592 | 0.551 | 0.597 | 0.704 |
| Scene track: Clinical variant | 82 | 31 | 0.662 | 0.535 | 0.704 | 0.703 |
| Scene track: Follow-up turn | 58 | 42 | 0.703 | 0.541 | 0.751 | 0.707 |
| Scene track: Several right answers | 26 | 23 | 0.713 | 0.538 | 0.664 | 0.710 |
| Call-list track: Translation | 178 | 73 | 0.727 | 0.582 | 0.708 | 0.711 |
| Call-list track: Structure-grounded | 63 | 55 | 0.751 | 0.585 | 0.730 | 0.716 |
| Call-list track: Clinical variant | 82 | 31 | 0.732 | 0.584 | 0.755 | 0.706 |
| Call-list track: Follow-up turn | 44 | 41 | 0.735 | 0.569 | 0.791 | 0.697 |
| Call-list track: Several right answers | 15 | 12 | 0.739 | 0.611 | 0.739 | 0.726 |
| Call-list track: Viewer settings | 34 | 34 | 0.747 | 0.597 | 0.707 | 0.714 |

Original tasks. A follow-up turn without target atoms has no target score and is left out of that mean.
