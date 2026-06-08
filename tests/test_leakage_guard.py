from pathlib import Path

import pytest

from grader.leakage_guard import assert_clean


def test_leakage_guard_trips_on_expected_json(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "expected.json").write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError):
        assert_clean(workspace)

