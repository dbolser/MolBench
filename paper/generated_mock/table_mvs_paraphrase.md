> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**MVS track: sensitivity to wording (24 requests, three phrasings each)**

| model | requests | full | terse | indirect | mean spread per request | requests where the outcome flips | phrasings whose own samples disagree |
|:---|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 24 | 0.569 | 0.556 | 0.625 | 0.486 | 16 of 24 | 70.8% |
| nvidia/nemotron-3-super-120b-a12b | 24 | 0.528 | 0.597 | 0.417 | 0.486 | 22 of 24 | 80.6% |
| openai/gpt-5.4-nano | 24 | 0.597 | 0.542 | 0.528 | 0.333 | 15 of 24 | 86.1% |
| z-ai/glm-5.2 | 24 | 0.389 | 0.597 | 0.514 | 0.472 | 18 of 24 | 75.0% |
| deepseek/deepseek-v3.2 | 24 | 0.514 | 0.639 | 0.583 | 0.514 | 18 of 24 | 70.8% |
| google/gemini-4-argon | 24 | 0.472 | 0.542 | 0.556 | 0.431 | 20 of 24 | 83.3% |
| google/gemma-3-27b-it | 24 | 0.500 | 0.514 | 0.514 | 0.431 | 16 of 24 | 79.2% |
| openai/gpt-oss-120b | 24 | 0.528 | 0.542 | 0.431 | 0.417 | 16 of 24 | 76.4% |
| meta-llama/llama-4-maverick | 24 | 0.597 | 0.625 | 0.528 | 0.431 | 16 of 24 | 76.4% |
| qwen/qwen3-30b-a3b-instruct-2507 | 24 | 0.569 | 0.444 | 0.514 | 0.472 | 16 of 24 | 72.2% |
| minimax/minimax-m3 | 24 | 0.486 | 0.569 | 0.500 | 0.472 | 18 of 24 | 75.0% |
| anthropic/claude-opus-5.5 | 24 | 0.556 | 0.514 | 0.542 | 0.458 | 19 of 24 | 80.6% |
| x-ai/grok-4.7 | 24 | 0.500 | 0.681 | 0.597 | 0.403 | 12 of 24 | 69.4% |
| claude-haiku-4-5 | 24 | 0.458 | 0.514 | 0.542 | 0.417 | 16 of 24 | 80.6% |
| openai/gpt-6.1-sol | 24 | 0.569 | 0.528 | 0.542 | 0.444 | 16 of 24 | 75.0% |
| deepseek/deepseek-v4-pro-0813 | 24 | 0.458 | 0.542 | 0.444 | 0.500 | 21 of 24 | 76.4% |
| deepseek/deepseek-v4-flash | 24 | 0.417 | 0.528 | 0.569 | 0.542 | 18 of 24 | 68.1% |
| openai/gpt-oss-20b | 24 | 0.444 | 0.569 | 0.583 | 0.431 | 18 of 24 | 81.9% |
| google/gemini-3.5-flash | 24 | 0.556 | 0.500 | 0.458 | 0.417 | 16 of 24 | 79.2% |
| mistralai/mistral-small-2603 | 24 | 0.597 | 0.514 | 0.625 | 0.458 | 17 of 24 | 73.6% |
| qwen/qwen3-next-80b-a3b-instruct | 24 | 0.431 | 0.486 | 0.486 | 0.500 | 20 of 24 | 70.8% |
| baseline-rules (keyword baseline) | 24 | 0.472 | 0.528 | 0.417 | 0.486 | 22 of 24 | 81.9% |
| **panel mean** | 24 | 0.511 | 0.550 | 0.528 | 0.453 | 72.2% | 76.3% |

Task success per phrasing. Spread: for each request, the highest minus the lowest task success among its three phrasings, then the mean over requests. A request flips when it is solved (more than half the samples right) in one phrasing and not in another. Sampling noise alone gives a spread above 0: the last column is the share of single phrasings whose own samples do not all agree, the noise the spread has to be read against.
