> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Clinical tier: results by what the task demands (panel mean)**

| stratum | MVS: tasks | MVS: task success [95% CI] | MVS: target score | MVS, with grounding pack: tasks | MVS, with grounding pack: task success [95% CI] | MVS, with grounding pack: target score | API: tasks | API: task success [95% CI] | API: target score |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all clinical tasks | 82 | 0.535 [0.524, 0.546] | 0.704 | 82 | 0.544 [0.530, 0.557] | 0.700 | 82 | 0.584 [0.569, 0.597] | 0.755 |
| without helix / strand context tasks | 72 | 0.535 [0.523, 0.547] | 0.694 | 72 | 0.538 [0.524, 0.552] | 0.690 | 72 | 0.581 [0.566, 0.595] | 0.752 |
| helix / strand context tasks only | 10 | 0.538 [0.490, 0.575] | 0.771 | 10 | 0.584 [0.561, 0.603] | 0.775 | 10 | 0.603 [0.558, 0.649] | 0.779 |
| `needs_offset`: yes | 49 | 0.543 [0.528, 0.558] | 0.702 | 49 | 0.534 [0.516, 0.554] | 0.685 | 49 | 0.580 [0.564, 0.597] | 0.749 |
| `needs_offset`: no | 23 | 0.517 [0.492, 0.537] | 0.677 | 23 | 0.546 [0.530, 0.570] | 0.701 | 23 | 0.583 [0.549, 0.613] | 0.759 |
| `chain_mismatch`: yes | 20 | 0.540 [0.529, 0.549] | 0.694 | 20 | 0.539 [0.506, 0.571] | 0.673 | 20 | 0.574 [0.558, 0.594] | 0.743 |
| `chain_mismatch`: no | 52 | 0.533 [0.516, 0.548] | 0.694 | 52 | 0.538 [0.524, 0.554] | 0.696 | 52 | 0.584 [0.564, 0.602] | 0.755 |
| `number_in_name_as_author_number_is_right`: yes | 34 | 0.533 [0.514, 0.551] | 0.697 | 34 | 0.555 [0.535, 0.580] | 0.711 | 34 | 0.584 [0.560, 0.606] | 0.760 |
| `number_in_name_as_author_number_is_right`: no | 38 | 0.536 [0.521, 0.554] | 0.692 | 38 | 0.523 [0.506, 0.540] | 0.672 | 38 | 0.579 [0.563, 0.597] | 0.745 |
| `name_in_mature_numbering`: yes | 13 | 0.568 [0.549, 0.589] | 0.734 | 13 | 0.545 [0.493, 0.604] | 0.696 | 13 | 0.595 [0.560, 0.626] | 0.764 |
| `name_in_mature_numbering`: no | 59 | 0.528 [0.514, 0.541] | 0.685 | 59 | 0.536 [0.524, 0.550] | 0.689 | 59 | 0.578 [0.564, 0.593] | 0.749 |
| `alphafold_model`: yes | 10 | 0.530 [0.515, 0.575] | 0.694 | 10 | 0.541 [0.517, 0.601] | 0.708 | 10 | 0.592 [0.532, 0.624] | 0.768 |
| `alphafold_model`: no | 62 | 0.536 [0.521, 0.549] | 0.694 | 62 | 0.537 [0.522, 0.552] | 0.687 | 62 | 0.579 [0.564, 0.594] | 0.749 |
| `author_label_numbers_differ`: yes | 23 | 0.536 [0.514, 0.556] | 0.695 | 23 | 0.534 [0.517, 0.554] | 0.695 | 23 | 0.563 [0.541, 0.580] | 0.741 |
| `author_label_numbers_differ`: no | 49 | 0.535 [0.519, 0.550] | 0.694 | 49 | 0.540 [0.522, 0.559] | 0.688 | 49 | 0.590 [0.572, 0.608] | 0.757 |

The helix / strand context tasks need the entry's own secondary-structure annotation, which only the grounding pack states, and are reported apart; the strata below them leave those tasks out. `needs_offset`: the residue's author number differs from its UniProt number (yes: 15 proteins, no: 14, 4 of them on both sides). `number_in_name_as_author_number_is_right`: using the number in the variant name as the author residue number already gives the right residue, so such a task can be solved without any mapping. On the API track the viewer maps UniProt numbering itself. Intervals: bootstrap over structures.
