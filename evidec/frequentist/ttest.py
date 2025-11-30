"""Evidec 向け二群 t 検定ヘルパー。

連続値の二群平均差を評価したいときに使う（例: 平均滞在時間、平均売上）。
Welch t-test をデフォルトにし、等分散仮定は `equal_var=True` で切替。
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray
from scipy import stats

NDArrayFloat: TypeAlias = NDArray[np.float64]


def _preprocess(data: Iterable[float] | NDArrayFloat, *, role: str = "input") -> NDArrayFloat:
    """入力データをt検定用に前処理する。

    処理内容:
    1. NumPy配列への変換
    2. NaNおよび無限大(inf)の除去
    3. サンプルサイズ要件の確認 (n >= 2)
    """
    array: NDArrayFloat = np.asarray(data, dtype=float)
    # NaNと無限大を除去
    array = array[~np.isnan(array) & ~np.isinf(array)]

    if array.size < 2:
        raise ValueError(
            f"{role}: NaN と無限大を除去した後も各サンプルに 2 件以上のデータが必要です"
        )
    return array


def _validate_assumptions(var1: float, var2: float) -> None:
    """t検定の前提条件を検証する。

    Args:
        var1: 対照群の不偏分散
        var2: 実験群の不偏分散
    """
    # 分散が両群とも0なら標準誤差が0となり検定不能
    if var1 == 0 and var2 == 0:
        raise ValueError("標準誤差が 0 です。入力にばらつきがありません")


def _ensure_nonzero_standard_error(se: float) -> None:
    """標準誤差が 0 でないことを検証する。"""
    if se == 0:
        raise ValueError("標準誤差が 0 です。入力にばらつきがありません")  # pragma: no cover


def _compute_basic_stats(
    control: NDArrayFloat, treatment: NDArrayFloat
) -> tuple[int, int, float, float, float]:
    """サンプル数・分散・効果量など基本統計量を計算する。"""
    n1, n2 = control.size, treatment.size
    effect = float(treatment.mean() - control.mean())
    var1 = float(control.var(ddof=1))
    var2 = float(treatment.var(ddof=1))
    return n1, n2, var1, var2, effect


def _compute_standard_error(
    var1: float, var2: float, n1: int, n2: int, equal_var: bool
) -> tuple[float, float]:
    """標準誤差と自由度を計算する。"""
    if equal_var:
        df = float(n1 + n2 - 2)
        pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / df
        se = np.sqrt(pooled_var * (1 / n1 + 1 / n2))
    else:
        df = _welch_df(var1, var2, n1, n2)
        se = np.sqrt(var1 / n1 + var2 / n2)
    return df, se


def _compute_confidence_interval(effect: float, se: float, df: float) -> tuple[float, float]:
    """95%信頼区間を計算する。"""
    t_crit = stats.t.ppf(0.975, df)
    ci_low = effect - t_crit * se
    ci_high = effect + t_crit * se
    return float(ci_low), float(ci_high)


def _welch_df(var1: float, var2: float, n1: int, n2: int) -> float:
    """Welchのt検定における自由度を計算する。"""
    num = (var1 / n1 + var2 / n2) ** 2
    denom = ((var1 / n1) ** 2) / (n1 - 1) + ((var2 / n2) ** 2) / (n2 - 1)
    return num / denom


def _prepare_samples(
    control_samples: Iterable[float] | NDArrayFloat,
    treatment_samples: Iterable[float] | NDArrayFloat,
) -> tuple[NDArrayFloat, NDArrayFloat]:
    """前処理を共通化したヘルパー。"""

    control = _preprocess(control_samples, role="control")
    treatment = _preprocess(treatment_samples, role="treatment")
    return control, treatment


def _run_ttest(
    control: NDArrayFloat, treatment: NDArrayFloat, equal_var: bool
) -> tuple[float, float, float, float]:
    """t検定の主要ロジックをまとめたヘルパー。"""

    n1, n2, var1, var2, effect = _compute_basic_stats(control, treatment)
    _validate_assumptions(var1, var2)

    _, p_value = stats.ttest_ind(treatment, control, equal_var=equal_var)

    df, se = _compute_standard_error(var1, var2, n1, n2, equal_var)
    _ensure_nonzero_standard_error(se)

    ci_low, ci_high = _compute_confidence_interval(effect, se, df)
    return float(effect), float(p_value), float(ci_low), float(ci_high)


def ttest_means(
    control_samples: Iterable[float] | NDArrayFloat,
    treatment_samples: Iterable[float] | NDArrayFloat,
    *,
    equal_var: bool = False,
) -> tuple[float, float, float, float]:
    """独立した二群の平均差を検定する。

    連続値データの比較に使用し、効果量・p値・95%信頼区間を返す。
    分散が等しい場合のみequal_var=Trueを推奨（それ以外はWelchのt検定を使用）。

    Returns:
        (effect, p_value, ci_low, ci_high) のタプル
        effect = treatment - control（実験群 - 対照群）
    """
    control, treatment = _prepare_samples(control_samples, treatment_samples)
    return _run_ttest(control, treatment, equal_var)


__all__ = ["ttest_means"]
