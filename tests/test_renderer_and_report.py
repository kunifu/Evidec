from evidec.core.decision_rule import Decision, DecisionRule, NonInferiorityRule
from evidec.core.experiment import Experiment
from evidec.core.report import EvidenceReport
from evidec.report.renderer import render_markdown


def _make_stat_result() -> tuple[Experiment, DecisionRule, EvidenceReport, str]:
    exp = Experiment(name="sample", metric="ctr", variant_names=("control", "treat"))
    result = exp.fit([0, 1, 0, 1], [0, 1, 1, 1])
    rule = DecisionRule(alpha=0.05, min_lift=0.0, metric_goal="increase")
    decision = rule.judge(result)
    report = EvidenceReport.from_result(exp, rule, decision, result)
    markdown = render_markdown(exp, decision, result, rule)
    return exp, rule, report, markdown


def test_標準ルールで最小リフトを表示する() -> None:
    # Arrange
    exp, rule, report, markdown = _make_stat_result()

    # Act
    decision_rule_text = report.decision_rule

    # Assert
    assert "最小リフト" in decision_rule_text
    assert "最小リフト" in markdown
    assert str(rule.min_lift) in markdown or "%" in markdown


def test_非劣性ルールでマージンを表示する() -> None:
    # Arrange
    exp = Experiment(name="ni", metric="ctr", variant_names=("control", "treat"))
    result = exp.fit([0, 1, 0, 1], [0, 1, 0, 1])
    rule = NonInferiorityRule(alpha=0.05, margin=0.02, metric_goal="increase")
    decision = rule.judge(result)

    # Act
    report = EvidenceReport.from_result(exp, rule, decision, result)
    markdown = render_markdown(exp, decision, result, rule)

    # Assert
    assert "許容悪化幅(下限)" in report.decision_rule
    assert "許容悪化幅(下限)" in markdown
    assert "-2.0%" in markdown


class DummyRule:
    alpha = 0.05
    min_lift = 0.02
    metric_goal = "increase"


def test_describe_threshold未実装でもフォールバック表示できる() -> None:
    # Arrange
    exp = Experiment(name="dummy", metric="ctr", variant_names=("control", "treat"))
    result = exp.fit([0, 1, 0, 1], [1, 1, 1, 1])
    decision = Decision(status="INCONCLUSIVE", reason="dummy", stats={})
    rule = DummyRule()

    # Act
    report = EvidenceReport.from_result(exp, rule, decision, result)
    markdown = render_markdown(exp, decision, result, rule)

    # Assert
    assert "最小リフト" in report.decision_rule
    assert "最小リフト" in markdown
