"""ベイズ事前を指定して Beta-Binomial 推定を行う簡単な例。"""

from __future__ import annotations

import numpy as np

from evidec import EvidenceReport, Experiment
from evidec.bayes import BayesDecisionRule, fit_beta_binomial_from_prior


def main() -> None:
    # 0/1 の観測データ（CTR などを想定）
    control = np.array([0, 1, 0, 1, 0, 0, 1, 0, 0, 1])
    treatment = np.array([0, 1, 1, 1, 0, 1, 1, 0, 1, 1])

    # 既知の平均 CVR ~3% を 200 サンプル相当の事前として設定
    bayes_result = fit_beta_binomial_from_prior(
        prior_mean=0.03,
        prior_strength=200,
        control_success=int(control.sum()),
        control_total=int(control.size),
        treatment_success=int(treatment.sum()),
        treatment_total=int(treatment.size),
        seed=42,
    )

    # 周辺の頻度論的な結果（既存フロー）も計算
    exp = Experiment(name="bayes_example", metric="ctr", variant_names=("control", "treatment"))
    stat_result = exp.fit(control, treatment)

    # ベイズ判定ルール（SAFE を INCONCLUSIVE として扱う版）
    bayes_rule = BayesDecisionRule()
    bayes_decision = bayes_rule.judge(bayes_result)

    # 従来の EvidenceReport に bayes_result を渡すと Markdown にベイズセクションが付く
    report = EvidenceReport.from_result(
        experiment=exp,
        rule=bayes_rule,
        decision=bayes_decision,
        stat_result=stat_result,
        bayes_result=bayes_result,
    )

    print(report.markdown)


if __name__ == "__main__":
    main()
