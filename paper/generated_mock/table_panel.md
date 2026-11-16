> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Model panel**

| model | route | weights | price in / out (USD per million tokens) | price read on | conditions run |
|:---|:---|:---|:---|:---|:---|
| moonshotai/kimi-k2.6 | `openrouter:moonshotai/kimi-k2.6` | open | 0.65 / 3.41 | 2026-11-16 | spec, spec_structured, spec_grounded |
| openai/gpt-5.4-nano | `openrouter:openai/gpt-5.4-nano` | closed | 0.2 / 1.25 | 2026-11-16 | spec, spec_structured, spec_grounded |
| google/gemma-3-27b-it | `openrouter:google/gemma-3-27b-it` | open | 0.08 / 0.35 | 2026-11-16 | spec, spec_structured, spec_grounded |
| anthropic/claude-opus-5.5 | `openrouter:anthropic/claude-opus-5.5` | closed | 4.0 / 20.0 | 2026-11-16 | spec, spec_structured, spec_grounded |
| x-ai/grok-4.7 | `openrouter:x-ai/grok-4.7` | closed | 2.0 / 6.0 | 2026-11-16 | spec, spec_structured, spec_grounded |
| z-ai/glm-5.2 | `openrouter:z-ai/glm-5.2` | open | 0.007 / 6.8 | 2026-11-16 | spec, spec_structured, spec_grounded |
| minimax/minimax-m3 | `openrouter:minimax/minimax-m3` | open | 0.3 / 1.2 | 2026-11-16 | spec, spec_structured, spec_grounded |
| nvidia/nemotron-3-super-120b-a12b | `openrouter:nvidia/nemotron-3-super-120b-a12b` | open | 0.075 / 0.4 | 2026-11-16 | spec, spec_structured, spec_grounded |
| deepseek/deepseek-v3.2 | `openrouter:deepseek/deepseek-v3.2` | open | 0.26 / 0.38 | 2026-11-16 | spec, spec_structured, spec_grounded, bare |
| google/gemini-4-argon | `openrouter:google/gemini-4-argon` | closed | 2.0 / 10.0 | 2026-11-16 | spec, spec_structured, spec_grounded |
| deepseek/deepseek-v4-pro-0813 | `openrouter:deepseek/deepseek-v4-pro-0813` | open | 0.111 / 4.44 | 2026-11-16 | spec, spec_structured, spec_grounded |
| meta-llama/llama-4-maverick | `openrouter:meta-llama/llama-4-maverick` | open | 0.35 / 1.0 | 2026-11-16 | spec, spec_structured, spec_grounded |
| openai/gpt-oss-20b | `openrouter:openai/gpt-oss-20b` | open | 0.075 / 0.3 | 2026-11-16 | spec, spec_structured, spec_grounded |
| qwen/qwen3-30b-a3b-instruct-2507 | `openrouter:qwen/qwen3-30b-a3b-instruct-2507` | open | 0.1 / 0.3 | 2026-11-16 | spec, spec_structured, spec_grounded, bare |
| deepseek/deepseek-v4-flash | `openrouter:deepseek/deepseek-v4-flash` | open | 0.09 / 0.18 | 2026-11-16 | spec, spec_structured, spec_grounded |
| google/gemini-3.5-flash | `openrouter:google/gemini-3.5-flash` | closed | 1.5 / 9.0 | 2026-11-16 | spec, spec_structured, spec_grounded |
| openai/gpt-oss-120b | `openrouter:openai/gpt-oss-120b` | open | 0.15 / 0.6 | 2026-11-16 | spec, spec_structured, spec_grounded |
| claude-haiku-4-5 | `anthropic:claude-haiku-4-5` | closed | 1.0 / 5.0 | 2026-11-16 | spec, spec_grounded, bare |
| openai/gpt-6.1-sol | `openrouter:openai/gpt-6.1-sol` | closed | 2.0 / 10.0 | 2026-11-16 | spec, spec_structured, spec_grounded |
| qwen/qwen3-next-80b-a3b-instruct | `openrouter:qwen/qwen3-next-80b-a3b-instruct` | open | 0.09 / 1.1 | 2026-11-16 | spec, spec_structured, spec_grounded |
| mistralai/mistral-small-2603 | `openrouter:mistralai/mistral-small-2603` | open | 0.15 / 0.6 | 2026-11-16 | spec, spec_structured, spec_grounded |
| baseline-rules (keyword baseline) | `baseline` | no model | 0.0 / 0.0 | 2026-11-16 | spec, spec_grounded |

From the run's scorecards (the manifest names each route and price). Reasoning effort sent: provider-default; no temperature is sent.
