from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.state.validation import validate_state_cell


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate S0/S1 snapshots and state_diff.json for a run cell.")
    parser.add_argument("--cell", required=True)
    args = parser.parse_args()
    issues = validate_state_cell(Path(args.cell))
    if issues:
        for issue in issues:
            print(f"ISSUE {issue}")
        raise SystemExit(1)
    print(f"state valid: {args.cell}")


if __name__ == "__main__":
    main()
