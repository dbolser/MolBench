> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**MVS track: leaderboard (381 original tasks, headline condition, 3 samples per task)**

| model | weights | strict F1 [95% CI] | task success [95% CI] | success, all samples | target score | valid output | F1 over valid outputs | F1 after JSON repair |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | open | 0.698 [0.676, 0.720] | 0.560 [0.532, 0.586] | 0.194 | 0.729 | 77.8% | 0.897 | 0.724 |
| openai/gpt-5.4-nano | closed | 0.695 [0.669, 0.721] | 0.552 [0.521, 0.583] | 0.139 | 0.722 | 77.7% | 0.895 | 0.718 |
| google/gemma-3-27b-it | open | 0.683 [0.659, 0.708] | 0.542 [0.511, 0.571] | 0.157 | 0.713 | 76.7% | 0.890 | 0.706 |
| anthropic/claude-opus-5.5 | closed | 0.695 [0.670, 0.718] | 0.547 [0.515, 0.575] | 0.168 | 0.723 | 78.0% | 0.890 | 0.720 |
| x-ai/grok-4.7 | closed | 0.689 [0.668, 0.710] | 0.549 [0.521, 0.577] | 0.160 | 0.718 | 77.1% | 0.894 | 0.709 |
| z-ai/glm-5.2 | open | 0.663 [0.641, 0.687] | 0.521 [0.490, 0.550] | 0.134 | 0.686 | 74.5% | 0.890 | 0.694 |
| minimax/minimax-m3 | open | 0.698 [0.673, 0.720] | 0.547 [0.520, 0.573] | 0.157 | 0.723 | 78.0% | 0.895 | 0.720 |
| nvidia/nemotron-3-super-120b-a12b | open | 0.690 [0.666, 0.714] | 0.560 [0.528, 0.589] | 0.163 | 0.721 | 76.8% | 0.898 | 0.715 |
| deepseek/deepseek-v3.2 | open | 0.680 [0.655, 0.704] | 0.531 [0.500, 0.562] | 0.152 | 0.710 | 76.6% | 0.888 | 0.718 |
| google/gemini-4-argon | closed | 0.679 [0.658, 0.699] | 0.535 [0.512, 0.558] | 0.136 | 0.704 | 76.3% | 0.890 | 0.699 |
| deepseek/deepseek-v4-pro-0813 | open | 0.677 [0.650, 0.701] | 0.548 [0.520, 0.576] | 0.168 | 0.700 | 75.5% | 0.896 | 0.701 |
| meta-llama/llama-4-maverick | open | 0.687 [0.665, 0.711] | 0.565 [0.536, 0.594] | 0.176 | 0.713 | 76.1% | 0.903 | 0.719 |
| openai/gpt-oss-20b | open | 0.665 [0.637, 0.693] | 0.533 [0.500, 0.566] | 0.152 | 0.691 | 74.0% | 0.898 | 0.690 |
| qwen/qwen3-30b-a3b-instruct-2507 | open | 0.687 [0.663, 0.711] | 0.559 [0.533, 0.586] | 0.150 | 0.710 | 76.3% | 0.900 | 0.718 |
| deepseek/deepseek-v4-flash | open | 0.668 [0.643, 0.694] | 0.527 [0.493, 0.556] | 0.178 | 0.694 | 75.2% | 0.887 | 0.686 |
| google/gemini-3.5-flash | closed | 0.689 [0.665, 0.712] | 0.554 [0.530, 0.577] | 0.144 | 0.718 | 77.0% | 0.895 | 0.722 |
| openai/gpt-oss-120b | open | 0.675 [0.652, 0.698] | 0.526 [0.500, 0.556] | 0.150 | 0.700 | 75.8% | 0.891 | 0.704 |
| claude-haiku-4-5 | closed | 0.671 [0.646, 0.695] | 0.535 [0.504, 0.564] | 0.142 | 0.697 | 75.2% | 0.891 | 0.695 |
| openai/gpt-6.1-sol | closed | 0.682 [0.657, 0.706] | 0.542 [0.509, 0.572] | 0.184 | 0.706 | 76.2% | 0.895 | 0.713 |
| qwen/qwen3-next-80b-a3b-instruct | open | 0.685 [0.661, 0.711] | 0.558 [0.527, 0.589] | 0.184 | 0.705 | 75.2% | 0.911 | 0.709 |
| mistralai/mistral-small-2603 | open | 0.658 [0.633, 0.685] | 0.523 [0.491, 0.556] | 0.139 | 0.691 | 74.3% | 0.886 | 0.684 |
| baseline-rules (keyword baseline) | no model | 0.683 [0.658, 0.708] | 0.547 [0.519, 0.574] | 0.168 | 0.709 | 76.5% | 0.894 | 0.705 |

Strict F1: mean score over all tasks, an output the viewer cannot show scores 0. Task success: share of samples whose final state is exactly right. Target score: the requested atoms alone. Valid output: share of samples that parse and that the viewer accepts. F1 after JSON repair: the same samples with broken JSON mended offline by `json-repair` (a counterfactual; the strict score is never changed). Intervals: bootstrap over structures.
