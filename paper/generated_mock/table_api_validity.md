> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**API track: what came back (samples, headline condition)**

| model | samples | valid | not JSON | not a valid call list | not valid, in all | of those: cut off at the token limit | of those: malformed | mended by JSON repair |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 1209 | 919 | 194 | 96 | 290 | 102 | 188 | 102 |
| nvidia/nemotron-3-super-120b-a12b | 1209 | 943 | 192 | 74 | 266 | 100 | 166 | 100 |
| openai/gpt-5.4-nano | 1209 | 929 | 190 | 90 | 280 | 91 | 189 | 91 |
| z-ai/glm-5.2 | 1209 | 954 | 173 | 82 | 255 | 79 | 176 | 79 |
| deepseek/deepseek-v3.2 | 1209 | 946 | 166 | 97 | 263 | 90 | 173 | 90 |
| google/gemini-4-argon | 1209 | 917 | 198 | 94 | 292 | 104 | 188 | 104 |
| google/gemma-3-27b-it | 1209 | 917 | 182 | 110 | 292 | 87 | 205 | 87 |
| openai/gpt-oss-120b | 1209 | 930 | 202 | 77 | 279 | 92 | 187 | 92 |
| meta-llama/llama-4-maverick | 1209 | 916 | 184 | 109 | 293 | 87 | 206 | 87 |
| qwen/qwen3-30b-a3b-instruct-2507 | 1209 | 908 | 203 | 98 | 301 | 100 | 201 | 100 |
| minimax/minimax-m3 | 1209 | 915 | 209 | 85 | 294 | 104 | 190 | 104 |
| anthropic/claude-opus-5.5 | 1209 | 930 | 178 | 101 | 279 | 89 | 190 | 89 |
| x-ai/grok-4.7 | 1209 | 930 | 203 | 76 | 279 | 92 | 187 | 92 |
| claude-haiku-4-5 | 1209 | 917 | 194 | 98 | 292 | 108 | 184 | 108 |
| openai/gpt-6.1-sol | 1209 | 906 | 208 | 95 | 303 | 101 | 202 | 101 |
| deepseek/deepseek-v4-pro-0813 | 1209 | 929 | 190 | 90 | 280 | 92 | 188 | 92 |
| deepseek/deepseek-v4-flash | 1209 | 914 | 191 | 104 | 295 | 85 | 210 | 85 |
| openai/gpt-oss-20b | 1209 | 914 | 200 | 95 | 295 | 95 | 200 | 95 |
| google/gemini-3.5-flash | 1209 | 920 | 204 | 85 | 289 | 98 | 191 | 98 |
| mistralai/mistral-small-2603 | 1209 | 914 | 202 | 93 | 295 | 95 | 200 | 95 |
| qwen/qwen3-next-80b-a3b-instruct | 1209 | 896 | 213 | 100 | 313 | 90 | 223 | 90 |
| baseline-rules (keyword baseline) | 1209 | 928 | 185 | 96 | 281 | 90 | 191 | 90 |

A sample is "cut off" when the provider reports that it stopped at the token limit; that says the limit was too low, not that the model cannot write the format. "Not a valid call list" samples are still graded.
