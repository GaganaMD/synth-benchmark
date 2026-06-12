from __future__ import annotations

from pathlib import Path

from synthbench.common import read_json
from synthbench.state.diff import compute_state_diff
from synthbench.state.snapshots import load_snapshot


def validate_state_cell(cell: str | Path) -> list[str]:
    root = Path(cell)
    issues = []
    s0_path = root / "state" / "S0.json"
    s1_path = root / "state" / "S1.json"
    diff_path = root / "state" / "state_diff.json"
    for label, path in (("S0", s0_path), ("S1", s1_path), ("state_diff", diff_path)):
        if not path.exists():
            issues.append(f"missing {label}: {path}")
    if issues:
        return issues

    s0 = load_snapshot(s0_path)
    s1 = load_snapshot(s1_path)
    diff = read_json(diff_path)
    if not s0.get("snapshot_id"):
        issues.append("S0 missing snapshot_id")
    if not s1.get("snapshot_id"):
        issues.append("S1 missing snapshot_id")
    if not s0.get("timestamp"):
        issues.append("S0 missing timestamp")
    if not s1.get("timestamp"):
        issues.append("S1 missing timestamp")
    if s0.get("workspace_hash") != s0.get("workspace", {}).get("tree_sha256"):
        issues.append("S0 workspace_hash does not match workspace tree hash")
    if s1.get("workspace_hash") != s1.get("workspace", {}).get("tree_sha256"):
        issues.append("S1 workspace_hash does not match workspace tree hash")

    recomputed = compute_state_diff(s0, s1)
    if diff.get("workspace_hash_before") != recomputed.get("workspace_hash_before"):
        issues.append("diff workspace_hash_before is not reproducible")
    if diff.get("workspace_hash_after") != recomputed.get("workspace_hash_after"):
        issues.append("diff workspace_hash_after is not reproducible")
    if diff.get("changes") != recomputed.get("changes"):
        issues.append("diff changes are not reproducible")
    return issues
