import numpy as np
import pytest

from evidec.bayesian.beta_binomial import (
    BayesResult,
    fit_beta_binomial,
    fit_beta_binomial_from_prior,
)


def test_fit_beta_binomial推定結果を返す() -> None:
    result = fit_beta_binomial(
        control_success=50,
        control_total=100,
        treatment_success=60,
        treatment_total=100,
        n_draws=5000,
        tolerance=-0.01,
        seed=0,
    )

    assert isinstance(result, BayesResult)
    assert 0.85 < result.p_improve < 0.99
    assert result.p_above_tol >= result.p_improve
    assert result.lift_ci[0] < result.lift_ci[1]
    assert np.isclose(result.params["alpha0"], 1.0)


def test_toleranceを緩めると非劣性確率が増える() -> None:
    strict = fit_beta_binomial(
        control_success=40,
        control_total=100,
        treatment_success=40,
        treatment_total=100,
        n_draws=4000,
        tolerance=0.0,
        seed=123,
    )
    relaxed = fit_beta_binomial(
        control_success=40,
        control_total=100,
        treatment_success=40,
        treatment_total=100,
        n_draws=4000,
        tolerance=-0.02,
        seed=123,
    )

    assert relaxed.p_above_tol > strict.p_above_tol
    assert strict.p_improve == relaxed.p_improve  # tolerance だけが変化


def test_seed指定で再現性がある() -> None:
    r1 = fit_beta_binomial(
        control_success=70,
        control_total=150,
        treatment_success=80,
        treatment_total=150,
        n_draws=3000,
        seed=2024,
    )
    r2 = fit_beta_binomial(
        control_success=70,
        control_total=150,
        treatment_success=80,
        treatment_total=150,
        n_draws=3000,
        seed=2024,
    )

    assert r1 == r2


def test不正入力ではValueErrorを送出する() -> None:
    with pytest.raises(ValueError):
        fit_beta_binomial(-1, 10, 5, 10)
    with pytest.raises(ValueError):
        fit_beta_binomial(5, 10, 11, 10)
    with pytest.raises(ValueError):
        fit_beta_binomial(5, 10, 5, 10, n_draws=0)
    with pytest.raises(ValueError):
        fit_beta_binomial(1, 0, 1, 10)


def test_to_dictでメタ情報を取得できる() -> None:
    result = fit_beta_binomial(10, 50, 12, 50, n_draws=1000, seed=7)

    result_dict = result.to_dict()

    assert result_dict["method"] == "beta-binomial"
    assert result_dict["params"]["seed"] == 7
    assert result_dict["params"]["control_total"] == 50


def test_prior_mean_strengthからalpha_betaを算出する() -> None:
    result = fit_beta_binomial_from_prior(
        prior_mean=0.03,
        prior_strength=100,
        control_success=3,
        control_total=100,
        treatment_success=6,
        treatment_total=100,
        seed=1,
        n_draws=2000,
    )

    assert pytest.approx(result.params["alpha0"]) == 3.0
    assert pytest.approx(result.params["beta0"]) == 97.0
    # prior_mean が成功率と近いので改善確率は高くないはず
    assert 0.4 <= result.p_improve <= 0.9


def test_priorの範囲外は例外() -> None:
    with pytest.raises(ValueError):
        fit_beta_binomial_from_prior(
            prior_mean=1.2,
            prior_strength=10,
            control_success=1,
            control_total=10,
            treatment_success=1,
            treatment_total=10,
        )
    with pytest.raises(ValueError):
        fit_beta_binomial_from_prior(
            prior_mean=0.5,
            prior_strength=0,
            control_success=1,
            control_total=10,
            treatment_success=1,
            treatment_total=10,
        )
