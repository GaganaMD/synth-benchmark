from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.registry.fixtures import materialize_from_blobs, register_fixture, require_fixture


def main() -> None:
    parser = argparse.ArgumentParser(description="Register or retrieve immutable workspace fixtures.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    reg = sub.add_parser("register")
    reg.add_argument("--fixture-version", required=True)
    reg.add_argument("--workspace", required=True)
    reg.add_argument("--fixture-root", default="immutable_inputs")
    reg.add_argument("--registry", default="registry/fixtures.jsonl")

    mat = sub.add_parser("materialize")
    mat.add_argument("--fixture-version", required=True)
    mat.add_argument("--out", required=True)
    mat.add_argument("--registry", default="registry/fixtures.jsonl")
    mat.add_argument("--overwrite", action="store_true")

    args = parser.parse_args()
    if args.cmd == "register":
        record = register_fixture(args.fixture_version, args.workspace, args.fixture_root, args.registry)
        print(f"registered fixture {record['fixture_version']} files={record['file_count']} workspace_hash={record['workspace_hash']}")
    else:
        record = require_fixture(args.fixture_version, args.registry)
        destination = materialize_from_blobs(record, args.out, args.overwrite)
        print(f"materialized fixture {record['fixture_version']} to {destination}")


if __name__ == "__main__":
    main()
