"""二項比率のz検定ユーティリティ。

0/1データの比率差を評価する際に使用（例: CTR, CVR）。
サンプル数が十分に大きいことを前提とした正規近似検定。
配列形式または集計済みの成功数/総数の両方に対応。
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import cast

import numpy as np
from scipy import stats


def _is_sequence_of_length_two(data: object) -> bool:
    """データが長さ2のシーケンス（タプルまたはリスト）かどうかを判定する。"""
    return isinstance(data, list | tuple) and len(data) == 2


def _count_success_total(data: Iterable[float] | tuple[int, int]) -> tuple[int, int]:
    """入力を(成功数, 総数)の形式に正規化する。

    以下の形式を受け付ける:
    - (成功数, 総数)のタプル/リスト
    - 0/1値またはbool値の配列
    """

    if _is_sequence_of_length_two(data):
        success, total = cast(tuple[int | np.integer, int | np.integer], data)
        if not isinstance(success, int | np.integer) or not isinstance(total, int | np.integer):
            raise ValueError("成功数と総数は整数で指定してください")
        if total <= 0:
            raise ValueError("総数は正の値である必要があります")
        if success < 0 or success > total:
            raise ValueError("成功数は 0 以上 総数 以下で指定してください")
        return int(success), int(total)

    array = np.asarray(data)
    if array.ndim == 0:
        raise ValueError("比率データには配列/シーケンスを指定してください")
    array = array[~np.isnan(array.astype(float))]  # drop NaN if any
    if array.size == 0:
        raise ValueError("NaN を除去した結果、配列が空になりました")

    if not np.issubdtype(array.dtype, np.number) and array.dtype != bool:
        raise ValueError("比率データは数値または bool である必要があります")

    unique_values = np.unique(array)
    if np.any((unique_values != 0) & (unique_values != 1)):
        raise ValueError("比率データの配列は 0/1 のみを含む必要があります")

    success_count = int(array.sum())
    total_count = int(array.size)
    return success_count, total_count


def ztest_proportions(
    control_success: Iterable[float] | tuple[int, int],
    control_total: int | None = None,
    treatment_success: Iterable[float] | tuple[int, int] | None = None,
    treatment_total: int | None = None,
    *,
    correction: bool = False,
) -> tuple[float, float, float, float]:
    """二項比率の差を検定する。

    成功数/総数または0/1配列を受け取り、比率差の有意性と95%信頼区間を返す。
    小標本では Agresti-Caffo 補正（各群に成功1・失敗1を加算）を適用し、
    警告を出さずに安定した推定を行う。

    Args:
        control_success: 対照群のデータ（配列または(成功数, 総数)）
        control_total: control_successが成功数のみの場合に総数を指定
        treatment_success: 実験群のデータ（配列または(成功数, 総数)）
        treatment_total: treatment_successが成功数のみの場合に総数を指定
        correction: 連続性修正を適用するか

    Returns:
        (effect, p_value, ci_low, ci_high) のタプル
        effect = treatment_rate - control_rate
    """

    if treatment_success is None:
        raise ValueError("treatment_success を指定してください")

    # Normalise inputs
    if control_total is not None:
        if not isinstance(control_success, int | np.integer):
            raise TypeError(
                "control_total を指定する場合、control_success は整数で指定してください"
            )
        control_pair = (int(control_success), int(control_total))
    else:
        control_pair = _count_success_total(control_success)

    if treatment_total is not None:
        if not isinstance(treatment_success, int | np.integer):
            raise TypeError(
                "treatment_total を指定する場合、treatment_success は整数で指定してください"
            )
        treatment_pair = (int(treatment_success), int(treatment_total))
    else:
        treatment_pair = _count_success_total(treatment_success)

    c_success, c_total = control_pair
    t_success, t_total = treatment_pair

    if c_total <= 0 or t_total <= 0:
        raise ValueError("総数は正の値である必要があります")

    control_rate = c_success / c_total
    treatment_rate = t_success / t_total

    pooled = (c_success + t_success) / (c_total + t_total)
    pooled_var = pooled * (1 - pooled) * (1 / c_total + 1 / t_total)
    if pooled_var <= 0:
        raise ValueError("プールした分散が 0 です。入力データを確認してください")

    se_diff = np.sqrt(
        control_rate * (1 - control_rate) / c_total
        + treatment_rate * (1 - treatment_rate) / t_total
    )
    if se_diff == 0:
        raise ValueError("標準誤差が 0 です。入力にばらつきがありません")

    min_cells = min(c_success, t_success, c_total - c_success, t_total - t_success)
    small_sample = min(c_total, t_total) < 30 or min_cells < 5

    if small_sample:
        c_success_adj = c_success + 1
        t_success_adj = t_success + 1
        c_total_adj = c_total + 2
        t_total_adj = t_total + 2
    else:
        c_success_adj = c_success
        t_success_adj = t_success
        c_total_adj = c_total
        t_total_adj = t_total

    control_rate_adj = c_success_adj / c_total_adj
    treatment_rate_adj = t_success_adj / t_total_adj
    effect_adj = treatment_rate_adj - control_rate_adj

    pooled_adj = (c_success_adj + t_success_adj) / (c_total_adj + t_total_adj)
    pooled_var_adj = pooled_adj * (1 - pooled_adj) * (1 / c_total_adj + 1 / t_total_adj)
    if pooled_var_adj <= 0:  # pragma: no cover (防御的チェック)
        raise ValueError("プールした分散が 0 です。入力データを確認してください")

    std_err_pool = np.sqrt(pooled_var_adj)
    continuity_adjustment = 0.5 * (1 / c_total_adj + 1 / t_total_adj) if correction else 0.0
    adjusted_effect = (
        effect_adj - np.sign(effect_adj) * continuity_adjustment if correction else effect_adj
    )
    z_score = adjusted_effect / std_err_pool
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

    se_diff_adj = np.sqrt(
        control_rate_adj * (1 - control_rate_adj) / c_total_adj
        + treatment_rate_adj * (1 - treatment_rate_adj) / t_total_adj
    )
    if se_diff_adj == 0:  # pragma: no cover (防御的チェック)
        raise ValueError("標準誤差が 0 です。入力にばらつきがありません")
    z_crit = stats.norm.ppf(0.975)
    ci_low = effect_adj - z_crit * se_diff_adj
    ci_high = effect_adj + z_crit * se_diff_adj

    return float(effect_adj), float(p_value), float(ci_low), float(ci_high)


__all__ = ["ztest_proportions"]
