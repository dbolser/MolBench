> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**MVS track: leaderboard (378 original tasks, headline condition, 3 samples per task)**

| model | weights | strict F1 [95% CI] | task success [95% CI] | success, all samples | target score | valid output | F1 over valid outputs | F1 after JSON repair |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | open | 0.698 [0.673, 0.721] | 0.561 [0.533, 0.588] | 0.198 | 0.724 | 77.8% | 0.897 | 0.723 |
| nvidia/nemotron-3-super-120b-a12b | open | 0.693 [0.667, 0.717] | 0.570 [0.538, 0.601] | 0.167 | 0.715 | 76.8% | 0.903 | 0.717 |
| openai/gpt-5.4-nano | closed | 0.691 [0.664, 0.717] | 0.543 [0.512, 0.575] | 0.132 | 0.720 | 77.7% | 0.890 | 0.713 |
| z-ai/glm-5.2 | open | 0.674 [0.653, 0.694] | 0.531 [0.501, 0.560] | 0.138 | 0.695 | 75.7% | 0.891 | 0.702 |
| deepseek/deepseek-v3.2 | open | 0.678 [0.656, 0.701] | 0.526 [0.499, 0.555] | 0.156 | 0.710 | 76.3% | 0.889 | 0.714 |
| google/gemini-4-argon | closed | 0.686 [0.662, 0.710] | 0.542 [0.521, 0.568] | 0.138 | 0.711 | 77.0% | 0.891 | 0.704 |
| google/gemma-3-27b-it | open | 0.684 [0.659, 0.709] | 0.538 [0.509, 0.569] | 0.161 | 0.709 | 77.2% | 0.885 | 0.707 |
| openai/gpt-oss-120b | open | 0.689 [0.666, 0.713] | 0.546 [0.518, 0.574] | 0.167 | 0.714 | 76.7% | 0.899 | 0.714 |
| meta-llama/llama-4-maverick | open | 0.686 [0.660, 0.711] | 0.564 [0.532, 0.594] | 0.188 | 0.708 | 75.9% | 0.904 | 0.719 |
| qwen/qwen3-30b-a3b-instruct-2507 | open | 0.689 [0.663, 0.714] | 0.563 [0.538, 0.589] | 0.151 | 0.711 | 76.7% | 0.899 | 0.716 |
| minimax/minimax-m3 | open | 0.694 [0.670, 0.717] | 0.547 [0.520, 0.575] | 0.153 | 0.719 | 77.1% | 0.900 | 0.716 |
| anthropic/claude-opus-5.5 | closed | 0.681 [0.657, 0.705] | 0.531 [0.501, 0.559] | 0.159 | 0.711 | 77.0% | 0.885 | 0.709 |
| x-ai/grok-4.7 | closed | 0.673 [0.650, 0.696] | 0.534 [0.504, 0.565] | 0.148 | 0.698 | 75.0% | 0.897 | 0.695 |
| claude-haiku-4-5 | closed | 0.676 [0.654, 0.696] | 0.539 [0.511, 0.567] | 0.156 | 0.702 | 75.9% | 0.890 | 0.699 |
| openai/gpt-6.1-sol | closed | 0.684 [0.657, 0.711] | 0.549 [0.515, 0.581] | 0.185 | 0.708 | 76.2% | 0.898 | 0.711 |
| deepseek/deepseek-v4-pro-0813 | open | 0.673 [0.651, 0.695] | 0.544 [0.520, 0.569] | 0.159 | 0.694 | 75.1% | 0.895 | 0.696 |
| deepseek/deepseek-v4-flash | open | 0.655 [0.628, 0.681] | 0.511 [0.481, 0.541] | 0.156 | 0.679 | 74.1% | 0.884 | 0.673 |
| openai/gpt-oss-20b | open | 0.661 [0.633, 0.689] | 0.519 [0.486, 0.551] | 0.138 | 0.686 | 74.3% | 0.890 | 0.684 |
| google/gemini-3.5-flash | closed | 0.673 [0.648, 0.698] | 0.539 [0.511, 0.567] | 0.135 | 0.697 | 75.3% | 0.894 | 0.705 |
| mistralai/mistral-small-2603 | open | 0.663 [0.637, 0.686] | 0.530 [0.498, 0.559] | 0.148 | 0.692 | 74.5% | 0.889 | 0.692 |
| qwen/qwen3-next-80b-a3b-instruct | open | 0.675 [0.651, 0.698] | 0.546 [0.518, 0.572] | 0.164 | 0.696 | 74.4% | 0.907 | 0.702 |
| baseline-rules (keyword baseline) | no model | 0.688 [0.663, 0.712] | 0.556 [0.527, 0.585] | 0.172 | 0.714 | 76.7% | 0.897 | 0.711 |

Strict F1: mean score over all tasks, an output the viewer cannot show scores 0. Task success: share of samples whose final state is exactly right. Target score: the requested atoms alone. Valid output: share of samples that parse and that the viewer accepts. F1 after JSON repair: the same samples with broken JSON mended offline by `json-repair` (a counterfactual; the strict score is never changed). Intervals: bootstrap over structures.
