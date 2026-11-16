> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Structured output (the provider's JSON mode) against plain output**

| model | tasks | n | valid output, plain | valid output, with | strict F1, plain | strict F1, with | task success, plain | task success, with | Δ task success [95% CI] | Δ target score |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | MVS track | 381 | 77.8% | 76.1% | 0.698 | 0.686 | 0.560 | 0.546 | -0.014 [-0.076, +0.048] | -0.022 |
| moonshotai/kimi-k2.6 | API track | 416 | 76.2% | 76.2% | 0.737 | 0.734 | 0.592 | 0.601 | +0.009 [-0.047, +0.062] | +0.001 |
| openai/gpt-5.4-nano | MVS track | 381 | 77.7% | 78.2% | 0.695 | 0.699 | 0.552 | 0.556 | +0.004 [-0.051, +0.061] | +0.005 |
| openai/gpt-5.4-nano | API track | 416 | 76.9% | 76.2% | 0.739 | 0.748 | 0.587 | 0.603 | +0.016 [-0.038, +0.070] | -0.005 |
| google/gemma-3-27b-it | MVS track | 381 | 76.7% | 76.6% | 0.683 | 0.684 | 0.542 | 0.549 | +0.007 [-0.047, +0.060] | +0.004 |
| google/gemma-3-27b-it | API track | 416 | 77.1% | 75.5% | 0.744 | 0.726 | 0.584 | 0.558 | -0.026 [-0.074, +0.019] | -0.016 |
| anthropic/claude-opus-5.5 | MVS track | 381 | 78.0% | 79.5% | 0.695 | 0.725 | 0.547 | 0.601 | +0.054 [+0.005, +0.103] | +0.030 |
| anthropic/claude-opus-5.5 | API track | 416 | 77.1% | 73.1% | 0.737 | 0.700 | 0.582 | 0.572 | -0.010 [-0.055, +0.033] | -0.026 |
| x-ai/grok-4.7 | MVS track | 381 | 77.1% | 78.2% | 0.689 | 0.696 | 0.549 | 0.541 | -0.008 [-0.066, +0.054] | +0.001 |
| x-ai/grok-4.7 | API track | 416 | 77.0% | 78.4% | 0.735 | 0.741 | 0.589 | 0.589 | -0.000 [-0.055, +0.052] | -0.006 |
| z-ai/glm-5.2 | MVS track | 381 | 74.5% | 78.0% | 0.663 | 0.709 | 0.521 | 0.577 | +0.057 [+0.002, +0.111] | +0.044 |
| z-ai/glm-5.2 | API track | 416 | 79.8% | 79.1% | 0.755 | 0.750 | 0.608 | 0.608 | -0.000 [-0.049, +0.052] | -0.011 |
| minimax/minimax-m3 | MVS track | 381 | 78.0% | 79.8% | 0.698 | 0.719 | 0.547 | 0.575 | +0.028 [-0.032, +0.086] | +0.019 |
| minimax/minimax-m3 | API track | 416 | 76.0% | 75.7% | 0.726 | 0.717 | 0.573 | 0.570 | -0.003 [-0.050, +0.042] | +0.004 |
| nvidia/nemotron-3-super-120b-a12b | MVS track | 381 | 76.8% | 78.2% | 0.690 | 0.711 | 0.560 | 0.575 | +0.015 [-0.050, +0.077] | +0.017 |
| nvidia/nemotron-3-super-120b-a12b | API track | 416 | 76.5% | 74.0% | 0.734 | 0.703 | 0.577 | 0.546 | -0.031 [-0.084, +0.020] | -0.015 |
| deepseek/deepseek-v3.2 | MVS track | 381 | 76.6% | 73.2% | 0.680 | 0.662 | 0.531 | 0.533 | +0.002 [-0.059, +0.067] | -0.033 |
| deepseek/deepseek-v3.2 | API track | 416 | 78.1% | 74.0% | 0.742 | 0.710 | 0.587 | 0.558 | -0.030 [-0.081, +0.019] | -0.025 |
| google/gemini-4-argon | MVS track | 381 | 76.3% | 73.2% | 0.679 | 0.670 | 0.535 | 0.562 | +0.027 [-0.018, +0.071] | -0.016 |
| google/gemini-4-argon | API track | 416 | 76.2% | 70.9% | 0.739 | 0.681 | 0.593 | 0.517 | -0.076 [-0.135, -0.016] | -0.064 |
| deepseek/deepseek-v4-pro-0813 | MVS track | 381 | 75.5% | 76.1% | 0.677 | 0.667 | 0.548 | 0.509 | -0.038 [-0.082, +0.004] | +0.003 |
| deepseek/deepseek-v4-pro-0813 | API track | 416 | 78.0% | 71.9% | 0.742 | 0.691 | 0.598 | 0.546 | -0.052 [-0.108, +0.002] | -0.049 |
| meta-llama/llama-4-maverick | MVS track | 381 | 76.1% | 76.1% | 0.687 | 0.682 | 0.565 | 0.538 | -0.027 [-0.081, +0.026] | -0.012 |
| meta-llama/llama-4-maverick | API track | 416 | 74.7% | 74.3% | 0.722 | 0.731 | 0.578 | 0.577 | -0.001 [-0.051, +0.048] | -0.005 |
| openai/gpt-oss-20b | MVS track | 381 | 74.0% | 74.8% | 0.665 | 0.666 | 0.533 | 0.538 | +0.005 [-0.054, +0.062] | -0.004 |
| openai/gpt-oss-20b | API track | 416 | 77.7% | 75.0% | 0.740 | 0.700 | 0.585 | 0.546 | -0.039 [-0.092, +0.017] | -0.037 |
| qwen/qwen3-30b-a3b-instruct-2507 | MVS track | 381 | 76.3% | 75.1% | 0.687 | 0.683 | 0.559 | 0.570 | +0.010 [-0.046, +0.072] | -0.008 |
| qwen/qwen3-30b-a3b-instruct-2507 | API track | 416 | 75.8% | 77.2% | 0.730 | 0.745 | 0.574 | 0.575 | +0.001 [-0.053, +0.051] | +0.022 |
| deepseek/deepseek-v4-flash | MVS track | 381 | 75.2% | 72.7% | 0.668 | 0.652 | 0.527 | 0.512 | -0.015 [-0.074, +0.039] | -0.013 |
| deepseek/deepseek-v4-flash | API track | 416 | 76.4% | 72.6% | 0.736 | 0.699 | 0.586 | 0.567 | -0.018 [-0.068, +0.030] | -0.039 |
| google/gemini-3.5-flash | MVS track | 381 | 77.0% | 76.6% | 0.689 | 0.681 | 0.554 | 0.541 | -0.013 [-0.064, +0.036] | -0.015 |
| google/gemini-3.5-flash | API track | 416 | 75.6% | 74.0% | 0.726 | 0.713 | 0.576 | 0.555 | -0.021 [-0.076, +0.035] | -0.016 |
| openai/gpt-oss-120b | MVS track | 381 | 75.8% | 78.0% | 0.675 | 0.692 | 0.526 | 0.549 | +0.023 [-0.029, +0.071] | +0.021 |
| openai/gpt-oss-120b | API track | 416 | 76.4% | 77.2% | 0.736 | 0.747 | 0.583 | 0.603 | +0.020 [-0.028, +0.068] | +0.010 |
| openai/gpt-6.1-sol | MVS track | 381 | 76.2% | 75.9% | 0.682 | 0.683 | 0.542 | 0.551 | +0.010 [-0.051, +0.071] | -0.001 |
| openai/gpt-6.1-sol | API track | 416 | 73.5% | 78.1% | 0.716 | 0.753 | 0.571 | 0.587 | +0.015 [-0.033, +0.064] | +0.029 |
| qwen/qwen3-next-80b-a3b-instruct | MVS track | 381 | 75.2% | 75.9% | 0.685 | 0.689 | 0.558 | 0.564 | +0.006 [-0.045, +0.060] | -0.001 |
| qwen/qwen3-next-80b-a3b-instruct | API track | 416 | 74.3% | 75.5% | 0.713 | 0.731 | 0.558 | 0.579 | +0.021 [-0.040, +0.087] | +0.017 |
| mistralai/mistral-small-2603 | MVS track | 381 | 74.3% | 78.5% | 0.658 | 0.708 | 0.523 | 0.551 | +0.028 [-0.038, +0.097] | +0.055 |
| mistralai/mistral-small-2603 | API track | 416 | 77.2% | 76.2% | 0.741 | 0.743 | 0.591 | 0.613 | +0.022 [-0.031, +0.073] | +0.005 |
| **panel mean** | MVS track | 381 |  |  |  |  |  |  | +0.008 [-0.002, +0.018] |  |
| **panel mean** | API track | 416 |  |  |  |  |  |  | -0.010 [-0.021, +0.001] |  |

The same prompt with JSON mode switched on, for every model whose route has it. "Plain" is the headline condition (3 samples per task); "with" has 1 sample per task. Each task's score is its mean over its samples, the same tasks on both sides; intervals: bootstrap over structures of the per-task difference.
