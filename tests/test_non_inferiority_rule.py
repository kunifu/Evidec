import pytest

from evidec.core.decision_rule import NonInferiorityRule
from evidec.core.experiment import StatResult


def _make_result(effect: float, ci_low: float, ci_high: float) -> StatResult:
    return StatResult(
        effect=effect,
        p_value=0.2,
        ci_low=ci_low,
        ci_high=ci_high,
        method="two-proportion z-test",
        metric="ctr",
        baseline=0.1,
    )


def test_増加目標でCI下限が許容内ならGO() -> None:
    # Arrange
    rule = NonInferiorityRule(alpha=0.05, margin=0.01, metric_goal="increase")
    result = _make_result(effect=-0.005, ci_low=-0.007, ci_high=0.003)

    # Act
    decision = rule.judge(result)

    # Assert
    assert decision.status == "GO"
    assert "悪化なし" in decision.reason


def test_増加目標でCI上限が悪化を示せばNO_GO() -> None:
    # Arrange
    rule = NonInferiorityRule(alpha=0.05, margin=0.01, metric_goal="increase")
    result = _make_result(effect=-0.02, ci_low=-0.030, ci_high=-0.012)

    # Act
    decision = rule.judge(result)

    # Assert
    assert decision.status == "NO_GO"
    assert "悪化" in decision.reason


def test_増加目標でCIが許容幅をまたげばINCONCLUSIVE() -> None:
    # Arrange
    rule = NonInferiorityRule(alpha=0.05, margin=0.01, metric_goal="increase")
    result = _make_result(effect=-0.001, ci_low=-0.012, ci_high=0.004)

    # Act
    decision = rule.judge(result)

    # Assert
    assert decision.status == "INCONCLUSIVE"


def test_減少目標でCI上限が許容内ならGO() -> None:
    # Arrange
    rule = NonInferiorityRule(alpha=0.05, margin=0.02, metric_goal="decrease")
    result = _make_result(effect=0.005, ci_low=-0.001, ci_high=0.015)

    # Act
    decision = rule.judge(result)

    # Assert
    assert decision.status == "GO"
    assert "悪化なし" in decision.reason


def test_減少目標でCI下限が許容外ならNO_GO() -> None:
    # Arrange
    rule = NonInferiorityRule(alpha=0.05, margin=0.01, metric_goal="decrease")
    result = _make_result(effect=0.03, ci_low=0.02, ci_high=0.04)

    # Act
    decision = rule.judge(result)

    # Assert
    assert decision.status == "NO_GO"
    assert "悪化" in decision.reason


def test_metric_goalが不正なら例外を投げる() -> None:
    # Arrange
    rule = NonInferiorityRule(alpha=0.05, margin=0.01, metric_goal="stay")

    # Act & Assert
    with pytest.raises(ValueError):
        _ = rule.judge(_make_result(effect=0.0, ci_low=-0.001, ci_high=0.001))


def test_min_liftは目標方向で符号が変わる() -> None:
    # Arrange
    increase_rule = NonInferiorityRule(alpha=0.05, margin=0.02, metric_goal="increase")
    decrease_rule = NonInferiorityRule(alpha=0.05, margin=0.02, metric_goal="decrease")

    # Act
    increase_min_lift = increase_rule.min_lift
    decrease_min_lift = decrease_rule.min_lift

    # Assert
    assert increase_min_lift == -0.02
    assert decrease_min_lift == 0.02


def test_describe_thresholdでマージン文字列を返す() -> None:
    # Arrange
    rule = NonInferiorityRule(alpha=0.05, margin=0.01, metric_goal="increase")

    # Act
    criterion, threshold = rule.describe_threshold(ratio_metric=True)

    # Assert
    assert "許容悪化幅(下限)" in criterion
    assert threshold == "-1.0%"


def test_describe_threshold_減少目標では上限表記になる() -> None:
    # Arrange
    rule = NonInferiorityRule(alpha=0.05, margin=0.02, metric_goal="decrease")

    # Act
    criterion, threshold = rule.describe_threshold(ratio_metric=True)

    # Assert
    assert "許容悪化幅(上限)" in criterion
    assert threshold == "+2.0%"
