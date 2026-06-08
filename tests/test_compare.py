from compare_harnesses import paired_permutation


def test_permutation_detects_real_difference():
    result = paired_permutation([1.0] * 8, [0.0] * 8)
    assert result["diff"] == 1.0
    assert result["p"] < 0.05


def test_permutation_calls_cancelling_difference_tie():
    result = paired_permutation([1, 0, 1, 0], [0, 1, 0, 1])
    assert result["diff"] == 0
    assert result["p"] == 1.0

