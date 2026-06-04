# Benchmark Data Log

This folder stores each benchmark-question dataset version as a separate CSV file.
The README is the running changelog for how the dataset changes across iterations.

## Current Version

| Version | File | Questions | Notes |
| --- | --- | ---: | --- |
| v2 | `76synth_benchmark_questions.csv` | 76 | Current dataset. Expands the benchmark from 41 to 76 questions. |
| v1 | `41synth_benchmark_questions.csv` | 41 | Prior dataset. Replaced by v2, retained in git history. |

## Version 2 Breakdown

File: `76synth_benchmark_questions.csv`

Total questions: 76

### Service Line

| Service line | Count | % of dataset |
| --- | ---: | ---: |
| CFO | 39 | 51.3% |
| DD | 37 | 48.7% |

### BI Experience Band

| BI band | Count | % of dataset |
| --- | ---: | ---: |
| Junior (0-3) | 30 | 39.5% |
| Senior (4-7) | 46 | 60.5% |

### Complexity

| Complexity | Count | % of dataset |
| --- | ---: | ---: |
| Easy | 25 | 32.9% |
| Medium | 27 | 35.5% |
| Hard | 24 | 31.6% |

### Gradability

| Gradability | Count | % of dataset |
| --- | ---: | ---: |
| Deterministic | 56 | 73.7% |
| Hybrid | 10 | 13.2% |
| Judgment | 10 | 13.2% |

## Version 1 Breakdown

File: `41synth_benchmark_questions.csv`

Total questions: 41

### Service Line

| Service line | Count | % of dataset |
| --- | ---: | ---: |
| CFO | 19 | 46.3% |
| DD | 22 | 53.7% |

### BI Experience Band

| BI band | Count | % of dataset |
| --- | ---: | ---: |
| Junior (0-3) | 13 | 31.7% |
| Senior (4-7) | 28 | 68.3% |

### Complexity

| Complexity | Count | % of dataset |
| --- | ---: | ---: |
| Easy | 10 | 24.4% |
| Medium | 16 | 39.0% |
| Hard | 15 | 36.6% |

### Gradability

| Gradability | Count | % of dataset |
| --- | ---: | ---: |
| Deterministic | 28 | 68.3% |
| Hybrid | 7 | 17.1% |
| Judgment | 6 | 14.6% |

## Iteration Notes

| Version | Change |
| --- | --- |
| v2 | Added 35 questions, moving from 41 to 76 total. CFO representation increased from 46.3% to 51.3%; DD moved from 53.7% to 48.7%. Junior questions increased from 31.7% to 39.5%. Deterministic questions increased from 68.3% to 73.7%. |
| v1 | Initial benchmark dataset with 41 questions across CFO and DD service lines. |

## Update Process

For each new dataset iteration:

1. Add the new CSV as `data/<question_count>synth_benchmark_questions.csv`.
2. Keep prior versions in git history, or retain them as files if side-by-side comparison is needed.
3. Update this README with total questions and distributions for:
   - `service_line`
   - `bi_band`
   - `complexity`
   - `gradability`
4. Include both count and percentage for every represented value.
