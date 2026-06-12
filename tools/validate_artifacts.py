from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.schemas.validation import contract_is_valid, validate_cell_contract, validate_document
from synthbench.common import read_json
from synthbench.trace.events import read_events, validate_trace


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate frozen benchmark artifact contracts.")
    parser.add_argument("--cell", help="Run cell directory containing manifest/events/state/canonical output.")
    parser.add_argument("--artifact-type", choices=["manifest", "canonical_output", "events", "S0", "S1", "state_diff"])
    parser.add_argument("--path", help="Validate a single artifact path with --artifact-type.")
    parser.add_argument("--require-canonical", action="store_true", help="Require canonical_output.json in cell validation.")
    parser.add_argument("--allow-migration", action="store_true", help="Validate after applying available in-memory migrations.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if bool(args.cell) == bool(args.path):
        raise SystemExit("provide exactly one of --cell or --path")
    if args.path and not args.artifact_type:
        raise SystemExit("--path requires --artifact-type")

    if args.cell:
        results = validate_cell_contract(args.cell, require_canonical=args.require_canonical, allow_migration=args.allow_migration)
        valid = contract_is_valid(results)
    else:
        if args.artifact_type == "events":
            event_issues = []
            events = read_events(args.path)
            for idx, event in enumerate(events):
                for issue in validate_document("events", event, allow_migration=args.allow_migration):
                    event_issues.append(f"event[{idx}] {issue}")
            event_issues.extend(validate_trace(events))
            results = {"events": event_issues}
        else:
            document = read_json(args.path, default=None)
            if not isinstance(document, dict):
                results = {args.artifact_type: [f"{args.path} must contain a JSON object"]}
            else:
                results = {args.artifact_type: validate_document(args.artifact_type, document, allow_migration=args.allow_migration)}
        valid = contract_is_valid(results)

    if args.json:
        print(json.dumps({"valid": valid, "results": results}, indent=2, sort_keys=True))
    else:
        for artifact, issues in results.items():
            if issues:
                for issue in issues:
                    print(f"ISSUE {artifact}: {issue}")
            else:
                print(f"valid {artifact}")
    if not valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
