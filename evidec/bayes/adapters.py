"""配列データから Beta-Binomial 推定を行う薄いヘルパー。"""

from __future__ import annotations

from typing import Any, cast

import numpy as np
from numpy.typing import ArrayLike, NDArray

from evidec.bayes.beta_binomial import BayesResult, fit_beta_binomial

__all__ = ["fit_beta_binomial_from_arrays"]

NDArrayFloat = NDArray[np.float64]


def _to_clean_binary_array(data: ArrayLike) -> NDArrayFloat:
    arr = np.asarray(data, dtype=np.float64)
    arr = arr[~np.isnan(arr)]
    arr = cast(NDArrayFloat, arr.astype(np.float64, copy=False))
    if arr.size == 0:
        raise ValueError("NaN を除去した結果、入力データが空です")
    unique = np.unique(arr)
    if not np.all((unique == 0) | (unique == 1)):
        raise ValueError("0/1 のみを含む配列を指定してください")
    return arr


def fit_beta_binomial_from_arrays(
    control: ArrayLike, treatment: ArrayLike, **kwargs: Any
) -> BayesResult:
    """0/1 配列を集計して Beta-Binomial 推定を実行する。"""

    control_arr = _to_clean_binary_array(control)
    treatment_arr = _to_clean_binary_array(treatment)

    control_success = int(np.sum(control_arr))
    control_total = int(control_arr.size)
    treatment_success = int(np.sum(treatment_arr))
    treatment_total = int(treatment_arr.size)

    return fit_beta_binomial(
        control_success,
        control_total,
        treatment_success,
        treatment_total,
        **kwargs,
    )
