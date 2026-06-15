# Phase 4C Trace Fidelity Integration

Phase 4C integrates transcript-derived trace reconstruction into run intelligence without altering native traces or official grading.

## Goals

- Preserve `events.jsonl` as the official native execution trace.
- Automatically generate `reconstructed_events.jsonl` from Codex transcript artifacts.
- Compute trace fidelity metrics for native and reconstructed traces.
- Add both views to `run_intelligence_report.json` and `run_intelligence_report.md`.
- Never overwrite original traces.

## Artifacts

For a run cell such as `runs/codex/TXN-001/seed-0`, intelligence generation now may create:

```text
runs/codex/TXN-001/seed-0/reconstructed_events.jsonl
runs/codex/TXN-001/seed-0/reconstructed_events.comparison.json
```

These artifacts are derived from:

```text
raw_response.txt
final_output.md
events.jsonl
manifest.json
```

## Metrics

The run intelligence report includes:

```json
{
  "trace_fidelity_analysis": {
    "official_metrics": {
      "tool_capture_recall": 0.055556,
      "file_capture_recall": 0.0,
      "verification_capture_recall": 0.5,
      "trace_fidelity_score": 0.185185
    },
    "reconstructed_metrics": {
      "tool_capture_recall": 1.0,
      "file_capture_recall": 1.0,
      "verification_capture_recall": 1.0,
      "trace_fidelity_score": 1.0
    }
  }
}
```

Metric definitions:

| Metric | Definition |
|---|---|
| `tool_capture_recall` | Native or reconstructed tool events divided by expected tool events inferred from transcript reconstruction. |
| `file_capture_recall` | Native or reconstructed file read/write events divided by reconstructed file read/write events. |
| `verification_capture_recall` | Native or reconstructed verification events divided by reconstructed verification events. |
| `trace_fidelity_score` | Mean of tool, file, and verification capture recall. |

## Official vs Reconstructed Metrics

`official_metrics` always describe native `events.jsonl`.

`reconstructed_metrics` describe `reconstructed_events.jsonl`.

Official grading continues to use native traces unless an evaluator explicitly opts into reconstructed events in a separate study. This keeps historical scores stable and preserves backward compatibility.

## Safety

Trace reconstruction is observational. It does not execute commands, modify task outputs, or mutate native traces.

## Limitations

- Transcript reconstruction depends on Codex CLI transcript format.
- Python heredocs are recognized as tool calls, but their internal file operations are inferred heuristically.
- Native structured telemetry should replace transcript parsing when available.
