"""二項比率のz検定ユーティリティ。

0/1データの比率差を評価する際に使用（例: CTR, CVR）。
サンプル数が十分に大きいことを前提とした正規近似検定。
配列形式または集計済みの成功数/総数の両方に対応。
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import cast, overload

import numpy as np
from scipy import stats


def _is_sequence_of_length_two(data: object) -> bool:
    """データが長さ2のシーケンス（タプルまたはリスト）かどうかを判定する。"""
    return isinstance(data, list | tuple) and len(data) == 2


def _preprocess(data: Iterable[float] | tuple[int, int]) -> tuple[int, int]:
    """入力を(成功数, 総数)の形式に正規化する。

    以下の形式を受け付ける:
    - (成功数, 総数)のタプル/リスト
    - 0/1値またはbool値の配列

    処理内容:
    1. 入力形式の判定と変換
    2. NaNの除去
    3. データ型と値の妥当性チェック
    4. 成功数と総数の計算
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


def _validate_assumptions(c_total: int, t_total: int, pooled_var: float) -> None:
    """z検定の前提条件を検証する。

    サンプルサイズとプールした分散の妥当性を確認する。
    """
    if c_total <= 0 or t_total <= 0:
        raise ValueError("総数は正の値である必要があります")
    if pooled_var <= 0:
        raise ValueError("プールした分散が 0 です。入力データを確認してください")


def _ensure_nonzero_standard_error(se: float) -> None:
    """標準誤差が 0 でないことを検証する。

    ばらつきのない入力では信頼区間や検定統計量が定義できないため。
    """
    if se == 0:
        raise ValueError("標準誤差が 0 です。入力にばらつきがありません")


def _compute_pooled_variance(
    c_success: int, c_total: int, t_success: int, t_total: int
) -> float:
    """プールした分散を計算する。"""
    pooled = (c_success + t_success) / (c_total + t_total)
    return pooled * (1 - pooled) * (1 / c_total + 1 / t_total)


def _compute_basic_stats(
    c_success: int, c_total: int, t_success: int, t_total: int
) -> tuple[float, float]:
    """比率差と標準誤差を計算する。"""
    control_rate = c_success / c_total
    treatment_rate = t_success / t_total
    effect = treatment_rate - control_rate
    se_diff = np.sqrt(
        control_rate * (1 - control_rate) / c_total
        + treatment_rate * (1 - treatment_rate) / t_total
    )
    return effect, se_diff


def _compute_confidence_interval(effect: float, se_diff: float) -> tuple[float, float]:
    """95%信頼区間を計算する。"""
    z_crit = stats.norm.ppf(0.975)
    ci_low = effect - z_crit * se_diff
    ci_high = effect + z_crit * se_diff
    return float(ci_low), float(ci_high)


def _apply_agresti_caffo_correction(
    c_success: int, c_total: int, t_success: int, t_total: int
) -> tuple[int, int, int, int]:
    """小標本に対してAgresti-Caffo補正を適用する。

    小標本の判定基準:
    - 最小サンプルサイズ < 30 または
    - 最小セル数 < 5

    補正内容: 各群に成功1・失敗1を加算
    """
    min_cells = min(c_success, t_success, c_total - c_success, t_total - t_success)
    small_sample = min(c_total, t_total) < 30 or min_cells < 5

    if small_sample:
        return c_success + 1, c_total + 2, t_success + 1, t_total + 2
    return c_success, c_total, t_success, t_total


@overload
def _normalize_counts(
    success: Iterable[float] | tuple[int, int], total: None, role: str
) -> tuple[int, int]:
    ...


@overload
def _normalize_counts(
    success: int | np.integer, total: int, role: str
) -> tuple[int, int]:
    ...


def _normalize_counts(
    success: Iterable[float] | tuple[int, int] | int | np.integer,
    total: int | None,
    role: str,
) -> tuple[int, int]:
    """成功数と総数の入力を検証し、(成功数, 総数)に正規化する。"""

    if total is not None:
        if not isinstance(success, int | np.integer):
            raise TypeError(
                f"{role}_total を指定する場合、{role}_success は整数で指定してください"
            )
        return int(success), int(total)

    if isinstance(success, (int, np.integer)):
        raise TypeError(
            f"{role}_total がない場合、"
            f"{role}_success には配列または(成功数, 総数)を指定してください"
        )

    normalized = _preprocess(cast(Iterable[float] | tuple[int, int], success))
    return normalized


def _normalize_group_input(
    success: Iterable[float] | tuple[int, int] | int | np.integer | None,
    total: int | None,
    role: str,
) -> tuple[int, int]:
    """群ごとの入力を共通のバリデーション/正規化フローで処理する。"""

    if success is None:  # pragma: no cover - public API で防衛的に保持
        raise ValueError(f"{role}_success を指定してください")

    if total is None:
        return _normalize_counts(cast(Iterable[float] | tuple[int, int], success), None, role)

    return _normalize_counts(cast(int | np.integer, success), total, role)


def _compute_z_score(
    effect: float, pooled_var: float, c_total: int, t_total: int, correction: bool
) -> float:
    """zスコアを計算する。"""

    std_err_pool = np.sqrt(pooled_var)
    continuity_adjustment = 0.5 * (1 / c_total + 1 / t_total) if correction else 0.0
    sign_effect = 0.0 if effect == 0 else math.copysign(1.0, effect)
    adjusted_effect = effect - sign_effect * continuity_adjustment if correction else effect
    return float(adjusted_effect / std_err_pool)


def _run_ztest(
    control: tuple[int, int], treatment: tuple[int, int], correction: bool
) -> tuple[float, float, float, float]:
    """検定の主要ロジックをまとめたヘルパー。"""

    c_success, c_total = control
    t_success, t_total = treatment

    # 補正前の入力がゼロ分散・不正な総数でないことを先に確認する
    _validate_assumptions(
        c_total, t_total, _compute_pooled_variance(c_success, c_total, t_success, t_total)
    )
    # 補正前に標準誤差=0（全0/全1など）を弾いておく
    _ensure_nonzero_standard_error(
        _compute_basic_stats(c_success, c_total, t_success, t_total)[1]
    )

    c_success, c_total, t_success, t_total = _apply_agresti_caffo_correction(
        c_success, c_total, t_success, t_total
    )

    pooled_var = _compute_pooled_variance(c_success, c_total, t_success, t_total)
    _validate_assumptions(c_total, t_total, pooled_var)

    effect, se_diff = _compute_basic_stats(c_success, c_total, t_success, t_total)
    _ensure_nonzero_standard_error(se_diff)

    z_score = _compute_z_score(effect, pooled_var, c_total, t_total, correction)
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    ci_low, ci_high = _compute_confidence_interval(effect, se_diff)

    return float(effect), float(p_value), float(ci_low), float(ci_high)


def ztest_proportions(
    control_success: Iterable[float] | tuple[int, int] | int | np.integer,
    control_total: int | None = None,
    treatment_success: Iterable[float] | tuple[int, int] | int | np.integer | None = None,
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

    control_pair = _normalize_group_input(control_success, control_total, "control")
    treatment_pair = _normalize_group_input(treatment_success, treatment_total, "treatment")

    return _run_ztest(control_pair, treatment_pair, correction)


__all__ = ["ztest_proportions"]
