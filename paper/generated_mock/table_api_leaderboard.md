> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**API track: leaderboard (416 original tasks, headline condition, 3 samples per task)**

| model | weights | strict F1 [95% CI] | task success [95% CI] | success, all samples | target score | valid output | F1 over valid outputs | F1 after JSON repair |
|:---|:---|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | open | 0.737 [0.711, 0.760] | 0.592 [0.564, 0.618] | 0.183 | 0.732 | 76.2% | 0.911 | 0.774 |
| openai/gpt-5.4-nano | closed | 0.739 [0.714, 0.763] | 0.587 [0.557, 0.617] | 0.200 | 0.734 | 76.9% | 0.910 | 0.776 |
| google/gemma-3-27b-it | open | 0.744 [0.724, 0.764] | 0.584 [0.557, 0.610] | 0.212 | 0.728 | 77.1% | 0.905 | 0.772 |
| anthropic/claude-opus-5.5 | closed | 0.737 [0.717, 0.757] | 0.582 [0.556, 0.608] | 0.188 | 0.725 | 77.1% | 0.908 | 0.770 |
| x-ai/grok-4.7 | closed | 0.735 [0.715, 0.755] | 0.589 [0.560, 0.617] | 0.226 | 0.731 | 77.0% | 0.907 | 0.767 |
| z-ai/glm-5.2 | open | 0.755 [0.734, 0.775] | 0.608 [0.583, 0.633] | 0.233 | 0.743 | 79.8% | 0.909 | 0.784 |
| minimax/minimax-m3 | open | 0.726 [0.703, 0.747] | 0.573 [0.546, 0.598] | 0.190 | 0.714 | 76.0% | 0.902 | 0.769 |
| nvidia/nemotron-3-super-120b-a12b | open | 0.734 [0.708, 0.759] | 0.577 [0.548, 0.607] | 0.180 | 0.716 | 76.5% | 0.904 | 0.772 |
| deepseek/deepseek-v3.2 | open | 0.742 [0.720, 0.764] | 0.587 [0.562, 0.615] | 0.240 | 0.733 | 78.1% | 0.903 | 0.778 |
| google/gemini-4-argon | closed | 0.739 [0.715, 0.761] | 0.593 [0.562, 0.623] | 0.207 | 0.725 | 76.2% | 0.912 | 0.776 |
| deepseek/deepseek-v4-pro-0813 | open | 0.742 [0.722, 0.764] | 0.598 [0.574, 0.623] | 0.200 | 0.731 | 78.0% | 0.906 | 0.774 |
| meta-llama/llama-4-maverick | open | 0.722 [0.703, 0.741] | 0.578 [0.551, 0.604] | 0.190 | 0.717 | 74.7% | 0.902 | 0.757 |
| openai/gpt-oss-20b | open | 0.740 [0.720, 0.760] | 0.585 [0.556, 0.611] | 0.190 | 0.732 | 77.7% | 0.901 | 0.772 |
| qwen/qwen3-30b-a3b-instruct-2507 | open | 0.730 [0.711, 0.749] | 0.574 [0.545, 0.600] | 0.188 | 0.717 | 75.8% | 0.906 | 0.767 |
| deepseek/deepseek-v4-flash | open | 0.736 [0.713, 0.758] | 0.586 [0.561, 0.612] | 0.200 | 0.727 | 76.4% | 0.909 | 0.771 |
| google/gemini-3.5-flash | closed | 0.726 [0.706, 0.746] | 0.576 [0.551, 0.600] | 0.192 | 0.715 | 75.6% | 0.905 | 0.762 |
| openai/gpt-oss-120b | open | 0.736 [0.718, 0.754] | 0.583 [0.556, 0.609] | 0.192 | 0.723 | 76.4% | 0.909 | 0.767 |
| claude-haiku-4-5 | closed | 0.732 [0.710, 0.752] | 0.583 [0.554, 0.611] | 0.195 | 0.721 | 76.1% | 0.908 | 0.767 |
| openai/gpt-6.1-sol | closed | 0.716 [0.694, 0.737] | 0.571 [0.546, 0.598] | 0.185 | 0.706 | 73.5% | 0.912 | 0.753 |
| qwen/qwen3-next-80b-a3b-instruct | open | 0.713 [0.687, 0.737] | 0.558 [0.527, 0.588] | 0.175 | 0.699 | 74.3% | 0.903 | 0.748 |
| mistralai/mistral-small-2603 | open | 0.741 [0.721, 0.763] | 0.591 [0.565, 0.616] | 0.207 | 0.727 | 77.2% | 0.915 | 0.776 |
| baseline-rules (keyword baseline) | no model | 0.743 [0.721, 0.764] | 0.596 [0.571, 0.622] | 0.209 | 0.733 | 76.8% | 0.910 | 0.774 |

Strict F1: mean score over all tasks, an output the viewer cannot show scores 0. Task success: share of samples whose final state is exactly right. Target score: the requested atoms alone. Valid output: share of samples that parse and that the viewer accepts. F1 after JSON repair: the same samples with broken JSON mended offline by `json-repair` (a counterfactual; the strict score is never changed). Intervals: bootstrap over structures.
