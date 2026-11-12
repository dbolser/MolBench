**Prompting conditions (PRELIMINARY).** `spec`: the system prompt contains the frozen MolViewSpec reference. `bare`: it contains only the output contract ("answer with one MolViewSpec JSON scene"). `_grounded`: the task's frozen grounding pack (facts about the structure, built offline) is added to the request. Each row is a mean over the models that ran that condition; the number of models differs by row and is stated. *Strict F1*, *Valid* and *F1 (valid)* as in the leaderboard table.

| Condition | Models | Valid / all | Strict F1 | Valid | F1 (valid) |
| :--- | ---: | ---: | ---: | ---: | ---: |
| `bare` | 3 | 0/210 | 0.000 | 0.0% | n/a (no valid output) |
| `bare_grounded` | 3 | 0/210 | 0.000 | 0.0% | n/a (no valid output) |
| `spec` | 15 | 784/1050 | 0.675 | 74.7% | 0.904 |
| `spec_grounded` | 15 | 739/1050 | 0.634 | 70.4% | 0.898 |
