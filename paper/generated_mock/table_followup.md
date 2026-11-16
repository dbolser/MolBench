> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Follow-up turns: the edit made, and what had to stay**

*MVS track.*

| model | tasks | task success | strict F1 | tasks with a preserved part | target score (those tasks) | preserved score | everything preserved | success, edit tasks (n) | success, no-change tasks (n) |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 58 | 0.500 | 0.670 | 53 | 0.732 | 0.645 | 50.3% | 0.500 (48) | 0.500 (10) |
| openai/gpt-5.4-nano | 58 | 0.552 | 0.727 | 53 | 0.772 | 0.690 | 56.0% | 0.569 (48) | 0.467 (10) |
| google/gemma-3-27b-it | 58 | 0.546 | 0.712 | 53 | 0.768 | 0.665 | 53.5% | 0.549 (48) | 0.533 (10) |
| anthropic/claude-opus-5.5 | 58 | 0.552 | 0.762 | 53 | 0.833 | 0.714 | 56.0% | 0.542 (48) | 0.600 (10) |
| x-ai/grok-4.7 | 58 | 0.557 | 0.694 | 53 | 0.750 | 0.682 | 58.5% | 0.535 (48) | 0.667 (10) |
| z-ai/glm-5.2 | 58 | 0.506 | 0.677 | 53 | 0.728 | 0.657 | 52.2% | 0.542 (48) | 0.333 (10) |
| minimax/minimax-m3 | 58 | 0.523 | 0.698 | 53 | 0.719 | 0.659 | 53.5% | 0.542 (48) | 0.433 (10) |
| nvidia/nemotron-3-super-120b-a12b | 58 | 0.546 | 0.684 | 53 | 0.789 | 0.662 | 56.0% | 0.542 (48) | 0.567 (10) |
| deepseek/deepseek-v3.2 | 58 | 0.598 | 0.770 | 53 | 0.825 | 0.752 | 62.9% | 0.625 (48) | 0.467 (10) |
| google/gemini-4-argon | 58 | 0.563 | 0.739 | 53 | 0.798 | 0.712 | 57.9% | 0.583 (48) | 0.467 (10) |
| deepseek/deepseek-v4-pro-0813 | 58 | 0.575 | 0.746 | 53 | 0.816 | 0.730 | 60.4% | 0.590 (48) | 0.500 (10) |
| meta-llama/llama-4-maverick | 58 | 0.575 | 0.700 | 53 | 0.768 | 0.682 | 58.5% | 0.590 (48) | 0.500 (10) |
| openai/gpt-oss-20b | 58 | 0.471 | 0.641 | 53 | 0.706 | 0.608 | 48.4% | 0.479 (48) | 0.433 (10) |
| qwen/qwen3-30b-a3b-instruct-2507 | 58 | 0.523 | 0.677 | 53 | 0.693 | 0.657 | 54.7% | 0.542 (48) | 0.433 (10) |
| deepseek/deepseek-v4-flash | 58 | 0.580 | 0.717 | 53 | 0.759 | 0.700 | 59.7% | 0.590 (48) | 0.533 (10) |
| google/gemini-3.5-flash | 58 | 0.517 | 0.680 | 53 | 0.763 | 0.632 | 49.7% | 0.514 (48) | 0.533 (10) |
| openai/gpt-oss-120b | 58 | 0.529 | 0.704 | 53 | 0.728 | 0.682 | 55.3% | 0.514 (48) | 0.600 (10) |
| claude-haiku-4-5 | 58 | 0.529 | 0.676 | 53 | 0.719 | 0.664 | 54.7% | 0.542 (48) | 0.467 (10) |
| openai/gpt-6.1-sol | 58 | 0.489 | 0.693 | 53 | 0.754 | 0.675 | 52.2% | 0.486 (48) | 0.500 (10) |
| qwen/qwen3-next-80b-a3b-instruct | 58 | 0.563 | 0.712 | 53 | 0.741 | 0.687 | 57.9% | 0.562 (48) | 0.567 (10) |
| mistralai/mistral-small-2603 | 58 | 0.569 | 0.685 | 53 | 0.750 | 0.681 | 60.4% | 0.576 (48) | 0.533 (10) |
| baseline-rules (keyword baseline) | 58 | 0.500 | 0.701 | 53 | 0.719 | 0.662 | 50.9% | 0.500 (48) | 0.500 (10) |

*API track.*

| model | tasks | task success | strict F1 | tasks with a preserved part | target score (those tasks) | preserved score | everything preserved | success, edit tasks (n) | success, no-change tasks (n) |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 44 | 0.508 | 0.709 | 40 | 0.782 | 0.659 | 50.0% | 0.500 (36) | 0.542 (8) |
| openai/gpt-5.4-nano | 44 | 0.568 | 0.738 | 40 | 0.808 | 0.681 | 55.0% | 0.574 (36) | 0.542 (8) |
| google/gemma-3-27b-it | 44 | 0.583 | 0.740 | 40 | 0.756 | 0.719 | 57.5% | 0.602 (36) | 0.500 (8) |
| anthropic/claude-opus-5.5 | 44 | 0.545 | 0.698 | 40 | 0.692 | 0.669 | 53.3% | 0.565 (36) | 0.458 (8) |
| x-ai/grok-4.7 | 44 | 0.523 | 0.680 | 40 | 0.769 | 0.665 | 53.3% | 0.491 (36) | 0.667 (8) |
| z-ai/glm-5.2 | 44 | 0.636 | 0.773 | 40 | 0.833 | 0.758 | 64.2% | 0.639 (36) | 0.625 (8) |
| minimax/minimax-m3 | 44 | 0.568 | 0.739 | 40 | 0.846 | 0.706 | 56.7% | 0.602 (36) | 0.417 (8) |
| nvidia/nemotron-3-super-120b-a12b | 44 | 0.644 | 0.786 | 40 | 0.808 | 0.775 | 65.8% | 0.593 (36) | 0.875 (8) |
| deepseek/deepseek-v3.2 | 44 | 0.538 | 0.721 | 40 | 0.769 | 0.695 | 53.3% | 0.537 (36) | 0.542 (8) |
| google/gemini-4-argon | 44 | 0.614 | 0.769 | 40 | 0.846 | 0.733 | 60.8% | 0.648 (36) | 0.458 (8) |
| deepseek/deepseek-v4-pro-0813 | 44 | 0.576 | 0.745 | 40 | 0.808 | 0.715 | 56.7% | 0.556 (36) | 0.667 (8) |
| meta-llama/llama-4-maverick | 44 | 0.568 | 0.730 | 40 | 0.782 | 0.697 | 56.7% | 0.574 (36) | 0.542 (8) |
| openai/gpt-oss-20b | 44 | 0.538 | 0.755 | 40 | 0.872 | 0.730 | 53.3% | 0.565 (36) | 0.417 (8) |
| qwen/qwen3-30b-a3b-instruct-2507 | 44 | 0.576 | 0.734 | 40 | 0.833 | 0.724 | 58.3% | 0.565 (36) | 0.625 (8) |
| deepseek/deepseek-v4-flash | 44 | 0.598 | 0.740 | 40 | 0.782 | 0.721 | 59.2% | 0.574 (36) | 0.708 (8) |
| google/gemini-3.5-flash | 44 | 0.614 | 0.755 | 40 | 0.821 | 0.727 | 61.7% | 0.648 (36) | 0.458 (8) |
| openai/gpt-oss-120b | 44 | 0.545 | 0.730 | 40 | 0.808 | 0.715 | 55.8% | 0.546 (36) | 0.542 (8) |
| claude-haiku-4-5 | 44 | 0.583 | 0.778 | 40 | 0.846 | 0.785 | 61.7% | 0.611 (36) | 0.458 (8) |
| openai/gpt-6.1-sol | 44 | 0.530 | 0.674 | 40 | 0.692 | 0.659 | 56.7% | 0.546 (36) | 0.458 (8) |
| qwen/qwen3-next-80b-a3b-instruct | 44 | 0.568 | 0.724 | 40 | 0.795 | 0.722 | 60.0% | 0.537 (36) | 0.708 (8) |
| mistralai/mistral-small-2603 | 44 | 0.523 | 0.724 | 40 | 0.744 | 0.681 | 50.8% | 0.519 (36) | 0.542 (8) |
| baseline-rules (keyword baseline) | 44 | 0.576 | 0.730 | 40 | 0.808 | 0.717 | 57.5% | 0.556 (36) | 0.667 (8) |

Target score: the atoms the edit request is about, alone. Preserved score: the parts of the start state the edit must leave alone, graded the same way (mean over the parts; "everything preserved" = share of samples where every part scores 1). An answer that makes the edit on an empty viewer scores its target and loses the preserved score. In a no-change task the start state returned unchanged is the right answer.
