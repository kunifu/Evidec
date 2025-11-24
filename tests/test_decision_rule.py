import pytest

from evidec.core import DecisionRule, StatResult
from evidec.utils.formatting import _fmt_numeric, _fmt_p


def make_result(effect: float, p_value: float, baseline: float = 0.2) -> StatResult:
    return StatResult(
        effect=effect,
        p_value=p_value,
        ci_low=effect - 0.01,
        ci_high=effect + 0.01,
        method="two-proportion z-test",
        metric="ctr",
        baseline=baseline,
    )


def test_有意かつリフト達成ならGOを返す():
    # Arrange
    rule = DecisionRule(alpha=0.05, min_lift=0.01, metric_goal="increase")
    result = make_result(0.02, 0.01)

    # Act
    decision = rule.judge(result)

    # Assert
    assert decision.status == "GO"
    assert "GO" in decision.reason


def test_p値が有意でなければINCONCLUSIVEを返す():
    # Arrange
    rule = DecisionRule(alpha=0.05, min_lift=0.01, metric_goal="increase")
    result = make_result(0.02, 0.2)

    # Act
    decision = rule.judge(result)

    # Assert
    assert decision.status == "INCONCLUSIVE"


def test_効果の符号が目標と逆ならNO_GOを返す():
    # Arrange
    rule = DecisionRule(alpha=0.05, min_lift=0.01, metric_goal="increase")
    result = make_result(-0.03, 0.01)

    # Act
    decision = rule.judge(result)

    # Assert
    assert decision.status == "NO_GO"


def test_リフト不足ならINCONCLUSIVEを返す():
    # Arrange
    rule = DecisionRule(alpha=0.05, min_lift=0.03, metric_goal="increase")
    result = make_result(0.01, 0.001)

    # Act
    decision = rule.judge(result)

    # Assert
    assert decision.status == "INCONCLUSIVE"


def test_減少目標で効果が負ならGOを返す():
    # Arrange
    rule = DecisionRule(alpha=0.05, min_lift=0.01, metric_goal="decrease")
    result = make_result(-0.02, 0.01)

    # Act
    decision = rule.judge(result)

    # Assert
    assert decision.status == "GO"


def test_metric_goalが不正ならValueErrorを投げる():
    # Arrange
    rule = DecisionRule(metric_goal="invalid")  # type: ignore[arg-type]
    result = make_result(0.01, 0.01)

    # Act & Assert
    with pytest.raises(ValueError):
        rule.judge(result)


def test_min_effect_size未達なら統計情報を含むINCONCLUSIVEを返す():
    # Arrange
    rule = DecisionRule(min_effect_size=0.05, min_lift=0.0, metric_goal="increase")
    result = make_result(effect=0.02, p_value=0.001, baseline=0.5)

    # Act
    decision = rule.judge(result)

    # Assert
    assert decision.status == "INCONCLUSIVE"
    assert "min_effect_size" in decision.reason
    assert decision.stats["min_effect_size"] == pytest.approx(0.05)


def test_formatヘルパーで数値とp値が整形される():
    # Arrange & Act
    p_value_formatted = _fmt_p(0.00001)
    numeric_plain = _fmt_numeric(0.12345, as_percent=False)
    numeric_percent = _fmt_numeric(0.12345, as_percent=True)

    # Assert
    assert p_value_formatted == "<0.0001"
    assert numeric_plain == "+0.123"
    assert numeric_percent == "+12.3%"
