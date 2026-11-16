> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**MVS track: public and held-back tasks (task success)**

| model | public tasks | public | held-back tasks | held back | held back − public [95% CI] |
|:---|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 298 | 0.556 | 80 | 0.579 | +0.023 [-0.046, +0.091] |
| nvidia/nemotron-3-super-120b-a12b | 298 | 0.576 | 80 | 0.546 | -0.030 [-0.110, +0.043] |
| openai/gpt-5.4-nano | 298 | 0.562 | 80 | 0.475 | -0.087 [-0.162, -0.017] |
| z-ai/glm-5.2 | 298 | 0.537 | 80 | 0.508 | -0.029 [-0.096, +0.038] |
| deepseek/deepseek-v3.2 | 298 | 0.515 | 80 | 0.567 | +0.052 [-0.023, +0.129] |
| google/gemini-4-argon | 298 | 0.554 | 80 | 0.500 | -0.054 [-0.100, -0.008] |
| google/gemma-3-27b-it | 298 | 0.547 | 80 | 0.504 | -0.043 [-0.092, +0.008] |
| openai/gpt-oss-120b | 298 | 0.555 | 80 | 0.512 | -0.042 [-0.110, +0.019] |
| meta-llama/llama-4-maverick | 298 | 0.569 | 80 | 0.546 | -0.024 [-0.091, +0.044] |
| qwen/qwen3-30b-a3b-instruct-2507 | 298 | 0.560 | 80 | 0.571 | +0.010 [-0.048, +0.070] |
| minimax/minimax-m3 | 298 | 0.539 | 80 | 0.575 | +0.036 [-0.032, +0.102] |
| anthropic/claude-opus-5.5 | 298 | 0.523 | 80 | 0.558 | +0.035 [-0.048, +0.109] |
| x-ai/grok-4.7 | 298 | 0.540 | 80 | 0.512 | -0.028 [-0.099, +0.048] |
| claude-haiku-4-5 | 298 | 0.541 | 80 | 0.529 | -0.012 [-0.071, +0.051] |
| openai/gpt-6.1-sol | 298 | 0.549 | 80 | 0.550 | +0.001 [-0.073, +0.070] |
| deepseek/deepseek-v4-pro-0813 | 298 | 0.529 | 80 | 0.600 | +0.071 [+0.016, +0.122] |
| deepseek/deepseek-v4-flash | 298 | 0.521 | 80 | 0.475 | -0.046 [-0.116, +0.018] |
| openai/gpt-oss-20b | 298 | 0.521 | 80 | 0.508 | -0.013 [-0.091, +0.066] |
| google/gemini-3.5-flash | 298 | 0.532 | 80 | 0.563 | +0.030 [-0.041, +0.100] |
| mistralai/mistral-small-2603 | 298 | 0.520 | 80 | 0.567 | +0.047 [-0.031, +0.120] |
| qwen/qwen3-next-80b-a3b-instruct | 298 | 0.543 | 80 | 0.558 | +0.016 [-0.047, +0.078] |
| baseline-rules (keyword baseline) | 298 | 0.548 | 80 | 0.583 | +0.035 [-0.048, +0.109] |
| **panel mean** | 298 | 0.542 | 80 | 0.538 | -0.004 [-0.018, +0.010] |
| panel, translation tier | 51 | 0.554 | 17 | 0.536 | -0.018 [-0.061, +0.027] |
| panel, grounded tier | 56 | 0.537 | 12 | 0.526 | -0.010 [-0.053, +0.044] |
| panel, interactions tier | 32 | 0.565 | 8 | 0.540 | -0.025 [-0.064, +0.027] |
| panel, resolve tier | 32 | 0.549 | 7 | 0.560 | +0.011 [-0.037, +0.058] |
| panel, clinical tier | 59 | 0.532 | 20 | 0.525 | -0.008 [-0.039, +0.015] |
| panel, follow-up tier | 47 | 0.536 | 11 | 0.547 | +0.011 [-0.027, +0.044] |
| panel, accept-set tier | 21 | 0.527 | 5 | 0.578 | +0.051 [+0.009, +0.092] |

Held-back tasks come from the same generators on structures no public task uses and were not published before the run. The two splits share no structure, so each side of the difference is resampled on its own.
