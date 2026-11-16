> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Tier by track: panel mean**

| tier | MVS tasks | MVS task success [95% CI] | MVS strict F1 [95% CI] | MVS target score | API tasks | API task success [95% CI] | API strict F1 [95% CI] | API target score |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| translation | 68 | 0.550 [0.532, 0.570] | 0.695 [0.680, 0.709] | 0.724 | 163 | 0.580 [0.570, 0.591] | 0.727 [0.717, 0.736] | 0.705 |
| grounded | 68 | 0.535 [0.520, 0.550] | 0.687 [0.676, 0.699] | 0.737 | 68 | 0.583 [0.566, 0.601] | 0.746 [0.725, 0.764] | 0.721 |
| interactions | 40 | 0.560 [0.542, 0.579] | 0.725 [0.709, 0.739] | 0.733 | – | – | – | – |
| resolve | 39 | 0.551 [0.533, 0.567] | 0.592 [0.576, 0.609] | 0.597 | – | – | – | – |
| clinical | 79 | 0.530 [0.518, 0.540] | 0.657 [0.644, 0.667] | 0.698 | 79 | 0.576 [0.559, 0.592] | 0.726 [0.714, 0.736] | 0.733 |
| follow-up | 58 | 0.538 [0.522, 0.555] | 0.699 [0.684, 0.715] | 0.725 | 44 | 0.561 [0.546, 0.578] | 0.727 [0.710, 0.743] | 0.759 |
| accept-set | 26 | 0.537 [0.502, 0.569] | 0.712 [0.685, 0.736] | 0.665 | 15 | 0.611 [0.576, 0.634] | 0.739 [0.708, 0.762] | 0.739 |
| tool-only | – | – | – | – | 34 | 0.591 [0.566, 0.618] | 0.743 [0.723, 0.763] | 0.695 |

Each task's value is its mean over the 21 models of the panel (keyword baseline left out); a cell is the mean over the tier's original tasks. Intervals: bootstrap over structures, the panel held fixed.
