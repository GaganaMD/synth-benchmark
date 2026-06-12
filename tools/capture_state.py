from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.common import read_json
from synthbench.state.diff import compute_state_diff, write_state_diff
from synthbench.state.snapshots import capture_snapshot, load_snapshot, write_snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture S0/S1 snapshots and compute state_diff.json for a run cell.")
    parser.add_argument("--cell", required=True)
    parser.add_argument("--label", required=True, choices=["S0", "S1"])
    parser.add_argument("--workspace-dir", help="Workspace directory. Defaults to manifest workspace_dir.")
    parser.add_argument("--outputs-dir", help="Outputs/artifacts directory. Defaults to cell/artifacts.")
    parser.add_argument("--mock-state", help="Optional JSON/text mock system state file.")
    parser.add_argument("--compute-diff", action="store_true", help="After S1 capture, compute state/state_diff.json.")
    args = parser.parse_args()

    cell = Path(args.cell)
    manifest = read_json(cell / "manifest.json")
    if not manifest:
        raise SystemExit(f"missing manifest: {cell / 'manifest.json'}")
    workspace = Path(args.workspace_dir or manifest["workspace_dir"])
    outputs = Path(args.outputs_dir or cell / "artifacts")
    mock_state = Path(args.mock_state) if args.mock_state else cell / "state" / "mock_state.json"
    if not mock_state.exists():
        mock_state = None
    snapshot = capture_snapshot(
        snapshot_id=f"{args.label}_{manifest.get('run_id')}",
        workspace_dir=workspace,
        outputs_dir=outputs,
        mock_state_path=mock_state,
    )
    snapshot_path = cell / "state" / f"{args.label}.json"
    write_snapshot(snapshot, snapshot_path)
    print(f"wrote {snapshot_path}")

    if args.compute_diff:
        if args.label != "S1":
            raise SystemExit("--compute-diff is only valid with --label S1")
        s0_path = cell / "state" / "S0.json"
        if not s0_path.exists():
            raise SystemExit(f"missing {s0_path}")
        diff = compute_state_diff(load_snapshot(s0_path), snapshot)
        diff["s0_snapshot_path"] = s0_path.as_posix()
        diff["s1_snapshot_path"] = snapshot_path.as_posix()
        write_state_diff(diff, cell / "state" / "state_diff.json")
        print(f"wrote {cell / 'state' / 'state_diff.json'}")


if __name__ == "__main__":
    main()
