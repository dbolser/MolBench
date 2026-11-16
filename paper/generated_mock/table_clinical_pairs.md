> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Clinical tier: the same variant on two structures (panel mean task success)**

| track | gene | variant | structure A | A needs offset | A success | structure B | B needs offset | B success |
|:---|:---|:---|:---|:---|---:|:---|:---|---:|
| API | HBB | E7V | AF-P68871-F1-MODEL_V6 | no | 0.651 | 1HHO | yes | 0.635 |
| MVS | HBB | E7V | AF-P68871-F1-MODEL_V6 | no | 0.571 | 1HHO | yes | 0.571 |
| API | CRYGD | R37P | AF-P07320-F1-MODEL_V6 | no | 0.603 | 1HK0 | yes | 0.619 |
| MVS | CRYGD | R37P | AF-P07320-F1-MODEL_V6 | no | 0.556 | 1HK0 | yes | 0.508 |
| API | HBB | R31T | AF-P68871-F1-MODEL_V6 | no | 0.603 | 1HHO | yes | 0.619 |
| MVS | HBB | R31T | AF-P68871-F1-MODEL_V6 | no | 0.429 | 1HHO | yes | 0.603 |
| API | HBB | Y146N | AF-P68871-F1-MODEL_V6 | no | 0.540 | 2HHB | yes | 0.556 |
| MVS | HBB | Y146N | AF-P68871-F1-MODEL_V6 | no | 0.460 | 2HHB | yes | 0.571 |
| API | TP53 | D281G | 1TUP | no | 0.508 | AF-P04637-F1-MODEL_V6 | no | 0.556 |
| MVS | TP53 | D281G | 1TUP | no | 0.571 | AF-P04637-F1-MODEL_V6 | no | 0.508 |
| API | CALM1 | F142L | AF-P0DP23-F1-MODEL_V6 | no | 0.651 | 6M7H | yes | 0.603 |
| MVS | CALM1 | F142L | AF-P0DP23-F1-MODEL_V6 | no | 0.556 | 6M7H | yes | 0.587 |
| API | HBB | K67T | AF-P68871-F1-MODEL_V6 | no | 0.667 | 1HHO | yes | 0.635 |
| MVS | HBB | K67T | AF-P68871-F1-MODEL_V6 | no | 0.508 | 1HHO | yes | 0.619 |
| API | HBB | H98Q | AF-P68871-F1-MODEL_V6 | no | 0.603 | 2HHB | yes | 0.540 |
| MVS | HBB | H98Q | AF-P68871-F1-MODEL_V6 | no | 0.603 | 2HHB | yes | 0.492 |
| API | LYZ | W82R | AF-P61626-F1-MODEL_V6 | no | 0.603 | 2NWD | yes | 0.635 |
| MVS | LYZ | W82R | AF-P61626-F1-MODEL_V6 | no | 0.603 | 2NWD | yes | 0.556 |
| API | TP53 | R248Q | 1TUP | no | 0.587 | AF-P04637-F1-MODEL_V6 | no | 0.444 |
| MVS | TP53 | R248Q | 1TUP | no | 0.635 | AF-P04637-F1-MODEL_V6 | no | 0.508 |

Each row is one request asked twice, on two structures of the same protein (CALM1, CRYGD, HBB, LYZ, TP53). Where the two differ only in whether the author numbering equals the UniProt numbering, the gap is the cost of the offset.
