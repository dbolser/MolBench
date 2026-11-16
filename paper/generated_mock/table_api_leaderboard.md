> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**API track: leaderboard (403 original tasks, headline condition, 3 samples per task)**

| model | weights | strict F1 [95% CI] | task success [95% CI] | success, all samples | target score | valid output | F1 over valid outputs | F1 after JSON repair |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | open | 0.741 [0.716, 0.765] | 0.595 [0.567, 0.622] | 0.194 | 0.732 | 76.0% | 0.916 | 0.784 |
| nvidia/nemotron-3-super-120b-a12b | open | 0.740 [0.714, 0.765] | 0.573 [0.544, 0.603] | 0.174 | 0.728 | 78.0% | 0.898 | 0.779 |
| openai/gpt-5.4-nano | closed | 0.738 [0.710, 0.765] | 0.582 [0.552, 0.613] | 0.199 | 0.730 | 76.8% | 0.906 | 0.777 |
| z-ai/glm-5.2 | open | 0.749 [0.729, 0.768] | 0.604 [0.579, 0.628] | 0.226 | 0.735 | 78.9% | 0.912 | 0.780 |
| deepseek/deepseek-v3.2 | open | 0.748 [0.725, 0.769] | 0.596 [0.569, 0.623] | 0.253 | 0.734 | 78.2% | 0.904 | 0.787 |
| google/gemini-4-argon | closed | 0.734 [0.715, 0.755] | 0.586 [0.559, 0.613] | 0.203 | 0.719 | 75.8% | 0.911 | 0.773 |
| google/gemma-3-27b-it | open | 0.736 [0.713, 0.756] | 0.581 [0.553, 0.611] | 0.206 | 0.719 | 75.8% | 0.909 | 0.769 |
| openai/gpt-oss-120b | open | 0.735 [0.714, 0.754] | 0.593 [0.566, 0.618] | 0.191 | 0.720 | 76.9% | 0.916 | 0.769 |
| meta-llama/llama-4-maverick | open | 0.727 [0.706, 0.746] | 0.576 [0.549, 0.602] | 0.189 | 0.723 | 75.8% | 0.898 | 0.762 |
| qwen/qwen3-30b-a3b-instruct-2507 | open | 0.725 [0.703, 0.745] | 0.572 [0.541, 0.603] | 0.171 | 0.711 | 75.1% | 0.907 | 0.766 |
| minimax/minimax-m3 | open | 0.725 [0.701, 0.748] | 0.571 [0.541, 0.599] | 0.194 | 0.708 | 75.7% | 0.904 | 0.768 |
| anthropic/claude-opus-5.5 | closed | 0.730 [0.710, 0.751] | 0.561 [0.533, 0.586] | 0.161 | 0.717 | 76.9% | 0.902 | 0.767 |
| x-ai/grok-4.7 | closed | 0.730 [0.710, 0.750] | 0.587 [0.560, 0.613] | 0.221 | 0.723 | 76.9% | 0.910 | 0.765 |
| claude-haiku-4-5 | closed | 0.730 [0.709, 0.751] | 0.583 [0.554, 0.611] | 0.203 | 0.720 | 75.8% | 0.909 | 0.770 |
| openai/gpt-6.1-sol | closed | 0.720 [0.694, 0.743] | 0.567 [0.539, 0.595] | 0.186 | 0.710 | 74.9% | 0.905 | 0.761 |
| deepseek/deepseek-v4-pro-0813 | open | 0.730 [0.706, 0.755] | 0.588 [0.560, 0.615] | 0.191 | 0.719 | 76.8% | 0.905 | 0.765 |
| deepseek/deepseek-v4-flash | open | 0.734 [0.710, 0.757] | 0.587 [0.559, 0.617] | 0.211 | 0.721 | 75.6% | 0.913 | 0.769 |
| openai/gpt-oss-20b | open | 0.723 [0.702, 0.745] | 0.572 [0.545, 0.597] | 0.179 | 0.713 | 75.6% | 0.897 | 0.762 |
| google/gemini-3.5-flash | closed | 0.727 [0.705, 0.748] | 0.571 [0.542, 0.599] | 0.184 | 0.713 | 76.1% | 0.900 | 0.765 |
| mistralai/mistral-small-2603 | open | 0.730 [0.709, 0.751] | 0.577 [0.555, 0.599] | 0.196 | 0.716 | 75.6% | 0.912 | 0.768 |
| qwen/qwen3-next-80b-a3b-instruct | open | 0.711 [0.683, 0.735] | 0.557 [0.527, 0.587] | 0.181 | 0.695 | 74.1% | 0.904 | 0.745 |
| baseline-rules (keyword baseline) | no model | 0.736 [0.713, 0.759] | 0.588 [0.562, 0.616] | 0.201 | 0.723 | 76.8% | 0.907 | 0.771 |

Strict F1: mean score over all tasks, an output the viewer cannot show scores 0. Task success: share of samples whose final state is exactly right. Target score: the requested atoms alone. Valid output: share of samples that parse and that the viewer accepts. F1 after JSON repair: the same samples with broken JSON mended offline by `json-repair` (a counterfactual; the strict score is never changed). Intervals: bootstrap over structures.
