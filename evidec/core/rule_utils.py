"""判定ルールに関する共通ユーティリティ。

report/decision で共有する軽量ロジックを集約する。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal, Protocol

from evidec.core.result import StatResult
from evidec.utils.formatting import _fmt_numeric

__all__ = ["RuleDisplayContext", "describe_rule_threshold", "is_ratio_metric"]


class RuleDisplayContext(Protocol):
    """レポート・レンダラーが参照する最低限の判定ルールインターフェース。"""

    alpha: float
    metric_goal: Literal["increase", "decrease"]
    min_lift: float


def is_ratio_metric(stat_result: StatResult) -> bool:
    """比率指標かどうかを判定する。"""

    return stat_result.baseline is not None and 0 <= stat_result.baseline <= 1


def describe_rule_threshold(rule: RuleDisplayContext, ratio_metric: bool) -> tuple[str, str]:
    """判定ルールの閾値を表示用に整形する。

    describe_threshold が実装されていればそれを利用し、
    未実装の場合は min_lift を使ったデフォルト表記を返す。
    """

    describe: Callable[[bool], tuple[str, str]] | None = getattr(rule, "describe_threshold", None)
    if callable(describe):
        return describe(ratio_metric)

    min_lift_str = _fmt_numeric(rule.min_lift, ratio_metric)
    criterion_text = f"α={rule.alpha:.3f}, 最小リフト={min_lift_str}, 目標={rule.metric_goal}"
    return criterion_text, min_lift_str
