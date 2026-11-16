> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**MVS track: what came back (samples, headline condition)**

| model | samples | valid | not JSON | JSON, not a scene | rejected by Mol* | not valid, in all | of those: cut off at the token limit | of those: malformed | mended by JSON repair |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 1134 | 882 | 162 | 40 | 50 | 252 | 95 | 157 | 95 |
| nvidia/nemotron-3-super-120b-a12b | 1134 | 871 | 176 | 39 | 48 | 263 | 82 | 181 | 82 |
| openai/gpt-5.4-nano | 1134 | 881 | 165 | 47 | 41 | 253 | 77 | 176 | 77 |
| z-ai/glm-5.2 | 1134 | 858 | 183 | 41 | 52 | 276 | 92 | 184 | 92 |
| deepseek/deepseek-v3.2 | 1134 | 865 | 187 | 40 | 42 | 269 | 105 | 164 | 105 |
| google/gemini-4-argon | 1134 | 873 | 182 | 39 | 40 | 261 | 79 | 182 | 79 |
| google/gemma-3-27b-it | 1134 | 876 | 171 | 48 | 39 | 258 | 86 | 172 | 86 |
| openai/gpt-oss-120b | 1134 | 870 | 174 | 43 | 47 | 264 | 89 | 175 | 89 |
| meta-llama/llama-4-maverick | 1134 | 861 | 186 | 43 | 44 | 273 | 87 | 186 | 87 |
| qwen/qwen3-30b-a3b-instruct-2507 | 1134 | 870 | 177 | 42 | 45 | 264 | 86 | 178 | 86 |
| minimax/minimax-m3 | 1134 | 874 | 170 | 49 | 41 | 260 | 83 | 177 | 83 |
| anthropic/claude-opus-5.5 | 1134 | 873 | 179 | 43 | 39 | 261 | 93 | 168 | 93 |
| x-ai/grok-4.7 | 1134 | 851 | 199 | 33 | 51 | 283 | 93 | 190 | 93 |
| claude-haiku-4-5 | 1134 | 861 | 173 | 53 | 47 | 273 | 91 | 182 | 91 |
| openai/gpt-6.1-sol | 1134 | 864 | 185 | 41 | 44 | 270 | 89 | 181 | 89 |
| deepseek/deepseek-v4-pro-0813 | 1134 | 852 | 180 | 49 | 53 | 282 | 88 | 194 | 88 |
| deepseek/deepseek-v4-flash | 1134 | 840 | 199 | 46 | 49 | 294 | 95 | 199 | 95 |
| openai/gpt-oss-20b | 1134 | 842 | 194 | 54 | 44 | 292 | 91 | 201 | 91 |
| google/gemini-3.5-flash | 1134 | 854 | 186 | 47 | 47 | 280 | 97 | 183 | 97 |
| mistralai/mistral-small-2603 | 1134 | 845 | 191 | 48 | 50 | 289 | 96 | 193 | 96 |
| qwen/qwen3-next-80b-a3b-instruct | 1134 | 844 | 193 | 43 | 54 | 290 | 88 | 202 | 88 |
| baseline-rules (keyword baseline) | 1134 | 870 | 180 | 44 | 40 | 264 | 80 | 184 | 80 |

A sample is "cut off" when the provider reports that it stopped at the token limit; that says the limit was too low, not that the model cannot write the format. "Not a valid call list" samples are still graded.
