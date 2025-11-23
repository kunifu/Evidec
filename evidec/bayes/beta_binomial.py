"""Beta-Binomial モデルによるベイズ推論を提供するモジュール。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

__all__ = ["BayesResult", "fit_beta_binomial", "fit_beta_binomial_from_prior"]


@dataclass(frozen=True)
class BayesResult:
    """Beta-Binomial 推定結果を保持するデータクラス。"""

    p_improve: float
    p_above_tol: float
    lift_mean: float
    lift_ci: tuple[float, float]
    tolerance: float
    method: str = "beta-binomial"
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "p_improve": self.p_improve,
            "p_above_tol": self.p_above_tol,
            "lift_mean": self.lift_mean,
            "lift_ci": self.lift_ci,
            "tolerance": self.tolerance,
            "method": self.method,
            "params": self.params,
        }


def _validate_inputs(
    control_success: int,
    control_total: int,
    treatment_success: int,
    treatment_total: int,
    n_draws: int,
) -> None:
    if control_total <= 0 or treatment_total <= 0:
        raise ValueError("試行数は正の整数で指定してください")
    if not (0 <= control_success <= control_total):
        raise ValueError("control_success は 0 以上 control_total 以下で指定してください")
    if not (0 <= treatment_success <= treatment_total):
        raise ValueError("treatment_success は 0 以上 treatment_total 以下で指定してください")
    if n_draws <= 0:
        raise ValueError("n_draws は 1 以上の整数を指定してください")


def _validate_prior(mean: float, strength: float) -> None:
    if not (0 < mean < 1):
        raise ValueError("prior_mean は 0 と 1 の間の値を指定してください")
    if strength <= 0:
        raise ValueError("prior_strength は正の値を指定してください")


def _mean_strength_to_alpha_beta(mean: float, strength: float) -> tuple[float, float]:
    _validate_prior(mean, strength)
    alpha0 = mean * strength
    beta0 = (1 - mean) * strength
    return alpha0, beta0


def fit_beta_binomial(
    control_success: int,
    control_total: int,
    treatment_success: int,
    treatment_total: int,
    *,
    alpha0: float = 1.0,
    beta0: float = 1.0,
    n_draws: int = 20000,
    tolerance: float = -0.005,
    seed: int | None = None,
) -> BayesResult:
    """Beta-Binomial モデルで改善確率を推定する。

    Args:
        control_success: 対照群の成功数
        control_total: 対照群の試行数
        treatment_success: 処理群の成功数
        treatment_total: 処理群の試行数
        alpha0: 事前分布の α
        beta0: 事前分布の β
        n_draws: サンプリング回数
        tolerance: 非劣性判定に用いる許容下限 (リフト)
        seed: 乱数シード（再現性確保のため任意指定）
    """
    _validate_inputs(control_success, control_total, treatment_success, treatment_total, n_draws)

    alpha_c = alpha0 + control_success
    beta_c = beta0 + (control_total - control_success)
    alpha_t = alpha0 + treatment_success
    beta_t = beta0 + (treatment_total - treatment_success)

    rng = np.random.default_rng(seed)
    sample_c = rng.beta(alpha_c, beta_c, size=n_draws)
    sample_t = rng.beta(alpha_t, beta_t, size=n_draws)

    lift = sample_t - sample_c
    p_improve = float(np.mean(lift > 0))
    p_above_tol = float(np.mean(lift > tolerance))
    lift_mean = float(np.mean(lift))
    ci_low, ci_high = np.percentile(lift, [2.5, 97.5])

    params = {
        "alpha0": alpha0,
        "beta0": beta0,
        "n_draws": n_draws,
        "tolerance": tolerance,
        "seed": seed,
        "control_success": control_success,
        "control_total": control_total,
        "treatment_success": treatment_success,
        "treatment_total": treatment_total,
    }

    return BayesResult(
        p_improve=p_improve,
        p_above_tol=p_above_tol,
        lift_mean=lift_mean,
        lift_ci=(float(ci_low), float(ci_high)),
        tolerance=tolerance,
        params=params,
    )


def fit_beta_binomial_from_prior(
    prior_mean: float,
    prior_strength: float,
    *,
    control_success: int,
    control_total: int,
    treatment_success: int,
    treatment_total: int,
    n_draws: int = 20000,
    tolerance: float = -0.005,
    seed: int | None = None,
) -> BayesResult:
    """事前平均と強度から Beta 事前を生成して推定を実行する。

    prior_mean は「期待される平均CVR」などの事前知識、
    prior_strength は「過去データ何件ぶんに相当させるか」を表す。
    """

    alpha0, beta0 = _mean_strength_to_alpha_beta(prior_mean, prior_strength)
    return fit_beta_binomial(
        control_success=control_success,
        control_total=control_total,
        treatment_success=treatment_success,
        treatment_total=treatment_total,
        alpha0=alpha0,
        beta0=beta0,
        n_draws=n_draws,
        tolerance=tolerance,
        seed=seed,
    )
