> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Calls, tokens and cost of the run**

| model | calls | input tokens | output tokens | of which reasoning | spec | spec_structured | spec_grounded | bare | total |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 3,933 | 11,770,779 | 813,015 | 0 | $6.96 | $2.32 | $1.14 | – | $10.42 |
| openai/gpt-5.4-nano | 3,933 | 11,923,917 | 811,136 | 0 | $2.26 | $0.76 | $0.38 | – | $3.40 |
| google/gemma-3-27b-it | 3,933 | 12,920,790 | 810,157 | 0 | $0.88 | $0.30 | $0.14 | – | $1.32 |
| anthropic/claude-opus-5.5 | 3,933 | 13,609,435 | 809,702 | 0 | $47.08 | $15.90 | $7.66 | – | $70.63 |
| x-ai/grok-4.7 | 3,933 | 13,609,435 | 813,053 | 0 | $21.47 | $7.22 | $3.40 | – | $32.10 |
| z-ai/glm-5.2 | 3,933 | 11,966,292 | 807,585 | 0 | $3.57 | $1.25 | $0.76 | – | $5.58 |
| minimax/minimax-m3 | 3,933 | 12,535,247 | 813,493 | 0 | $3.16 | $1.06 | $0.51 | – | $4.74 |
| nvidia/nemotron-3-super-120b-a12b | 3,933 | 12,366,207 | 806,256 | 0 | $0.83 | $0.28 | $0.14 | – | $1.25 |
| deepseek/deepseek-v3.2 | 5,208 | 12,959,719 | 1,217,584 | 0 | $2.35 | $0.79 | $0.36 | $0.33 | $3.83 |
| google/gemini-4-argon | 3,933 | 13,609,435 | 799,481 | 0 | $23.49 | $7.88 | $3.84 | – | $35.21 |
| deepseek/deepseek-v4-pro-0813 | 3,933 | 13,609,435 | 804,344 | 0 | $3.32 | $1.13 | $0.64 | – | $5.08 |
| meta-llama/llama-4-maverick | 3,933 | 12,749,180 | 801,351 | 0 | $3.52 | $1.18 | $0.56 | – | $5.26 |
| openai/gpt-oss-20b | 3,933 | 12,216,398 | 795,618 | 0 | $0.77 | $0.26 | $0.12 | – | $1.15 |
| qwen/qwen3-30b-a3b-instruct-2507 | 5,208 | 13,532,537 | 1,226,058 | 0 | $1.02 | $0.34 | $0.16 | $0.20 | $1.72 |
| deepseek/deepseek-v4-flash | 3,933 | 12,309,595 | 795,633 | 0 | $0.84 | $0.28 | $0.13 | – | $1.25 |
| google/gemini-3.5-flash | 3,933 | 12,871,203 | 799,558 | 0 | $17.65 | $5.95 | $2.90 | – | $26.50 |
| openai/gpt-oss-120b | 3,933 | 12,220,101 | 800,438 | 0 | $1.54 | $0.52 | $0.25 | – | $2.31 |
| claude-haiku-4-5 | 4,329 | 11,286,006 | 1,027,173 | 0 | $11.75 | – | $1.91 | $2.76 | $16.42 |
| openai/gpt-6.1-sol | 3,933 | 13,609,435 | 806,743 | 0 | $23.53 | $7.94 | $3.82 | – | $35.29 |
| qwen/qwen3-next-80b-a3b-instruct | 3,933 | 12,186,797 | 794,205 | 0 | $1.29 | $0.44 | $0.24 | – | $1.97 |
| mistralai/mistral-small-2603 | 3,933 | 12,309,595 | 800,858 | 0 | $1.55 | $0.52 | $0.25 | – | $2.33 |
| baseline-rules (keyword baseline) | 3,054 | 9,530,238 | 626,543 | 0 | $0.00 | – | $0.00 | – | $0.00 |

Total $267.77. Cost is what the provider billed for each call where it reports that, otherwise tokens times the manifest price. Reasoning tokens are counted where the provider reports them.
