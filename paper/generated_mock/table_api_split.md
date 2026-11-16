> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**API track: public and held-back tasks (task success)**

| model | public tasks | public | held-back tasks | held back | held back − public [95% CI] |
|:---|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 316 | 0.605 | 87 | 0.556 | -0.050 [-0.117, +0.020] |
| nvidia/nemotron-3-super-120b-a12b | 316 | 0.579 | 87 | 0.552 | -0.027 [-0.093, +0.037] |
| openai/gpt-5.4-nano | 316 | 0.583 | 87 | 0.579 | -0.005 [-0.065, +0.054] |
| z-ai/glm-5.2 | 316 | 0.614 | 87 | 0.567 | -0.047 [-0.087, -0.008] |
| deepseek/deepseek-v3.2 | 316 | 0.605 | 87 | 0.559 | -0.046 [-0.100, +0.019] |
| google/gemini-4-argon | 316 | 0.575 | 87 | 0.628 | +0.053 [-0.003, +0.117] |
| google/gemma-3-27b-it | 316 | 0.590 | 87 | 0.552 | -0.038 [-0.103, +0.027] |
| openai/gpt-oss-120b | 316 | 0.590 | 87 | 0.605 | +0.016 [-0.040, +0.076] |
| meta-llama/llama-4-maverick | 316 | 0.566 | 87 | 0.609 | +0.043 [-0.018, +0.111] |
| qwen/qwen3-30b-a3b-instruct-2507 | 316 | 0.572 | 87 | 0.575 | +0.003 [-0.051, +0.059] |
| minimax/minimax-m3 | 316 | 0.565 | 87 | 0.590 | +0.025 [-0.025, +0.079] |
| anthropic/claude-opus-5.5 | 316 | 0.563 | 87 | 0.552 | -0.012 [-0.078, +0.055] |
| x-ai/grok-4.7 | 316 | 0.582 | 87 | 0.605 | +0.023 [-0.039, +0.084] |
| claude-haiku-4-5 | 316 | 0.580 | 87 | 0.594 | +0.014 [-0.049, +0.070] |
| openai/gpt-6.1-sol | 316 | 0.568 | 87 | 0.567 | -0.000 [-0.068, +0.068] |
| deepseek/deepseek-v4-pro-0813 | 316 | 0.580 | 87 | 0.617 | +0.037 [-0.019, +0.096] |
| deepseek/deepseek-v4-flash | 316 | 0.584 | 87 | 0.598 | +0.013 [-0.059, +0.092] |
| openai/gpt-oss-20b | 316 | 0.572 | 87 | 0.571 | -0.001 [-0.067, +0.066] |
| google/gemini-3.5-flash | 316 | 0.566 | 87 | 0.586 | +0.020 [-0.060, +0.095] |
| mistralai/mistral-small-2603 | 316 | 0.571 | 87 | 0.598 | +0.027 [-0.026, +0.081] |
| qwen/qwen3-next-80b-a3b-instruct | 316 | 0.547 | 87 | 0.594 | +0.046 [-0.036, +0.117] |
| baseline-rules (keyword baseline) | 316 | 0.588 | 87 | 0.590 | +0.002 [-0.051, +0.054] |
| **panel mean** | 316 | 0.579 | 87 | 0.583 | +0.004 [-0.010, +0.017] |
| panel, translation tier | 127 | 0.576 | 36 | 0.598 | +0.022 [+0.001, +0.045] |
| panel, grounded tier | 56 | 0.582 | 12 | 0.586 | +0.003 [-0.047, +0.062] |
| panel, clinical tier | 59 | 0.578 | 20 | 0.571 | -0.008 [-0.042, +0.030] |
| panel, follow-up tier | 34 | 0.569 | 10 | 0.537 | -0.032 [-0.065, +0.004] |
| panel, accept-set tier | 11 | 0.612 | 4 | 0.607 | -0.005 [-0.062, +0.048] |
| panel, tool-only tier | 29 | 0.589 | 5 | 0.600 | +0.011 [-0.058, +0.078] |

Held-back tasks come from the same generators on structures no public task uses and were not published before the run. The two splits share no structure, so each side of the difference is resampled on its own.
