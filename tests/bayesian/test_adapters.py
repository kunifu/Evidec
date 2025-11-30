import numpy as np
import pytest

from evidec.bayesian.adapters import fit_beta_binomial_from_arrays
from evidec.bayesian.beta_binomial import BayesResult


def test配列を集計してBayesResultを返す() -> None:
    control = np.array([0, 1, 0, 1, 0])
    treatment = np.array([1, 1, 1, 0, 1])

    result = fit_beta_binomial_from_arrays(control, treatment, n_draws=1500, seed=0)

    assert isinstance(result, BayesResult)
    assert result.params["control_success"] == 2
    assert result.params["treatment_total"] == 5


def test0_1以外の値が含まれていれば例外() -> None:
    with pytest.raises(ValueError):
        fit_beta_binomial_from_arrays([0.1, 0.9], [0, 1, 1])


def testNaNのみの場合は例外() -> None:
    with pytest.raises(ValueError):
        fit_beta_binomial_from_arrays([np.nan, np.nan], [0, 1])
