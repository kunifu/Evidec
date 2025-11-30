"""判定ルールと意思決定ロジックをまとめたモジュール。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from evidec.core.result import StatResult
from evidec.core.rule_utils import is_ratio_metric
from evidec.utils.formatting import _fmt_ci, _fmt_numeric, _fmt_p

DecisionStatus = Literal["GO", "NO_GO", "INCONCLUSIVE"]

__all__ = ["DecisionRule", "NonInferiorityRule", "Decision", "DecisionStatus", "RuleFormatter"]


class RuleFormatter(Protocol):
    """判定ルールの表示情報を提供するための共通インターフェース。"""

    def describe_threshold(self, ratio_metric: bool) -> tuple[str, str]:
        """判定基準の説明文と主要な閾値（表示用文字列）を返す。"""


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

    def judge(self, result: StatResult) -> Decision:
        """統計結果に基づいてビジネス判断を下す。

        p値、有意性、最小リフト、目標方向を考慮して、
        実験結果の採用可否を判定する。
        """
        self._validate_goal()
        ratio_metric = is_ratio_metric(result)

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

    def describe_threshold(self, ratio_metric: bool) -> tuple[str, str]:
        """判定基準を表示用に文字列化する。

        Returns:
            criterion_text: 判定基準の説明文
            threshold_str: 表示に用いる主要な閾値文字列（min_lift を可視化）
        """

        min_lift_str = _fmt_numeric(self.min_lift, ratio_metric)
        criterion_text = (
            f"α={self.alpha:.3f}, 最小リフト={min_lift_str}, 目標={self.metric_goal}"
        )
        return criterion_text, min_lift_str


@dataclass(frozen=True)
class NonInferiorityRule:
    """悪化していないことを確認するための非劣性判定ルール。

    margin は「許容される悪化幅」の絶対値を表す。
    例: metric_goal="increase", margin=0.01 の場合、
    CI 下限が -0.01 より大きければ「悪化なし (GO)」とみなす。
    """

    alpha: float = 0.05
    margin: float = 0.01
    metric_goal: Literal["increase", "decrease"] = "increase"

    def _validate_goal(self) -> None:
        if self.metric_goal not in ("increase", "decrease"):
            raise ValueError("metric_goal は 'increase' か 'decrease' を指定してください")

    def judge(self, result: StatResult) -> Decision:
        """非劣性 (悪化していないこと) を判定する。

        - metric_goal="increase": CI下限が -margin より大きければ GO、
          CI上限が -margin 未満なら NO_GO、それ以外は INCONCLUSIVE。
        - metric_goal="decrease": CI上限が margin 以下なら GO、
          CI下限が margin を超えれば NO_GO、それ以外は INCONCLUSIVE。
        """

        self._validate_goal()
        ratio_metric = is_ratio_metric(result)

        ci_low, ci_high = result.ci_low, result.ci_high

        # 判定ロジック（有害方向に対する許容幅で判断）
        if self.metric_goal == "increase":
            go = ci_low >= -self.margin
            nogo = ci_high < -self.margin
        else:  # decrease が目標 → 有害方向は正の差分
            go = ci_high <= self.margin
            nogo = ci_low > self.margin

        margin_str = _fmt_numeric(self.margin, ratio_metric, force_sign=False)
        ci_str = _fmt_ci(ci_low, ci_high, ratio_metric)

        if go:
            status: DecisionStatus = "GO"
            if self.metric_goal == "increase":
                reason_detail = (
                    f"CI下限={_fmt_numeric(ci_low, ratio_metric)} ≥ -{margin_str}"
                )
            else:
                reason_detail = (
                    f"CI上限={_fmt_numeric(ci_high, ratio_metric)} ≤ +{margin_str}"
                )
            reason = f"非劣性クリア: {reason_detail} → 悪化なしと判断"
        elif nogo:
            status = "NO_GO"
            if self.metric_goal == "increase":
                reason_detail = (
                    f"CI上限={_fmt_numeric(ci_high, ratio_metric)} < -{margin_str}"
                )
            else:
                reason_detail = (
                    f"CI下限={_fmt_numeric(ci_low, ratio_metric)} > +{margin_str}"
                )
            reason = f"悪化懸念: {reason_detail}"
        else:
            status = "INCONCLUSIVE"
            limit_str = f"-{margin_str}" if self.metric_goal == "increase" else f"+{margin_str}"
            reason = (
                "判断保留: CIが許容悪化幅をまたぐ "
                f"(CI={ci_str}, 許容ライン={limit_str})"
            )

        stats: dict[str, float | str] = {
            "p_value": result.p_value,
            "alpha": self.alpha,
            "effect": result.effect,
            "margin": self.margin,
            "method": result.method,
            "ci_low": result.ci_low,
            "ci_high": result.ci_high,
        }

        return Decision(status=status, reason=reason, stats=stats)

    @property
    def min_lift(self) -> float:
        """非劣性ルールにおける表示用の閾値。

        renderer などで一貫した表示を行うため、
        increase 目標の場合は -margin（許容する下振れ）、
        decrease 目標の場合は +margin（許容する上振れ）を返す。
        """

        return -self.margin if self.metric_goal == "increase" else self.margin

    def describe_threshold(self, ratio_metric: bool) -> tuple[str, str]:
        """非劣性マージンを用いた判定基準の説明文と閾値を返す。"""

        margin_val_str = _fmt_numeric(self.margin, ratio_metric, force_sign=False)

        if self.metric_goal == "increase":
            threshold_val = f"-{margin_val_str}"
            criterion_text = (
                f"α={self.alpha:.3f}, 許容悪化幅(下限)={threshold_val}, 目標={self.metric_goal}"
            )
        else:
            threshold_val = f"+{margin_val_str}"
            criterion_text = (
                f"α={self.alpha:.3f}, 許容悪化幅(上限)={threshold_val}, 目標={self.metric_goal}"
            )
        return criterion_text, threshold_val
