from pathlib import Path

from metrics.registry import is_live
from synthbench.common import write_json
from tools.update_metric_status import update_metric_status


def test_registry_is_live_only_on_real_value(tmp_path: Path):
    results = tmp_path / "results" / "h"
    results.mkdir(parents=True)
    write_json(results / "results.json", {"suite_metrics": {"m": {"metric_id": 11, "value": None, "status": "mock"}}})
    assert is_live(11, tmp_path / "results") is False
    write_json(results / "results.json", {"suite_metrics": {"m": {"metric_id": 11, "value": 0.9, "status": "live"}}})
    assert is_live(11, tmp_path / "results") is True


def test_update_metric_status_flips_pending_and_is_idempotent(tmp_path: Path):
    docs = tmp_path / "metrics_v2.md"
    docs.write_text(
        '| # | Metric | Role | Watchdog / counter | Optimise or report? | Fast/slow | Status |\n'
        '|---|---|---|---|---|---|---|\n'
        '| 11 | State-audit pass rate | quality | over-queue | optimise | slow | pending live exec |\n\n'
        '"pending live exec" = the metric is defined but produces a real number only once\n'
        'the harness runs against live tools. Treat a 0 there as "not yet measured," not a result.\n',
        encoding="utf-8",
    )
    results = tmp_path / "results" / "h"
    results.mkdir(parents=True)
    write_json(results / "results.json", {"suite_metrics": {"state": {"metric_id": 11, "value": 0.99, "status": "live"}}})
    assert update_metric_status(docs, tmp_path / "results") is True
    first = docs.read_text(encoding="utf-8")
    assert "| 11 | State-audit pass rate | quality | over-queue | optimise | slow | live |" in first
    assert update_metric_status(docs, tmp_path / "results") is False
    assert docs.read_text(encoding="utf-8") == first

