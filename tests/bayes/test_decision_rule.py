from evidec.bayes.beta_binomial import BayesResult
from evidec.bayes.decision_rule import BayesDecisionRule


def _result(**kwargs: float) -> BayesResult:
    base = dict(
        p_improve=0.90,
        p_above_tol=0.90,
        lift_mean=0.01,
        lift_ci=(-0.005, 0.025),
        tolerance=-0.005,
    )
    base.update(kwargs)
    return BayesResult(params={}, **base)


def test_GO条件を満たすとGOを返す() -> None:
    rule = BayesDecisionRule()
    decision = rule.judge(
        _result(p_improve=0.97, p_above_tol=0.99, lift_mean=0.02, lift_ci=(0.01, 0.03))
    )

    assert decision.status == "GO"
    assert "GO" in decision.reason


def test_SAFEはINCONCLUSIVEとして扱う() -> None:
    rule = BayesDecisionRule()
    bayes = _result(p_improve=0.82, p_above_tol=0.98, lift_mean=0.0, lift_ci=(-0.01, 0.01))

    decision = rule.judge(bayes)

    assert decision.status == "INCONCLUSIVE"
    assert "SAFE" in decision.reason
    assert decision.stats.get("label") == "SAFE"


def test_p_above_tolが低い場合はNO_GO() -> None:
    rule = BayesDecisionRule()
    bayes = _result(p_improve=0.9, p_above_tol=0.4, lift_mean=-0.01, lift_ci=(-0.03, 0.01))

    decision = rule.judge(bayes)

    assert decision.status == "NO_GO"
    assert "NO_GO" in decision.reason


def test_閾値未達の場合はINCONCLUSIVE() -> None:
    rule = BayesDecisionRule()
    bayes = _result(p_improve=0.5, p_above_tol=0.98, lift_mean=0.0, lift_ci=(-0.01, 0.01))

    decision = rule.judge(bayes)

    assert decision.status == "INCONCLUSIVE"
    assert "閾値" in decision.reason or "INCONCLUSIVE" in decision.reason


def test_describe_thresholdで閾値説明を返す() -> None:
    rule = BayesDecisionRule(p_improve_go=0.9, p_safe=0.97, min_lift=0.01)

    criterion, threshold = rule.describe_threshold(ratio_metric=True)

    assert "P(Δ>0)≥90%" in criterion
    assert "P(Δ>+1.00%)" in criterion
    assert "90%" in threshold
