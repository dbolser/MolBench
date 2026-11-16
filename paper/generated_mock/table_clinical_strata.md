> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Clinical tier: results by what the task demands (panel mean)**

| stratum | MVS: tasks | MVS: task success [95% CI] | MVS: target score | MVS, with grounding pack: tasks | MVS, with grounding pack: task success [95% CI] | MVS, with grounding pack: target score | API: tasks | API: task success [95% CI] | API: target score |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all clinical tasks | 79 | 0.530 [0.518, 0.540] | 0.698 | 79 | 0.536 [0.523, 0.549] | 0.697 | 79 | 0.576 [0.560, 0.593] | 0.733 |
| without helix / strand context tasks | 69 | 0.531 [0.518, 0.542] | 0.690 | 69 | 0.532 [0.519, 0.546] | 0.687 | 69 | 0.576 [0.560, 0.591] | 0.731 |
| helix / strand context tasks only | 10 | 0.525 [0.474, 0.571] | 0.748 | 10 | 0.560 [0.524, 0.595] | 0.768 | 10 | 0.576 [0.532, 0.626] | 0.741 |
| `needs_offset`: yes | 47 | 0.539 [0.525, 0.552] | 0.698 | 47 | 0.525 [0.509, 0.540] | 0.682 | 47 | 0.572 [0.556, 0.588] | 0.729 |
| `needs_offset`: no | 22 | 0.514 [0.485, 0.534] | 0.675 | 22 | 0.547 [0.526, 0.573] | 0.696 | 22 | 0.584 [0.546, 0.613] | 0.737 |
| `chain_mismatch`: yes | 19 | 0.539 [0.517, 0.558] | 0.696 | 19 | 0.528 [0.495, 0.556] | 0.669 | 19 | 0.586 [0.560, 0.610] | 0.741 |
| `chain_mismatch`: no | 50 | 0.528 [0.511, 0.542] | 0.688 | 50 | 0.534 [0.520, 0.548] | 0.693 | 50 | 0.573 [0.553, 0.591] | 0.728 |
| `number_in_name_as_author_number_is_right`: yes | 34 | 0.527 [0.507, 0.543] | 0.694 | 34 | 0.544 [0.524, 0.563] | 0.695 | 34 | 0.577 [0.554, 0.599] | 0.733 |
| `number_in_name_as_author_number_is_right`: no | 35 | 0.535 [0.517, 0.551] | 0.686 | 35 | 0.521 [0.502, 0.539] | 0.678 | 35 | 0.575 [0.560, 0.592] | 0.730 |
| `name_in_mature_numbering`: yes | 14 | 0.552 [0.530, 0.573] | 0.727 | 14 | 0.516 [0.481, 0.549] | 0.668 | 14 | 0.577 [0.542, 0.607] | 0.731 |
| `name_in_mature_numbering`: no | 55 | 0.526 [0.511, 0.539] | 0.681 | 55 | 0.536 [0.521, 0.552] | 0.691 | 55 | 0.576 [0.560, 0.591] | 0.732 |
| `alphafold_model`: yes | 7 | 0.526 [0.476, 0.546] | 0.695 | 7 | 0.551 [0.530, 0.603] | 0.696 | 7 | 0.596 [0.532, 0.622] | 0.738 |
| `alphafold_model`: no | 62 | 0.531 [0.518, 0.543] | 0.690 | 62 | 0.530 [0.516, 0.543] | 0.685 | 62 | 0.574 [0.558, 0.589] | 0.731 |
| `author_label_numbers_differ`: yes | 24 | 0.534 [0.515, 0.549] | 0.694 | 24 | 0.530 [0.507, 0.554] | 0.691 | 24 | 0.558 [0.525, 0.584] | 0.719 |
| `author_label_numbers_differ`: no | 45 | 0.529 [0.511, 0.544] | 0.689 | 45 | 0.533 [0.518, 0.549] | 0.684 | 45 | 0.586 [0.569, 0.604] | 0.738 |

The helix / strand context tasks need the entry's own secondary-structure annotation, which only the grounding pack states, and are reported apart; the strata below them leave those tasks out. `needs_offset`: the residue's author number differs from its UniProt number (yes: 15 proteins, no: 13, 1 of them on both sides). `number_in_name_as_author_number_is_right`: using the number in the variant name as the author residue number already gives the right residue, so such a task can be solved without any mapping. On the API track the viewer maps UniProt numbering itself. Intervals: bootstrap over structures.
