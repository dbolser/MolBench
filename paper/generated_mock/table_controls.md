**Grader control set: the grader's own error rate**

| track | grader | controls | identical | equivalent | wrong | false passes | false fails |
|:---|:---|---:|---:|---:|---:|---:|---:|
| MVS | this grader | 1030 | 150 | 440 | 440 | 0 of 440 (0.0%) | 0 of 590 (0.0%) |
| MVS | previous grader | 1030 | 150 | 440 | 440 | 0 of 440 (0.0%) | 222 of 590 (37.6%) |
| API | this grader | 850 | 150 | 360 | 340 | 0 of 340 (0.0%) | 0 of 510 (0.0%) |
| API | previous grader | 850 | 150 | 360 | 340 | 75 of 340 (22.1%) | 247 of 510 (48.4%) |

From `tests/controls/summary.json` (built by `scripts/grader_controls.py`; these are measured values, not run results). A false pass is a wrong answer graded as a task success; a false fail is an identical or equivalent answer graded as not a success.
