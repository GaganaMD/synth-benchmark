from grader.judge import DIMENSIONS, judge
from grader.taxonomy import label_run


def test_judge_mock_runs_all_dimensions():
    result = judge("answer", "criterion")
    assert result["mock"] is True
    assert result["overall_mean"] == 75.0
    assert len(result["dimensions"]) == len(DIMENSIONS)


def test_taxonomy_labels_control_violation_and_timeout():
    assert label_run({"control_violation": True}) == {"outcome": "control_violation", "process": "safety_failure"}
    assert label_run({"timed_out": True}) == {"outcome": "timeout", "process": "budget_exhausted"}

