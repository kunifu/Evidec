import numpy as np
import pytest

from evidec.core.experiment import Experiment


def test_experiment_detects_proportion_inputs():
    exp = Experiment(name="ctr_test", metric="ctr", variant_names=("control", "treatment"))
    control = np.array([0, 1, 0, 1, 0, 0, 1, 0, 0, 1] * 5)
    treatment = np.array([1, 1, 1, 0, 1, 1, 0, 1, 1, 1] * 5)

    result = exp.fit(control, treatment)

    assert result.method == "two-proportion z-test"
    assert result.baseline == pytest.approx(control.mean())
    assert exp.summary()["metric"] == "ctr"


def test_experiment_uses_ttest_for_continuous_inputs():
    exp = Experiment(name="avg_test", metric="avg", variant_names=("control", "treatment"))
    control = np.array([1.0, 2.0, 3.0, 2.5, 2.1])
    treatment = np.array([2.0, 2.5, 3.5, 3.0, 2.9])

    result = exp.fit(control, treatment)

    assert result.method == "two-sample t-test"
    assert result.effect == pytest.approx(treatment.mean() - control.mean())


def test_experiment_requires_two_variants():
    exp = Experiment(name="bad", metric="ctr", variant_names=("control",))
    with pytest.raises(ValueError):
        exp.fit((1, 10), (2, 10))


def test_experiment_requires_counts_for_both_or_neither():
    exp = Experiment(name="mix", metric="ctr", variant_names=("control", "treatment"))
    with pytest.raises(ValueError):
        exp.fit((1, 10), [0, 1, 0, 1])


def test_experiment_handles_count_inputs_and_summary_guard():
    exp = Experiment(name="ctr_test", metric="ctr", variant_names=("control", "treatment"))

    with pytest.raises(ValueError):
        exp.summary()

    result = exp.fit((5, 10), (7, 10))

    assert result.baseline == pytest.approx(0.5)
    assert result.to_dict()["method"] == "two-proportion z-test"
    assert exp.summary()["baseline"] == pytest.approx(0.5)


def test_experiment_raises_on_all_nan_inputs():
    exp = Experiment(name="nan", metric="ctr", variant_names=("c", "t"))
    with pytest.raises(ValueError):
        exp.fit(np.array([np.nan]), np.array([np.nan]))
