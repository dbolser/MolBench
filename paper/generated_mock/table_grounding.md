> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Grounding pack against none, on the lookup tiers**

| model | tasks | n | valid output, plain | valid output, with | strict F1, plain | strict F1, with | task success, plain | task success, with | Δ task success [95% CI] | Δ target score |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | resolve tier | 39 | 76.1% | 79.5% | 0.588 | 0.575 | 0.556 | 0.530 | -0.026 [-0.137, +0.085] | -0.009 |
| moonshotai/kimi-k2.6 | clinical tier | 79 | 79.3% | 75.9% | 0.684 | 0.672 | 0.544 | 0.553 | +0.008 [-0.080, +0.105] | -0.011 |
| nvidia/nemotron-3-super-120b-a12b | resolve tier | 39 | 81.2% | 71.8% | 0.632 | 0.553 | 0.598 | 0.513 | -0.085 [-0.214, +0.043] | -0.081 |
| nvidia/nemotron-3-super-120b-a12b | clinical tier | 79 | 78.1% | 75.5% | 0.690 | 0.663 | 0.578 | 0.544 | -0.034 [-0.126, +0.058] | -0.019 |
| openai/gpt-5.4-nano | resolve tier | 39 | 76.9% | 77.8% | 0.571 | 0.549 | 0.547 | 0.530 | -0.017 [-0.145, +0.120] | -0.021 |
| openai/gpt-5.4-nano | clinical tier | 79 | 76.4% | 77.2% | 0.645 | 0.680 | 0.494 | 0.565 | +0.072 [-0.041, +0.178] | +0.021 |
| z-ai/glm-5.2 | resolve tier | 39 | 76.9% | 77.8% | 0.558 | 0.543 | 0.530 | 0.504 | -0.026 [-0.171, +0.137] | -0.013 |
| z-ai/glm-5.2 | clinical tier | 79 | 75.1% | 77.6% | 0.660 | 0.698 | 0.544 | 0.595 | +0.051 [-0.023, +0.124] | +0.038 |
| deepseek/deepseek-v3.2 | resolve tier | 39 | 82.1% | 77.8% | 0.639 | 0.598 | 0.590 | 0.547 | -0.043 [-0.179, +0.094] | -0.043 |
| deepseek/deepseek-v3.2 | clinical tier | 79 | 76.8% | 75.1% | 0.662 | 0.635 | 0.519 | 0.489 | -0.030 [-0.118, +0.058] | -0.038 |
| google/gemini-4-argon | resolve tier | 39 | 75.2% | 72.6% | 0.558 | 0.603 | 0.530 | 0.573 | +0.043 [-0.060, +0.154] | +0.051 |
| google/gemini-4-argon | clinical tier | 79 | 75.5% | 77.2% | 0.650 | 0.681 | 0.519 | 0.561 | +0.042 [-0.029, +0.114] | +0.036 |
| google/gemma-3-27b-it | resolve tier | 39 | 81.2% | 78.6% | 0.575 | 0.632 | 0.530 | 0.581 | +0.051 [-0.094, +0.188] | +0.060 |
| google/gemma-3-27b-it | clinical tier | 79 | 73.8% | 74.7% | 0.633 | 0.656 | 0.498 | 0.536 | +0.038 [-0.038, +0.135] | +0.021 |
| openai/gpt-oss-120b | resolve tier | 39 | 76.9% | 77.8% | 0.609 | 0.613 | 0.573 | 0.573 | -0.000 [-0.137, +0.137] | +0.009 |
| openai/gpt-oss-120b | clinical tier | 79 | 76.8% | 74.7% | 0.673 | 0.655 | 0.553 | 0.536 | -0.017 [-0.103, +0.066] | -0.015 |
| meta-llama/llama-4-maverick | resolve tier | 39 | 85.5% | 75.2% | 0.675 | 0.632 | 0.607 | 0.607 | +0.000 [-0.128, +0.137] | -0.047 |
| meta-llama/llama-4-maverick | clinical tier | 79 | 75.5% | 79.7% | 0.674 | 0.705 | 0.565 | 0.591 | +0.025 [-0.059, +0.113] | +0.021 |
| qwen/qwen3-30b-a3b-instruct-2507 | resolve tier | 39 | 75.2% | 73.5% | 0.551 | 0.613 | 0.504 | 0.556 | +0.051 [-0.060, +0.171] | +0.068 |
| qwen/qwen3-30b-a3b-instruct-2507 | clinical tier | 79 | 74.7% | 77.2% | 0.645 | 0.688 | 0.515 | 0.582 | +0.068 [-0.008, +0.140] | +0.034 |
| minimax/minimax-m3 | resolve tier | 39 | 76.1% | 77.8% | 0.643 | 0.573 | 0.607 | 0.538 | -0.068 [-0.171, +0.034] | -0.073 |
| minimax/minimax-m3 | clinical tier | 79 | 80.6% | 78.5% | 0.689 | 0.675 | 0.540 | 0.540 | -0.000 [-0.088, +0.084] | -0.025 |
| anthropic/claude-opus-5.5 | resolve tier | 39 | 77.8% | 70.1% | 0.594 | 0.500 | 0.547 | 0.462 | -0.085 [-0.222, +0.060] | -0.098 |
| anthropic/claude-opus-5.5 | clinical tier | 79 | 76.4% | 75.1% | 0.645 | 0.655 | 0.498 | 0.527 | +0.030 [-0.068, +0.125] | +0.015 |
| x-ai/grok-4.7 | resolve tier | 39 | 76.1% | 82.9% | 0.566 | 0.667 | 0.521 | 0.615 | +0.094 [-0.026, +0.222] | +0.098 |
| x-ai/grok-4.7 | clinical tier | 79 | 75.9% | 78.5% | 0.659 | 0.677 | 0.532 | 0.540 | +0.008 [-0.080, +0.103] | +0.019 |
| claude-haiku-4-5 | resolve tier | 39 | 82.1% | 76.1% | 0.600 | 0.547 | 0.556 | 0.513 | -0.043 [-0.162, +0.085] | -0.060 |
| claude-haiku-4-5 | clinical tier | 79 | 75.1% | 73.8% | 0.654 | 0.656 | 0.527 | 0.557 | +0.030 [-0.042, +0.108] | -0.019 |
| openai/gpt-6.1-sol | resolve tier | 39 | 82.1% | 78.6% | 0.641 | 0.564 | 0.607 | 0.521 | -0.085 [-0.205, +0.034] | -0.077 |
| openai/gpt-6.1-sol | clinical tier | 79 | 78.1% | 71.7% | 0.688 | 0.637 | 0.574 | 0.536 | -0.038 [-0.159, +0.101] | -0.053 |
| deepseek/deepseek-v4-pro-0813 | resolve tier | 39 | 80.3% | 75.2% | 0.571 | 0.585 | 0.530 | 0.564 | +0.034 [-0.068, +0.145] | +0.013 |
| deepseek/deepseek-v4-pro-0813 | clinical tier | 79 | 70.9% | 73.4% | 0.640 | 0.636 | 0.549 | 0.506 | -0.042 [-0.140, +0.062] | +0.011 |
| deepseek/deepseek-v4-flash | resolve tier | 39 | 70.9% | 71.8% | 0.506 | 0.598 | 0.479 | 0.547 | +0.068 [-0.043, +0.179] | +0.103 |
| deepseek/deepseek-v4-flash | clinical tier | 79 | 69.6% | 73.8% | 0.596 | 0.619 | 0.473 | 0.473 | -0.000 [-0.072, +0.068] | +0.027 |
| openai/gpt-oss-20b | resolve tier | 39 | 82.1% | 70.1% | 0.620 | 0.560 | 0.564 | 0.504 | -0.060 [-0.162, +0.043] | -0.064 |
| openai/gpt-oss-20b | clinical tier | 79 | 71.3% | 71.3% | 0.602 | 0.616 | 0.456 | 0.485 | +0.030 [-0.041, +0.095] | +0.011 |
| google/gemini-3.5-flash | resolve tier | 39 | 79.5% | 72.6% | 0.600 | 0.560 | 0.530 | 0.513 | -0.017 [-0.137, +0.094] | -0.043 |
| google/gemini-3.5-flash | clinical tier | 79 | 76.4% | 69.2% | 0.661 | 0.605 | 0.536 | 0.489 | -0.046 [-0.155, +0.051] | -0.044 |
| mistralai/mistral-small-2603 | resolve tier | 39 | 75.2% | 70.1% | 0.513 | 0.560 | 0.462 | 0.530 | +0.068 [-0.051, +0.188] | +0.043 |
| mistralai/mistral-small-2603 | clinical tier | 79 | 75.1% | 71.3% | 0.660 | 0.605 | 0.544 | 0.473 | -0.072 [-0.148, +0.005] | -0.057 |
| qwen/qwen3-next-80b-a3b-instruct | resolve tier | 39 | 75.2% | 79.5% | 0.624 | 0.611 | 0.607 | 0.581 | -0.026 [-0.137, +0.094] | -0.009 |
| qwen/qwen3-next-80b-a3b-instruct | clinical tier | 79 | 75.1% | 79.3% | 0.677 | 0.693 | 0.578 | 0.570 | -0.008 [-0.080, +0.082] | +0.013 |
| baseline-rules (keyword baseline) | resolve tier | 39 | 80.3% | 81.2% | 0.588 | 0.611 | 0.573 | 0.556 | -0.017 [-0.154, +0.111] | +0.030 |
| baseline-rules (keyword baseline) | clinical tier | 79 | 77.2% | 76.4% | 0.676 | 0.659 | 0.557 | 0.523 | -0.034 [-0.104, +0.040] | -0.006 |
| **panel mean** | resolve tier | 39 |  |  |  |  |  |  | -0.008 [-0.035, +0.020] |  |
| **panel mean** | clinical tier | 79 |  |  |  |  |  |  | +0.005 [-0.011, +0.024] |  |

The task's frozen grounding pack appended to the request, on the tiers whose answer needs a fact from outside the request. "Plain" is the headline condition (3 samples per task); "with" has 3 samples per task. Each task's score is its mean over its samples, the same tasks on both sides; intervals: bootstrap over structures of the per-task difference.
