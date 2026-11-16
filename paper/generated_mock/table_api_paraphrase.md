> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**API track: sensitivity to wording (20 requests, three phrasings each)**

| model | requests | full | terse | indirect | mean spread per request | requests where the outcome flips | phrasings whose own samples disagree |
|:---|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 20 | 0.800 | 0.667 | 0.683 | 0.417 | 8 of 20 | 63.3% |
| nvidia/nemotron-3-super-120b-a12b | 20 | 0.617 | 0.533 | 0.633 | 0.367 | 11 of 20 | 80.0% |
| openai/gpt-5.4-nano | 20 | 0.500 | 0.600 | 0.500 | 0.400 | 14 of 20 | 80.0% |
| z-ai/glm-5.2 | 20 | 0.567 | 0.517 | 0.633 | 0.467 | 16 of 20 | 71.7% |
| deepseek/deepseek-v3.2 | 20 | 0.683 | 0.517 | 0.483 | 0.517 | 16 of 20 | 75.0% |
| google/gemini-4-argon | 20 | 0.567 | 0.600 | 0.550 | 0.367 | 13 of 20 | 81.7% |
| google/gemma-3-27b-it | 20 | 0.617 | 0.600 | 0.600 | 0.450 | 14 of 20 | 75.0% |
| openai/gpt-oss-120b | 20 | 0.600 | 0.617 | 0.567 | 0.400 | 15 of 20 | 81.7% |
| meta-llama/llama-4-maverick | 20 | 0.567 | 0.500 | 0.567 | 0.400 | 14 of 20 | 78.3% |
| qwen/qwen3-30b-a3b-instruct-2507 | 20 | 0.483 | 0.600 | 0.567 | 0.350 | 13 of 20 | 83.3% |
| minimax/minimax-m3 | 20 | 0.667 | 0.483 | 0.633 | 0.450 | 15 of 20 | 76.7% |
| anthropic/claude-opus-5.5 | 20 | 0.517 | 0.600 | 0.600 | 0.500 | 14 of 20 | 73.3% |
| x-ai/grok-4.7 | 20 | 0.567 | 0.550 | 0.583 | 0.533 | 16 of 20 | 70.0% |
| claude-haiku-4-5 | 20 | 0.583 | 0.667 | 0.533 | 0.450 | 13 of 20 | 75.0% |
| openai/gpt-6.1-sol | 20 | 0.617 | 0.533 | 0.550 | 0.483 | 14 of 20 | 65.0% |
| deepseek/deepseek-v4-pro-0813 | 20 | 0.650 | 0.583 | 0.533 | 0.400 | 17 of 20 | 86.7% |
| deepseek/deepseek-v4-flash | 20 | 0.517 | 0.533 | 0.500 | 0.500 | 12 of 20 | 66.7% |
| openai/gpt-oss-20b | 20 | 0.533 | 0.517 | 0.550 | 0.483 | 17 of 20 | 80.0% |
| google/gemini-3.5-flash | 20 | 0.617 | 0.583 | 0.467 | 0.500 | 16 of 20 | 70.0% |
| mistralai/mistral-small-2603 | 20 | 0.600 | 0.483 | 0.533 | 0.483 | 16 of 20 | 75.0% |
| qwen/qwen3-next-80b-a3b-instruct | 20 | 0.583 | 0.567 | 0.583 | 0.450 | 14 of 20 | 70.0% |
| baseline-rules (keyword baseline) | 20 | 0.517 | 0.633 | 0.550 | 0.517 | 15 of 20 | 63.3% |
| **panel mean** | 20 | 0.593 | 0.564 | 0.564 | 0.446 | 71.0% | 75.2% |

Task success per phrasing. Spread: for each request, the highest minus the lowest task success among its three phrasings, then the mean over requests. A request flips when it is solved (more than half the samples right) in one phrasing and not in another. Sampling noise alone gives a spread above 0: the last column is the share of single phrasings whose own samples do not all agree, the noise the spread has to be read against.
