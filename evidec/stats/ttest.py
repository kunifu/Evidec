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


def _preprocess(data: Iterable[float] | NDArrayFloat) -> NDArrayFloat:
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
        raise ValueError("NaN と無限大を除去した後も各サンプルに 2 件以上のデータが必要です")
    return array


def _validate_assumptions(var1: float, var2: float, equal_var: bool) -> None:
    """統計量の前提条件を検証する。

    Args:
        var1: 対照群の不偏分散
        var2: 実験群の不偏分散
        equal_var: 等分散を仮定するかどうか
    """
    # Welch's t-testの場合、両方の分散が0だと自由度計算でゼロ除算が発生する
    if not equal_var and var1 == 0 and var2 == 0:
        raise ValueError("標準誤差が 0 です。入力にばらつきがありません")


def _validate_postcalc(se: float) -> None:
    """計算後の統計量がt検定として成立しているかを検証する。"""
    if se == 0:
        raise ValueError("標準誤差が 0 です。入力にばらつきがありません")


def _welch_df(var1: float, var2: float, n1: int, n2: int) -> float:
    """Welchのt検定における自由度を計算する。"""
    num = (var1 / n1 + var2 / n2) ** 2
    denom = ((var1 / n1) ** 2) / (n1 - 1) + ((var2 / n2) ** 2) / (n2 - 1)
    return num / denom


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
    # 1. 前処理 (Preprocessing)
    control = _preprocess(control_samples)
    treatment = _preprocess(treatment_samples)

    # 2. 基本統計量の計算 (Basic Statistics)
    n1, n2 = control.size, treatment.size
    control_mean = float(control.mean())
    treatment_mean = float(treatment.mean())
    effect = treatment_mean - control_mean

    # ddof=1 で不偏分散を計算（標本から母集団の分散を推定するため）
    var1 = float(control.var(ddof=1))
    var2 = float(treatment.var(ddof=1))

    # 3. 前提条件の検証 (Assumption Validation)
    _validate_assumptions(var1, var2, equal_var)

    # 4. 検定統計量の計算 (Test Statistics Calculation)
    # p値はscipyに任せる（scipyも内部でWelch/Studentを切り替えている）
    _, p_value = stats.ttest_ind(treatment, control, equal_var=equal_var)

    if equal_var:
        df = float(n1 + n2 - 2)
        pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / df
        se = np.sqrt(pooled_var * (1 / n1 + 1 / n2))
    else:
        df = _welch_df(var1, var2, n1, n2)
        se = np.sqrt(var1 / n1 + var2 / n2)

    # 5. 事後検証 (Post-calculation Validation)
    _validate_postcalc(se)

    # 6. 信頼区間の計算 (Confidence Interval)
    # 95%信頼区間の臨界値（両側5%、上側2.5%点）
    t_crit = stats.t.ppf(0.975, df)
    ci_low = effect - t_crit * se
    ci_high = effect + t_crit * se

    return float(effect), float(p_value), float(ci_low), float(ci_high)


__all__ = ["ttest_means"]
