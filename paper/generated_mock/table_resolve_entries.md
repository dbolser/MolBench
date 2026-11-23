> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Resolve tier: which entry the answer loads (share of samples)**

| model | condition | samples | an accepted entry | a real entry of something else | an id that does not exist | not a PDB entry | no entry loaded | task success | success on the reference entry (samples) | success on another accepted entry (samples) |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | spec | 117 | 64.1% | 9.4% | 6.0% | 0.0% | 20.5% | 0.556 | 0.867 (75) | – |
| openai/gpt-5.4-nano | spec | 117 | 65.0% | 12.8% | 5.1% | 0.0% | 17.1% | 0.547 | 0.842 (76) | – |
| google/gemma-3-27b-it | spec | 117 | 64.1% | 9.4% | 11.1% | 0.0% | 15.4% | 0.530 | 0.827 (75) | – |
| anthropic/claude-opus-5.5 | spec | 117 | 65.0% | 6.0% | 9.4% | 0.0% | 19.7% | 0.547 | 0.842 (76) | – |
| x-ai/grok-4.7 | spec | 117 | 65.0% | 8.5% | 7.7% | 0.0% | 18.8% | 0.521 | 0.803 (76) | – |
| z-ai/glm-5.2 | spec | 117 | 61.5% | 12.0% | 6.8% | 0.0% | 19.7% | 0.530 | 0.861 (72) | – |
| minimax/minimax-m3 | spec | 117 | 71.8% | 5.1% | 3.4% | 0.0% | 19.7% | 0.607 | 0.845 (84) | – |
| nvidia/nemotron-3-super-120b-a12b | spec | 117 | 70.1% | 7.7% | 7.7% | 0.0% | 14.5% | 0.598 | 0.854 (82) | – |
| deepseek/deepseek-v3.2 | spec | 117 | 69.2% | 6.0% | 7.7% | 0.0% | 17.1% | 0.590 | 0.852 (81) | – |
| google/gemini-4-argon | spec | 117 | 61.5% | 8.5% | 8.5% | 0.0% | 21.4% | 0.530 | 0.861 (72) | – |
| deepseek/deepseek-v4-pro-0813 | spec | 117 | 63.2% | 7.7% | 12.8% | 0.0% | 16.2% | 0.530 | 0.838 (74) | – |
| meta-llama/llama-4-maverick | spec | 117 | 76.1% | 6.8% | 6.0% | 0.0% | 11.1% | 0.607 | 0.798 (89) | – |
| openai/gpt-oss-20b | spec | 117 | 66.7% | 7.7% | 8.5% | 0.0% | 17.1% | 0.564 | 0.846 (78) | – |
| qwen/qwen3-30b-a3b-instruct-2507 | spec | 117 | 65.0% | 9.4% | 6.8% | 0.0% | 18.8% | 0.504 | 0.776 (76) | – |
| deepseek/deepseek-v4-flash | spec | 117 | 57.3% | 6.8% | 11.1% | 0.0% | 24.8% | 0.479 | 0.836 (67) | – |
| google/gemini-3.5-flash | spec | 117 | 65.8% | 9.4% | 5.1% | 0.0% | 19.7% | 0.530 | 0.805 (77) | – |
| openai/gpt-oss-120b | spec | 117 | 69.2% | 6.8% | 6.0% | 0.0% | 17.9% | 0.573 | 0.827 (81) | – |
| claude-haiku-4-5 | spec | 117 | 65.0% | 7.7% | 11.1% | 0.0% | 16.2% | 0.556 | 0.855 (76) | – |
| openai/gpt-6.1-sol | spec | 117 | 66.7% | 7.7% | 7.7% | 0.0% | 17.9% | 0.607 | 0.910 (78) | – |
| qwen/qwen3-next-80b-a3b-instruct | spec | 117 | 66.7% | 5.1% | 6.0% | 0.0% | 22.2% | 0.607 | 0.910 (78) | – |
| mistralai/mistral-small-2603 | spec | 117 | 59.0% | 11.1% | 9.4% | 0.0% | 20.5% | 0.462 | 0.783 (69) | – |
| baseline-rules (keyword baseline) | spec | 117 | 62.4% | 10.3% | 10.3% | 0.0% | 17.1% | 0.573 | 0.918 (73) | – |
| baseline-literal (literal baseline) | spec | 117 | 62.4% | 3.4% | 7.7% | 0.0% | 26.5% | 0.530 | 0.849 (73) | – |
| **all models, spec** | spec | 2457 | 65.6% | 8.2% | 7.8% | 0.0% | 18.4% | – | – | – |
| moonshotai/kimi-k2.6 | spec_grounded | 117 | 63.2% | 11.1% | 8.5% | 0.0% | 17.1% | 0.530 | 0.838 (74) | – |
| openai/gpt-5.4-nano | spec_grounded | 117 | 61.5% | 9.4% | 12.0% | 0.0% | 17.1% | 0.530 | 0.861 (72) | – |
| google/gemma-3-27b-it | spec_grounded | 117 | 70.9% | 3.4% | 8.5% | 0.0% | 17.1% | 0.581 | 0.819 (83) | – |
| anthropic/claude-opus-5.5 | spec_grounded | 117 | 56.4% | 8.5% | 8.5% | 0.0% | 26.5% | 0.462 | 0.818 (66) | – |
| x-ai/grok-4.7 | spec_grounded | 117 | 70.9% | 7.7% | 4.3% | 0.0% | 17.1% | 0.615 | 0.867 (83) | – |
| z-ai/glm-5.2 | spec_grounded | 117 | 62.4% | 11.1% | 9.4% | 0.0% | 17.1% | 0.504 | 0.808 (73) | – |
| minimax/minimax-m3 | spec_grounded | 117 | 64.1% | 9.4% | 7.7% | 0.0% | 18.8% | 0.538 | 0.840 (75) | – |
| nvidia/nemotron-3-super-120b-a12b | spec_grounded | 117 | 65.0% | 6.8% | 6.0% | 0.0% | 22.2% | 0.513 | 0.789 (76) | – |
| deepseek/deepseek-v3.2 | spec_grounded | 117 | 68.4% | 6.8% | 6.0% | 0.0% | 18.8% | 0.547 | 0.800 (80) | – |
| google/gemini-4-argon | spec_grounded | 117 | 68.4% | 6.0% | 5.1% | 0.0% | 20.5% | 0.573 | 0.838 (80) | – |
| deepseek/deepseek-v4-pro-0813 | spec_grounded | 117 | 64.1% | 10.3% | 5.1% | 0.0% | 20.5% | 0.564 | 0.880 (75) | – |
| meta-llama/llama-4-maverick | spec_grounded | 117 | 68.4% | 4.3% | 6.0% | 0.0% | 21.4% | 0.607 | 0.887 (80) | – |
| openai/gpt-oss-20b | spec_grounded | 117 | 65.0% | 6.8% | 2.6% | 0.0% | 25.6% | 0.504 | 0.776 (76) | – |
| qwen/qwen3-30b-a3b-instruct-2507 | spec_grounded | 117 | 71.8% | 4.3% | 4.3% | 0.0% | 19.7% | 0.556 | 0.774 (84) | – |
| deepseek/deepseek-v4-flash | spec_grounded | 117 | 70.1% | 6.0% | 3.4% | 0.0% | 20.5% | 0.547 | 0.780 (82) | – |
| google/gemini-3.5-flash | spec_grounded | 117 | 65.8% | 6.8% | 6.8% | 0.0% | 20.5% | 0.513 | 0.779 (77) | – |
| openai/gpt-oss-120b | spec_grounded | 117 | 66.7% | 5.1% | 8.5% | 0.0% | 19.7% | 0.573 | 0.859 (78) | – |
| claude-haiku-4-5 | spec_grounded | 117 | 59.8% | 7.7% | 10.3% | 0.0% | 22.2% | 0.513 | 0.857 (70) | – |
| openai/gpt-6.1-sol | spec_grounded | 117 | 62.4% | 9.4% | 9.4% | 0.0% | 18.8% | 0.521 | 0.836 (73) | – |
| qwen/qwen3-next-80b-a3b-instruct | spec_grounded | 117 | 69.2% | 10.3% | 6.0% | 0.0% | 14.5% | 0.581 | 0.840 (81) | – |
| mistralai/mistral-small-2603 | spec_grounded | 117 | 63.2% | 7.7% | 4.3% | 0.0% | 24.8% | 0.530 | 0.838 (74) | – |
| baseline-rules (keyword baseline) | spec_grounded | 117 | 65.0% | 5.1% | 11.1% | 0.0% | 18.8% | 0.556 | 0.855 (76) | – |
| baseline-literal (literal baseline) | spec_grounded | 117 | 70.1% | 7.7% | 4.3% | 0.0% | 17.9% | 0.598 | 0.854 (82) | – |
| **all models, spec_grounded** | spec_grounded | 2457 | 65.6% | 7.6% | 6.8% | 0.0% | 20.0% | – | – | – |

The request names a protein; many entries are right (the frozen accepted list). A wrong id is either a real entry of something else or an id that no entry has (the list of current PDB ids frozen on 2026-11-13). "No entry loaded" includes answers that could not be read. The last two columns split the answers on an accepted entry: only the reference entry of a task has a frozen atom table, and on any other accepted entry an answer is compared with the reference as written, so a correct selection by chain id fails there. Paraphrases are left out.
