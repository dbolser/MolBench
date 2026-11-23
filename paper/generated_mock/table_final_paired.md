> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Paired comparison of the two formats**

| Model | Pairs | Both right | Scene right, call list wrong | Call list right, scene wrong | Both wrong | McNemar p |
|:---|---:|---:|---:|---:|---:|---:|
| kimi-k2.6 | 258 | 134 (97) | 58 (54) | 37 (69) | 29 (38) | 0.040 (0.207) |
| gpt-5.4-nano | 258 | 126 (90) | 56 (59) | 45 (74) | 31 (35) | 0.320 (0.225) |
| gemma-3-27b-it | 258 | 122 (85) | 60 (51) | 42 (74) | 34 (48) | 0.092 (0.049) |
| claude-opus-5.5 † | 258 | 125 (90) | 68 (52) | 46 (77) | 19 (39) | 0.049 (0.034) |
| grok-4.7 † | 258 | 134 (96) | 58 (50) | 29 (64) | 37 (48) | 0.002 (0.223) |
| glm-5.2 | 258 | 119 (86) | 55 (47) | 54 (89) | 30 (36) | 1.000 (< 0.001) |
| minimax-m3 | 258 | 120 (90) | 65 (58) | 38 (65) | 35 (45) | 0.010 (0.589) |
| nemotron-3-super-120b-a12b | 258 | 117 (90) | 68 (56) | 49 (77) | 24 (35) | 0.096 (0.082) |
| deepseek-v3.2 | 258 | 124 (87) | 63 (53) | 38 (70) | 33 (48) | 0.017 (0.149) |
| gemini-4-argon † | 258 | 120 (87) | 56 (50) | 50 (77) | 32 (44) | 0.627 (0.021) |
| deepseek-v4-pro-0813 † | 258 | 128 (90) | 49 (50) | 47 (78) | 34 (40) | 0.919 (0.017) |
| llama-4-maverick | 258 | 125 (95) | 60 (60) | 38 (60) | 35 (43) | 0.033 (1.000) |
| gpt-oss-20b | 258 | 120 (86) | 61 (54) | 41 (69) | 36 (49) | 0.059 (0.207) |
| qwen3-30b-a3b-instruct-2507 | 258 | 127 (105) | 60 (52) | 35 (54) | 36 (47) | 0.013 (0.923) |
| deepseek-v4-flash | 258 | 119 (91) | 66 (52) | 42 (72) | 31 (43) | 0.026 (0.088) |
| gemini-3.5-flash | 258 | 112 (83) | 78 (71) | 38 (64) | 30 (40) | < 0.001 (0.606) |
| gpt-oss-120b | 258 | 120 (78) | 60 (51) | 44 (78) | 34 (51) | 0.141 (0.022) |
| claude-haiku-4-5 | 258 | 124 (84) | 56 (52) | 38 (76) | 40 (46) | 0.079 (0.042) |
| gpt-6.1-sol † | 258 | 113 (82) | 69 (50) | 39 (69) | 37 (57) | 0.005 (0.099) |
| qwen3-next-80b-a3b-instruct | 258 | 114 (84) | 69 (63) | 41 (67) | 34 (44) | 0.010 (0.793) |
| mistral-small-2603 | 258 | 125 (86) | 57 (49) | 40 (74) | 36 (49) | 0.104 (0.030) |

A side is right when at least two of its three sampled answers are right. Each cell: counted by the target score (the requested atoms drawn exactly as asked), and in brackets by task success (the whole final state exactly right).
