"""Evidence Report を Markdown 文字列に整形するレンダラー。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from evidec.core.formatters import _fmt_numeric, _fmt_p

if TYPE_CHECKING:  # pragma: no cover
    from evidec.core.decision_rule import Decision, DecisionRule
    from evidec.core.experiment import Experiment, StatResult


def render_markdown(
    experiment: Experiment, decision: Decision, stat_result: StatResult, rule: DecisionRule
) -> str:
    """実験結果を構造化されたMarkdownレポートに整形する。

    統計結果・判定ルール・意思決定を統合し、
    ビジネスチームが共有しやすい形式で出力する。
    """
    ratio = stat_result.baseline is not None and 0 <= stat_result.baseline <= 1

    effect_str = _fmt_numeric(stat_result.effect, ratio)
    ci_low_str = _fmt_numeric(stat_result.ci_low, ratio)
    ci_high_str = _fmt_numeric(stat_result.ci_high, ratio)
    baseline_str = (
        _fmt_numeric(stat_result.baseline, ratio) if stat_result.baseline is not None else "n/a"
    )
    min_lift_str = _fmt_numeric(rule.min_lift, ratio)

    lines = [
        f"# エビデンスレポート: {experiment.name}",
        "## サマリー",
        f"- 指標: **{experiment.metric}**",
        f"- 群: {experiment.variant_names[0]} vs {experiment.variant_names[1]}",
        f"- 判定: **{decision.status}**",
        f"- 理由: {decision.reason}",
        "",
        "## 統計的根拠",
        f"- 検定手法: {stat_result.method}",
        f"- 効果 (処理 - 対照): {effect_str}",
        f"- 95%信頼区間: [{ci_low_str}, {ci_high_str}]",
        f"- p値: {_fmt_p(stat_result.p_value)}",
        f"- ベースライン ({experiment.variant_names[0]}): {baseline_str}",
        "",
        "## 判定ルール",
        f"- 有意水準 α: {rule.alpha:.3f}",
        f"- 最小リフト: {min_lift_str}",
        f"- 目標方向: {rule.metric_goal}",
        f"- 最小効果量: {rule.min_effect_size if rule.min_effect_size is not None else 'n/a'}",
        "",
        "## 解釈",
        decision.reason,
    ]
    return "\n".join(lines)


__all__ = ["render_markdown"]
