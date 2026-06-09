# Complete Pipeline

Working notes and checklist for sharing, documenting, and evaluating the full Synth Benchmarking Pipeline.

## To Share

- [ ] Good legal paper from a good author
- [ ] Google Slides deck: https://docs.google.com/presentation/d/1Bnutl7z5361Yw3xGSceg9PRx14vA2XeUtRLe_Q_3Ra4/edit?usp=sharing
- [ ] Overleaf architecture for the entire pipeline

## Documentation

- [ ] Document types of data location: offline or OneDrive
- [ ] Evaluate a harness paper:
  - [ ] What they did
  - [ ] Why they did it
  - [ ] What evaluations they considered
- [ ] Identify evaluation metrics for long-horizon agents
- [ ] Extract factors that matter most while benchmarking harnesses from papers
- [ ] Determine whether evaluation metrics differ for short-horizon and long-horizon tasks
- [ ] Define determinism-by-design: meaning and significance
- [ ] Define our metrics

## Evaluation Pipeline

- [ ] See and evaluate the output, then map it to the metrics
- [ ] Create scripts to run all data points, collect output, and evaluate based on the defined metrics
- [ ] Run a fabrication check and confirm whether current metrics cover this
- [ ] Identify differences in the rubric

## Open Questions

- [ ] Should one task have multiple metrics, or just one?
- [ ] Should metrics be triggered based on output format?
- [ ] Is output-format-based triggering the right approach?
- [ ] What are current benchmark papers doing now?
