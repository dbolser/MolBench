> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**API track: sensitivity to wording (19 requests, three phrasings each)**

| model | requests | full | terse | indirect | mean spread per request | requests where the outcome flips | phrasings whose own samples disagree |
|:---|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 19 | 0.702 | 0.632 | 0.684 | 0.456 | 9 of 19 | 66.7% |
| openai/gpt-5.4-nano | 19 | 0.614 | 0.632 | 0.491 | 0.509 | 15 of 19 | 71.9% |
| google/gemma-3-27b-it | 19 | 0.526 | 0.526 | 0.544 | 0.368 | 14 of 19 | 87.7% |
| anthropic/claude-opus-5.5 | 19 | 0.544 | 0.596 | 0.561 | 0.474 | 13 of 19 | 75.4% |
| x-ai/grok-4.7 | 19 | 0.614 | 0.614 | 0.649 | 0.544 | 13 of 19 | 64.9% |
| z-ai/glm-5.2 | 19 | 0.614 | 0.544 | 0.649 | 0.456 | 14 of 19 | 66.7% |
| minimax/minimax-m3 | 19 | 0.614 | 0.456 | 0.667 | 0.456 | 15 of 19 | 77.2% |
| nvidia/nemotron-3-super-120b-a12b | 19 | 0.649 | 0.561 | 0.614 | 0.386 | 11 of 19 | 80.7% |
| deepseek/deepseek-v3.2 | 19 | 0.667 | 0.509 | 0.544 | 0.386 | 14 of 19 | 86.0% |
| google/gemini-4-argon | 19 | 0.561 | 0.632 | 0.456 | 0.439 | 13 of 19 | 75.4% |
| deepseek/deepseek-v4-pro-0813 | 19 | 0.614 | 0.614 | 0.561 | 0.404 | 15 of 19 | 82.5% |
| meta-llama/llama-4-maverick | 19 | 0.544 | 0.491 | 0.561 | 0.456 | 13 of 19 | 70.2% |
| openai/gpt-oss-20b | 19 | 0.596 | 0.579 | 0.544 | 0.386 | 13 of 19 | 82.5% |
| qwen/qwen3-30b-a3b-instruct-2507 | 19 | 0.421 | 0.509 | 0.474 | 0.439 | 13 of 19 | 71.9% |
| deepseek/deepseek-v4-flash | 19 | 0.509 | 0.561 | 0.596 | 0.456 | 13 of 19 | 70.2% |
| google/gemini-3.5-flash | 19 | 0.579 | 0.649 | 0.526 | 0.351 | 11 of 19 | 82.5% |
| openai/gpt-oss-120b | 19 | 0.561 | 0.544 | 0.596 | 0.474 | 16 of 19 | 75.4% |
| claude-haiku-4-5 | 19 | 0.544 | 0.632 | 0.579 | 0.421 | 13 of 19 | 80.7% |
| openai/gpt-6.1-sol | 19 | 0.526 | 0.649 | 0.526 | 0.561 | 15 of 19 | 57.9% |
| qwen/qwen3-next-80b-a3b-instruct | 19 | 0.579 | 0.579 | 0.667 | 0.456 | 14 of 19 | 71.9% |
| mistralai/mistral-small-2603 | 19 | 0.649 | 0.579 | 0.544 | 0.491 | 14 of 19 | 73.7% |
| baseline-rules (keyword baseline) | 19 | 0.596 | 0.596 | 0.632 | 0.474 | 14 of 19 | 68.4% |
| **panel mean** | 19 | 0.582 | 0.576 | 0.573 | 0.446 | 70.4% | 74.9% |

Task success per phrasing. Spread: for each request, the highest minus the lowest task success among its three phrasings, then the mean over requests. A request flips when it is solved (more than half the samples right) in one phrasing and not in another. Sampling noise alone gives a spread above 0: the last column is the share of single phrasings whose own samples do not all agree, the noise the spread has to be read against.
