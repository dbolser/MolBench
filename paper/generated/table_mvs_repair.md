**Offline JSON-repair counterfactual, `spec` condition (PRELIMINARY).** Each invalid-JSON output with archived raw text was passed through the `json-repair` library and graded again. No model was called. *Strict F1* is the reported score. *Repaired F1* adds the score of the repaired outputs. The repaired scenes were graded as trees but **not** checked by Mol\*, so repaired F1 is an upper bound. Outputs with no archived raw text stay at 0 (*Raw text* < *Invalid JSON*).

| Model | Invalid JSON | Raw text | Repaired to a scene | Strict F1 | Repaired F1 | Change |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| deepseek-v3.2 | 0 | 0 | 0 | 0.903 | 0.903 | +0.000 |
| deepseek-v4-flash | 4 | 4 | 4 | 0.859 | 0.913 | +0.054 |
| claude-haiku-4-5 | 0 | 0 | 0 | 0.857 | 0.857 | +0.000 |
| gemini-3.5-flash | 4 | 4 | 3 | 0.849 | 0.866 | +0.018 |
| minimax-m3 | 5 | 5 | 4 | 0.817 | 0.862 | +0.045 |
| qwen3-next-80b-a3b-instruct | 3 | 3 | 3 | 0.805 | 0.848 | +0.043 |
| glm-5.2 | 5 | 5 | 5 | 0.805 | 0.869 | +0.064 |
| llama-4-maverick | 1 | 1 | 1 | 0.792 | 0.797 | +0.005 |
| gemma-3-27b-it | 4 | 4 | 4 | 0.713 | 0.757 | +0.044 |
| kimi-k2.6 | 18 | 18 | 7 | 0.657 | 0.754 | +0.097 |
| gpt-5.4-nano | 15 | 15 | 15 | 0.654 | 0.798 | +0.144 |
| gpt-oss-120b | 26 | 26 | 26 | 0.561 | 0.874 | +0.313 |
| qwen3-30b-a3b-instruct-2507 | 28 | 0 | 0 | 0.519 | 0.519 | +0.000 |
| gpt-oss-20b | 50 | 50 | 47 | 0.252 | 0.868 | +0.616 |
| nemotron-3-super-120b-a12b | 64 | 64 | 64 | 0.078 | 0.911 | +0.833 |
