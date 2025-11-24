"""Evidence Report を Markdown 文字列に整形するレンダラー。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from evidec.report.formatters import _fmt_numeric, _fmt_p

if TYPE_CHECKING:  # pragma: no cover
    from evidec.decision.rule import Decision, DecisionRule
    from evidec.experiment.experiment import Experiment
    from evidec.experiment.result import StatResult


def render_markdown(
    experiment: Experiment, decision: Decision, stat_result: StatResult, rule: DecisionRule
) -> str:
    """実験結果を構造化されたMarkdownレポートに整形する。

    意思決定に必要な情報を「結論」「主要結果」「詳細」の順に整理し、
    シンプルで読みやすい形式で出力する。
    """
    ratio = stat_result.baseline is not None and 0 <= stat_result.baseline <= 1

    effect_str = _fmt_numeric(stat_result.effect, ratio)
    ci_low_str = _fmt_numeric(stat_result.ci_low, ratio)
    ci_high_str = _fmt_numeric(stat_result.ci_high, ratio)
    baseline_str = (
        _fmt_numeric(stat_result.baseline, ratio) if stat_result.baseline is not None else "n/a"
    )
    min_lift_str = _fmt_numeric(rule.min_lift, ratio)
    p_str = _fmt_p(stat_result.p_value)
    abs_lift_pp_str = (
        f"{stat_result.effect * 100:+.1f}pp" if ratio else effect_str
    )  # 比率指標はポイント差(pp)を明示

    # 相対リフト
    lift_ratio_str = "n/a"
    if stat_result.baseline is not None and stat_result.baseline != 0:
        lift_ratio = stat_result.effect / stat_result.baseline
        lift_ratio_str = _fmt_numeric(lift_ratio, True)

    # 判定ステータスとアイコン
    status_emoji = {
        "GO": "✅",
        "NO_GO": "❌",
        "INCONCLUSIVE": "⚠️",
    }.get(decision.status, "")

    # 推奨アクション
    action_recommendation = ""
    if decision.status == "GO":
        if stat_result.p_value < 0.001:
            action_recommendation = "全面ロールアウトを推奨（確度高）"
        else:
            action_recommendation = "段階的ロールアウトを推奨（モニタリング継続）"
    elif decision.status == "NO_GO":
        action_recommendation = "ロールアウト非推奨（現状維持または改善へ）"
    else:
        action_recommendation = "判断保留（追加データ収集またはテスト延長）"

    # 統計的有意性
    is_significant = stat_result.p_value <= rule.alpha
    significance_text = "有意差あり" if is_significant else "有意差なし"

    lines = [
        f"# エビデンスレポート: {experiment.name}",
        "",
        "## 結論",
        f"- **判定**: {status_emoji} **{decision.status}**",
        f"- **推奨アクション**: {action_recommendation}",
        f"- **理由**: {decision.reason}",
        "",
        "## 主要結果",
        f"- **指標**: {experiment.metric}",
        f"- **変化量 (絶対)**: {abs_lift_pp_str}",
        f"- **変化率 (相対)**: {lift_ratio_str}",
        f"- **確信度**: {significance_text} (p={p_str})",
        f"- **95%信頼区間**: [{ci_low_str}, {ci_high_str}]",
        "",
        "## 実験詳細",
        f"- **群構成**: {experiment.variant_names[0]} (Base) "
        f"vs {experiment.variant_names[1]} (Test)",
        f"- **ベースライン値**: {baseline_str}",
        f"- **検定手法**: {stat_result.method}",
        f"- **判定基準**: α={rule.alpha:.3f}, 最小リフト={min_lift_str}, 目標={rule.metric_goal}",
        "",
        "> **注記**",
        "> - 信頼区間が0を含まない場合、効果の方向性は確実です。",
        "> - p値は「差が偶然生じる確率」を表します。基準値(α)より小さい場合に有意とみなします。",
    ]

    return "\n".join(lines)


__all__ = ["render_markdown"]
