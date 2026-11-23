**Grader control set: the grader's own error rate**

| track | grader | controls | identical | equivalent | wrong | false passes | false fails |
|:---|:---|---:|---:|---:|---:|---:|---:|
| MVS | this grader | 1155 | 150 | 500 | 505 | 0 of 505 (0.0%) | 0 of 650 (0.0%) |
| MVS | previous grader | 1155 | 150 | 500 | 505 | 16 of 505 (3.2%) | 284 of 650 (43.7%) |
| API | this grader | 1020 | 150 | 425 | 445 | 0 of 445 (0.0%) | 0 of 575 (0.0%) |
| API | previous grader | 1020 | 150 | 425 | 445 | 95 of 445 (21.3%) | 319 of 575 (55.5%) |

From `tests/controls/summary.json` (built by `scripts/grader_controls.py`; these are measured values, not run results). A false pass is a wrong answer graded as a task success; a false fail is an identical or equivalent answer graded as not a success.
