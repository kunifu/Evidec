"""EvidenceReport のデータモデルと生成ヘルパー。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from evidec.decision.rule_utils import RuleDisplayContext, describe_rule_threshold, is_ratio_metric
from evidec.report.renderer import render_markdown
from evidec.utils.formatting import _fmt_ci, _fmt_numeric, _fmt_p

if TYPE_CHECKING:  # pragma: no cover
    from evidec.bayes.beta_binomial import BayesResult
    from evidec.decision.rule import Decision
    from evidec.experiment.experiment import Experiment
    from evidec.experiment.result import StatResult

__all__ = ["EvidenceReport"]


@dataclass(frozen=True)
class EvidenceReport:
    """実験結果の証拠レポート。

    統計結果、判定ルール、意思決定の根拠をまとめた
    ビジネス向けのレポートデータ。

    Attributes:
        summary: レポートの要約（実験名 + 判定結果）
        statistical_evidence: 統計的な証拠（効果量・信頼区間・p値）
        decision_rule: 適用された判定ルール
        interpretation: 判定の解釈と理由
        markdown: 完全なMarkdown形式のレポート
    """

    summary: str
    statistical_evidence: str
    decision_rule: str
    interpretation: str
    markdown: str
    bayes_result: BayesResult | None = None

    @classmethod
    def from_result(
        cls,
        experiment: Experiment,
        rule: RuleDisplayContext,
        decision: Decision,
        stat_result: StatResult,
        bayes_result: BayesResult | None = None,
    ) -> EvidenceReport:
        """実験結果から証拠レポートを生成する。

        統計結果・判定ルール・意思決定を統合し、
        ビジネス向けの構造化されたレポートを作成する。
        """
        ratio = is_ratio_metric(stat_result)
        effect_str = _fmt_numeric(stat_result.effect, ratio)
        ci_str = _fmt_ci(stat_result.ci_low, stat_result.ci_high, ratio)

        summary = f"{experiment.name}: {decision.status} ({decision.reason})"
        statistical = (
            f"{stat_result.method} 効果={effect_str}, 95%CI={ci_str}, "
            f"p値={_fmt_p(stat_result.p_value)}"
        )

        decision_rule, _ = describe_rule_threshold(rule, ratio)

        interpretation = decision.reason
        markdown = render_markdown(experiment, decision, stat_result, rule, bayes_result)
        return cls(
            summary=summary,
            statistical_evidence=statistical,
            decision_rule=decision_rule,
            interpretation=interpretation,
            markdown=markdown,
            bayes_result=bayes_result,
        )
