from __future__ import annotations

import argparse
import csv

from grader.judge import judge


def validate(path: str) -> dict:
    diffs = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            result = judge(row.get("answer", ""), row.get("criterion", ""))
            human = float(row["human_score"])
            diffs.append(abs(result["overall_mean"] - human))
    mad = sum(diffs) / len(diffs) if diffs else 0.0
    return {"mean_abs_deviation": mad, "target": "< 3 on 0-100", "passed": mad < 3}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("human_scores_csv")
    args = parser.parse_args()
    print(validate(args.human_scores_csv))


if __name__ == "__main__":
    main()

