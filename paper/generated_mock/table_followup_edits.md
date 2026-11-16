> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Follow-up turns by kind of edit (panel mean)**

| edit | MVS tasks | MVS success | MVS target | MVS preserved | API tasks | API success | API target | API preserved |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| add a component (a chain), keeping the rest | 2 | 0.556 | 0.770 | 0.663 | – | – | – | – |
| add a component (a residue), keeping the rest | 4 | 0.556 | 0.738 | 0.692 | 4 | 0.563 | 0.774 | 0.726 |
| add a component (the ligand), keeping the rest | 2 | 0.548 | 0.825 | 0.687 | – | – | – | – |
| also: a label | 2 | 0.540 | 0.794 | 0.667 | – | – | – | – |
| also: a scene setting | 2 | 0.571 | 0.737 | 0.720 | 2 | 0.587 | 0.748 | 0.737 |
| also: camera focus | 2 | 0.516 | 0.730 | 0.623 | 2 | 0.563 | 0.849 | 0.706 |
| also: colour a second component | 2 | 0.508 | 0.722 | 0.615 | 2 | 0.627 | 0.825 | 0.726 |
| change a representation | 4 | 0.500 | 0.685 | 0.696 | – | – | – | – |
| change one property of an existing component (opacity) | 2 | 0.579 | 0.683 | 0.786 | – | – | – | – |
| change the representation (order-sensitive on this track) | – | – | – | – | 2 | 0.540 | 0.767 | – |
| ellipsis: colour the component not yet coloured | 2 | 0.548 | 0.722 | 0.635 | 2 | 0.563 | 0.794 | 0.679 |
| narrow to one component | 2 | 0.556 | 0.647 | 0.647 | – | – | – | – |
| no change: a question | 2 | 0.492 | 0.671 | 0.671 | 2 | 0.556 | 0.710 | 0.729 |
| no change: already true | 6 | 0.484 | 0.703 | 0.679 | 6 | 0.537 | 0.730 | 0.714 |
| no change: the format cannot express the request | 2 | 0.587 | 0.748 | 0.748 | – | – | – | – |
| pronoun: change a representation | 1 | 0.492 | 0.651 | – | – | – | – | – |
| pronoun: recolour | 2 | 0.524 | 0.643 | – | – | – | – | – |
| recolour a component named by its current colour | 3 | 0.492 | 0.799 | 0.646 | 3 | 0.566 | 0.762 | 0.677 |
| recolour by reference to the scene | 4 | 0.595 | 0.789 | 0.702 | 4 | 0.540 | 0.733 | 0.631 |
| recolour one existing component | 5 | 0.584 | 0.787 | 0.686 | 5 | 0.584 | 0.806 | 0.702 |
| remove / hide something | 5 | 0.543 | 0.637 | 0.637 | 2 | 0.508 | 0.678 | 0.627 |
| undo earlier choices (all colouring) | – | – | – | – | 1 | 0.603 | 0.603 | 0.603 |
| undo one earlier choice | – | – | – | – | 2 | 0.524 | 0.730 | 0.730 |
| undo one earlier choice (a hidden component) | – | – | – | – | 2 | 0.627 | 0.786 | 0.786 |
| undo one earlier choice (a setting) | – | – | – | – | 1 | 0.571 | 0.786 | 0.786 |
| undo-like recolour | 2 | 0.524 | 0.730 | 0.627 | 2 | 0.540 | 0.754 | 0.647 |

"–" in a score column: no task of that kind has such a part (an edit that removes something has no target on the MVS track; an edit that touches everything has nothing to preserve).
