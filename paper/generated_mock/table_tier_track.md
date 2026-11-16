> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Tier by track: panel mean**

| tier | MVS tasks | MVS task success [95% CI] | MVS strict F1 [95% CI] | MVS target score | API tasks | API task success [95% CI] | API strict F1 [95% CI] | API target score |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| translation | 73 | 0.551 [0.534, 0.570] | 0.694 [0.682, 0.707] | 0.720 | 178 | 0.582 [0.571, 0.593] | 0.727 [0.718, 0.735] | 0.706 |
| grounded | 63 | 0.534 [0.518, 0.549] | 0.687 [0.675, 0.699] | 0.743 | 63 | 0.585 [0.565, 0.605] | 0.751 [0.730, 0.768] | 0.729 |
| interactions | 40 | 0.560 [0.542, 0.579] | 0.725 [0.709, 0.739] | 0.733 | – | – | – | – |
| resolve | 39 | 0.551 [0.533, 0.567] | 0.592 [0.576, 0.609] | 0.597 | – | – | – | – |
| clinical | 82 | 0.535 [0.523, 0.546] | 0.662 [0.650, 0.672] | 0.704 | 82 | 0.584 [0.569, 0.597] | 0.732 [0.722, 0.741] | 0.738 |
| follow-up | 58 | 0.541 [0.526, 0.557] | 0.703 [0.690, 0.717] | 0.751 | 44 | 0.569 [0.552, 0.586] | 0.735 [0.715, 0.753] | 0.791 |
| accept-set | 26 | 0.538 [0.505, 0.570] | 0.713 [0.685, 0.738] | 0.664 | 15 | 0.611 [0.576, 0.634] | 0.739 [0.708, 0.762] | 0.739 |
| tool-only | – | – | – | – | 34 | 0.597 [0.574, 0.621] | 0.747 [0.728, 0.765] | 0.707 |

Each task's value is its mean over the 21 models of the panel (keyword baseline left out); a cell is the mean over the tier's original tasks. Intervals: bootstrap over structures, the panel held fixed.
