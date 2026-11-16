> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**The two tracks, model by model**

| model | MVS task success | API task success | API − MVS | MVS strict F1 | API strict F1 | API − MVS |
|:---|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 0.561 | 0.595 | +0.034 | 0.698 | 0.741 | +0.043 |
| nvidia/nemotron-3-super-120b-a12b | 0.570 | 0.573 | +0.004 | 0.693 | 0.740 | +0.046 |
| openai/gpt-5.4-nano | 0.543 | 0.582 | +0.039 | 0.691 | 0.738 | +0.047 |
| z-ai/glm-5.2 | 0.531 | 0.604 | +0.073 | 0.674 | 0.749 | +0.076 |
| deepseek/deepseek-v3.2 | 0.526 | 0.596 | +0.070 | 0.678 | 0.748 | +0.070 |
| google/gemini-4-argon | 0.542 | 0.586 | +0.044 | 0.686 | 0.734 | +0.048 |
| google/gemma-3-27b-it | 0.538 | 0.581 | +0.044 | 0.684 | 0.736 | +0.052 |
| openai/gpt-oss-120b | 0.546 | 0.593 | +0.047 | 0.689 | 0.735 | +0.046 |
| meta-llama/llama-4-maverick | 0.564 | 0.576 | +0.011 | 0.686 | 0.727 | +0.041 |
| qwen/qwen3-30b-a3b-instruct-2507 | 0.563 | 0.572 | +0.010 | 0.689 | 0.725 | +0.035 |
| minimax/minimax-m3 | 0.547 | 0.571 | +0.024 | 0.694 | 0.725 | +0.031 |
| anthropic/claude-opus-5.5 | 0.531 | 0.561 | +0.030 | 0.681 | 0.730 | +0.049 |
| x-ai/grok-4.7 | 0.534 | 0.587 | +0.053 | 0.673 | 0.730 | +0.058 |
| claude-haiku-4-5 | 0.539 | 0.583 | +0.044 | 0.676 | 0.730 | +0.054 |
| openai/gpt-6.1-sol | 0.549 | 0.567 | +0.018 | 0.684 | 0.720 | +0.036 |
| deepseek/deepseek-v4-pro-0813 | 0.544 | 0.588 | +0.044 | 0.673 | 0.730 | +0.058 |
| deepseek/deepseek-v4-flash | 0.511 | 0.587 | +0.076 | 0.655 | 0.734 | +0.079 |
| openai/gpt-oss-20b | 0.519 | 0.572 | +0.053 | 0.661 | 0.723 | +0.062 |
| google/gemini-3.5-flash | 0.539 | 0.571 | +0.032 | 0.673 | 0.727 | +0.053 |
| mistralai/mistral-small-2603 | 0.530 | 0.577 | +0.047 | 0.663 | 0.730 | +0.068 |
| qwen/qwen3-next-80b-a3b-instruct | 0.546 | 0.557 | +0.012 | 0.675 | 0.711 | +0.036 |
| baseline-rules (keyword baseline) | 0.556 | 0.588 | +0.033 | 0.688 | 0.736 | +0.047 |

All original tasks of each track (not only twins), headline condition. Over the 21 models (keyword baseline left out), Pearson r between the two tracks is -0.183 for task success and 0.157 for strict F1.
