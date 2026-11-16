> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**API track: public and held-back tasks (task success)**

| model | public tasks | public | held-back tasks | held back | held back − public [95% CI] |
|:---|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 327 | 0.594 | 89 | 0.584 | -0.010 [-0.073, +0.057] |
| openai/gpt-5.4-nano | 327 | 0.585 | 89 | 0.596 | +0.010 [-0.066, +0.085] |
| google/gemma-3-27b-it | 327 | 0.586 | 89 | 0.577 | -0.009 [-0.062, +0.042] |
| anthropic/claude-opus-5.5 | 327 | 0.576 | 89 | 0.603 | +0.027 [-0.046, +0.095] |
| x-ai/grok-4.7 | 327 | 0.587 | 89 | 0.596 | +0.008 [-0.063, +0.078] |
| z-ai/glm-5.2 | 327 | 0.621 | 89 | 0.562 | -0.059 [-0.112, -0.006] |
| minimax/minimax-m3 | 327 | 0.566 | 89 | 0.599 | +0.033 [-0.015, +0.089] |
| nvidia/nemotron-3-super-120b-a12b | 327 | 0.581 | 89 | 0.562 | -0.019 [-0.085, +0.043] |
| deepseek/deepseek-v3.2 | 327 | 0.595 | 89 | 0.558 | -0.037 [-0.096, +0.036] |
| google/gemini-4-argon | 327 | 0.584 | 89 | 0.625 | +0.041 [-0.034, +0.116] |
| deepseek/deepseek-v4-pro-0813 | 327 | 0.592 | 89 | 0.618 | +0.026 [-0.033, +0.089] |
| meta-llama/llama-4-maverick | 327 | 0.580 | 89 | 0.569 | -0.011 [-0.071, +0.063] |
| openai/gpt-oss-20b | 327 | 0.589 | 89 | 0.569 | -0.020 [-0.089, +0.053] |
| qwen/qwen3-30b-a3b-instruct-2507 | 327 | 0.572 | 89 | 0.581 | +0.009 [-0.040, +0.060] |
| deepseek/deepseek-v4-flash | 327 | 0.580 | 89 | 0.607 | +0.027 [-0.031, +0.087] |
| google/gemini-3.5-flash | 327 | 0.568 | 89 | 0.607 | +0.039 [-0.022, +0.093] |
| openai/gpt-oss-120b | 327 | 0.580 | 89 | 0.596 | +0.015 [-0.050, +0.083] |
| claude-haiku-4-5 | 327 | 0.583 | 89 | 0.581 | -0.003 [-0.072, +0.064] |
| openai/gpt-6.1-sol | 327 | 0.574 | 89 | 0.562 | -0.012 [-0.080, +0.058] |
| qwen/qwen3-next-80b-a3b-instruct | 327 | 0.549 | 89 | 0.592 | +0.042 [-0.041, +0.119] |
| mistralai/mistral-small-2603 | 327 | 0.578 | 89 | 0.637 | +0.059 [-0.015, +0.124] |
| baseline-rules (keyword baseline) | 327 | 0.584 | 89 | 0.640 | +0.056 [-0.001, +0.113] |
| **panel mean** | 327 | 0.582 | 89 | 0.589 | +0.007 [-0.007, +0.021] |
| panel, translation tier | 138 | 0.577 | 40 | 0.598 | +0.020 [-0.003, +0.044] |
| panel, grounded tier | 52 | 0.584 | 11 | 0.590 | +0.007 [-0.047, +0.064] |
| panel, clinical tier | 63 | 0.582 | 19 | 0.590 | +0.008 [-0.012, +0.030] |
| panel, follow-up tier | 34 | 0.577 | 10 | 0.543 | -0.034 [-0.068, +0.005] |
| panel, accept-set tier | 11 | 0.612 | 4 | 0.607 | -0.005 [-0.062, +0.048] |
| panel, tool-only tier | 29 | 0.597 | 5 | 0.600 | +0.003 [-0.063, +0.069] |

Held-back tasks come from the same generators on structures no public task uses and were not published before the run. The two splits share no structure, so each side of the difference is resampled on its own.
