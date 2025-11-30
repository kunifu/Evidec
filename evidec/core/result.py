"""統計検定結果のデータ構造。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

__all__ = ["StatResult"]


@dataclass(frozen=True)
class StatResult:
    effect: float
    p_value: float
    ci_low: float
    ci_high: float
    method: Literal["two-proportion z-test", "two-sample t-test"]
    metric: str
    baseline: float | None

    def to_dict(self) -> dict[str, float | str | None]:
        return {
            "effect": self.effect,
            "p_value": self.p_value,
            "ci_low": self.ci_low,
            "ci_high": self.ci_high,
            "method": self.method,
            "metric": self.metric,
            "baseline": self.baseline,
        }

