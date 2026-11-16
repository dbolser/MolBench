> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Calls, tokens and cost of the run**

| model | calls | input tokens | output tokens | of which reasoning | spec | spec_structured | spec_grounded | bare | total |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 3,878 | 11,255,419 | 820,931 | 0 | $6.78 | $2.25 | $1.08 | – | $10.12 |
| nvidia/nemotron-3-super-120b-a12b | 3,878 | 11,824,750 | 812,563 | 0 | $0.81 | $0.27 | $0.13 | – | $1.21 |
| openai/gpt-5.4-nano | 3,878 | 11,401,803 | 817,431 | 0 | $2.20 | $0.74 | $0.36 | – | $3.30 |
| z-ai/glm-5.2 | 3,878 | 11,442,459 | 817,818 | 0 | $3.62 | $1.27 | $0.76 | – | $5.64 |
| deepseek/deepseek-v3.2 | 5,156 | 12,322,391 | 1,228,021 | 0 | $2.26 | $0.76 | $0.34 | $0.31 | $3.67 |
| google/gemini-4-argon | 3,878 | 13,013,592 | 810,280 | 0 | $22.85 | $7.65 | $3.64 | – | $34.13 |
| google/gemma-3-27b-it | 3,878 | 12,354,988 | 813,716 | 0 | $0.85 | $0.29 | $0.13 | – | $1.27 |
| openai/gpt-oss-120b | 3,878 | 11,685,115 | 810,935 | 0 | $1.50 | $0.51 | $0.24 | – | $2.24 |
| meta-llama/llama-4-maverick | 3,878 | 12,191,013 | 804,320 | 0 | $3.40 | $1.14 | $0.53 | – | $5.07 |
| qwen/qwen3-30b-a3b-instruct-2507 | 5,156 | 12,866,932 | 1,231,191 | 0 | $0.99 | $0.33 | $0.15 | $0.19 | $1.66 |
| minimax/minimax-m3 | 3,878 | 11,986,428 | 811,966 | 0 | $3.06 | $1.03 | $0.48 | – | $4.57 |
| anthropic/claude-opus-5.5 | 3,878 | 13,013,592 | 812,869 | 0 | $45.64 | $15.45 | $7.22 | – | $68.31 |
| x-ai/grok-4.7 | 3,878 | 13,013,592 | 811,657 | 0 | $20.71 | $6.98 | $3.21 | – | $30.90 |
| claude-haiku-4-5 | 4,287 | 10,705,728 | 1,034,093 | 0 | $11.41 | – | $1.81 | $2.66 | $15.88 |
| openai/gpt-6.1-sol | 3,878 | 13,013,592 | 810,592 | 0 | $22.82 | $7.72 | $3.60 | – | $34.13 |
| deepseek/deepseek-v4-pro-0813 | 3,878 | 13,013,592 | 806,115 | 0 | $3.29 | $1.12 | $0.61 | – | $5.02 |
| deepseek/deepseek-v4-flash | 3,878 | 11,770,587 | 797,045 | 0 | $0.81 | $0.27 | $0.12 | – | $1.20 |
| openai/gpt-oss-20b | 3,878 | 11,681,513 | 798,778 | 0 | $0.75 | $0.25 | $0.12 | – | $1.12 |
| google/gemini-3.5-flash | 3,878 | 12,307,743 | 799,640 | 0 | $17.14 | $5.79 | $2.74 | – | $25.66 |
| mistralai/mistral-small-2603 | 3,878 | 11,770,587 | 809,252 | 0 | $1.51 | $0.51 | $0.24 | – | $2.25 |
| qwen/qwen3-next-80b-a3b-instruct | 3,878 | 11,653,287 | 797,738 | 0 | $1.27 | $0.43 | $0.22 | – | $1.93 |
| baseline-rules (keyword baseline) | 3,009 | 9,105,117 | 626,174 | 0 | $0.00 | – | $0.00 | – | $0.00 |

Total $259.28. Cost is what the provider billed for each call where it reports that, otherwise tokens times the manifest price. Reasoning tokens are counted where the provider reports them.
