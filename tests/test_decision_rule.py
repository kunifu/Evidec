import pytest

from evidec.core.decision_rule import DecisionRule, _fmt_numeric, _fmt_p
from evidec.core.experiment import StatResult


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


def test_go_when_significant_and_meets_lift():
    rule = DecisionRule(alpha=0.05, min_lift=0.01, metric_goal="increase")
    decision = rule.judge(make_result(0.02, 0.01))
    assert decision.status == "GO"
    assert "GO" in decision.reason


def test_inconclusive_when_not_significant():
    rule = DecisionRule(alpha=0.05, min_lift=0.01, metric_goal="increase")
    decision = rule.judge(make_result(0.02, 0.2))
    assert decision.status == "INCONCLUSIVE"


def test_no_go_when_direction_reversed():
    rule = DecisionRule(alpha=0.05, min_lift=0.01, metric_goal="increase")
    decision = rule.judge(make_result(-0.03, 0.01))
    assert decision.status == "NO_GO"


def test_inconclusive_when_lift_too_small():
    rule = DecisionRule(alpha=0.05, min_lift=0.03, metric_goal="increase")
    decision = rule.judge(make_result(0.01, 0.001))
    assert decision.status == "INCONCLUSIVE"


def test_go_for_decrease_goal():
    rule = DecisionRule(alpha=0.05, min_lift=0.01, metric_goal="decrease")
    decision = rule.judge(make_result(-0.02, 0.01))
    assert decision.status == "GO"


def test_invalid_metric_goal_raises_value_error():
    rule = DecisionRule(metric_goal="invalid")  # type: ignore[arg-type]
    result = make_result(0.01, 0.01)
    with pytest.raises(ValueError):
        rule.judge(result)


def test_effect_size_requirement_sets_stats_and_reason():
    rule = DecisionRule(min_effect_size=0.05, min_lift=0.0, metric_goal="increase")
    result = make_result(effect=0.02, p_value=0.001, baseline=0.5)

    decision = rule.judge(result)

    assert decision.status == "INCONCLUSIVE"
    assert "min_effect_size" in decision.reason
    assert decision.stats["min_effect_size"] == pytest.approx(0.05)


def test_format_helpers_cover_numeric_and_pvalue():
    assert _fmt_p(0.00001) == "<0.0001"
    assert _fmt_numeric(0.12345, as_percent=False) == "+0.123"
    assert _fmt_numeric(0.12345, as_percent=True) == "+12.3%"
