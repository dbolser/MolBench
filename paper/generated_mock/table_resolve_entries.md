> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Resolve tier: which entry the answer loads (share of samples)**

| model | condition | samples | an accepted entry | a real entry of something else | an id that does not exist | not a PDB entry | no entry loaded | task success |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | spec | 117 | 64.1% | 9.4% | 6.0% | 0.0% | 20.5% | 0.556 |
| nvidia/nemotron-3-super-120b-a12b | spec | 117 | 70.1% | 7.7% | 7.7% | 0.0% | 14.5% | 0.598 |
| openai/gpt-5.4-nano | spec | 117 | 65.0% | 12.8% | 5.1% | 0.0% | 17.1% | 0.547 |
| z-ai/glm-5.2 | spec | 117 | 61.5% | 12.0% | 6.8% | 0.0% | 19.7% | 0.530 |
| deepseek/deepseek-v3.2 | spec | 117 | 69.2% | 6.0% | 7.7% | 0.0% | 17.1% | 0.590 |
| google/gemini-4-argon | spec | 117 | 61.5% | 8.5% | 8.5% | 0.0% | 21.4% | 0.530 |
| google/gemma-3-27b-it | spec | 117 | 64.1% | 9.4% | 11.1% | 0.0% | 15.4% | 0.530 |
| openai/gpt-oss-120b | spec | 117 | 69.2% | 6.8% | 6.0% | 0.0% | 17.9% | 0.573 |
| meta-llama/llama-4-maverick | spec | 117 | 76.1% | 6.8% | 6.0% | 0.0% | 11.1% | 0.607 |
| qwen/qwen3-30b-a3b-instruct-2507 | spec | 117 | 65.0% | 9.4% | 6.8% | 0.0% | 18.8% | 0.504 |
| minimax/minimax-m3 | spec | 117 | 71.8% | 5.1% | 3.4% | 0.0% | 19.7% | 0.607 |
| anthropic/claude-opus-5.5 | spec | 117 | 65.0% | 6.0% | 9.4% | 0.0% | 19.7% | 0.547 |
| x-ai/grok-4.7 | spec | 117 | 65.0% | 8.5% | 7.7% | 0.0% | 18.8% | 0.521 |
| claude-haiku-4-5 | spec | 117 | 65.0% | 7.7% | 11.1% | 0.0% | 16.2% | 0.556 |
| openai/gpt-6.1-sol | spec | 117 | 66.7% | 7.7% | 7.7% | 0.0% | 17.9% | 0.607 |
| deepseek/deepseek-v4-pro-0813 | spec | 117 | 63.2% | 7.7% | 12.8% | 0.0% | 16.2% | 0.530 |
| deepseek/deepseek-v4-flash | spec | 117 | 57.3% | 6.8% | 11.1% | 0.0% | 24.8% | 0.479 |
| openai/gpt-oss-20b | spec | 117 | 66.7% | 7.7% | 8.5% | 0.0% | 17.1% | 0.564 |
| google/gemini-3.5-flash | spec | 117 | 65.8% | 9.4% | 5.1% | 0.0% | 19.7% | 0.530 |
| mistralai/mistral-small-2603 | spec | 117 | 59.0% | 11.1% | 9.4% | 0.0% | 20.5% | 0.462 |
| qwen/qwen3-next-80b-a3b-instruct | spec | 117 | 66.7% | 5.1% | 6.0% | 0.0% | 22.2% | 0.607 |
| baseline-rules (keyword baseline) | spec | 117 | 62.4% | 10.3% | 10.3% | 0.0% | 17.1% | 0.573 |
| **all models, spec** | spec | 2457 | 65.6% | 8.2% | 7.8% | 0.0% | 18.4% | – |
| moonshotai/kimi-k2.6 | spec_grounded | 117 | 63.2% | 11.1% | 8.5% | 0.0% | 17.1% | 0.530 |
| nvidia/nemotron-3-super-120b-a12b | spec_grounded | 117 | 65.0% | 6.8% | 6.0% | 0.0% | 22.2% | 0.513 |
| openai/gpt-5.4-nano | spec_grounded | 117 | 61.5% | 9.4% | 12.0% | 0.0% | 17.1% | 0.530 |
| z-ai/glm-5.2 | spec_grounded | 117 | 62.4% | 11.1% | 9.4% | 0.0% | 17.1% | 0.504 |
| deepseek/deepseek-v3.2 | spec_grounded | 117 | 68.4% | 6.8% | 6.0% | 0.0% | 18.8% | 0.547 |
| google/gemini-4-argon | spec_grounded | 117 | 68.4% | 6.0% | 5.1% | 0.0% | 20.5% | 0.573 |
| google/gemma-3-27b-it | spec_grounded | 117 | 70.9% | 3.4% | 8.5% | 0.0% | 17.1% | 0.581 |
| openai/gpt-oss-120b | spec_grounded | 117 | 66.7% | 5.1% | 8.5% | 0.0% | 19.7% | 0.573 |
| meta-llama/llama-4-maverick | spec_grounded | 117 | 68.4% | 4.3% | 6.0% | 0.0% | 21.4% | 0.607 |
| qwen/qwen3-30b-a3b-instruct-2507 | spec_grounded | 117 | 71.8% | 4.3% | 4.3% | 0.0% | 19.7% | 0.556 |
| minimax/minimax-m3 | spec_grounded | 117 | 64.1% | 9.4% | 7.7% | 0.0% | 18.8% | 0.538 |
| anthropic/claude-opus-5.5 | spec_grounded | 117 | 56.4% | 8.5% | 8.5% | 0.0% | 26.5% | 0.462 |
| x-ai/grok-4.7 | spec_grounded | 117 | 70.9% | 7.7% | 4.3% | 0.0% | 17.1% | 0.615 |
| claude-haiku-4-5 | spec_grounded | 117 | 59.8% | 7.7% | 10.3% | 0.0% | 22.2% | 0.513 |
| openai/gpt-6.1-sol | spec_grounded | 117 | 62.4% | 9.4% | 9.4% | 0.0% | 18.8% | 0.521 |
| deepseek/deepseek-v4-pro-0813 | spec_grounded | 117 | 64.1% | 10.3% | 5.1% | 0.0% | 20.5% | 0.564 |
| deepseek/deepseek-v4-flash | spec_grounded | 117 | 70.1% | 6.0% | 3.4% | 0.0% | 20.5% | 0.547 |
| openai/gpt-oss-20b | spec_grounded | 117 | 65.0% | 6.8% | 2.6% | 0.0% | 25.6% | 0.504 |
| google/gemini-3.5-flash | spec_grounded | 117 | 65.8% | 6.8% | 6.8% | 0.0% | 20.5% | 0.513 |
| mistralai/mistral-small-2603 | spec_grounded | 117 | 63.2% | 7.7% | 4.3% | 0.0% | 24.8% | 0.530 |
| qwen/qwen3-next-80b-a3b-instruct | spec_grounded | 117 | 69.2% | 10.3% | 6.0% | 0.0% | 14.5% | 0.581 |
| baseline-rules (keyword baseline) | spec_grounded | 117 | 65.0% | 5.1% | 11.1% | 0.0% | 18.8% | 0.556 |
| **all models, spec_grounded** | spec_grounded | 2457 | 65.6% | 7.6% | 6.8% | 0.0% | 20.0% | – |

The request names a protein; many entries are right (the frozen accepted list). A wrong id is either a real entry of something else or an id that no entry has (the list of current PDB ids frozen on 2026-11-13). "No entry loaded" includes answers that could not be read. Paraphrases are left out.
