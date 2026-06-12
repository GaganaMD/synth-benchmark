from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.common import write_json
from synthbench.schemas.artifacts import all_schemas, schema_filename


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate JSON schema files and artifact contract documentation.")
    parser.add_argument("--schema-dir", default="schemas/artifacts")
    parser.add_argument("--docs-out", default="docs/ARTIFACT_CONTRACTS.md")
    args = parser.parse_args()

    schema_dir = Path(args.schema_dir)
    schema_dir.mkdir(parents=True, exist_ok=True)
    schemas = all_schemas()
    for artifact_type, schema in schemas.items():
        write_json(schema_dir / schema_filename(artifact_type), schema)
    Path(args.docs_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.docs_out).write_text(_render_markdown(schemas, schema_dir), encoding="utf-8")
    print(f"wrote {len(schemas)} schemas to {schema_dir}")
    print(f"wrote {args.docs_out}")


def _render_markdown(schemas: dict[str, dict[str, Any]], schema_dir: Path) -> str:
    lines = [
        "# Artifact Contracts",
        "",
        "Generated from `synthbench.schemas.artifacts`. Do not edit schema tables by hand; rerun `tools/generate_schema_docs.py` after schema changes.",
        "",
        "Phase 5.5 freezes the benchmark artifact contracts at schema version `1.0`.",
        "",
        "## Artifacts",
        "",
    ]
    for artifact_type, schema in schemas.items():
        filename = schema_filename(artifact_type)
        lines.extend(
            [
                f"### `{artifact_type}`",
                "",
                f"Schema file: [`schemas/artifacts/{filename}`](../schemas/artifacts/{filename})",
                "",
                f"Title: {schema.get('title')}",
                "",
                "Required fields:",
                "",
            ]
        )
        for field in schema.get("required", []):
            prop = schema.get("properties", {}).get(field, {})
            field_type = prop.get("type", "any")
            lines.append(f"- `{field}`: `{field_type}`")
        lines.extend(["", ""])
    lines.extend(
        [
            "## Validation",
            "",
            "Validate a full run cell:",
            "",
            "```bash",
            "python3 tools/validate_artifacts.py --cell runs/codex/TXN-001/seed-0 --require-canonical",
            "```",
            "",
            "Validate one artifact:",
            "",
            "```bash",
            "python3 tools/validate_artifacts.py --artifact-type manifest --path runs/codex/TXN-001/seed-0/manifest.json",
            "```",
            "",
            "## Compatibility",
            "",
            "The validator checks every artifact's `schema_version` against the frozen current version. Missing versions are reported as compatibility issues. `--allow-migration` applies available in-memory migrations before validation.",
            "",
            "## Migration Strategy",
            "",
            "Migration hooks live in `synthbench.schemas.migrations`. Version `1.0` is the baseline. Future versions should add explicit artifact-specific transforms and keep validators able to read older benchmark records without changing graders.",
            "",
            "Write a migrated copy without modifying the original:",
            "",
            "```bash",
            "python3 tools/migrate_artifact.py --artifact-type manifest --path old/manifest.json --output migrated/manifest.json",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
