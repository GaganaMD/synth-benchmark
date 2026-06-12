from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.common import read_json, write_json
from synthbench.state.audit import audit_files, duplicate_outputs, duplicate_postings, duplicate_side_effects


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit filesystem outputs and duplicate side effects for a run cell.")
    parser.add_argument("--cell", required=True)
    parser.add_argument("--expected-output", action="append", default=[])
    parser.add_argument("--postings-json", help="Optional JSON list of observed postings for duplicate detection.")
    args = parser.parse_args()

    cell = Path(args.cell)
    diff = read_json(cell / "state" / "state_diff.json")
    if not diff:
        raise SystemExit(f"missing diff: {cell / 'state' / 'state_diff.json'}")

    file_audit = audit_files(args.expected_output, diff)
    postings = []
    if args.postings_json:
        postings = json.loads(Path(args.postings_json).read_text(encoding="utf-8"))
        if not isinstance(postings, list):
            raise SystemExit("--postings-json must contain a JSON list")
    observed_outputs = file_audit["observed_outputs"]
    report = {
        "schema_version": "1.0",
        "cell": cell.as_posix(),
        "file_audit": file_audit,
        "duplicates": {
            "duplicate_outputs": duplicate_outputs(observed_outputs),
            "duplicate_postings": duplicate_postings(postings),
            "duplicate_side_effects": duplicate_side_effects(file_audit["effects"]),
        },
    }
    out = cell / "state" / "side_effect_audit.json"
    write_json(out, report)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
