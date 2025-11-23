import numpy as np
import pytest

from evidec.stats import ttest_means, ztest_proportions


def test_ztest_matches_expected_values():
    effect, p_value, ci_low, ci_high = ztest_proportions((30, 200), None, (50, 210), None)

    assert effect == pytest.approx(0.0880952381, rel=1e-6)
    assert p_value == pytest.approx(0.0244540348, rel=1e-6)
    assert ci_low == pytest.approx(0.0121523216, rel=1e-6)
    assert ci_high == pytest.approx(0.1640381546, rel=1e-6)


def test_ztest_handles_small_sample_without_warning():
    effect, p_value, ci_low, ci_high = ztest_proportions(
        [0, 1, 0, 1, 0], None, [1, 1, 0, 0, 1], None
    )

    assert -1.0 < effect < 1.0
    assert 0 < p_value <= 1
    assert ci_low < ci_high


def test_ttest_matches_expected_values():
    control = np.array([10.1, 9.8, 10.4, 9.9, 10.0])
    treatment = np.array([10.8, 10.5, 10.6, 10.7, 10.9])

    effect, p_value, ci_low, ci_high = ttest_means(control, treatment)

    assert effect == pytest.approx(0.66, rel=1e-6)
    assert p_value == pytest.approx(0.0010986043, rel=1e-6)
    assert ci_low == pytest.approx(0.3653900813, rel=1e-6)
    assert ci_high == pytest.approx(0.9546099187, rel=1e-6)


def test_ttest_requires_minimum_samples():
    with pytest.raises(ValueError):
        ttest_means([1.0], [1.0, 2.0])


def test_ttest_equal_var_branch_runs():
    effect, p_value, _, _ = ttest_means([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], equal_var=True)

    assert effect == pytest.approx(3.0)
    assert 0 < p_value < 0.05
