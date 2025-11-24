import numpy as np
import pytest

from evidec.stats import ttest_means, ztest_proportions


def test_z検定が期待値を返す():
    # Arrange
    control = (30, 200)
    treatment = (50, 210)

    # Act
    effect, p_value, ci_low, ci_high = ztest_proportions(control, None, treatment, None)

    # Assert
    assert effect == pytest.approx(0.0880952381, rel=1e-6)
    assert p_value == pytest.approx(0.0244540348, rel=1e-6)
    assert ci_low == pytest.approx(0.0121523216, rel=1e-6)
    assert ci_high == pytest.approx(0.1640381546, rel=1e-6)


def test_z検定が少サンプルでも値を返す():
    # Arrange
    control = [0, 1, 0, 1, 0]
    treatment = [1, 1, 0, 0, 1]

    # Act
    effect, p_value, ci_low, ci_high = ztest_proportions(control, None, treatment, None)

    # Assert
    assert -1.0 < effect < 1.0
    assert 0 < p_value <= 1
    assert ci_low < ci_high


def test_t検定が期待値を返す():
    # Arrange
    control = np.array([10.1, 9.8, 10.4, 9.9, 10.0])
    treatment = np.array([10.8, 10.5, 10.6, 10.7, 10.9])

    # Act
    effect, p_value, ci_low, ci_high = ttest_means(control, treatment)

    # Assert
    assert effect == pytest.approx(0.66, rel=1e-6)
    assert p_value == pytest.approx(0.0010986043, rel=1e-6)
    assert ci_low == pytest.approx(0.3653900813, rel=1e-6)
    assert ci_high == pytest.approx(0.9546099187, rel=1e-6)


def test_t検定は最小サンプル未満で例外を投げる():
    # Arrange
    control = [1.0]
    treatment = [1.0, 2.0]

    # Act & Assert
    with pytest.raises(ValueError):
        ttest_means(control, treatment)


def test_t検定はequal_var指定でも実行される():
    # Arrange
    control = [1.0, 2.0, 3.0]
    treatment = [4.0, 5.0, 6.0]

    # Act
    effect, p_value, _, _ = ttest_means(control, treatment, equal_var=True)

    # Assert
    assert effect == pytest.approx(3.0)
    assert 0 < p_value < 0.05


def test_t検定は分散ゼロなら例外を投げる():
    # Arrange
    control = [1.0, 1.0, 1.0]
    treatment = [2.0, 2.0, 2.0]

    # Act & Assert
    with pytest.raises(ValueError, match="標準誤差が 0 です"):
        ttest_means(control, treatment)


def test_t検定はequal_varで分散ゼロなら例外を投げる():
    # Arrange
    control = [1.0, 1.0, 1.0]
    treatment = [2.0, 2.0, 2.0]

    # Act & Assert
    with pytest.raises(ValueError, match="標準誤差が 0 です"):
        ttest_means(control, treatment, equal_var=True)


def test_t検定は無限大を含むと例外を投げる():
    # Arrange
    control = [1.0, np.inf]
    treatment = [3.0, np.inf]

    # Act & Assert
    with pytest.raises(ValueError, match="NaN と無限大を除去した後も"):
        ttest_means(control, treatment)
