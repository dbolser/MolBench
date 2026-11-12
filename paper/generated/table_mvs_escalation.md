**Tree score vs render-checked score, `spec` condition (PRELIMINARY).** *Tree F1*: the strict F1 from comparing scene trees. A valid scene that scores below 1 is *escalated*: it is rendered next to the reference. It is *rescued* (counted as correct) if the two images are near-identical pixel for pixel, or if the image-pair judge model calls them the same. *Validated F1* is the tree F1 with rescued scenes set to 1. Scores are never lowered by escalation.

| Model | Tree F1 | Validated F1 | Change | Escalated | Rescued (pixels) | Rescued (judge) | Judged different |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deepseek-v3.2 | 0.903 | 0.921 | +0.018 | 24 | 0 | 6 | 18 |
| deepseek-v4-flash | 0.859 | 0.870 | +0.011 | 21 | 4 | 3 | 14 |
| claude-haiku-4-5 | 0.857 | 0.877 | +0.020 | 25 | 0 | 3 | 22 |
| gemini-3.5-flash | 0.849 | 0.870 | +0.021 | 17 | 0 | 4 | 13 |
| minimax-m3 | 0.817 | 0.825 | +0.009 | 21 | 0 | 3 | 18 |
| qwen3-next-80b-a3b-instruct | 0.805 | 0.831 | +0.025 | 32 | 0 | 8 | 24 |
| glm-5.2 | 0.805 | 0.832 | +0.027 | 23 | 0 | 7 | 16 |
| llama-4-maverick | 0.792 | 0.799 | +0.007 | 8 | 1 | 2 | 5 |
| gemma-3-27b-it | 0.713 | 0.718 | +0.004 | 23 | 0 | 3 | 20 |
| kimi-k2.6 | 0.657 | 0.680 | +0.023 | 18 | 2 | 5 | 11 |
| gpt-5.4-nano | 0.654 | 0.682 | +0.028 | 42 | 18 | 4 | 20 |
| gpt-oss-120b | 0.561 | 0.574 | +0.012 | 19 | 0 | 5 | 14 |
| qwen3-30b-a3b-instruct-2507 | 0.519 | 0.529 | +0.010 | 13 | 0 | 4 | 9 |
| gpt-oss-20b | 0.252 | 0.256 | +0.003 | 6 | 0 | 1 | 5 |
| nemotron-3-super-120b-a12b | 0.078 | 0.079 | +0.001 | 2 | 0 | 1 | 1 |
