from __future__ import annotations

import argparse
import itertools
import random

from synthbench.common import read_json


def paired_scores(path_a: str, path_b: str) -> tuple[list[float], list[float]]:
    a = read_json(path_a)
    b = read_json(path_b)
    amap = {row["task_id"]: row["score"] for row in a.get("results", [])}
    bmap = {row["task_id"]: row["score"] for row in b.get("results", [])}
    ids = sorted(set(amap) & set(bmap))
    return [amap[i] for i in ids], [bmap[i] for i in ids]


def paired_permutation(a: list[float], b: list[float], iters: int = 10000, seed: int = 7) -> dict:
    diffs = [x - y for x, y in zip(a, b)]
    if not diffs:
        return {"diff": 0.0, "p": 1.0}
    observed = sum(diffs) / len(diffs)
    rng = random.Random(seed)
    more_extreme = 0
    total = 0
    if len(diffs) <= 12:
        signs_iter = itertools.product([1, -1], repeat=len(diffs))
    else:
        signs_iter = ([rng.choice([1, -1]) for _ in diffs] for _ in range(iters))
    for signs in signs_iter:
        total += 1
        perm = sum(d * s for d, s in zip(diffs, signs)) / len(diffs)
        if abs(perm) >= abs(observed):
            more_extreme += 1
    return {"diff": observed, "p": more_extreme / total}


def compare(path_a: str, path_b: str, alpha: float = 0.05, iters: int = 10000) -> dict:
    a, b = paired_scores(path_a, path_b)
    test = paired_permutation(a, b, iters=iters)
    if test["p"] < alpha and test["diff"] > 0:
        outcome = "significant-win"
    elif test["p"] < alpha and test["diff"] < 0:
        outcome = "significant-loss"
    else:
        outcome = "tie"
    return test | {"outcome": outcome, "n": len(a)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("A")
    parser.add_argument("B")
    parser.add_argument("--iters", type=int, default=10000)
    args = parser.parse_args()
    result = compare(args.A, args.B, iters=args.iters)
    print(result)


if __name__ == "__main__":
    main()

