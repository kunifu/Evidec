import numpy as np
import pytest

from evidec.stats import ztest_proportions
from evidec.stats.ztest import _count_success_total


@pytest.mark.parametrize(
    "data",
    [
        (1.5, 10),  # non-integer success
        (1, 0),  # non-positive total
        (5, 3),  # success greater than total
    ],
)
def test_count_tuple_validation_errors(data):
    with pytest.raises(ValueError):
        _count_success_total(data)


@pytest.mark.parametrize(
    "data, expected",
    [
        (1, ValueError),
        (np.array([np.nan]), ValueError),
        (np.array(["a", "b"]), ValueError),
        (np.array([b"1", b"0"]), ValueError),
        (np.array([0, 1, 2]), ValueError),
    ],
)
def test_count_array_validation_errors(data, expected):
    with pytest.raises(expected):
        _count_success_total(data)


def test_count_success_total_accepts_bool_array():
    successes, total = _count_success_total(np.array([True, False, True, True]))
    assert successes == 3
    assert total == 4


def test_ztest_requires_treatment_success():
    with pytest.raises(ValueError):
        ztest_proportions((1, 10), None, None)


def test_ztest_requires_int_when_total_is_passed():
    with pytest.raises(TypeError):
        ztest_proportions(1.2, 10, (1, 10), None)
    with pytest.raises(TypeError):
        ztest_proportions((1, 10), None, 1.3, 10)


def test_ztest_validates_positive_totals_after_normalisation():
    with pytest.raises(ValueError):
        ztest_proportions(1, -5, 1, 10)


def test_ztest_pooled_variance_and_se_zero_checks():
    with pytest.raises(ValueError):
        ztest_proportions((0, 10), None, (0, 10), None)

    with pytest.raises(ValueError):
        ztest_proportions((10, 10), None, (0, 10), None)
