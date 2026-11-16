> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**MVS track: public and held-back tasks (task success)**

| model | public tasks | public | held-back tasks | held back | held back − public [95% CI] |
|:---|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 305 | 0.556 | 76 | 0.575 | +0.018 [-0.052, +0.087] |
| openai/gpt-5.4-nano | 305 | 0.566 | 76 | 0.496 | -0.071 [-0.141, +0.001] |
| google/gemma-3-27b-it | 305 | 0.549 | 76 | 0.513 | -0.035 [-0.096, +0.023] |
| anthropic/claude-opus-5.5 | 305 | 0.539 | 76 | 0.579 | +0.040 [-0.054, +0.119] |
| x-ai/grok-4.7 | 305 | 0.555 | 76 | 0.522 | -0.033 [-0.092, +0.040] |
| z-ai/glm-5.2 | 305 | 0.529 | 76 | 0.487 | -0.042 [-0.100, +0.011] |
| minimax/minimax-m3 | 305 | 0.541 | 76 | 0.570 | +0.029 [-0.032, +0.091] |
| nvidia/nemotron-3-super-120b-a12b | 305 | 0.569 | 76 | 0.522 | -0.047 [-0.130, +0.031] |
| deepseek/deepseek-v3.2 | 305 | 0.525 | 76 | 0.557 | +0.032 [-0.052, +0.120] |
| google/gemini-4-argon | 305 | 0.550 | 76 | 0.474 | -0.076 [-0.138, -0.016] |
| deepseek/deepseek-v4-pro-0813 | 305 | 0.530 | 76 | 0.618 | +0.088 [+0.023, +0.151] |
| meta-llama/llama-4-maverick | 305 | 0.570 | 76 | 0.544 | -0.027 [-0.083, +0.029] |
| openai/gpt-oss-20b | 305 | 0.536 | 76 | 0.522 | -0.014 [-0.104, +0.074] |
| qwen/qwen3-30b-a3b-instruct-2507 | 305 | 0.557 | 76 | 0.566 | +0.008 [-0.053, +0.073] |
| deepseek/deepseek-v4-flash | 305 | 0.536 | 76 | 0.491 | -0.044 [-0.130, +0.029] |
| google/gemini-3.5-flash | 305 | 0.550 | 76 | 0.570 | +0.020 [-0.042, +0.078] |
| openai/gpt-oss-120b | 305 | 0.528 | 76 | 0.518 | -0.010 [-0.079, +0.053] |
| claude-haiku-4-5 | 305 | 0.534 | 76 | 0.535 | +0.001 [-0.062, +0.068] |
| openai/gpt-6.1-sol | 305 | 0.549 | 76 | 0.513 | -0.035 [-0.108, +0.026] |
| qwen/qwen3-next-80b-a3b-instruct | 305 | 0.558 | 76 | 0.557 | -0.001 [-0.074, +0.071] |
| mistralai/mistral-small-2603 | 305 | 0.513 | 76 | 0.566 | +0.053 [-0.033, +0.128] |
| baseline-rules (keyword baseline) | 305 | 0.544 | 76 | 0.557 | +0.013 [-0.055, +0.078] |
| **panel mean** | 305 | 0.545 | 76 | 0.538 | -0.007 [-0.024, +0.010] |
| panel, translation tier | 55 | 0.557 | 18 | 0.534 | -0.023 [-0.063, +0.022] |
| panel, grounded tier | 52 | 0.536 | 11 | 0.522 | -0.014 [-0.060, +0.044] |
| panel, interactions tier | 32 | 0.565 | 8 | 0.540 | -0.025 [-0.064, +0.027] |
| panel, resolve tier | 32 | 0.549 | 7 | 0.560 | +0.011 [-0.037, +0.058] |
| panel, clinical tier | 63 | 0.536 | 19 | 0.532 | -0.004 [-0.037, +0.018] |
| panel, follow-up tier | 50 | 0.542 | 8 | 0.536 | -0.006 [-0.051, +0.031] |
| panel, accept-set tier | 21 | 0.529 | 5 | 0.578 | +0.049 [+0.009, +0.091] |

Held-back tasks come from the same generators on structures no public task uses and were not published before the run. The two splits share no structure, so each side of the difference is resampled on its own.
