"""NonInferiorityRule を最小構成で使うサンプル。"""

from __future__ import annotations

from evidec import EvidenceReport, Experiment, NonInferiorityRule


def main() -> EvidenceReport:
    """非劣性(悪化していないこと)を確認する最小例。"""

    # 非劣性を確認したい指標 (CTR を想定)。
    exp = Experiment(name="non_inferiority_ctr", metric="ctr", variant_names=("control", "test"))

    # 成功数/試行数で指定 (control: 50/100, test: 52/100)。
    result = exp.fit((50, 100), (52, 100))

    # 許容悪化幅 1pp で非劣性判定。
    rule = NonInferiorityRule(alpha=0.05, margin=0.01, metric_goal="increase")
    decision = rule.judge(result)

    # レポート生成 (Markdown は report.markdown)。
    report = EvidenceReport.from_result(exp, rule, decision, result)
    return report


if __name__ == "__main__":
    report = main()
    print(report.markdown)
