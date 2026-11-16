> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Bare prompt (output contract only) against the prompt with the reference**

| model | tasks | n | valid output, plain | valid output, with | strict F1, plain | strict F1, with | task success, plain | task success, with | Δ task success [95% CI] | Δ target score |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| deepseek/deepseek-v3.2 | MVS track | 378 | 76.3% | 76.6% | 0.678 | 0.680 | 0.526 | 0.535 | +0.010 [-0.030, +0.048] | -0.002 |
| qwen/qwen3-30b-a3b-instruct-2507 | MVS track | 378 | 76.7% | 77.4% | 0.689 | 0.695 | 0.563 | 0.547 | -0.016 [-0.056, +0.021] | +0.008 |
| claude-haiku-4-5 | MVS track | 378 | 75.9% | 75.3% | 0.676 | 0.676 | 0.539 | 0.532 | -0.007 [-0.051, +0.036] | -0.000 |
| **panel mean** | MVS track | 378 |  |  |  |  |  |  | -0.004 [-0.027, +0.018] |  |

The system prompt without the format reference, MVS track. "Plain" is the headline condition (3 samples per task); "with" has 3 samples per task. Each task's score is its mean over its samples, the same tasks on both sides; intervals: bootstrap over structures of the per-task difference.
