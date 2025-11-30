"""ベイズ版の判定ルールを提供するモジュール。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from evidec.bayesian.beta_binomial import BayesResult
from evidec.core.decision_rule import Decision, DecisionStatus

__all__ = ["BayesDecisionRule"]


@dataclass(frozen=True)
class BayesDecisionRule:
    """Beta-Binomial 推定結果に基づき意思決定を行うルール。"""

    # 表示用のダミーα・目標方向（頻度論ルールとの互換表示のため）
    alpha: float = 0.05
    metric_goal: Literal["increase", "decrease"] = "increase"

    p_improve_go: float = 0.95
    p_safe: float = 0.975
    p_improve_safe: float = 0.80
    min_lift: float = 0.0

    def judge(self, bayes: BayesResult) -> Decision:
        """ベイズ推定結果に基づいて GO/NO_GO/INCONCLUSIVE を判定する。"""

        if (
            bayes.p_improve >= self.p_improve_go
            and bayes.p_above_tol >= self.p_safe
            and bayes.lift_mean >= self.min_lift
        ):
            status: DecisionStatus = "GO"
            reason = (
                f"P(Δ>0)={bayes.p_improve:.1%}≥{self.p_improve_go:.0%}, "
                f"P(Δ>{bayes.tolerance:+.1%})={bayes.p_above_tol:.1%}≥{self.p_safe:.0%} → GO"
            )
        elif bayes.p_above_tol < self.p_safe:
            status = "NO_GO"
            reason = "悪化リスクが許容を超過 → NO_GO"
        elif bayes.p_improve >= self.p_improve_safe:
            status = "INCONCLUSIVE"
            reason = "SAFE: 悪化リスクは低いが改善確率が基準未満 → INCONCLUSIVE"
        else:
            status = "INCONCLUSIVE"
            reason = "確率指標が閾値に達していない → INCONCLUSIVE"

        stats: dict[str, float | str] = {
            "p_improve": bayes.p_improve,
            "p_above_tol": bayes.p_above_tol,
            "lift_mean": bayes.lift_mean,
            "tolerance": bayes.tolerance,
            "p_improve_go": self.p_improve_go,
            "p_safe": self.p_safe,
            "p_improve_safe": self.p_improve_safe,
            "min_lift": self.min_lift,
        }
        if "SAFE" in reason:
            stats["label"] = "SAFE"

        return Decision(status=status, reason=reason, stats=stats)

    def describe_threshold(self, ratio_metric: bool) -> tuple[str, str]:
        """レポート表示用の閾値説明を返す。"""

        lift_str = f"{self.min_lift:+.2%}" if ratio_metric else f"{self.min_lift:+.4f}"
        criterion = f"P(Δ>0)≥{self.p_improve_go:.0%}, P(Δ>{lift_str})≥{self.p_safe:.0%}"
        return criterion, f"P(Δ>0)≥{self.p_improve_go:.0%}"
