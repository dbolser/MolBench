> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Paired comparison of the two formats**

**Table 9a. Primary comparison. A side is right when at least 2 of its 3 answers are target-right. The 250 pairs that have a target score.**

| Model | Pairs | Right on both sides | Right in the scene only | Right in the call list only | Right on neither side | McNemar p | Difference: scene only minus call list only, as a share of the pairs (95% interval) |
|:---|---:|---:|---:|---:|---:|---:|---:|
| kimi-k2.6 | 250 | 134 | 58 | 37 | 21 | 0.040 | +0.084 [+0.008, +0.167] |
| gpt-5.4-nano | 250 | 126 | 56 | 45 | 23 | 0.320 | +0.044 [-0.038, +0.131] |
| gemma-3-27b-it | 250 | 122 | 60 | 42 | 26 | 0.092 | +0.072 [-0.004, +0.147] |
| claude-opus-5.5 † | 250 | 125 | 68 | 46 | 11 | 0.049 | +0.088 [+0.004, +0.169] |
| grok-4.7 † | 250 | 134 | 58 | 29 | 29 | 0.002 | +0.116 [+0.057, +0.175] |
| glm-5.2 | 250 | 119 | 55 | 54 | 22 | 1.000 | +0.004 [-0.081, +0.089] |
| minimax-m3 | 250 | 120 | 65 | 38 | 27 | 0.010 | +0.108 [+0.035, +0.178] |
| nemotron-3-super-120b-a12b | 250 | 117 | 68 | 49 | 16 | 0.096 | +0.076 [+0.000, +0.151] |
| deepseek-v3.2 | 250 | 124 | 63 | 38 | 25 | 0.017 | +0.100 [+0.024, +0.180] |
| gemini-4-argon † | 250 | 120 | 56 | 50 | 24 | 0.627 | +0.024 [-0.056, +0.100] |
| deepseek-v4-pro-0813 † | 250 | 128 | 49 | 47 | 26 | 0.919 | +0.008 [-0.070, +0.086] |
| llama-4-maverick | 250 | 125 | 60 | 38 | 27 | 0.033 | +0.088 [+0.012, +0.161] |
| gpt-oss-20b | 250 | 120 | 61 | 41 | 28 | 0.059 | +0.080 [-0.009, +0.166] |
| qwen3-30b-a3b-instruct-2507 | 250 | 127 | 60 | 35 | 28 | 0.013 | +0.100 [+0.024, +0.178] |
| deepseek-v4-flash | 250 | 119 | 66 | 42 | 23 | 0.026 | +0.096 [+0.021, +0.180] |
| gemini-3.5-flash | 250 | 112 | 78 | 38 | 22 | < 0.001 | +0.160 [+0.080, +0.239] |
| gpt-oss-120b | 250 | 120 | 60 | 44 | 26 | 0.141 | +0.064 [-0.019, +0.146] |
| claude-haiku-4-5 | 250 | 124 | 56 | 38 | 32 | 0.079 | +0.072 [-0.008, +0.161] |
| gpt-6.1-sol † | 250 | 113 | 69 | 39 | 29 | 0.005 | +0.120 [+0.056, +0.185] |
| qwen3-next-80b-a3b-instruct | 250 | 114 | 69 | 41 | 26 | 0.010 | +0.112 [+0.019, +0.211] |
| mistral-small-2603 | 250 | 125 | 57 | 40 | 28 | 0.104 | +0.068 [-0.008, +0.140] |

**Table 9b. Secondary comparison. A side is right when at least 2 of its 3 answers are task successes. All 258 pairs.**

| Model | Pairs | Right on both sides | Right in the scene only | Right in the call list only | Right on neither side | McNemar p | Difference: scene only minus call list only, as a share of the pairs (95% interval) |
|:---|---:|---:|---:|---:|---:|---:|---:|
| kimi-k2.6 | 258 | 97 | 54 | 69 | 38 | 0.207 | -0.058 [-0.142, +0.027] |
| gpt-5.4-nano | 258 | 90 | 59 | 74 | 35 | 0.225 | -0.058 [-0.145, +0.033] |
| gemma-3-27b-it | 258 | 85 | 51 | 74 | 48 | 0.049 | -0.089 [-0.168, -0.004] |
| claude-opus-5.5 † | 258 | 90 | 52 | 77 | 39 | 0.034 | -0.097 [-0.184, -0.011] |
| grok-4.7 † | 258 | 96 | 50 | 64 | 48 | 0.223 | -0.054 [-0.122, +0.017] |
| glm-5.2 | 258 | 86 | 47 | 89 | 36 | < 0.001 | -0.163 [-0.258, -0.068] |
| minimax-m3 | 258 | 90 | 58 | 65 | 45 | 0.589 | -0.027 [-0.100, +0.047] |
| nemotron-3-super-120b-a12b | 258 | 90 | 56 | 77 | 35 | 0.082 | -0.081 [-0.161, +0.000] |
| deepseek-v3.2 | 258 | 87 | 53 | 70 | 48 | 0.149 | -0.066 [-0.147, +0.019] |
| gemini-4-argon † | 258 | 87 | 50 | 77 | 44 | 0.021 | -0.105 [-0.181, -0.027] |
| deepseek-v4-pro-0813 † | 258 | 90 | 50 | 78 | 40 | 0.017 | -0.109 [-0.210, -0.011] |
| llama-4-maverick | 258 | 95 | 60 | 60 | 43 | 1.000 | +0.000 [-0.085, +0.083] |
| gpt-oss-20b | 258 | 86 | 54 | 69 | 49 | 0.207 | -0.058 [-0.149, +0.035] |
| qwen3-30b-a3b-instruct-2507 | 258 | 105 | 52 | 54 | 47 | 0.923 | -0.008 [-0.091, +0.074] |
| deepseek-v4-flash | 258 | 91 | 52 | 72 | 43 | 0.088 | -0.078 [-0.169, +0.011] |
| gemini-3.5-flash | 258 | 83 | 71 | 64 | 40 | 0.606 | +0.027 [-0.067, +0.118] |
| gpt-oss-120b | 258 | 78 | 51 | 78 | 51 | 0.022 | -0.105 [-0.194, -0.012] |
| claude-haiku-4-5 | 258 | 84 | 52 | 76 | 46 | 0.042 | -0.093 [-0.185, +0.000] |
| gpt-6.1-sol † | 258 | 82 | 50 | 69 | 57 | 0.099 | -0.074 [-0.153, +0.004] |
| qwen3-next-80b-a3b-instruct | 258 | 84 | 63 | 67 | 44 | 0.793 | -0.016 [-0.121, +0.088] |
| mistral-small-2603 | 258 | 86 | 49 | 74 | 49 | 0.030 | -0.097 [-0.185, -0.012] |
