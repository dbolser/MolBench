> **PROVIDER PILOT.** A trial of the path to a provider on a few tasks, not the benchmark run: these numbers show that the path works, not how good a model is.

**Provider pilot: claude-haiku-4-5, 39 tasks, 1 sample per task, 46 calls, US $0.21**

| Condition and track | Tasks | Valid answers | Task success rate, strict | Target score, strict | F1, strict | Cost (USD) |
|:---|---:|---:|---:|---:|---:|---:|
| Main, scene track | 21 | 100.0% | 0.667 (14 of 21) | 0.658 | 0.891 | 0.10 |
| Main, call-list track | 18 | 100.0% | 0.333 (6 of 18) | 0.430 | 0.556 | 0.08 |
| Main + grounding pack, scene track | 7 | 85.7% | 0.857 (6 of 7) | 0.857 | 0.857 | 0.03 |

Run of 2026-11-16 on the provider's own service; the archived answers were graded on 2026-11-23 with the grader and corpus as they stood after the faults the pilot showed were fixed (`PILOT.md` in the repository). The tasks were picked by rule to cover every category, track and kind of task, including the three wordings of one request; they are not a sample of the corpus, and one answer per task says nothing about the spread between answers. *Valid answers*: answers that parse and that the viewer accepts. *Strict*: every answer counts, and an unshowable answer scores 0. The grounding pack states the residue that a variant maps to, so that row is an upper bound.
