> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Scores by category and track, mean over the models (21 models, 3 samples per task)**

| Category | Tasks | Structures | Task success rate, strict | Target score, strict | F1, strict | Task success rate, valid-only | Target score, valid-only |
|:---|---:|---:|---:|---:|---:|---:|---:|
| **Scene track** |  |  |  |  |  |  |  |
| Translation | 73 | 67 | 0.551 | 0.720 | 0.694 | 0.727 | 0.949 |
| Structure-grounded | 63 | 55 | 0.534 | 0.743 | 0.687 | 0.710 | 0.989 |
| Name resolution | 39 | 39 | 0.551 | 0.597 | 0.592 | 0.704 | 0.762 |
|  *of which:* answers on the reference entry | – | – | 0.840 | 0.910 | 0.902 | 0.885 | 0.958 |
|  *of which:* answers on another entry that the task accepts (graded by the weaker rule of Section 4.1) | – | – | – | – | – | – | – |
| Clinical variant | 82 | 31 | 0.535 | 0.704 | 0.662 | 0.703 | 0.924 |
| Interactions | 40 | 38 | 0.560 | 0.733 | 0.725 | 0.736 | 0.963 |
| Follow-up turn | 58 | 42 | 0.541 | 0.751 | 0.703 | 0.707 | 0.971 |
| Several right answers | 26 | 23 | 0.538 | 0.664 | 0.713 | 0.710 | 0.875 |
| **Call-list track** |  |  |  |  |  |  |  |
| Translation | 178 | 73 | 0.582 | 0.708 | 0.727 | 0.711 | 0.877 |
| Structure-grounded | 63 | 55 | 0.585 | 0.730 | 0.751 | 0.716 | 0.905 |
| Clinical variant | 82 | 31 | 0.584 | 0.755 | 0.732 | 0.706 | 0.929 |
| Follow-up turn | 44 | 41 | 0.569 | 0.791 | 0.735 | 0.697 | 0.996 |
| Several right answers | 15 | 12 | 0.611 | 0.739 | 0.739 | 0.726 | 0.893 |
| Viewer settings | 34 | 34 | 0.597 | 0.707 | 0.747 | 0.714 | 0.855 |
