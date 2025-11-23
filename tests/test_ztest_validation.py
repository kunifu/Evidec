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
def test_成功数タプルが不正なら例外を投げる(data):
    # Arrange
    invalid = data

    # Act & Assert
    with pytest.raises(ValueError):
        _count_success_total(invalid)


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
def test_配列入力が不正なら例外を投げる(data, expected):
    # Arrange
    invalid = data

    # Act & Assert
    with pytest.raises(expected):
        _count_success_total(invalid)


def test_bool配列を成功数に変換できる():
    # Arrange
    raw = np.array([True, False, True, True])

    # Act
    successes, total = _count_success_total(raw)

    # Assert
    assert successes == 3
    assert total == 4


def test_トリートメント成功数が必須():
    # Arrange
    control = (1, 10)

    # Act & Assert
    with pytest.raises(ValueError):
        ztest_proportions(control, None, None)


def test_total指定時はintでないとエラーになる():
    # Arrange
    control_value = 1.2
    treatment_value = 1.3

    # Act & Assert
    with pytest.raises(TypeError):
        ztest_proportions(control_value, 10, (1, 10), None)
    with pytest.raises(TypeError):
        ztest_proportions((1, 10), None, treatment_value, 10)


def test_total正規化後が正でないとエラーになる():
    # Arrange & Act & Assert
    with pytest.raises(ValueError):
        ztest_proportions(1, -5, 1, 10)


def test_分散ゼロやSEゼロならエラーになる():
    # Arrange
    all_zero = (0, 10)
    all_one = (10, 10)

    # Act & Assert
    with pytest.raises(ValueError):
        ztest_proportions(all_zero, None, all_zero, None)

    with pytest.raises(ValueError):
        ztest_proportions(all_one, None, all_zero, None)
