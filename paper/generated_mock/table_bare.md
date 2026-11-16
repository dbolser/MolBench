> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Bare prompt (output contract only) against the prompt with the reference**

| model | tasks | n | valid output, plain | valid output, with | strict F1, plain | strict F1, with | task success, plain | task success, with | Δ task success [95% CI] | Δ target score |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| deepseek/deepseek-v3.2 | MVS track | 381 | 76.6% | 76.9% | 0.680 | 0.682 | 0.531 | 0.535 | +0.003 [-0.039, +0.044] | +0.007 |
| qwen/qwen3-30b-a3b-instruct-2507 | MVS track | 381 | 76.3% | 77.5% | 0.687 | 0.696 | 0.559 | 0.549 | -0.011 [-0.047, +0.028] | +0.011 |
| claude-haiku-4-5 | MVS track | 381 | 75.2% | 75.1% | 0.671 | 0.673 | 0.535 | 0.527 | -0.008 [-0.047, +0.030] | +0.004 |
| **panel mean** | MVS track | 381 |  |  |  |  |  |  | -0.005 [-0.027, +0.016] |  |

The system prompt without the format reference, MVS track. "Plain" is the headline condition (3 samples per task); "with" has 3 samples per task. Each task's score is its mean over its samples, the same tasks on both sides; intervals: bootstrap over structures of the per-task difference.
