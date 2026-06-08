from __future__ import annotations

import argparse
import re
from pathlib import Path

from metrics.registry import is_live


PENDING = "pending live exec"
LIVE = "live"
PENDING_IDS = [11, 12, 14, 15, 16, 17, 18, 19]


def _update_table_line(line: str, live_ids: set[int]) -> str:
    if not line.startswith("|"):
        return line
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if len(cells) < 7:
        return line
    try:
        metric_id = int(cells[0])
    except ValueError:
        return line
    if metric_id in live_ids and cells[-1] == PENDING:
        cells[-1] = LIVE
        return "| " + " | ".join(cells) + " |"
    return line


def _update_caveat_list(text: str, live_ids: set[int]) -> str:
    still_pending = [str(i) for i in PENDING_IDS if i not in live_ids]
    replacement = (
        f'"{PENDING}" = the metric is defined but produces a real number only once\n'
        f"the harness runs against live tools. Still pending metric IDs: {', '.join(still_pending) if still_pending else 'none'}.\n"
        'Treat a 0 there as "not yet measured," not a result.'
    )
    pattern = re.compile(
        rf'"{re.escape(PENDING)}" = the metric is defined but produces a real number only once\n'
        r'the harness runs against live tools\. Treat a 0 there as "not yet measured," not a result\.',
        re.MULTILINE,
    )
    if pattern.search(text):
        return pattern.sub(replacement, text)
    pattern2 = re.compile(
        rf'"{re.escape(PENDING)}" = the metric is defined but produces a real number only once\n'
        r"the harness runs against live tools\. Still pending metric IDs: .*?\n"
        r'Treat a 0 there as "not yet measured," not a result\.',
        re.MULTILINE,
    )
    return pattern2.sub(replacement, text)


def update_metric_status(docs_path: str | Path = "docs/metrics_v2.md", results_root: str | Path = "results") -> bool:
    path = Path(docs_path)
    text = path.read_text(encoding="utf-8")
    live_ids = {metric_id for metric_id in PENDING_IDS if is_live(metric_id, results_root)}
    lines = [_update_table_line(line, live_ids) for line in text.splitlines()]
    updated = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    updated = _update_caveat_list(updated, live_ids)
    if updated != text:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs", default="docs/metrics_v2.md")
    parser.add_argument("--results", default="results")
    args = parser.parse_args()
    changed = update_metric_status(args.docs, args.results)
    print("updated" if changed else "no changes")


if __name__ == "__main__":
    main()

