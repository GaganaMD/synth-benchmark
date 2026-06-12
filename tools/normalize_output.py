from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.common import read_json
from synthbench.normalization.output import normalize_cell, validate_canonical_output


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize adapter output into canonical_output.json.")
    parser.add_argument("--cell", required=True, help="Run cell directory, e.g. runs/codex/TXN-001/seed-0")
    parser.add_argument("--adapter-id", help="Override adapter ID. Defaults to submission.adapter or manifest harness.")
    parser.add_argument("--output", help="Output path. Defaults to <cell>/canonical_output.json")
    parser.add_argument("--validate-only", action="store_true", help="Validate an existing canonical output instead of regenerating.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    cell = Path(args.cell)
    output_path = Path(args.output) if args.output else cell / "canonical_output.json"
    if args.validate_only:
        canonical = read_json(output_path, default=None)
        if canonical is None:
            raise SystemExit(f"missing canonical output: {output_path}")
        issues = validate_canonical_output(canonical)
    else:
        canonical = normalize_cell(cell, adapter_id=args.adapter_id, output_path=output_path)
        issues = canonical["validation"]["issues"]

    if args.json:
        print(json.dumps({"output": output_path.as_posix(), "valid": not issues, "issues": issues}, indent=2, sort_keys=True))
    elif issues:
        for issue in issues:
            print(f"ISSUE {issue}")
    else:
        print(f"canonical output valid: {output_path}")
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
