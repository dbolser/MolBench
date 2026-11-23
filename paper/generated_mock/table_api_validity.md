> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**API track: what came back (samples, headline condition)**

| model | samples | valid | not JSON | not a valid call list | not valid, in all | of those: cut off at the token limit | of those: malformed | mended by JSON repair |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 1248 | 951 | 198 | 99 | 297 | 104 | 193 | 104 |
| openai/gpt-5.4-nano | 1248 | 960 | 197 | 91 | 288 | 99 | 189 | 99 |
| google/gemma-3-27b-it | 1248 | 962 | 175 | 111 | 286 | 80 | 206 | 80 |
| anthropic/claude-opus-5.5 | 1248 | 962 | 178 | 108 | 286 | 91 | 195 | 91 |
| x-ai/grok-4.7 | 1248 | 961 | 203 | 84 | 287 | 97 | 190 | 97 |
| z-ai/glm-5.2 | 1248 | 996 | 177 | 75 | 252 | 79 | 173 | 79 |
| minimax/minimax-m3 | 1248 | 948 | 214 | 86 | 300 | 114 | 186 | 114 |
| nvidia/nemotron-3-super-120b-a12b | 1248 | 955 | 210 | 83 | 293 | 113 | 180 | 113 |
| deepseek/deepseek-v3.2 | 1248 | 975 | 174 | 99 | 273 | 92 | 181 | 92 |
| google/gemini-4-argon | 1248 | 951 | 198 | 99 | 297 | 103 | 194 | 103 |
| deepseek/deepseek-v4-pro-0813 | 1248 | 973 | 189 | 86 | 275 | 99 | 176 | 99 |
| meta-llama/llama-4-maverick | 1248 | 932 | 201 | 115 | 316 | 94 | 222 | 94 |
| openai/gpt-oss-20b | 1248 | 970 | 193 | 85 | 278 | 88 | 190 | 88 |
| qwen/qwen3-30b-a3b-instruct-2507 | 1248 | 946 | 203 | 99 | 302 | 100 | 202 | 100 |
| deepseek/deepseek-v4-flash | 1248 | 954 | 189 | 105 | 294 | 89 | 205 | 89 |
| google/gemini-3.5-flash | 1248 | 944 | 211 | 93 | 304 | 104 | 200 | 104 |
| openai/gpt-oss-120b | 1248 | 954 | 199 | 95 | 294 | 96 | 198 | 96 |
| claude-haiku-4-5 | 1248 | 950 | 201 | 97 | 298 | 111 | 187 | 111 |
| openai/gpt-6.1-sol | 1248 | 917 | 225 | 106 | 331 | 111 | 220 | 111 |
| qwen/qwen3-next-80b-a3b-instruct | 1248 | 927 | 218 | 103 | 321 | 98 | 223 | 98 |
| mistralai/mistral-small-2603 | 1248 | 963 | 197 | 88 | 285 | 95 | 190 | 95 |
| baseline-rules (keyword baseline) | 1248 | 958 | 188 | 102 | 290 | 91 | 199 | 91 |
| baseline-literal (literal baseline) | 1248 | 950 | 210 | 88 | 298 | 117 | 181 | 117 |

A sample is "cut off" when the provider reports that it stopped at the token limit; that says the limit was too low, not that the model cannot write the format. "Not a valid call list" samples are still graded.
