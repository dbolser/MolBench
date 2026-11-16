**Grader control set: the grader's own error rate**

| track | grader | controls | identical | equivalent | wrong | false passes | false fails |
|:---|:---|---:|---:|---:|---:|---:|---:|
| MVS | this grader | 1110 | 150 | 480 | 480 | 0 of 480 (0.0%) | 0 of 630 (0.0%) |
| MVS | previous grader | 1110 | 150 | 480 | 480 | 13 of 480 (2.7%) | 264 of 630 (41.9%) |
| API | this grader | 995 | 150 | 425 | 420 | 0 of 420 (0.0%) | 0 of 575 (0.0%) |
| API | previous grader | 995 | 150 | 425 | 420 | 75 of 420 (17.9%) | 311 of 575 (54.1%) |

From `tests/controls/summary.json` (built by `scripts/grader_controls.py`; these are measured values, not run results). A false pass is a wrong answer graded as a task success; a false fail is an identical or equivalent answer graded as not a success.
