> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Accept-set tier: which reading the right answers took**

| track | template | tasks | readings accepted | task success | right samples | of those, on the first-listed reading | readings ever chosen |
|:---|:---|---:|---:|---:|---:|---:|---:|
| MVS | `acc-chain-colours` | 3 | 10 | 0.529 | 100 | 36.0% | 10 of 10 |
| MVS | `acc-ligand-colours` | 3 | 6 | 0.471 | 89 | 50.6% | 6 of 6 |
| MVS | `acc-ligand-copy` | 3 | 9 | 0.466 | 88 | 37.5% | 9 of 9 |
| MVS | `acc-ligand-which` | 3 | 12 | 0.561 | 106 | 23.6% | 12 of 12 |
| MVS | `acc-metal-copy` | 3 | 14 | 0.566 | 107 | 26.2% | 14 of 14 |
| MVS | `acc-metal-which` | 2 | 6 | 0.524 | 66 | 36.4% | 6 of 6 |
| MVS | `acc-representation-open` | 3 | 12 | 0.582 | 110 | 22.7% | 12 of 12 |
| MVS | `acc-residue-colour` | 3 | 9 | 0.556 | 105 | 23.8% | 9 of 9 |
| MVS | `acc-residue-copy` | 3 | 9 | 0.587 | 111 | 34.2% | 9 of 9 |
| API | `acc-chain-colours` | 3 | 10 | 0.550 | 104 | 44.2% | 10 of 10 |
| API | `acc-ligand-colours` | 3 | 6 | 0.667 | 126 | 55.6% | 6 of 6 |
| API | `acc-ligand-copy` | 3 | 9 | 0.587 | 111 | 38.7% | 9 of 9 |
| API | `acc-ligand-which` | 3 | 9 | 0.640 | 121 | 39.7% | 9 of 9 |
| API | `acc-residue-colour` | 3 | 9 | 0.608 | 115 | 35.7% | 9 of 9 |

An accept-set request leaves one countable thing open (which of two copies, which chain gets which colour) and every reading is accepted. Readings are counted, not the call forms a reading can be written in on the API track. Pooled over the panel's models, headline condition. The first-listed reading is the one the reference draws; a share near 1 / (readings per task) would mean no preferred reading.
