> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Clinical tier: task success when the number in the variant name is already the author number, and when a mapping is needed**

| model | MVS: name number is right | MVS: mapping needed | MVS + pack: name number is right | MVS + pack: mapping needed | API: name number is right | API: mapping needed |
|:---|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 0.529 | 0.552 | 0.578 | 0.533 | 0.608 | 0.667 |
| nvidia/nemotron-3-super-120b-a12b | 0.569 | 0.600 | 0.549 | 0.543 | 0.608 | 0.629 |
| openai/gpt-5.4-nano | 0.549 | 0.486 | 0.549 | 0.581 | 0.647 | 0.543 |
| z-ai/glm-5.2 | 0.510 | 0.571 | 0.539 | 0.657 | 0.578 | 0.600 |
| deepseek/deepseek-v3.2 | 0.422 | 0.571 | 0.500 | 0.448 | 0.608 | 0.619 |
| google/gemini-4-argon | 0.490 | 0.495 | 0.559 | 0.571 | 0.529 | 0.543 |
| google/gemma-3-27b-it | 0.588 | 0.429 | 0.500 | 0.533 | 0.598 | 0.657 |
| openai/gpt-oss-120b | 0.559 | 0.533 | 0.559 | 0.552 | 0.598 | 0.638 |
| meta-llama/llama-4-maverick | 0.500 | 0.619 | 0.559 | 0.610 | 0.618 | 0.514 |
| qwen/qwen3-30b-a3b-instruct-2507 | 0.520 | 0.524 | 0.588 | 0.543 | 0.549 | 0.638 |
| minimax/minimax-m3 | 0.559 | 0.524 | 0.559 | 0.533 | 0.539 | 0.514 |
| anthropic/claude-opus-5.5 | 0.569 | 0.448 | 0.549 | 0.476 | 0.608 | 0.514 |
| x-ai/grok-4.7 | 0.520 | 0.581 | 0.539 | 0.533 | 0.529 | 0.505 |
| claude-haiku-4-5 | 0.510 | 0.543 | 0.569 | 0.495 | 0.500 | 0.600 |
| openai/gpt-6.1-sol | 0.490 | 0.638 | 0.647 | 0.438 | 0.627 | 0.543 |
| deepseek/deepseek-v4-pro-0813 | 0.559 | 0.571 | 0.578 | 0.457 | 0.480 | 0.562 |
| deepseek/deepseek-v4-flash | 0.451 | 0.457 | 0.510 | 0.448 | 0.627 | 0.495 |
| openai/gpt-oss-20b | 0.490 | 0.429 | 0.490 | 0.476 | 0.559 | 0.562 |
| google/gemini-3.5-flash | 0.569 | 0.505 | 0.490 | 0.467 | 0.539 | 0.543 |
| mistralai/mistral-small-2603 | 0.569 | 0.562 | 0.490 | 0.429 | 0.608 | 0.552 |
| qwen/qwen3-next-80b-a3b-instruct | 0.539 | 0.600 | 0.520 | 0.610 | 0.569 | 0.638 |
| baseline-rules (keyword baseline) | 0.578 | 0.533 | 0.539 | 0.543 | 0.588 | 0.619 |

Helix / strand context tasks left out.
