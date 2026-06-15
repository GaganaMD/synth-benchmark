from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.trace.reconstruction import reconstruct_cell_events


def main() -> None:
    parser = argparse.ArgumentParser(description="Prototype reconstruction of inner Codex tool events from raw transcript text.")
    parser.add_argument("--cell", required=True, help="Run cell, e.g. runs/codex/TXN-001/seed-0")
    parser.add_argument("--output", help="JSONL output path. Defaults to <cell>/reconstructed_events.jsonl")
    parser.add_argument("--comparison-output", help="JSON comparison path. Defaults to <output>.comparison.json")
    args = parser.parse_args()

    cell = Path(args.cell)
    output_path = Path(args.output) if args.output else cell / "reconstructed_events.jsonl"
    comparison_path = Path(args.comparison_output) if args.comparison_output else output_path.with_suffix(".comparison.json")
    _events, comparison = reconstruct_cell_events(cell, output_path=output_path, comparison_path=comparison_path)
    print(json.dumps({"output": output_path.as_posix(), "comparison": comparison_path.as_posix(), **comparison}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
