> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Grounding pack against none, on the lookup tiers**

| model | tasks | n | valid output, plain | valid output, with | strict F1, plain | strict F1, with | task success, plain | task success, with | Δ task success [95% CI] | Δ target score |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | resolve tier | 39 | 76.1% | 79.5% | 0.588 | 0.575 | 0.556 | 0.530 | -0.026 [-0.137, +0.085] | -0.009 |
| moonshotai/kimi-k2.6 | clinical tier | 82 | 80.9% | 76.4% | 0.706 | 0.682 | 0.577 | 0.577 | +0.000 [-0.091, +0.092] | -0.028 |
| openai/gpt-5.4-nano | resolve tier | 39 | 76.9% | 77.8% | 0.571 | 0.549 | 0.547 | 0.530 | -0.017 [-0.145, +0.120] | -0.021 |
| openai/gpt-5.4-nano | clinical tier | 82 | 75.2% | 75.6% | 0.652 | 0.657 | 0.528 | 0.533 | +0.004 [-0.096, +0.094] | +0.006 |
| google/gemma-3-27b-it | resolve tier | 39 | 81.2% | 78.6% | 0.575 | 0.632 | 0.530 | 0.581 | +0.051 [-0.094, +0.188] | +0.060 |
| google/gemma-3-27b-it | clinical tier | 82 | 74.8% | 76.4% | 0.653 | 0.687 | 0.528 | 0.585 | +0.057 [-0.026, +0.138] | +0.026 |
| anthropic/claude-opus-5.5 | resolve tier | 39 | 77.8% | 70.1% | 0.594 | 0.500 | 0.547 | 0.462 | -0.085 [-0.222, +0.060] | -0.098 |
| anthropic/claude-opus-5.5 | clinical tier | 82 | 78.0% | 74.4% | 0.673 | 0.659 | 0.541 | 0.545 | +0.004 [-0.069, +0.080] | -0.008 |
| x-ai/grok-4.7 | resolve tier | 39 | 76.1% | 82.9% | 0.566 | 0.667 | 0.521 | 0.615 | +0.094 [-0.026, +0.222] | +0.098 |
| x-ai/grok-4.7 | clinical tier | 82 | 82.5% | 75.6% | 0.712 | 0.656 | 0.565 | 0.524 | -0.041 [-0.129, +0.040] | -0.061 |
| z-ai/glm-5.2 | resolve tier | 39 | 76.9% | 77.8% | 0.558 | 0.543 | 0.530 | 0.504 | -0.026 [-0.171, +0.137] | -0.013 |
| z-ai/glm-5.2 | clinical tier | 82 | 72.4% | 74.8% | 0.635 | 0.655 | 0.520 | 0.537 | +0.016 [-0.056, +0.081] | +0.020 |
| minimax/minimax-m3 | resolve tier | 39 | 76.1% | 77.8% | 0.643 | 0.573 | 0.607 | 0.538 | -0.068 [-0.171, +0.034] | -0.073 |
| minimax/minimax-m3 | clinical tier | 82 | 79.3% | 78.5% | 0.664 | 0.674 | 0.504 | 0.537 | +0.033 [-0.069, +0.128] | +0.002 |
| nvidia/nemotron-3-super-120b-a12b | resolve tier | 39 | 81.2% | 71.8% | 0.632 | 0.553 | 0.598 | 0.513 | -0.085 [-0.214, +0.043] | -0.081 |
| nvidia/nemotron-3-super-120b-a12b | clinical tier | 82 | 79.3% | 78.5% | 0.685 | 0.677 | 0.549 | 0.545 | -0.004 [-0.077, +0.076] | -0.014 |
| deepseek/deepseek-v3.2 | resolve tier | 39 | 82.1% | 77.8% | 0.639 | 0.598 | 0.590 | 0.547 | -0.043 [-0.179, +0.094] | -0.043 |
| deepseek/deepseek-v3.2 | clinical tier | 82 | 79.3% | 77.2% | 0.678 | 0.658 | 0.528 | 0.520 | -0.008 [-0.086, +0.073] | -0.039 |
| google/gemini-4-argon | resolve tier | 39 | 75.2% | 72.6% | 0.558 | 0.603 | 0.530 | 0.573 | +0.043 [-0.060, +0.154] | +0.051 |
| google/gemini-4-argon | clinical tier | 82 | 75.2% | 77.2% | 0.636 | 0.679 | 0.488 | 0.561 | +0.073 [-0.000, +0.138] | +0.030 |
| deepseek/deepseek-v4-pro-0813 | resolve tier | 39 | 80.3% | 75.2% | 0.571 | 0.585 | 0.530 | 0.564 | +0.034 [-0.068, +0.145] | +0.013 |
| deepseek/deepseek-v4-pro-0813 | clinical tier | 82 | 69.1% | 73.2% | 0.622 | 0.640 | 0.528 | 0.520 | -0.008 [-0.120, +0.113] | +0.022 |
| meta-llama/llama-4-maverick | resolve tier | 39 | 85.5% | 75.2% | 0.675 | 0.632 | 0.607 | 0.607 | +0.000 [-0.128, +0.137] | -0.047 |
| meta-llama/llama-4-maverick | clinical tier | 82 | 75.2% | 81.3% | 0.665 | 0.718 | 0.553 | 0.602 | +0.049 [-0.038, +0.136] | +0.047 |
| openai/gpt-oss-20b | resolve tier | 39 | 82.1% | 70.1% | 0.620 | 0.560 | 0.564 | 0.504 | -0.060 [-0.162, +0.043] | -0.064 |
| openai/gpt-oss-20b | clinical tier | 82 | 72.8% | 72.0% | 0.641 | 0.603 | 0.528 | 0.451 | -0.077 [-0.171, +0.011] | -0.022 |
| qwen/qwen3-30b-a3b-instruct-2507 | resolve tier | 39 | 75.2% | 73.5% | 0.551 | 0.613 | 0.504 | 0.556 | +0.051 [-0.060, +0.171] | +0.068 |
| qwen/qwen3-30b-a3b-instruct-2507 | clinical tier | 82 | 74.8% | 74.8% | 0.655 | 0.665 | 0.537 | 0.557 | +0.020 [-0.069, +0.120] | +0.008 |
| deepseek/deepseek-v4-flash | resolve tier | 39 | 70.9% | 71.8% | 0.506 | 0.598 | 0.479 | 0.547 | +0.068 [-0.043, +0.179] | +0.103 |
| deepseek/deepseek-v4-flash | clinical tier | 82 | 74.0% | 74.8% | 0.640 | 0.647 | 0.516 | 0.520 | +0.004 [-0.070, +0.083] | +0.008 |
| google/gemini-3.5-flash | resolve tier | 39 | 79.5% | 72.6% | 0.600 | 0.560 | 0.530 | 0.513 | -0.017 [-0.137, +0.094] | -0.043 |
| google/gemini-3.5-flash | clinical tier | 82 | 80.9% | 69.1% | 0.698 | 0.619 | 0.565 | 0.533 | -0.033 [-0.116, +0.057] | -0.087 |
| openai/gpt-oss-120b | resolve tier | 39 | 76.9% | 77.8% | 0.609 | 0.613 | 0.573 | 0.573 | -0.000 [-0.137, +0.137] | +0.009 |
| openai/gpt-oss-120b | clinical tier | 82 | 72.0% | 74.8% | 0.614 | 0.645 | 0.480 | 0.508 | +0.028 [-0.067, +0.120] | +0.037 |
| claude-haiku-4-5 | resolve tier | 39 | 82.1% | 76.1% | 0.600 | 0.547 | 0.556 | 0.513 | -0.043 [-0.162, +0.085] | -0.060 |
| claude-haiku-4-5 | clinical tier | 82 | 74.8% | 74.4% | 0.656 | 0.666 | 0.537 | 0.569 | +0.033 [-0.028, +0.109] | -0.002 |
| openai/gpt-6.1-sol | resolve tier | 39 | 82.1% | 78.6% | 0.641 | 0.564 | 0.607 | 0.521 | -0.085 [-0.205, +0.034] | -0.077 |
| openai/gpt-6.1-sol | clinical tier | 82 | 76.8% | 76.0% | 0.667 | 0.687 | 0.537 | 0.598 | +0.061 [-0.056, +0.180] | +0.000 |
| qwen/qwen3-next-80b-a3b-instruct | resolve tier | 39 | 75.2% | 79.5% | 0.624 | 0.611 | 0.607 | 0.581 | -0.026 [-0.137, +0.094] | -0.009 |
| qwen/qwen3-next-80b-a3b-instruct | clinical tier | 82 | 77.6% | 78.0% | 0.707 | 0.693 | 0.614 | 0.577 | -0.037 [-0.119, +0.060] | -0.008 |
| mistralai/mistral-small-2603 | resolve tier | 39 | 75.2% | 70.1% | 0.513 | 0.560 | 0.462 | 0.530 | +0.068 [-0.051, +0.188] | +0.043 |
| mistralai/mistral-small-2603 | clinical tier | 82 | 74.8% | 74.8% | 0.647 | 0.645 | 0.516 | 0.516 | -0.000 [-0.089, +0.089] | -0.006 |
| baseline-rules (keyword baseline) | resolve tier | 39 | 80.3% | 81.2% | 0.588 | 0.611 | 0.573 | 0.556 | -0.017 [-0.154, +0.111] | +0.030 |
| baseline-rules (keyword baseline) | clinical tier | 82 | 73.6% | 76.0% | 0.639 | 0.661 | 0.516 | 0.528 | +0.012 [-0.054, +0.070] | +0.033 |
| **panel mean** | resolve tier | 39 |  |  |  |  |  |  | -0.008 [-0.035, +0.020] |  |
| **panel mean** | clinical tier | 82 |  |  |  |  |  |  | +0.008 [-0.005, +0.023] |  |

The task's frozen grounding pack appended to the request, on the tiers whose answer needs a fact from outside the request. "Plain" is the headline condition (3 samples per task); "with" has 3 samples per task. Each task's score is its mean over its samples, the same tasks on both sides; intervals: bootstrap over structures of the per-task difference.
