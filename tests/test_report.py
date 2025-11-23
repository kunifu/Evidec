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

    assert "## 統計的根拠" in report.markdown
    assert f"判定: **{decision.status}**" in report.markdown
    assert report.summary.startswith(exp.name)
