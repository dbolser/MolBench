> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Structured output (the provider's JSON mode) against plain output**

| model | tasks | n | valid output, plain | valid output, with | strict F1, plain | strict F1, with | task success, plain | task success, with | Δ task success [95% CI] | Δ target score |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | MVS track | 378 | 77.8% | 75.4% | 0.698 | 0.680 | 0.561 | 0.545 | -0.016 [-0.073, +0.044] | -0.025 |
| moonshotai/kimi-k2.6 | API track | 403 | 76.0% | 75.9% | 0.741 | 0.726 | 0.595 | 0.598 | +0.003 [-0.051, +0.057] | -0.014 |
| nvidia/nemotron-3-super-120b-a12b | MVS track | 378 | 76.8% | 79.6% | 0.693 | 0.715 | 0.570 | 0.566 | -0.004 [-0.072, +0.061] | +0.031 |
| nvidia/nemotron-3-super-120b-a12b | API track | 403 | 78.0% | 73.2% | 0.740 | 0.698 | 0.573 | 0.553 | -0.020 [-0.076, +0.034] | -0.037 |
| openai/gpt-5.4-nano | MVS track | 378 | 77.7% | 79.1% | 0.691 | 0.702 | 0.543 | 0.550 | +0.007 [-0.050, +0.070] | +0.014 |
| openai/gpt-5.4-nano | API track | 403 | 76.8% | 76.2% | 0.738 | 0.761 | 0.582 | 0.610 | +0.028 [-0.023, +0.080] | +0.011 |
| z-ai/glm-5.2 | MVS track | 378 | 75.7% | 78.8% | 0.674 | 0.715 | 0.531 | 0.579 | +0.048 [-0.001, +0.099] | +0.039 |
| z-ai/glm-5.2 | API track | 403 | 78.9% | 78.2% | 0.749 | 0.737 | 0.604 | 0.573 | -0.031 [-0.084, +0.023] | -0.008 |
| deepseek/deepseek-v3.2 | MVS track | 378 | 76.3% | 75.1% | 0.678 | 0.683 | 0.526 | 0.548 | +0.022 [-0.032, +0.079] | -0.011 |
| deepseek/deepseek-v3.2 | API track | 403 | 78.2% | 76.4% | 0.748 | 0.726 | 0.596 | 0.556 | -0.040 [-0.096, +0.012] | -0.021 |
| google/gemini-4-argon | MVS track | 378 | 77.0% | 73.8% | 0.686 | 0.673 | 0.542 | 0.556 | +0.013 [-0.031, +0.054] | -0.017 |
| google/gemini-4-argon | API track | 403 | 75.8% | 71.5% | 0.734 | 0.670 | 0.586 | 0.501 | -0.085 [-0.145, -0.026] | -0.071 |
| google/gemma-3-27b-it | MVS track | 378 | 77.2% | 75.7% | 0.684 | 0.674 | 0.538 | 0.542 | +0.004 [-0.049, +0.061] | -0.010 |
| google/gemma-3-27b-it | API track | 403 | 75.8% | 75.9% | 0.736 | 0.736 | 0.581 | 0.573 | -0.008 [-0.060, +0.047] | +0.003 |
| openai/gpt-oss-120b | MVS track | 378 | 76.7% | 79.9% | 0.689 | 0.713 | 0.546 | 0.569 | +0.023 [-0.031, +0.072] | +0.024 |
| openai/gpt-oss-120b | API track | 403 | 76.9% | 78.2% | 0.735 | 0.745 | 0.593 | 0.596 | +0.002 [-0.050, +0.054] | +0.012 |
| meta-llama/llama-4-maverick | MVS track | 378 | 75.9% | 77.2% | 0.686 | 0.700 | 0.564 | 0.556 | -0.009 [-0.077, +0.050] | +0.009 |
| meta-llama/llama-4-maverick | API track | 403 | 75.8% | 73.4% | 0.727 | 0.712 | 0.576 | 0.558 | -0.017 [-0.068, +0.034] | -0.025 |
| qwen/qwen3-30b-a3b-instruct-2507 | MVS track | 378 | 76.7% | 74.1% | 0.689 | 0.668 | 0.563 | 0.550 | -0.012 [-0.069, +0.045] | -0.025 |
| qwen/qwen3-30b-a3b-instruct-2507 | API track | 403 | 75.1% | 80.4% | 0.725 | 0.762 | 0.572 | 0.600 | +0.028 [-0.033, +0.091] | +0.044 |
| minimax/minimax-m3 | MVS track | 378 | 77.1% | 79.6% | 0.694 | 0.718 | 0.547 | 0.574 | +0.027 [-0.032, +0.084] | +0.022 |
| minimax/minimax-m3 | API track | 403 | 75.7% | 75.9% | 0.725 | 0.710 | 0.571 | 0.566 | -0.005 [-0.056, +0.044] | -0.008 |
| anthropic/claude-opus-5.5 | MVS track | 378 | 77.0% | 78.6% | 0.681 | 0.713 | 0.531 | 0.587 | +0.056 [+0.006, +0.109] | +0.030 |
| anthropic/claude-opus-5.5 | API track | 403 | 76.9% | 73.2% | 0.730 | 0.706 | 0.561 | 0.571 | +0.010 [-0.036, +0.055] | -0.018 |
| x-ai/grok-4.7 | MVS track | 378 | 75.0% | 79.4% | 0.673 | 0.710 | 0.534 | 0.561 | +0.026 [-0.032, +0.086] | +0.034 |
| x-ai/grok-4.7 | API track | 403 | 76.9% | 78.7% | 0.730 | 0.744 | 0.587 | 0.591 | +0.003 [-0.052, +0.056] | +0.006 |
| openai/gpt-6.1-sol | MVS track | 378 | 76.2% | 76.7% | 0.684 | 0.691 | 0.549 | 0.563 | +0.014 [-0.048, +0.079] | +0.006 |
| openai/gpt-6.1-sol | API track | 403 | 74.9% | 76.9% | 0.720 | 0.741 | 0.567 | 0.576 | +0.008 [-0.041, +0.057] | +0.012 |
| deepseek/deepseek-v4-pro-0813 | MVS track | 378 | 75.1% | 76.2% | 0.673 | 0.673 | 0.544 | 0.521 | -0.023 [-0.066, +0.020] | +0.007 |
| deepseek/deepseek-v4-pro-0813 | API track | 403 | 76.8% | 72.2% | 0.730 | 0.687 | 0.588 | 0.541 | -0.047 [-0.105, +0.012] | -0.044 |
| deepseek/deepseek-v4-flash | MVS track | 378 | 74.1% | 73.8% | 0.655 | 0.661 | 0.511 | 0.519 | +0.007 [-0.047, +0.061] | +0.010 |
| deepseek/deepseek-v4-flash | API track | 403 | 75.6% | 73.7% | 0.734 | 0.711 | 0.587 | 0.571 | -0.017 [-0.073, +0.038] | -0.024 |
| openai/gpt-oss-20b | MVS track | 378 | 74.3% | 75.4% | 0.661 | 0.670 | 0.519 | 0.540 | +0.021 [-0.044, +0.080] | +0.007 |
| openai/gpt-oss-20b | API track | 403 | 75.6% | 77.4% | 0.723 | 0.726 | 0.572 | 0.586 | +0.014 [-0.038, +0.069] | +0.003 |
| google/gemini-3.5-flash | MVS track | 378 | 75.3% | 75.9% | 0.673 | 0.681 | 0.539 | 0.556 | +0.017 [-0.039, +0.066] | +0.009 |
| google/gemini-3.5-flash | API track | 403 | 76.1% | 72.0% | 0.727 | 0.697 | 0.571 | 0.546 | -0.025 [-0.079, +0.038] | -0.030 |
| mistralai/mistral-small-2603 | MVS track | 378 | 74.5% | 77.5% | 0.663 | 0.691 | 0.530 | 0.513 | -0.017 [-0.081, +0.051] | +0.034 |
| mistralai/mistral-small-2603 | API track | 403 | 75.6% | 76.7% | 0.730 | 0.747 | 0.577 | 0.610 | +0.034 [-0.018, +0.085] | +0.022 |
| qwen/qwen3-next-80b-a3b-instruct | MVS track | 378 | 74.4% | 74.9% | 0.675 | 0.682 | 0.546 | 0.556 | +0.010 [-0.046, +0.063] | +0.006 |
| qwen/qwen3-next-80b-a3b-instruct | API track | 403 | 74.1% | 76.7% | 0.711 | 0.735 | 0.557 | 0.576 | +0.018 [-0.044, +0.080] | +0.027 |
| **panel mean** | MVS track | 378 |  |  |  |  |  |  | +0.011 [-0.001, +0.022] |  |
| **panel mean** | API track | 403 |  |  |  |  |  |  | -0.007 [-0.020, +0.005] |  |

The same prompt with JSON mode switched on, for every model whose route has it. "Plain" is the headline condition (3 samples per task); "with" has 1 sample per task. Each task's score is its mean over its samples, the same tasks on both sides; intervals: bootstrap over structures of the per-task difference.
