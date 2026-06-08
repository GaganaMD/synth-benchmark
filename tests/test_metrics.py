from metrics.calibration import brier, compute as compute_calibration, ece
from metrics.deployment import compute_autonomy, compute_time_saved
from metrics.timeout import compute as compute_timeout
from metrics.tool_use import compute as compute_tool_use


def test_brier_and_ece_known_inputs():
    pairs = [(0.9, 1), (0.8, 1), (0.2, 0), (0.1, 0)]
    assert round(brier(pairs), 4) == 0.025
    assert round(ece(pairs), 4) == 0.15


def test_calibration_mock_is_deterministic():
    result = compute_calibration(mode="mock")
    assert result["status"] == "mock"
    assert result["value"]["brier"] is not None
    assert result["value"]["ece"] is not None


def test_tool_use_pass_vs_shortcut_trajectory():
    task = {"expected_tool_calls": "3+ tool calls", "complexity": "Hard"}
    good = {
        "trajectory": {
            "tool_calls": [1, 2, 3],
            "read_all_inputs": True,
            "wrote_deliverable": True,
            "recovered_from_tool_error": True,
        }
    }
    bad = {
        "trajectory": {
            "tool_calls": [1],
            "read_all_inputs": False,
            "wrote_deliverable": False,
            "recovered_from_tool_error": False,
        }
    }
    assert compute_tool_use(task, good)["value"] == 1
    assert compute_tool_use(task, bad)["value"] < 1


def test_timeout_rate_counting():
    result = compute_timeout([{"timed_out": True, "score": 0}, {"timed_out": False, "score": 1}], mode="live")
    assert result["status"] == "live"
    assert result["value"] == 0.5
    assert len(result["score_vs_budget"]) == 2


def test_guardrail_voids_on_safety_violation_and_bad_auto_post():
    rows = [{"no_human_touch": True, "correct": True, "auto_handled": True, "expert_time_mins": 10, "agent_minutes": 1}]
    assert compute_autonomy(rows, bad_auto_post=0, safety_violations=1)["status"] == "VOID (unsafe)"
    assert compute_time_saved(rows, bad_auto_post=0.02, safety_violations=0)["status"] == "VOID (unsafe)"

