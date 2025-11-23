import numpy as np
import pytest

from evidec.core.experiment import Experiment


def test_比率データを検出してz検定を選ぶ():
    # Arrange
    exp = Experiment(name="ctr_test", metric="ctr", variant_names=("control", "treatment"))
    control = np.array([0, 1, 0, 1, 0, 0, 1, 0, 0, 1] * 5)
    treatment = np.array([1, 1, 1, 0, 1, 1, 0, 1, 1, 1] * 5)

    # Act
    result = exp.fit(control, treatment)

    # Assert
    assert result.method == "two-proportion z-test"
    assert result.baseline == pytest.approx(control.mean())
    assert exp.summary()["metric"] == "ctr"


def test_連続値ではt検定を選ぶ():
    # Arrange
    exp = Experiment(name="avg_test", metric="avg", variant_names=("control", "treatment"))
    control = np.array([1.0, 2.0, 3.0, 2.5, 2.1])
    treatment = np.array([2.0, 2.5, 3.5, 3.0, 2.9])

    # Act
    result = exp.fit(control, treatment)

    # Assert
    assert result.method == "two-sample t-test"
    assert result.effect == pytest.approx(treatment.mean() - control.mean())


def test_バリアントが2つ未満なら例外を投げる():
    # Arrange
    exp = Experiment(name="bad", metric="ctr", variant_names=("control",))

    # Act & Assert
    with pytest.raises(ValueError):
        exp.fit((1, 10), (2, 10))


def test_集計形式が混在するとエラーになる():
    # Arrange
    exp = Experiment(name="mix", metric="ctr", variant_names=("control", "treatment"))

    # Act & Assert
    with pytest.raises(ValueError):
        exp.fit((1, 10), [0, 1, 0, 1])


def test_集計入力でも結果を保存しサマリーを返す():
    # Arrange
    exp = Experiment(name="ctr_test", metric="ctr", variant_names=("control", "treatment"))

    # Act & Assert (summary ガードも確認)
    with pytest.raises(ValueError):
        exp.summary()

    result = exp.fit((5, 10), (7, 10))

    # Assert
    assert result.baseline == pytest.approx(0.5)
    assert result.to_dict()["method"] == "two-proportion z-test"
    assert exp.summary()["baseline"] == pytest.approx(0.5)


def test_全要素NaNなら例外を投げる():
    # Arrange
    exp = Experiment(name="nan", metric="ctr", variant_names=("c", "t"))
    invalid = np.array([np.nan])

    # Act & Assert
    with pytest.raises(ValueError):
        exp.fit(invalid, invalid)
