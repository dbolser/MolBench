> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**MVS track: sensitivity to wording (22 requests, three phrasings each)**

| model | requests | full | terse | indirect | mean spread per request | requests where the outcome flips | phrasings whose own samples disagree |
|:---|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 22 | 0.636 | 0.545 | 0.652 | 0.455 | 14 of 22 | 72.7% |
| openai/gpt-5.4-nano | 22 | 0.591 | 0.576 | 0.530 | 0.379 | 14 of 22 | 81.8% |
| google/gemma-3-27b-it | 22 | 0.545 | 0.545 | 0.545 | 0.409 | 15 of 22 | 81.8% |
| anthropic/claude-opus-5.5 | 22 | 0.576 | 0.545 | 0.561 | 0.409 | 16 of 22 | 83.3% |
| x-ai/grok-4.7 | 22 | 0.485 | 0.606 | 0.591 | 0.424 | 14 of 22 | 72.7% |
| z-ai/glm-5.2 | 22 | 0.455 | 0.561 | 0.515 | 0.439 | 18 of 22 | 80.3% |
| minimax/minimax-m3 | 22 | 0.485 | 0.591 | 0.515 | 0.500 | 16 of 22 | 72.7% |
| nvidia/nemotron-3-super-120b-a12b | 22 | 0.576 | 0.652 | 0.409 | 0.470 | 19 of 22 | 80.3% |
| deepseek/deepseek-v3.2 | 22 | 0.561 | 0.561 | 0.576 | 0.500 | 16 of 22 | 72.7% |
| google/gemini-4-argon | 22 | 0.530 | 0.561 | 0.485 | 0.439 | 19 of 22 | 83.3% |
| deepseek/deepseek-v4-pro-0813 | 22 | 0.485 | 0.530 | 0.424 | 0.530 | 19 of 22 | 72.7% |
| meta-llama/llama-4-maverick | 22 | 0.652 | 0.606 | 0.545 | 0.439 | 15 of 22 | 69.7% |
| openai/gpt-oss-20b | 22 | 0.455 | 0.576 | 0.591 | 0.470 | 16 of 22 | 77.3% |
| qwen/qwen3-30b-a3b-instruct-2507 | 22 | 0.500 | 0.409 | 0.530 | 0.500 | 14 of 22 | 65.2% |
| deepseek/deepseek-v4-flash | 22 | 0.485 | 0.576 | 0.515 | 0.561 | 16 of 22 | 65.2% |
| google/gemini-3.5-flash | 22 | 0.606 | 0.530 | 0.455 | 0.409 | 13 of 22 | 77.3% |
| openai/gpt-oss-120b | 22 | 0.530 | 0.530 | 0.394 | 0.424 | 16 of 22 | 78.8% |
| claude-haiku-4-5 | 22 | 0.515 | 0.545 | 0.485 | 0.409 | 16 of 22 | 83.3% |
| openai/gpt-6.1-sol | 22 | 0.515 | 0.515 | 0.545 | 0.394 | 14 of 22 | 78.8% |
| qwen/qwen3-next-80b-a3b-instruct | 22 | 0.485 | 0.485 | 0.455 | 0.470 | 19 of 22 | 77.3% |
| mistralai/mistral-small-2603 | 22 | 0.606 | 0.500 | 0.636 | 0.455 | 16 of 22 | 74.2% |
| baseline-rules (keyword baseline) | 22 | 0.545 | 0.530 | 0.455 | 0.439 | 18 of 22 | 83.3% |
| **panel mean** | 22 | 0.537 | 0.550 | 0.522 | 0.452 | 72.5% | 76.3% |

Task success per phrasing. Spread: for each request, the highest minus the lowest task success among its three phrasings, then the mean over requests. A request flips when it is solved (more than half the samples right) in one phrasing and not in another. Sampling noise alone gives a spread above 0: the last column is the share of single phrasings whose own samples do not all agree, the noise the spread has to be read against.
