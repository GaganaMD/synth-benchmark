from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.common import read_json, write_json
from synthbench.schemas.artifacts import CURRENT_VERSION
from synthbench.schemas.migrations import migrate_artifact
from synthbench.trace.events import read_events


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate a benchmark artifact to a target schema version.")
    parser.add_argument("--artifact-type", required=True, choices=["manifest", "canonical_output", "events", "S0", "S1", "state_diff"])
    parser.add_argument("--path", required=True)
    parser.add_argument("--output", required=True, help="Write migrated artifact here. Originals are not modified.")
    parser.add_argument("--target-version", default=CURRENT_VERSION)
    args = parser.parse_args()

    schema_type = "event" if args.artifact_type == "events" else "snapshot" if args.artifact_type in {"S0", "S1"} else args.artifact_type
    source = Path(args.path)
    output = Path(args.output)
    if args.artifact_type == "events":
        migrated = [migrate_artifact(schema_type, event, args.target_version) for event in read_events(source)]
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("".join(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n" for event in migrated), encoding="utf-8")
    else:
        document = read_json(source, default=None)
        if not isinstance(document, dict):
            raise SystemExit(f"{source} must contain a JSON object")
        write_json(output, migrate_artifact(schema_type, document, args.target_version))
    print(f"wrote migrated artifact: {output}")


if __name__ == "__main__":
    main()
