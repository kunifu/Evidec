"""実験の実行を管理するクラス。"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Literal, TypeAlias, cast

import numpy as np
from numpy.typing import NDArray

from evidec.core.result import StatResult
from evidec.frequentist import ttest_means, ztest_proportions

NDArrayFloat: TypeAlias = NDArray[np.float64]

__all__ = ["Experiment"]


@dataclass(frozen=True)
class Experiment:
    """A/Bテストの実験設定と実行を管理するクラス。

    実験の基本情報と統計検定の実行を担当し、
    結果をStatResultとして保持する。

    Attributes:
        name: 実験名
        metric: 測定対象のメトリクス名（例: "ctr", "cvr"）
        variant_names: 比較対象のバリアント名（control, treatment）
    """

    name: str
    metric: str
    variant_names: tuple[str, str]
    _last_result: StatResult | None = field(default=None, init=False, repr=False, compare=False)

    def _is_count_tuple(self, data: object) -> bool:
        return (
            isinstance(data, (tuple, list))
            and len(data) == 2
            and all(isinstance(x, (int, np.integer)) for x in data)
        )

    def _to_array(self, data: Iterable[float] | NDArrayFloat) -> NDArrayFloat:
        arr: NDArrayFloat = np.asarray(data, dtype=float)
        arr = arr[~np.isnan(arr)]
        if arr.size == 0:
            raise ValueError("NaN を除去した結果、入力データが空です")
        return arr

    def _is_binary_array(self, arr: NDArrayFloat) -> bool:
        unique = np.unique(arr)
        return bool(np.all((unique == 0) | (unique == 1)))

    def _resolve_kind(
        self, control_data: object, treatment_data: object
    ) -> Literal["proportion", "mean"]:
        control_is_count = self._is_count_tuple(control_data)
        treatment_is_count = self._is_count_tuple(treatment_data)
        if control_is_count or treatment_is_count:
            if not (control_is_count and treatment_is_count):
                raise ValueError("対照・処理の両方で (成功数, 総数) を指定してください")
            return "proportion"

        control_arr = self._to_array(control_data)  # type: ignore[arg-type]
        treatment_arr = self._to_array(treatment_data)  # type: ignore[arg-type]
        if self._is_binary_array(control_arr) and self._is_binary_array(treatment_arr):
            return "proportion"
        return "mean"

    def fit(self, control_data: object, treatment_data: object) -> StatResult:
        """適切な統計検定を実行し、結果をStatResultとして返す。

        データ形式に応じて自動的に検定手法を選択：
        - 0/1値または(成功数, 総数)形式 → 比率のz検定
        - 連続値 → 平均のt検定
        """

        if len(self.variant_names) != 2:
            raise ValueError("variant_names は2要素を含む必要があります")

        kind = self._resolve_kind(control_data, treatment_data)

        if kind == "proportion":
            control_input = cast(Iterable[float] | tuple[int, int], control_data)
            treatment_input = cast(Iterable[float] | tuple[int, int], treatment_data)
            effect, p_value, ci_low, ci_high = ztest_proportions(
                control_input, None, treatment_input, None
            )
            if self._is_count_tuple(control_data):
                control_success, control_total = cast(tuple[int, int], control_data)
                baseline = control_success / control_total
            else:
                control_arr = self._to_array(cast(Iterable[float], control_data))
                baseline = float(control_arr.mean())
            method: Literal["two-proportion z-test", "two-sample t-test"] = "two-proportion z-test"
        else:
            control_arr = self._to_array(cast(Iterable[float], control_data))
            treatment_arr = self._to_array(cast(Iterable[float], treatment_data))
            effect, p_value, ci_low, ci_high = ttest_means(control_arr, treatment_arr)
            baseline = float(control_arr.mean())
            method = "two-sample t-test"

        result = StatResult(
            effect=effect,
            p_value=p_value,
            ci_low=ci_low,
            ci_high=ci_high,
            method=method,
            metric=self.metric,
            baseline=baseline,
        )
        object.__setattr__(self, "_last_result", result)
        return result

    def summary(self) -> dict[str, float | str | None]:
        if self._last_result is None:
            raise ValueError("summary() を呼ぶ前に fit() を実行してください")
        res = self._last_result
        return {
            "name": self.name,
            "metric": self.metric,
            "effect": round(res.effect, 4),
            "p_value": round(res.p_value, 4),
            "ci_low": round(res.ci_low, 4),
            "ci_high": round(res.ci_high, 4),
            "method": res.method,
            "baseline": res.baseline,
        }
