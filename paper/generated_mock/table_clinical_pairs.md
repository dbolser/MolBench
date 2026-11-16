> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Clinical tier: the same variant on two structures (panel mean task success)**

| track | gene | variant | structure A | A needs offset | A success | structure B | B needs offset | B success |
|:---|:---|:---|:---|:---|---:|:---|:---|---:|
| API | HBB | E7V | AF-P68871-F1-MODEL_V6 | no | 0.651 | 1HHO | yes | 0.635 |
| MVS | HBB | E7V | AF-P68871-F1-MODEL_V6 | no | 0.571 | 1HHO | yes | 0.571 |
| API | HBB | Y146C | AF-P68871-F1-MODEL_V6 | no | 0.540 | 2HHB | yes | 0.651 |
| MVS | HBB | Y146C | AF-P68871-F1-MODEL_V6 | no | 0.476 | 2HHB | yes | 0.571 |
| API | HBB | F43S | AF-P68871-F1-MODEL_V6 | no | 0.651 | 5NI1 | yes | 0.587 |
| MVS | HBB | F43S | AF-P68871-F1-MODEL_V6 | no | 0.571 | 5NI1 | yes | 0.492 |
| API | TP53 | D281A | 1TUP | no | 0.635 | AF-P04637-F1-MODEL_V6 | no | 0.619 |
| MVS | TP53 | D281A | 1TUP | no | 0.540 | AF-P04637-F1-MODEL_V6 | no | 0.444 |
| API | HBB | K67T | AF-P68871-F1-MODEL_V6 | no | 0.667 | 1HHO | yes | 0.635 |
| MVS | HBB | K67T | AF-P68871-F1-MODEL_V6 | no | 0.508 | 1HHO | yes | 0.619 |
| API | HBB | H98Q | AF-P68871-F1-MODEL_V6 | no | 0.603 | 2HHB | yes | 0.540 |
| MVS | HBB | H98Q | AF-P68871-F1-MODEL_V6 | no | 0.603 | 2HHB | yes | 0.492 |
| API | TP53 | R248Q | 1TUP | no | 0.587 | AF-P04637-F1-MODEL_V6 | no | 0.444 |
| MVS | TP53 | R248Q | 1TUP | no | 0.635 | AF-P04637-F1-MODEL_V6 | no | 0.508 |

Each row is one request asked twice, on two structures of the same protein (HBB, TP53). Where the two differ only in whether the author numbering equals the UniProt numbering, the gap is the cost of the offset.
