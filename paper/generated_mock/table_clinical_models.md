> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Clinical tier: task success when the number in the variant name is already the author number, and when a mapping is needed**

| model | MVS: name number is right | MVS: mapping needed | MVS + pack: name number is right | MVS + pack: mapping needed | API: name number is right | API: mapping needed |
|:---|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 0.588 | 0.570 | 0.569 | 0.561 | 0.569 | 0.614 |
| openai/gpt-5.4-nano | 0.539 | 0.535 | 0.520 | 0.535 | 0.637 | 0.544 |
| google/gemma-3-27b-it | 0.588 | 0.500 | 0.588 | 0.570 | 0.588 | 0.675 |
| anthropic/claude-opus-5.5 | 0.569 | 0.500 | 0.588 | 0.465 | 0.588 | 0.667 |
| x-ai/grok-4.7 | 0.588 | 0.561 | 0.539 | 0.456 | 0.549 | 0.526 |
| z-ai/glm-5.2 | 0.520 | 0.526 | 0.441 | 0.596 | 0.569 | 0.649 |
| minimax/minimax-m3 | 0.480 | 0.526 | 0.510 | 0.561 | 0.549 | 0.579 |
| nvidia/nemotron-3-super-120b-a12b | 0.569 | 0.518 | 0.627 | 0.500 | 0.569 | 0.570 |
| deepseek/deepseek-v3.2 | 0.490 | 0.535 | 0.529 | 0.456 | 0.618 | 0.588 |
| google/gemini-4-argon | 0.471 | 0.500 | 0.578 | 0.535 | 0.559 | 0.632 |
| deepseek/deepseek-v4-pro-0813 | 0.520 | 0.553 | 0.549 | 0.482 | 0.500 | 0.588 |
| meta-llama/llama-4-maverick | 0.500 | 0.579 | 0.569 | 0.614 | 0.637 | 0.482 |
| openai/gpt-oss-20b | 0.549 | 0.518 | 0.461 | 0.465 | 0.569 | 0.605 |
| qwen/qwen3-30b-a3b-instruct-2507 | 0.539 | 0.544 | 0.598 | 0.491 | 0.647 | 0.570 |
| deepseek/deepseek-v4-flash | 0.490 | 0.509 | 0.529 | 0.544 | 0.627 | 0.509 |
| google/gemini-3.5-flash | 0.608 | 0.518 | 0.510 | 0.544 | 0.578 | 0.509 |
| openai/gpt-oss-120b | 0.480 | 0.474 | 0.569 | 0.482 | 0.588 | 0.623 |
| claude-haiku-4-5 | 0.520 | 0.561 | 0.608 | 0.491 | 0.520 | 0.614 |
| openai/gpt-6.1-sol | 0.471 | 0.596 | 0.627 | 0.561 | 0.647 | 0.491 |
| qwen/qwen3-next-80b-a3b-instruct | 0.608 | 0.632 | 0.569 | 0.605 | 0.529 | 0.614 |
| mistralai/mistral-small-2603 | 0.510 | 0.509 | 0.578 | 0.456 | 0.618 | 0.509 |
| baseline-rules (keyword baseline) | 0.549 | 0.509 | 0.500 | 0.553 | 0.598 | 0.632 |

Helix / strand context tasks left out.
