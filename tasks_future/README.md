# Tasks kept for future work (not part of the benchmark)

Nothing under `tasks_future/` is loaded, run or graded: the task loader reads `tasks/`
only.

## `visual_rubric/` (Component 2: open-ended requests judged against a rubric)

Two hand-written requests (`vis-101`, `vis-102`) whose answer is not one determined
scene but anything that meets a list of rubric points, to be judged from a render by a
vision model. FINAL_PLAN decision 8 puts this component out of the first paper: every
task of the final corpus has a reference built by script and is graded on what the
viewer would draw, and these two have neither (their `reference_hint` was written by
hand and never checked against the structure). They are kept, unchanged and in the old
file format, as the seed of that future component. Before they could come back they
would need rubric points derived from the structure by script, and a judge validated
against human raters.
