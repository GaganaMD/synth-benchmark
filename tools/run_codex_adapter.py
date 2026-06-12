from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.adapters.codex import CodexAdapterConfig, run_codex_adapter


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute one prepared run cell through the Codex adapter.")
    parser.add_argument("--cell", required=True, help="Run cell directory, e.g. runs/codex/TXN-001/seed-0")
    parser.add_argument("--mode", choices=["dry-run", "codex"], default="dry-run")
    parser.add_argument("--codex-command", nargs="+", default=["codex", "exec"], help="Command used in --mode codex.")
    parser.add_argument("--timeout-s", type=int)
    parser.add_argument("--retries", type=int, default=0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        result = run_codex_adapter(
            args.cell,
            CodexAdapterConfig(
                mode=args.mode,
                codex_command=tuple(args.codex_command),
                timeout_s=args.timeout_s,
                retries=args.retries,
            ),
        )
    except Exception as exc:
        raise SystemExit(f"adapter failed: {type(exc).__name__}: {exc}") from exc
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"{result['status']}: {result['cell']}")
        print(f"events: {result['events']}")
        print(f"state_diff: {result['state']['diff']}")


if __name__ == "__main__":
    main()
