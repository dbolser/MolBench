> **MOCK DATA.** Dry run answered by the mock model: the table has its final shape, **every number in it is fake**.

**Follow-up turns: the edit made, and what had to stay**

*MVS track.*

| model | tasks | task success | strict F1 | tasks with a preserved part | target score (those tasks) | preserved score | everything preserved | success, edit tasks (n) | success, no-change tasks (n) |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 58 | 0.557 | 0.697 | 53 | 0.711 | 0.667 | 55.3% | 0.542 (48) | 0.633 (10) |
| nvidia/nemotron-3-super-120b-a12b | 58 | 0.580 | 0.706 | 53 | 0.731 | 0.673 | 57.9% | 0.562 (48) | 0.667 (10) |
| openai/gpt-5.4-nano | 58 | 0.586 | 0.742 | 53 | 0.780 | 0.712 | 60.4% | 0.590 (48) | 0.567 (10) |
| z-ai/glm-5.2 | 58 | 0.540 | 0.702 | 53 | 0.747 | 0.697 | 58.5% | 0.542 (48) | 0.533 (10) |
| deepseek/deepseek-v3.2 | 58 | 0.580 | 0.771 | 53 | 0.808 | 0.733 | 58.5% | 0.611 (48) | 0.433 (10) |
| google/gemini-4-argon | 58 | 0.569 | 0.761 | 53 | 0.817 | 0.739 | 59.7% | 0.583 (48) | 0.500 (10) |
| google/gemma-3-27b-it | 58 | 0.575 | 0.733 | 53 | 0.753 | 0.703 | 58.5% | 0.556 (48) | 0.667 (10) |
| openai/gpt-oss-120b | 58 | 0.529 | 0.688 | 53 | 0.714 | 0.665 | 54.1% | 0.549 (48) | 0.433 (10) |
| meta-llama/llama-4-maverick | 58 | 0.540 | 0.667 | 53 | 0.700 | 0.657 | 56.6% | 0.549 (48) | 0.500 (10) |
| qwen/qwen3-30b-a3b-instruct-2507 | 58 | 0.575 | 0.707 | 53 | 0.707 | 0.682 | 59.1% | 0.590 (48) | 0.500 (10) |
| minimax/minimax-m3 | 58 | 0.483 | 0.664 | 53 | 0.683 | 0.627 | 49.7% | 0.493 (48) | 0.433 (10) |
| anthropic/claude-opus-5.5 | 58 | 0.500 | 0.716 | 53 | 0.744 | 0.659 | 49.7% | 0.500 (48) | 0.500 (10) |
| x-ai/grok-4.7 | 58 | 0.506 | 0.657 | 53 | 0.696 | 0.638 | 52.2% | 0.514 (48) | 0.467 (10) |
| claude-haiku-4-5 | 58 | 0.575 | 0.722 | 53 | 0.759 | 0.714 | 60.4% | 0.556 (48) | 0.667 (10) |
| openai/gpt-6.1-sol | 58 | 0.483 | 0.682 | 53 | 0.745 | 0.673 | 52.2% | 0.479 (48) | 0.500 (10) |
| deepseek/deepseek-v4-pro-0813 | 58 | 0.540 | 0.708 | 53 | 0.734 | 0.695 | 57.9% | 0.569 (48) | 0.400 (10) |
| deepseek/deepseek-v4-flash | 58 | 0.552 | 0.696 | 53 | 0.718 | 0.684 | 57.2% | 0.562 (48) | 0.500 (10) |
| openai/gpt-oss-20b | 58 | 0.483 | 0.671 | 53 | 0.707 | 0.643 | 49.7% | 0.500 (48) | 0.400 (10) |
| google/gemini-3.5-flash | 58 | 0.471 | 0.643 | 53 | 0.673 | 0.594 | 45.9% | 0.486 (48) | 0.400 (10) |
| mistralai/mistral-small-2603 | 58 | 0.563 | 0.686 | 53 | 0.715 | 0.681 | 59.1% | 0.569 (48) | 0.533 (10) |
| qwen/qwen3-next-80b-a3b-instruct | 58 | 0.511 | 0.664 | 53 | 0.673 | 0.630 | 52.2% | 0.535 (48) | 0.400 (10) |
| baseline-rules (keyword baseline) | 58 | 0.500 | 0.693 | 53 | 0.715 | 0.660 | 53.5% | 0.472 (48) | 0.633 (10) |

*API track.*

| model | tasks | task success | strict F1 | tasks with a preserved part | target score (those tasks) | preserved score | everything preserved | success, edit tasks (n) | success, no-change tasks (n) |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| moonshotai/kimi-k2.6 | 44 | 0.538 | 0.709 | 40 | 0.734 | 0.654 | 53.3% | 0.546 (36) | 0.500 (8) |
| nvidia/nemotron-3-super-120b-a12b | 44 | 0.576 | 0.755 | 40 | 0.803 | 0.751 | 58.3% | 0.602 (36) | 0.458 (8) |
| openai/gpt-5.4-nano | 44 | 0.545 | 0.726 | 40 | 0.737 | 0.670 | 52.5% | 0.537 (36) | 0.583 (8) |
| z-ai/glm-5.2 | 44 | 0.636 | 0.773 | 40 | 0.802 | 0.762 | 64.2% | 0.657 (36) | 0.542 (8) |
| deepseek/deepseek-v3.2 | 44 | 0.598 | 0.753 | 40 | 0.782 | 0.725 | 60.0% | 0.583 (36) | 0.667 (8) |
| google/gemini-4-argon | 44 | 0.652 | 0.800 | 40 | 0.830 | 0.772 | 65.0% | 0.630 (36) | 0.750 (8) |
| google/gemma-3-27b-it | 44 | 0.553 | 0.693 | 40 | 0.712 | 0.672 | 54.2% | 0.556 (36) | 0.542 (8) |
| openai/gpt-oss-120b | 44 | 0.591 | 0.742 | 40 | 0.782 | 0.729 | 60.8% | 0.583 (36) | 0.625 (8) |
| meta-llama/llama-4-maverick | 44 | 0.523 | 0.711 | 40 | 0.734 | 0.683 | 51.7% | 0.546 (36) | 0.417 (8) |
| qwen/qwen3-30b-a3b-instruct-2507 | 44 | 0.568 | 0.709 | 40 | 0.752 | 0.699 | 57.5% | 0.565 (36) | 0.583 (8) |
| minimax/minimax-m3 | 44 | 0.598 | 0.739 | 40 | 0.768 | 0.713 | 60.0% | 0.611 (36) | 0.542 (8) |
| anthropic/claude-opus-5.5 | 44 | 0.538 | 0.715 | 40 | 0.733 | 0.687 | 52.5% | 0.556 (36) | 0.458 (8) |
| x-ai/grok-4.7 | 44 | 0.561 | 0.730 | 40 | 0.788 | 0.720 | 57.5% | 0.537 (36) | 0.667 (8) |
| claude-haiku-4-5 | 44 | 0.621 | 0.798 | 40 | 0.863 | 0.808 | 65.8% | 0.639 (36) | 0.542 (8) |
| openai/gpt-6.1-sol | 44 | 0.515 | 0.688 | 40 | 0.718 | 0.672 | 55.0% | 0.509 (36) | 0.542 (8) |
| deepseek/deepseek-v4-pro-0813 | 44 | 0.545 | 0.707 | 40 | 0.732 | 0.671 | 53.3% | 0.565 (36) | 0.458 (8) |
| deepseek/deepseek-v4-flash | 44 | 0.621 | 0.731 | 40 | 0.747 | 0.708 | 61.7% | 0.602 (36) | 0.708 (8) |
| openai/gpt-oss-20b | 44 | 0.485 | 0.703 | 40 | 0.756 | 0.670 | 47.5% | 0.500 (36) | 0.417 (8) |
| google/gemini-3.5-flash | 44 | 0.545 | 0.717 | 40 | 0.744 | 0.685 | 54.2% | 0.574 (36) | 0.417 (8) |
| mistralai/mistral-small-2603 | 44 | 0.455 | 0.662 | 40 | 0.684 | 0.615 | 43.3% | 0.463 (36) | 0.417 (8) |
| qwen/qwen3-next-80b-a3b-instruct | 44 | 0.523 | 0.700 | 40 | 0.745 | 0.697 | 55.0% | 0.519 (36) | 0.542 (8) |
| baseline-rules (keyword baseline) | 44 | 0.576 | 0.736 | 40 | 0.787 | 0.717 | 57.5% | 0.565 (36) | 0.625 (8) |

Target score: the atoms the edit request is about, alone. Preserved score: the parts of the start state the edit must leave alone, graded the same way (mean over the parts; "everything preserved" = share of samples where every part scores 1). An answer that makes the edit on an empty viewer scores its target and loses the preserved score. In a no-change task the start state returned unchanged is the right answer.
