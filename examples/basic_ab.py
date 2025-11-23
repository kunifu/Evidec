"""evidec の最小 A/B テスト例。"""

from __future__ import annotations

import numpy as np

from evidec import DecisionRule, EvidenceReport, Experiment


def main() -> EvidenceReport:
    control = np.array([0, 1, 0, 1, 0, 0, 1, 0, 0, 1] * 10)
    treatment = np.array([1, 1, 1, 0, 1, 1, 0, 1, 1, 1] * 10)

    exp = Experiment(name="cta_color_test", metric="ctr", variant_names=("対照群", "実験群"))
    result = exp.fit(control, treatment)

    rule = DecisionRule(alpha=0.05, min_lift=0.01, metric_goal="increase")
    decision = rule.judge(result)

    report = EvidenceReport.from_result(exp, rule, decision, result)
    return report


if __name__ == "__main__":
    report = main()
    print(report.markdown)
