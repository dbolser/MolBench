**What happened to each output, `spec` condition (PRELIMINARY).** Every output falls into exactly one class. *Valid scene*: parses as JSON, Mol\* accepts it as MolViewSpec and loads the structure. *Invalid JSON*: no parsable JSON object. *JSON, not a scene*: valid JSON that is not a MolViewSpec tree. *Scene rejected by Mol\**: a tree with a wrong node or parameter. *Structure failed to load*: the scene is well formed but names a file that does not load. All classes except the first score 0.

| Model | valid scene | invalid JSON | scene rejected by Mol* | structure failed to load |
| :--- | ---: | ---: | ---: | ---: |
| deepseek-v3.2 | 69 | 0 | 0 | 1 |
| claude-haiku-4-5 | 67 | 0 | 3 | 0 |
| gemini-3.5-flash | 66 | 4 | 0 | 0 |
| deepseek-v4-flash | 65 | 4 | 1 | 0 |
| qwen3-next-80b-a3b-instruct | 64 | 3 | 3 | 0 |
| minimax-m3 | 63 | 5 | 2 | 0 |
| glm-5.2 | 63 | 5 | 1 | 1 |
| gemma-3-27b-it | 57 | 4 | 9 | 0 |
| llama-4-maverick | 57 | 1 | 11 | 1 |
| gpt-5.4-nano | 53 | 15 | 2 | 0 |
| kimi-k2.6 | 51 | 18 | 1 | 0 |
| gpt-oss-120b | 44 | 26 | 0 | 0 |
| qwen3-30b-a3b-instruct-2507 | 39 | 28 | 3 | 0 |
| gpt-oss-20b | 20 | 50 | 0 | 0 |
| nemotron-3-super-120b-a12b | 6 | 64 | 0 | 0 |
| **All models** | 784 | 227 | 36 | 3 |
