> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**The two tracks, model by model**

| model | MVS task success | API task success | API − MVS | MVS strict F1 | API strict F1 | API − MVS |
|:---|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 0.560 | 0.592 | +0.032 | 0.698 | 0.737 | +0.039 |
| openai/gpt-5.4-nano | 0.552 | 0.587 | +0.035 | 0.695 | 0.739 | +0.044 |
| google/gemma-3-27b-it | 0.542 | 0.584 | +0.043 | 0.683 | 0.744 | +0.061 |
| anthropic/claude-opus-5.5 | 0.547 | 0.582 | +0.035 | 0.695 | 0.737 | +0.042 |
| x-ai/grok-4.7 | 0.549 | 0.589 | +0.040 | 0.689 | 0.735 | +0.045 |
| z-ai/glm-5.2 | 0.521 | 0.608 | +0.088 | 0.663 | 0.755 | +0.092 |
| minimax/minimax-m3 | 0.547 | 0.573 | +0.026 | 0.698 | 0.726 | +0.028 |
| nvidia/nemotron-3-super-120b-a12b | 0.560 | 0.577 | +0.017 | 0.690 | 0.734 | +0.043 |
| deepseek/deepseek-v3.2 | 0.531 | 0.587 | +0.056 | 0.680 | 0.742 | +0.062 |
| google/gemini-4-argon | 0.535 | 0.593 | +0.058 | 0.679 | 0.739 | +0.060 |
| deepseek/deepseek-v4-pro-0813 | 0.548 | 0.598 | +0.050 | 0.677 | 0.742 | +0.066 |
| meta-llama/llama-4-maverick | 0.565 | 0.578 | +0.013 | 0.687 | 0.722 | +0.035 |
| openai/gpt-oss-20b | 0.533 | 0.585 | +0.052 | 0.665 | 0.740 | +0.075 |
| qwen/qwen3-30b-a3b-instruct-2507 | 0.559 | 0.574 | +0.015 | 0.687 | 0.730 | +0.044 |
| deepseek/deepseek-v4-flash | 0.527 | 0.586 | +0.059 | 0.668 | 0.736 | +0.069 |
| google/gemini-3.5-flash | 0.554 | 0.576 | +0.022 | 0.689 | 0.726 | +0.037 |
| openai/gpt-oss-120b | 0.526 | 0.583 | +0.058 | 0.675 | 0.736 | +0.060 |
| claude-haiku-4-5 | 0.535 | 0.583 | +0.048 | 0.671 | 0.732 | +0.061 |
| openai/gpt-6.1-sol | 0.542 | 0.571 | +0.030 | 0.682 | 0.716 | +0.034 |
| qwen/qwen3-next-80b-a3b-instruct | 0.558 | 0.558 | +0.000 | 0.685 | 0.713 | +0.028 |
| mistralai/mistral-small-2603 | 0.523 | 0.591 | +0.067 | 0.658 | 0.741 | +0.083 |
| baseline-rules (keyword baseline) | 0.547 | 0.596 | +0.049 | 0.683 | 0.743 | +0.060 |
| baseline-literal (literal baseline) | 0.547 | 0.576 | +0.029 | 0.688 | 0.726 | +0.038 |

All original tasks of each track (not only twins), headline condition. Over the 21 models (scripted baselines left out), Pearson r between the two tracks is -0.514 for task success and -0.413 for strict F1.
