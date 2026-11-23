> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**The same request in both formats: paired analysis**

*All twins outside the clinical tier (176 pairs). Solved = requested atoms drawn as asked (target score 1).*

| model | pairs | both solved | MVS only | API only | neither | MVS solved | API solved | McNemar p (exact) |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 176 | 94 | 38 | 25 | 19 | 75.0% | 67.6% | 0.130 |
| openai/gpt-5.4-nano | 176 | 91 | 36 | 27 | 22 | 72.2% | 67.0% | 0.314 |
| google/gemma-3-27b-it | 176 | 81 | 40 | 28 | 27 | 68.8% | 61.9% | 0.182 |
| anthropic/claude-opus-5.5 | 176 | 88 | 47 | 28 | 13 | 76.7% | 65.9% | 0.037 |
| x-ai/grok-4.7 | 176 | 94 | 36 | 22 | 24 | 73.9% | 65.9% | 0.087 |
| z-ai/glm-5.2 | 176 | 91 | 29 | 33 | 23 | 68.2% | 70.5% | 0.704 |
| minimax/minimax-m3 | 176 | 90 | 41 | 21 | 24 | 74.4% | 63.1% | 0.015 |
| nvidia/nemotron-3-super-120b-a12b | 176 | 82 | 45 | 33 | 16 | 72.2% | 65.3% | 0.213 |
| deepseek/deepseek-v3.2 | 176 | 85 | 41 | 25 | 25 | 71.6% | 62.5% | 0.064 |
| google/gemini-4-argon | 176 | 90 | 33 | 29 | 24 | 69.9% | 67.6% | 0.704 |
| deepseek/deepseek-v4-pro-0813 | 176 | 95 | 28 | 34 | 19 | 69.9% | 73.3% | 0.526 |
| meta-llama/llama-4-maverick | 176 | 87 | 40 | 25 | 24 | 72.2% | 63.6% | 0.082 |
| openai/gpt-oss-20b | 176 | 85 | 39 | 30 | 22 | 70.5% | 65.3% | 0.336 |
| qwen/qwen3-30b-a3b-instruct-2507 | 176 | 89 | 41 | 20 | 26 | 73.9% | 61.9% | 0.010 |
| deepseek/deepseek-v4-flash | 176 | 87 | 43 | 24 | 22 | 73.9% | 63.1% | 0.027 |
| google/gemini-3.5-flash | 176 | 78 | 55 | 24 | 19 | 75.6% | 58.0% | < 0.001 |
| openai/gpt-oss-120b | 176 | 90 | 39 | 23 | 24 | 73.3% | 64.2% | 0.056 |
| claude-haiku-4-5 | 176 | 85 | 37 | 30 | 24 | 69.3% | 65.3% | 0.464 |
| openai/gpt-6.1-sol | 176 | 81 | 45 | 22 | 28 | 71.6% | 58.5% | 0.007 |
| qwen/qwen3-next-80b-a3b-instruct | 176 | 73 | 48 | 27 | 28 | 68.8% | 56.8% | 0.020 |
| mistralai/mistral-small-2603 | 176 | 89 | 38 | 28 | 21 | 72.2% | 66.5% | 0.268 |
| baseline-rules (keyword baseline) | 176 | 88 | 35 | 32 | 21 | 69.9% | 68.2% | 0.807 |
| baseline-literal (literal baseline) | 176 | 90 | 42 | 19 | 25 | 75.0% | 61.9% | 0.004 |
| **pooled over models** | 3696 | 1825 | 839 | 558 | 474 | 72.1% | 64.5% | < 0.001 |

*Sensitivity: without the twins whose API side needs a hide toggle the request does not state (161 pairs). Solved = requested atoms drawn as asked (target score 1).*

| model | pairs | both solved | MVS only | API only | neither | MVS solved | API solved | McNemar p (exact) |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 161 | 85 | 35 | 23 | 18 | 74.5% | 67.1% | 0.148 |
| openai/gpt-5.4-nano | 161 | 86 | 31 | 23 | 21 | 72.7% | 67.7% | 0.341 |
| google/gemma-3-27b-it | 161 | 78 | 36 | 23 | 24 | 70.8% | 62.7% | 0.117 |
| anthropic/claude-opus-5.5 | 161 | 83 | 46 | 20 | 12 | 80.1% | 64.0% | 0.002 |
| x-ai/grok-4.7 | 161 | 88 | 33 | 19 | 21 | 75.2% | 66.5% | 0.070 |
| z-ai/glm-5.2 | 161 | 83 | 28 | 30 | 20 | 68.9% | 70.2% | 0.896 |
| minimax/minimax-m3 | 161 | 85 | 39 | 18 | 19 | 77.0% | 64.0% | 0.008 |
| nvidia/nemotron-3-super-120b-a12b | 161 | 79 | 40 | 28 | 14 | 73.9% | 66.5% | 0.182 |
| deepseek/deepseek-v3.2 | 161 | 79 | 40 | 21 | 21 | 73.9% | 62.1% | 0.020 |
| google/gemini-4-argon | 161 | 84 | 33 | 24 | 20 | 72.7% | 67.1% | 0.289 |
| deepseek/deepseek-v4-pro-0813 | 161 | 90 | 24 | 29 | 18 | 70.8% | 73.9% | 0.583 |
| meta-llama/llama-4-maverick | 161 | 82 | 38 | 21 | 20 | 74.5% | 64.0% | 0.036 |
| openai/gpt-oss-20b | 161 | 81 | 37 | 27 | 16 | 73.3% | 67.1% | 0.260 |
| qwen/qwen3-30b-a3b-instruct-2507 | 161 | 83 | 37 | 17 | 24 | 74.5% | 62.1% | 0.009 |
| deepseek/deepseek-v4-flash | 161 | 83 | 40 | 20 | 18 | 76.4% | 64.0% | 0.013 |
| google/gemini-3.5-flash | 161 | 76 | 49 | 19 | 17 | 77.6% | 59.0% | < 0.001 |
| openai/gpt-oss-120b | 161 | 86 | 35 | 18 | 22 | 75.2% | 64.6% | 0.027 |
| claude-haiku-4-5 | 161 | 83 | 35 | 23 | 20 | 73.3% | 65.8% | 0.148 |
| openai/gpt-6.1-sol | 161 | 75 | 42 | 17 | 27 | 72.7% | 57.1% | 0.002 |
| qwen/qwen3-next-80b-a3b-instruct | 161 | 70 | 46 | 22 | 23 | 72.0% | 57.1% | 0.005 |
| mistralai/mistral-small-2603 | 161 | 82 | 38 | 22 | 19 | 74.5% | 64.6% | 0.052 |
| baseline-rules (keyword baseline) | 161 | 80 | 34 | 28 | 19 | 70.8% | 67.1% | 0.526 |
| baseline-literal (literal baseline) | 161 | 86 | 40 | 13 | 22 | 78.3% | 61.5% | < 0.001 |
| **pooled over models** | 3381 | 1721 | 782 | 464 | 414 | 74.0% | 64.6% | < 0.001 |

*Clinical twins (reported apart: the PDBe viewer maps UniProt numbering itself, an MVS scene cannot) (82 pairs). Solved = requested atoms drawn as asked (target score 1).*

| model | pairs | both solved | MVS only | API only | neither | MVS solved | API solved | McNemar p (exact) |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 82 | 40 | 20 | 12 | 10 | 73.2% | 63.4% | 0.215 |
| openai/gpt-5.4-nano | 82 | 35 | 20 | 18 | 9 | 67.1% | 64.6% | 0.871 |
| google/gemma-3-27b-it | 82 | 41 | 20 | 14 | 7 | 74.4% | 67.1% | 0.392 |
| anthropic/claude-opus-5.5 | 82 | 37 | 21 | 18 | 6 | 70.7% | 67.1% | 0.749 |
| x-ai/grok-4.7 | 82 | 40 | 22 | 7 | 13 | 75.6% | 57.3% | 0.008 |
| z-ai/glm-5.2 | 82 | 28 | 26 | 21 | 7 | 65.9% | 59.8% | 0.560 |
| minimax/minimax-m3 | 82 | 30 | 24 | 17 | 11 | 65.9% | 57.3% | 0.349 |
| nvidia/nemotron-3-super-120b-a12b | 82 | 35 | 23 | 16 | 8 | 70.7% | 62.2% | 0.337 |
| deepseek/deepseek-v3.2 | 82 | 39 | 22 | 13 | 8 | 74.4% | 63.4% | 0.175 |
| google/gemini-4-argon | 82 | 30 | 23 | 21 | 8 | 64.6% | 62.2% | 0.880 |
| deepseek/deepseek-v4-pro-0813 | 82 | 33 | 21 | 13 | 15 | 65.9% | 56.1% | 0.229 |
| meta-llama/llama-4-maverick | 82 | 38 | 20 | 13 | 11 | 70.7% | 62.2% | 0.296 |
| openai/gpt-oss-20b | 82 | 35 | 22 | 11 | 14 | 69.5% | 56.1% | 0.080 |
| qwen/qwen3-30b-a3b-instruct-2507 | 82 | 38 | 19 | 15 | 10 | 69.5% | 64.6% | 0.608 |
| deepseek/deepseek-v4-flash | 82 | 32 | 23 | 18 | 9 | 67.1% | 61.0% | 0.533 |
| google/gemini-3.5-flash | 82 | 34 | 23 | 14 | 11 | 69.5% | 58.5% | 0.188 |
| openai/gpt-oss-120b | 82 | 30 | 21 | 21 | 10 | 62.2% | 62.2% | 1.000 |
| claude-haiku-4-5 | 82 | 39 | 19 | 8 | 16 | 70.7% | 57.3% | 0.052 |
| openai/gpt-6.1-sol | 82 | 32 | 24 | 17 | 9 | 68.3% | 59.8% | 0.349 |
| qwen/qwen3-next-80b-a3b-instruct | 82 | 41 | 21 | 14 | 6 | 75.6% | 67.1% | 0.311 |
| mistralai/mistral-small-2603 | 82 | 36 | 19 | 12 | 15 | 67.1% | 58.5% | 0.281 |
| baseline-rules (keyword baseline) | 82 | 38 | 15 | 19 | 10 | 64.6% | 69.5% | 0.608 |
| baseline-literal (literal baseline) | 82 | 28 | 21 | 23 | 10 | 59.8% | 62.2% | 0.880 |
| **pooled over models** | 1722 | 743 | 453 | 313 | 213 | 69.5% | 61.3% | < 0.001 |

*All twins outside the clinical tier (176 pairs). Solved = final state exactly right (task success).*

| model | pairs | both solved | MVS only | API only | neither | MVS solved | API solved | McNemar p (exact) |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 176 | 65 | 37 | 49 | 25 | 58.0% | 64.8% | 0.235 |
| openai/gpt-5.4-nano | 176 | 61 | 41 | 50 | 24 | 58.0% | 63.1% | 0.402 |
| google/gemma-3-27b-it | 176 | 53 | 39 | 51 | 33 | 52.3% | 59.1% | 0.246 |
| anthropic/claude-opus-5.5 | 176 | 58 | 36 | 54 | 28 | 53.4% | 63.6% | 0.073 |
| x-ai/grok-4.7 | 176 | 66 | 32 | 47 | 31 | 55.7% | 64.2% | 0.115 |
| z-ai/glm-5.2 | 176 | 63 | 26 | 63 | 24 | 50.6% | 71.6% | < 0.001 |
| minimax/minimax-m3 | 176 | 68 | 39 | 40 | 29 | 60.8% | 61.4% | 1.000 |
| nvidia/nemotron-3-super-120b-a12b | 176 | 61 | 39 | 55 | 21 | 56.8% | 65.9% | 0.121 |
| deepseek/deepseek-v3.2 | 176 | 60 | 37 | 45 | 34 | 55.1% | 59.7% | 0.440 |
| google/gemini-4-argon | 176 | 62 | 33 | 51 | 30 | 54.0% | 64.2% | 0.063 |
| deepseek/deepseek-v4-pro-0813 | 176 | 65 | 33 | 57 | 21 | 55.7% | 69.3% | 0.015 |
| meta-llama/llama-4-maverick | 176 | 64 | 42 | 40 | 30 | 60.2% | 59.1% | 0.912 |
| openai/gpt-oss-20b | 176 | 58 | 39 | 51 | 28 | 55.1% | 61.9% | 0.246 |
| qwen/qwen3-30b-a3b-instruct-2507 | 176 | 70 | 40 | 36 | 30 | 62.5% | 60.2% | 0.731 |
| deepseek/deepseek-v4-flash | 176 | 65 | 34 | 48 | 29 | 56.2% | 64.2% | 0.151 |
| google/gemini-3.5-flash | 176 | 53 | 50 | 46 | 27 | 58.5% | 56.2% | 0.760 |
| openai/gpt-oss-120b | 176 | 54 | 39 | 51 | 32 | 52.8% | 59.7% | 0.246 |
| claude-haiku-4-5 | 176 | 53 | 35 | 60 | 28 | 50.0% | 64.2% | 0.013 |
| openai/gpt-6.1-sol | 176 | 59 | 33 | 43 | 41 | 52.3% | 58.0% | 0.302 |
| qwen/qwen3-next-80b-a3b-instruct | 176 | 50 | 45 | 46 | 35 | 54.0% | 54.5% | 1.000 |
| mistralai/mistral-small-2603 | 176 | 60 | 33 | 52 | 31 | 52.8% | 63.6% | 0.050 |
| baseline-rules (keyword baseline) | 176 | 63 | 37 | 53 | 23 | 56.8% | 65.9% | 0.113 |
| baseline-literal (literal baseline) | 176 | 62 | 39 | 41 | 34 | 57.4% | 58.5% | 0.911 |
| **pooled over models** | 3696 | 1268 | 782 | 1035 | 611 | 55.5% | 62.3% | < 0.001 |

*Sensitivity: without the twins whose API side needs a hide toggle the request does not state (161 pairs). Solved = final state exactly right (task success).*

| model | pairs | both solved | MVS only | API only | neither | MVS solved | API solved | McNemar p (exact) |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 161 | 56 | 34 | 47 | 24 | 55.9% | 64.0% | 0.182 |
| openai/gpt-5.4-nano | 161 | 56 | 36 | 46 | 23 | 57.1% | 63.4% | 0.320 |
| google/gemma-3-27b-it | 161 | 50 | 35 | 46 | 30 | 52.8% | 59.6% | 0.266 |
| anthropic/claude-opus-5.5 | 161 | 53 | 35 | 46 | 27 | 54.7% | 61.5% | 0.266 |
| x-ai/grok-4.7 | 161 | 60 | 29 | 44 | 28 | 55.3% | 64.6% | 0.101 |
| z-ai/glm-5.2 | 161 | 55 | 25 | 60 | 21 | 49.7% | 71.4% | < 0.001 |
| minimax/minimax-m3 | 161 | 63 | 37 | 37 | 24 | 62.1% | 62.1% | 1.000 |
| nvidia/nemotron-3-super-120b-a12b | 161 | 58 | 34 | 50 | 19 | 57.1% | 67.1% | 0.101 |
| deepseek/deepseek-v3.2 | 161 | 54 | 36 | 41 | 30 | 55.9% | 59.0% | 0.649 |
| google/gemini-4-argon | 161 | 56 | 33 | 46 | 26 | 55.3% | 63.4% | 0.177 |
| deepseek/deepseek-v4-pro-0813 | 161 | 60 | 29 | 52 | 20 | 55.3% | 69.6% | 0.014 |
| meta-llama/llama-4-maverick | 161 | 59 | 40 | 36 | 26 | 61.5% | 59.0% | 0.731 |
| openai/gpt-oss-20b | 161 | 54 | 37 | 48 | 22 | 56.5% | 63.4% | 0.278 |
| qwen/qwen3-30b-a3b-instruct-2507 | 161 | 64 | 36 | 33 | 28 | 62.1% | 60.2% | 0.810 |
| deepseek/deepseek-v4-flash | 161 | 61 | 31 | 44 | 25 | 57.1% | 65.2% | 0.165 |
| google/gemini-3.5-flash | 161 | 51 | 44 | 41 | 25 | 59.0% | 57.1% | 0.828 |
| openai/gpt-oss-120b | 161 | 50 | 35 | 46 | 30 | 52.8% | 59.6% | 0.266 |
| claude-haiku-4-5 | 161 | 51 | 33 | 53 | 24 | 52.2% | 64.6% | 0.040 |
| openai/gpt-6.1-sol | 161 | 53 | 30 | 38 | 40 | 51.6% | 56.5% | 0.396 |
| qwen/qwen3-next-80b-a3b-instruct | 161 | 47 | 43 | 41 | 30 | 55.9% | 54.7% | 0.913 |
| mistralai/mistral-small-2603 | 161 | 53 | 33 | 46 | 29 | 53.4% | 61.5% | 0.177 |
| baseline-rules (keyword baseline) | 161 | 55 | 36 | 49 | 21 | 56.5% | 64.6% | 0.193 |
| baseline-literal (literal baseline) | 161 | 58 | 37 | 35 | 31 | 59.0% | 57.8% | 0.906 |
| **pooled over models** | 3381 | 1164 | 725 | 941 | 551 | 55.9% | 62.3% | < 0.001 |

*Clinical twins (reported apart: the PDBe viewer maps UniProt numbering itself, an MVS scene cannot) (82 pairs). Solved = final state exactly right (task success).*

| model | pairs | both solved | MVS only | API only | neither | MVS solved | API solved | McNemar p (exact) |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 82 | 32 | 17 | 20 | 13 | 59.8% | 63.4% | 0.743 |
| openai/gpt-5.4-nano | 82 | 29 | 18 | 24 | 11 | 57.3% | 64.6% | 0.441 |
| google/gemma-3-27b-it | 82 | 32 | 12 | 23 | 15 | 53.7% | 67.1% | 0.090 |
| anthropic/claude-opus-5.5 | 82 | 32 | 16 | 23 | 11 | 58.5% | 67.1% | 0.337 |
| x-ai/grok-4.7 | 82 | 30 | 18 | 17 | 17 | 58.5% | 57.3% | 1.000 |
| z-ai/glm-5.2 | 82 | 23 | 21 | 26 | 12 | 53.7% | 59.8% | 0.560 |
| minimax/minimax-m3 | 82 | 22 | 19 | 25 | 16 | 50.0% | 57.3% | 0.451 |
| nvidia/nemotron-3-super-120b-a12b | 82 | 29 | 17 | 22 | 14 | 56.1% | 62.2% | 0.522 |
| deepseek/deepseek-v3.2 | 82 | 27 | 16 | 25 | 14 | 52.4% | 63.4% | 0.211 |
| google/gemini-4-argon | 82 | 25 | 17 | 26 | 14 | 51.2% | 62.2% | 0.222 |
| deepseek/deepseek-v4-pro-0813 | 82 | 25 | 17 | 21 | 19 | 51.2% | 56.1% | 0.627 |
| meta-llama/llama-4-maverick | 82 | 31 | 18 | 20 | 13 | 59.8% | 62.2% | 0.871 |
| openai/gpt-oss-20b | 82 | 28 | 15 | 18 | 21 | 52.4% | 56.1% | 0.728 |
| qwen/qwen3-30b-a3b-instruct-2507 | 82 | 35 | 12 | 18 | 17 | 57.3% | 64.6% | 0.362 |
| deepseek/deepseek-v4-flash | 82 | 26 | 18 | 24 | 14 | 53.7% | 61.0% | 0.441 |
| google/gemini-3.5-flash | 82 | 30 | 21 | 18 | 13 | 62.2% | 58.5% | 0.749 |
| openai/gpt-oss-120b | 82 | 24 | 12 | 27 | 19 | 43.9% | 62.2% | 0.024 |
| claude-haiku-4-5 | 82 | 31 | 17 | 16 | 18 | 58.5% | 57.3% | 1.000 |
| openai/gpt-6.1-sol | 82 | 23 | 17 | 26 | 16 | 48.8% | 59.8% | 0.222 |
| qwen/qwen3-next-80b-a3b-instruct | 82 | 34 | 18 | 21 | 9 | 63.4% | 67.1% | 0.749 |
| mistralai/mistral-small-2603 | 82 | 26 | 16 | 22 | 18 | 51.2% | 58.5% | 0.418 |
| baseline-rules (keyword baseline) | 82 | 27 | 13 | 30 | 12 | 48.8% | 69.5% | 0.014 |
| baseline-literal (literal baseline) | 82 | 22 | 19 | 29 | 12 | 50.0% | 62.2% | 0.193 |
| **pooled over models** | 1722 | 594 | 352 | 462 | 314 | 54.9% | 61.3% | < 0.001 |

*Pooled over models, by tier.*

| tier | model × pair | both solved | MVS only | API only | neither | MVS solved | API solved | pairs | McNemar p (exact) |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| translation | 1302 | 450 | 265 | 369 | 218 | 54.9% | 62.9% | 62 | < 0.001 |
| grounded | 1323 | 452 | 292 | 368 | 211 | 56.2% | 62.0% | 63 | 0.003 |
| clinical | 1722 | 594 | 352 | 462 | 314 | 54.9% | 61.3% | 82 | < 0.001 |
| follow-up | 756 | 253 | 171 | 202 | 130 | 56.1% | 60.2% | 36 | 0.120 |
| accept-set | 315 | 113 | 54 | 96 | 52 | 53.0% | 66.3% | 15 | < 0.001 |

A pair is one request posed on both tracks with the same target atoms. A side is solved when more than half of its samples are right, by two measures: the target score (the requested atoms drawn exactly as asked, whatever else is on screen), which is the same test on both tracks and is the primary one, and task success (the whole final state exactly right), which is not: the API track accepts the viewer's default view, with water and ligands on screen, where an MVS scene that draws them is marked wrong. McNemar's exact test uses the discordant pairs only (solved on one side and not the other). The pooled rows add the counts of all models (scripted baselines left out); the same pairs recur across models, so their p value is descriptive.
