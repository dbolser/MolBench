> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Calls, tokens and cost of the run**

| model | calls | input tokens | output tokens | of which reasoning | spec | spec_structured | spec_grounded | bare | total |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 3,933 | 12,367,070 | 813,015 | 0 | $7.21 | $2.40 | $1.20 | – | $10.81 |
| openai/gpt-5.4-nano | 3,933 | 12,527,803 | 811,136 | 0 | $2.34 | $0.79 | $0.40 | – | $3.52 |
| google/gemma-3-27b-it | 3,933 | 13,575,139 | 810,157 | 0 | $0.91 | $0.31 | $0.15 | – | $1.37 |
| anthropic/claude-opus-5.5 | 3,933 | 14,298,848 | 809,702 | 0 | $48.82 | $16.48 | $8.08 | – | $73.39 |
| x-ai/grok-4.7 | 3,933 | 14,298,848 | 813,053 | 0 | $22.34 | $7.52 | $3.62 | – | $33.48 |
| z-ai/glm-5.2 | 3,933 | 12,572,440 | 807,585 | 0 | $3.57 | $1.25 | $0.76 | – | $5.58 |
| minimax/minimax-m3 | 3,933 | 13,170,204 | 813,493 | 0 | $3.28 | $1.10 | $0.54 | – | $4.93 |
| nvidia/nemotron-3-super-120b-a12b | 3,933 | 12,992,565 | 806,256 | 0 | $0.86 | $0.29 | $0.15 | – | $1.30 |
| deepseek/deepseek-v3.2 | 5,208 | 13,581,855 | 1,217,584 | 0 | $2.45 | $0.82 | $0.39 | $0.33 | $3.99 |
| google/gemini-4-argon | 3,933 | 14,298,848 | 799,481 | 0 | $24.36 | $8.18 | $4.05 | – | $36.59 |
| deepseek/deepseek-v4-pro-0813 | 3,933 | 14,298,848 | 804,344 | 0 | $3.37 | $1.14 | $0.65 | – | $5.16 |
| meta-llama/llama-4-maverick | 3,933 | 13,395,007 | 801,351 | 0 | $3.66 | $1.23 | $0.60 | – | $5.49 |
| openai/gpt-oss-20b | 3,933 | 12,835,131 | 795,618 | 0 | $0.80 | $0.27 | $0.13 | – | $1.20 |
| qwen/qwen3-30b-a3b-instruct-2507 | 5,208 | 14,182,259 | 1,226,058 | 0 | $1.06 | $0.36 | $0.17 | $0.20 | $1.79 |
| deepseek/deepseek-v4-flash | 3,933 | 12,933,144 | 795,633 | 0 | $0.87 | $0.29 | $0.14 | – | $1.31 |
| google/gemini-3.5-flash | 3,933 | 13,523,224 | 799,558 | 0 | $18.27 | $6.16 | $3.05 | – | $27.48 |
| openai/gpt-oss-120b | 3,933 | 12,839,006 | 800,438 | 0 | $1.60 | $0.54 | $0.27 | – | $2.41 |
| claude-haiku-4-5 | 4,329 | 11,829,816 | 1,027,173 | 0 | $12.19 | – | $2.02 | $2.76 | $16.97 |
| openai/gpt-6.1-sol | 3,933 | 14,298,848 | 806,743 | 0 | $24.40 | $8.23 | $4.03 | – | $36.67 |
| qwen/qwen3-next-80b-a3b-instruct | 3,933 | 12,804,122 | 794,205 | 0 | $1.33 | $0.45 | $0.24 | – | $2.03 |
| mistralai/mistral-small-2603 | 3,933 | 12,933,144 | 800,858 | 0 | $1.61 | $0.54 | $0.26 | – | $2.42 |
| baseline-rules (keyword baseline) | 3,054 | 10,022,082 | 626,543 | 0 | $0.00 | – | $0.00 | – | $0.00 |
| baseline-literal (literal baseline) | 3,054 | 10,022,082 | 627,397 | 0 | $0.00 | – | $0.00 | – | $0.00 |

Total $277.86. Cost is what the provider billed for each call where it reports that, otherwise tokens times the manifest price. Reasoning tokens are counted where the provider reports them.
