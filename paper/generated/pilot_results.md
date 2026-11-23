> **PILOT.** A provider-path pilot on a few tasks, not the benchmark run: these numbers show that the path works, not how good a model is.

**Provider-path pilot: claude-haiku-4-5, 39 tasks, 1 sample per task, 46 calls, US $0.21**

| Condition and track | Tasks | Valid outputs | F1 (strict) | Task success (strict) | Target score (strict) | Cost (USD) |
|:---|---:|---:|---:|---:|---:|---:|
| Format reference, scene track | 21 | 100.0% | 0.891 | 0.667 (14 of 21) | 0.658 | 0.10 |
| Format reference, call-list track | 18 | 100.0% | 0.556 | 0.333 (6 of 18) | 0.430 | 0.08 |
| Format reference + grounding pack, scene track | 7 | 85.7% | 0.857 | 0.857 (6 of 7) | 0.857 | 0.03 |

Run of 2026-11-16 on the direct provider route; the archived answers were graded on 2026-11-23 with the grader and corpus as they stood after the faults the pilot showed were fixed (`PILOT.md`). The tasks were picked by rule to cover every tier, track and kind of task, including the paraphrases of one request; they are not a sample of the corpus, and one answer per task says nothing about the spread between answers. *Valid outputs*: answers that parse and that the viewer accepts. *Strict*: an invalid answer counts as 0. The grounding pack states the residue a variant maps to, so that row is an upper bound.
