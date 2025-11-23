import numpy as np

from evidec.core.decision_rule import DecisionRule
from evidec.core.experiment import Experiment
from evidec.core.report import EvidenceReport


def test_evidence_report_contains_sections():
    exp = Experiment(name="ctr_report", metric="ctr", variant_names=("control", "treatment"))
    control = np.concatenate([np.zeros(70), np.ones(30)])
    treatment = np.concatenate([np.zeros(60), np.ones(40)])

    result = exp.fit(control, treatment)
    rule = DecisionRule(alpha=0.05, min_lift=0.01, metric_goal="increase")
    decision = rule.judge(result)

    report = EvidenceReport.from_result(exp, rule, decision, result)

    assert "## 主要結果" in report.markdown
    assert f"**判定**: ⚠️ **{decision.status}**" in report.markdown
    assert report.summary.startswith(exp.name)


def test_evidence_report_contains_simplified_sections():
    exp = Experiment(name="ctr_report", metric="ctr", variant_names=("control", "treatment"))
    control = np.concatenate([np.zeros(70), np.ones(30)])
    treatment = np.concatenate([np.zeros(60), np.ones(40)])

    result = exp.fit(control, treatment)
    rule = DecisionRule(alpha=0.05, min_lift=0.01, metric_goal="increase")
    decision = rule.judge(result)

    report = EvidenceReport.from_result(exp, rule, decision, result)

    assert "## 結論" in report.markdown
    assert "## 実験詳細" in report.markdown
    assert "> **注記**" in report.markdown
    assert "変化率 (相対)" in report.markdown


def test_render_markdown_reports_significant_and_staged_rollout():
    exp = Experiment(
        name="ctr_significant_go", metric="ctr", variant_names=("control", "treatment")
    )
    result = exp.fit((60, 200), (80, 200))
    rule = DecisionRule(alpha=0.05, min_lift=0.01, metric_goal="increase")
    decision = rule.judge(result)

    report = EvidenceReport.from_result(exp, rule, decision, result)

    assert decision.status == "GO"
    assert "有意差あり" in report.markdown
    assert "段階的ロールアウトを推奨" in report.markdown


def test_render_markdown_handles_negative_effect_and_no_go_rollout():
    exp = Experiment(name="ctr_negative", metric="ctr", variant_names=("control", "treatment"))
    result = exp.fit((80, 100), (50, 100))
    rule = DecisionRule(alpha=0.05, metric_goal="increase")
    decision = rule.judge(result)

    report = EvidenceReport.from_result(exp, rule, decision, result)

    assert decision.status == "NO_GO"
    assert "ロールアウト非推奨" in report.markdown


def test_render_markdown_handles_zero_baseline_without_relative_lift():
    exp = Experiment(name="ctr_zero_baseline", metric="ctr", variant_names=("control", "treatment"))
    result = exp.fit((0, 50), (5, 50))
    rule = DecisionRule(alpha=0.05, metric_goal="increase")
    decision = rule.judge(result)

    report = EvidenceReport.from_result(exp, rule, decision, result)

    assert decision.status == "INCONCLUSIVE"
    # ベースライン0の場合は相対リフトが計算できず "n/a" になる
    assert "**変化率 (相対)**: n/a" in report.markdown


def test_report_shows_point_and_relative_lift_clearly():
    exp = Experiment(name="ctr_clear_labels", metric="ctr", variant_names=("control", "treatment"))
    result = exp.fit((30, 100), (40, 100))
    rule = DecisionRule(alpha=0.05, min_lift=0.01, metric_goal="increase")
    decision = rule.judge(result)

    report = EvidenceReport.from_result(exp, rule, decision, result)

    assert "**変化量 (絶対)**: +10.0pp" in report.markdown
    assert "**変化率 (相対)**: +33.3%" in report.markdown
