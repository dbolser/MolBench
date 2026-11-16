> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**The same request in both formats: paired analysis**

*All twins outside the clinical tier (176 pairs).*

| model | pairs | both solved | MVS only | API only | neither | MVS solved | API solved | McNemar p (exact) |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 176 | 63 | 40 | 46 | 27 | 58.5% | 61.9% | 0.590 |
| nvidia/nemotron-3-super-120b-a12b | 176 | 59 | 44 | 50 | 23 | 58.5% | 61.9% | 0.606 |
| openai/gpt-5.4-nano | 176 | 62 | 40 | 48 | 26 | 58.0% | 62.5% | 0.456 |
| z-ai/glm-5.2 | 176 | 60 | 30 | 62 | 24 | 51.1% | 69.3% | 0.001 |
| deepseek/deepseek-v3.2 | 176 | 57 | 34 | 48 | 37 | 51.7% | 59.7% | 0.151 |
| google/gemini-4-argon | 176 | 64 | 32 | 53 | 27 | 54.5% | 66.5% | 0.029 |
| google/gemma-3-27b-it | 176 | 56 | 38 | 48 | 34 | 53.4% | 59.1% | 0.332 |
| openai/gpt-oss-120b | 176 | 56 | 38 | 53 | 29 | 53.4% | 61.9% | 0.142 |
| meta-llama/llama-4-maverick | 176 | 64 | 41 | 38 | 33 | 59.7% | 58.0% | 0.822 |
| qwen/qwen3-30b-a3b-instruct-2507 | 176 | 73 | 40 | 33 | 30 | 64.2% | 60.2% | 0.483 |
| minimax/minimax-m3 | 176 | 65 | 40 | 42 | 29 | 59.7% | 60.8% | 0.912 |
| anthropic/claude-opus-5.5 | 176 | 58 | 35 | 52 | 31 | 52.8% | 62.5% | 0.086 |
| x-ai/grok-4.7 | 176 | 65 | 29 | 48 | 34 | 53.4% | 64.2% | 0.040 |
| claude-haiku-4-5 | 176 | 53 | 38 | 60 | 25 | 51.7% | 64.2% | 0.033 |
| openai/gpt-6.1-sol | 176 | 60 | 33 | 45 | 38 | 52.8% | 59.7% | 0.213 |
| deepseek/deepseek-v4-pro-0813 | 176 | 62 | 34 | 56 | 24 | 54.5% | 67.0% | 0.026 |
| deepseek/deepseek-v4-flash | 176 | 61 | 38 | 47 | 30 | 56.2% | 61.4% | 0.386 |
| openai/gpt-oss-20b | 176 | 57 | 40 | 49 | 30 | 55.1% | 60.2% | 0.397 |
| google/gemini-3.5-flash | 176 | 50 | 50 | 46 | 30 | 56.8% | 54.5% | 0.760 |
| mistralai/mistral-small-2603 | 176 | 56 | 38 | 50 | 32 | 53.4% | 60.2% | 0.241 |
| qwen/qwen3-next-80b-a3b-instruct | 176 | 45 | 47 | 46 | 38 | 52.3% | 51.7% | 1.000 |
| baseline-rules (keyword baseline) | 176 | 63 | 37 | 52 | 24 | 56.8% | 65.3% | 0.137 |
| **pooled over models** | 3696 | 1246 | 799 | 1020 | 631 | 55.3% | 61.3% | < 0.001 |

*Sensitivity: without the twins whose API side needs a hide toggle the request does not state (158 pairs).*

| model | pairs | both solved | MVS only | API only | neither | MVS solved | API solved | McNemar p (exact) |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 158 | 53 | 36 | 43 | 26 | 56.3% | 60.8% | 0.500 |
| nvidia/nemotron-3-super-120b-a12b | 158 | 54 | 38 | 45 | 21 | 58.2% | 62.7% | 0.510 |
| openai/gpt-5.4-nano | 158 | 57 | 34 | 44 | 23 | 57.6% | 63.9% | 0.308 |
| z-ai/glm-5.2 | 158 | 50 | 29 | 58 | 21 | 50.0% | 68.4% | 0.002 |
| deepseek/deepseek-v3.2 | 158 | 50 | 33 | 43 | 32 | 52.5% | 58.9% | 0.302 |
| google/gemini-4-argon | 158 | 57 | 31 | 48 | 22 | 55.7% | 66.5% | 0.071 |
| google/gemma-3-27b-it | 158 | 53 | 33 | 43 | 29 | 54.4% | 60.8% | 0.302 |
| openai/gpt-oss-120b | 158 | 51 | 34 | 47 | 26 | 53.8% | 62.0% | 0.182 |
| meta-llama/llama-4-maverick | 158 | 57 | 38 | 34 | 29 | 60.1% | 57.6% | 0.724 |
| qwen/qwen3-30b-a3b-instruct-2507 | 158 | 66 | 35 | 30 | 27 | 63.9% | 60.8% | 0.620 |
| minimax/minimax-m3 | 158 | 59 | 36 | 39 | 24 | 60.1% | 62.0% | 0.818 |
| anthropic/claude-opus-5.5 | 158 | 53 | 33 | 43 | 29 | 54.4% | 60.8% | 0.302 |
| x-ai/grok-4.7 | 158 | 59 | 26 | 44 | 29 | 53.8% | 65.2% | 0.041 |
| claude-haiku-4-5 | 158 | 51 | 34 | 52 | 21 | 53.8% | 65.2% | 0.066 |
| openai/gpt-6.1-sol | 158 | 53 | 29 | 40 | 36 | 51.9% | 58.9% | 0.228 |
| deepseek/deepseek-v4-pro-0813 | 158 | 56 | 29 | 50 | 23 | 53.8% | 67.1% | 0.024 |
| deepseek/deepseek-v4-flash | 158 | 56 | 34 | 43 | 25 | 57.0% | 62.7% | 0.362 |
| openai/gpt-oss-20b | 158 | 52 | 36 | 46 | 24 | 55.7% | 62.0% | 0.320 |
| google/gemini-3.5-flash | 158 | 46 | 44 | 40 | 28 | 57.0% | 54.4% | 0.744 |
| mistralai/mistral-small-2603 | 158 | 48 | 38 | 43 | 29 | 54.4% | 57.6% | 0.657 |
| qwen/qwen3-next-80b-a3b-instruct | 158 | 41 | 43 | 41 | 33 | 53.2% | 51.9% | 0.913 |
| baseline-rules (keyword baseline) | 158 | 53 | 35 | 48 | 22 | 55.7% | 63.9% | 0.187 |
| **pooled over models** | 3318 | 1122 | 723 | 916 | 557 | 55.6% | 61.4% | < 0.001 |

*Clinical twins (reported apart: the PDBe viewer maps UniProt numbering itself, an MVS scene cannot) (79 pairs).*

| model | pairs | both solved | MVS only | API only | neither | MVS solved | API solved | McNemar p (exact) |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 79 | 34 | 10 | 21 | 14 | 55.7% | 69.6% | 0.071 |
| nvidia/nemotron-3-super-120b-a12b | 79 | 33 | 16 | 18 | 12 | 62.0% | 64.6% | 0.864 |
| openai/gpt-5.4-nano | 79 | 21 | 17 | 29 | 12 | 48.1% | 63.3% | 0.104 |
| z-ai/glm-5.2 | 79 | 23 | 21 | 24 | 11 | 55.7% | 59.5% | 0.766 |
| deepseek/deepseek-v3.2 | 79 | 27 | 13 | 25 | 14 | 50.6% | 65.8% | 0.073 |
| google/gemini-4-argon | 79 | 24 | 19 | 18 | 18 | 54.4% | 53.2% | 1.000 |
| google/gemma-3-27b-it | 79 | 30 | 9 | 25 | 15 | 49.4% | 69.6% | 0.009 |
| openai/gpt-oss-120b | 79 | 32 | 13 | 22 | 12 | 57.0% | 68.4% | 0.175 |
| meta-llama/llama-4-maverick | 79 | 35 | 16 | 17 | 11 | 64.6% | 65.8% | 1.000 |
| qwen/qwen3-30b-a3b-instruct-2507 | 79 | 29 | 14 | 22 | 14 | 54.4% | 64.6% | 0.243 |
| minimax/minimax-m3 | 79 | 20 | 26 | 18 | 15 | 58.2% | 48.1% | 0.291 |
| anthropic/claude-opus-5.5 | 79 | 20 | 19 | 26 | 14 | 49.4% | 58.2% | 0.371 |
| x-ai/grok-4.7 | 79 | 26 | 15 | 19 | 19 | 51.9% | 57.0% | 0.608 |
| claude-haiku-4-5 | 79 | 23 | 17 | 21 | 18 | 50.6% | 55.7% | 0.627 |
| openai/gpt-6.1-sol | 79 | 25 | 22 | 19 | 13 | 59.5% | 55.7% | 0.755 |
| deepseek/deepseek-v4-pro-0813 | 79 | 23 | 22 | 21 | 13 | 57.0% | 55.7% | 1.000 |
| deepseek/deepseek-v4-flash | 79 | 19 | 19 | 27 | 14 | 48.1% | 58.2% | 0.302 |
| openai/gpt-oss-20b | 79 | 23 | 8 | 20 | 28 | 39.2% | 54.4% | 0.036 |
| google/gemini-3.5-flash | 79 | 32 | 15 | 19 | 13 | 59.5% | 64.6% | 0.608 |
| mistralai/mistral-small-2603 | 79 | 30 | 15 | 16 | 18 | 57.0% | 58.2% | 1.000 |
| qwen/qwen3-next-80b-a3b-instruct | 79 | 35 | 11 | 23 | 10 | 58.2% | 73.4% | 0.058 |
| baseline-rules (keyword baseline) | 79 | 30 | 18 | 21 | 10 | 60.8% | 64.6% | 0.749 |
| **pooled over models** | 1659 | 564 | 337 | 450 | 308 | 54.3% | 61.1% | < 0.001 |

*Pooled over models, by tier.*

| tier | model × pair | both solved | MVS only | API only | neither | MVS solved | API solved | pairs | McNemar p (exact) |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| translation | 1197 | 406 | 245 | 341 | 205 | 54.4% | 62.4% | 57 | < 0.001 |
| grounded | 1428 | 489 | 313 | 392 | 234 | 56.2% | 61.7% | 68 | 0.003 |
| clinical | 1659 | 564 | 337 | 450 | 308 | 54.3% | 61.1% | 79 | < 0.001 |
| follow-up | 756 | 238 | 187 | 191 | 140 | 56.2% | 56.7% | 36 | 0.877 |
| accept-set | 315 | 113 | 54 | 96 | 52 | 53.0% | 66.3% | 15 | < 0.001 |

A pair is one request posed on both tracks with the same target atoms. A side is solved when more than half of its samples are exactly right. McNemar's exact test uses the discordant pairs only (solved on one side and not the other). The pooled rows add the counts of all models (keyword baseline left out); the same pairs recur across models, so their p value is descriptive.
