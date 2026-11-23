> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**MVS track: what came back (samples, headline condition)**

| model | samples | valid | not JSON | JSON, not a scene | rejected by Mol* | not valid, in all | of those: cut off at the token limit | of those: malformed | mended by JSON repair |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 1143 | 889 | 168 | 37 | 49 | 254 | 92 | 162 | 92 |
| openai/gpt-5.4-nano | 1143 | 888 | 169 | 45 | 41 | 255 | 74 | 181 | 74 |
| google/gemma-3-27b-it | 1143 | 877 | 168 | 54 | 44 | 266 | 81 | 185 | 81 |
| anthropic/claude-opus-5.5 | 1143 | 892 | 174 | 42 | 35 | 251 | 87 | 164 | 87 |
| x-ai/grok-4.7 | 1143 | 881 | 180 | 30 | 52 | 262 | 87 | 175 | 87 |
| z-ai/glm-5.2 | 1143 | 851 | 197 | 42 | 53 | 292 | 104 | 188 | 104 |
| minimax/minimax-m3 | 1143 | 891 | 166 | 41 | 45 | 252 | 82 | 170 | 82 |
| nvidia/nemotron-3-super-120b-a12b | 1143 | 878 | 183 | 37 | 45 | 265 | 88 | 177 | 88 |
| deepseek/deepseek-v3.2 | 1143 | 875 | 184 | 43 | 41 | 268 | 107 | 161 | 107 |
| google/gemini-4-argon | 1143 | 872 | 193 | 42 | 36 | 271 | 83 | 188 | 83 |
| deepseek/deepseek-v4-pro-0813 | 1143 | 863 | 179 | 44 | 57 | 280 | 86 | 194 | 86 |
| meta-llama/llama-4-maverick | 1143 | 870 | 185 | 46 | 42 | 273 | 94 | 179 | 94 |
| openai/gpt-oss-20b | 1143 | 846 | 194 | 50 | 53 | 297 | 90 | 207 | 90 |
| qwen/qwen3-30b-a3b-instruct-2507 | 1143 | 872 | 180 | 40 | 51 | 271 | 93 | 178 | 93 |
| deepseek/deepseek-v4-flash | 1143 | 860 | 198 | 43 | 42 | 283 | 96 | 187 | 96 |
| google/gemini-3.5-flash | 1143 | 880 | 174 | 45 | 44 | 263 | 95 | 168 | 95 |
| openai/gpt-oss-120b | 1143 | 866 | 183 | 48 | 46 | 277 | 92 | 185 | 92 |
| claude-haiku-4-5 | 1143 | 860 | 178 | 54 | 51 | 283 | 93 | 190 | 93 |
| openai/gpt-6.1-sol | 1143 | 871 | 189 | 38 | 45 | 272 | 98 | 174 | 98 |
| qwen/qwen3-next-80b-a3b-instruct | 1143 | 859 | 182 | 50 | 52 | 284 | 83 | 201 | 83 |
| mistralai/mistral-small-2603 | 1143 | 849 | 184 | 52 | 58 | 294 | 87 | 207 | 87 |
| baseline-rules (keyword baseline) | 1143 | 874 | 173 | 50 | 46 | 269 | 78 | 191 | 78 |
| baseline-literal (literal baseline) | 1143 | 873 | 189 | 47 | 34 | 270 | 100 | 170 | 100 |

A sample is "cut off" when the provider reports that it stopped at the token limit; that says the limit was too low, not that the model cannot write the format. "Not a valid call list" samples are still graded.
