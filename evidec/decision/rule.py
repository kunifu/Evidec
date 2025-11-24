"""判定ルールと意思決定ロジックをまとめたモジュール。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from evidec.experiment.result import StatResult
from evidec.report.formatters import _fmt_ci, _fmt_numeric, _fmt_p

DecisionStatus = Literal["GO", "NO_GO", "INCONCLUSIVE"]

__all__ = ["DecisionRule", "Decision", "DecisionStatus"]


@dataclass(frozen=True)
class Decision:
    status: DecisionStatus
    reason: str
    stats: dict[str, float | str]


@dataclass(frozen=True)
class DecisionRule:
    """実験結果の判定基準を定義するルール。

    Attributes:
        alpha: 有意水準（通常0.05）。p値がこの値以下で統計的有意と判定。
        min_lift: 最小リフト。統計的有意性がある場合でも、
                 ビジネス的に意味のある最小限の改善幅を要求する基準。
                 例: min_lift=0.01 の場合、1%以上の改善が必要。
        metric_goal: 目標とする改善方向（"increase" または "decrease"）。
        min_effect_size: 最小効果量（オプション）。効果の絶対値がこの値を
                        下回る場合はINCONCLUSIVEと判定。
    """

    alpha: float = 0.05
    min_lift: float = 0.0
    metric_goal: Literal["increase", "decrease"] = "increase"
    min_effect_size: float | None = None

    def _validate_goal(self) -> None:
        if self.metric_goal not in ("increase", "decrease"):
            raise ValueError("metric_goal は 'increase' か 'decrease' を指定してください")

    def _is_ratio_metric(self, result: StatResult) -> bool:
        return result.baseline is not None and 0 <= result.baseline <= 1

    def judge(self, result: StatResult) -> Decision:
        """統計結果に基づいてビジネス判断を下す。

        p値、有意性、最小リフト、目標方向を考慮して、
        実験結果の採用可否を判定する。
        """
        self._validate_goal()
        ratio_metric = self._is_ratio_metric(result)

        effect = result.effect
        ci_str = _fmt_ci(result.ci_low, result.ci_high, ratio_metric)
        p_str = _fmt_p(result.p_value)
        desired_effect = effect if self.metric_goal == "increase" else -effect
        direction_ok = desired_effect >= 0
        magnitude_ok = desired_effect >= self.min_lift
        effect_size_ok = (
            True if self.min_effect_size is None else abs(effect) >= self.min_effect_size
        )
        significant = result.p_value <= self.alpha

        lift_str = _fmt_numeric(desired_effect, ratio_metric)
        min_lift_str = _fmt_numeric(self.min_lift, ratio_metric)
        effect_str = _fmt_numeric(effect, ratio_metric)
        common_prefix = f"p={p_str}, CI={ci_str}, lift={lift_str}, min_lift={min_lift_str}"

        if not direction_ok:
            status: DecisionStatus = "NO_GO"
            reason = (
                f"{common_prefix}, effect={effect_str} が目標方向("
                f"metric_goal={self.metric_goal})と逆 → NO_GO"
            )
        elif significant and magnitude_ok and effect_size_ok:
            status = "GO"
            reason = f"{common_prefix}, p ≤ α={self.alpha:.3f} かつ lift ≥ min_lift → GO"
        elif not significant:
            status = "INCONCLUSIVE"
            reason = f"{common_prefix}, p > α={self.alpha:.3f} → INCONCLUSIVE"
        elif not magnitude_ok:
            status = "INCONCLUSIVE"
            reason = f"{common_prefix}, p ≤ α={self.alpha:.3f} だが lift < min_lift → INCONCLUSIVE"
        else:  # effect_size_ok is False
            status = "INCONCLUSIVE"
            reason = (
                f"{common_prefix}, |effect|={abs(effect):.4f} < "
                f"min_effect_size={self.min_effect_size:.4f} → INCONCLUSIVE"
            )

        stats: dict[str, float | str] = {
            "p_value": result.p_value,
            "alpha": self.alpha,
            "effect": result.effect,
            "min_lift": self.min_lift,
            "method": result.method,
            "ci_low": result.ci_low,
            "ci_high": result.ci_high,
        }
        if self.min_effect_size is not None:
            stats["min_effect_size"] = self.min_effect_size

        return Decision(status=status, reason=reason, stats=stats)
