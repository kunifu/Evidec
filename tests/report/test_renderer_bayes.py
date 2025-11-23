from evidec.bayes.beta_binomial import BayesResult
from evidec.core.decision_rule import DecisionRule
from evidec.core.experiment import Experiment
from evidec.core.report import EvidenceReport
from evidec.report.renderer import render_markdown


def _make_stat_result():
    exp = Experiment(name="bayes", metric="ctr", variant_names=("control", "treat"))
    stat = exp.fit([0, 1, 0, 1], [0, 1, 1, 1])
    rule = DecisionRule(alpha=0.05, min_lift=0.0, metric_goal="increase")
    decision = rule.judge(stat)
    return exp, stat, rule, decision


def test_bayesセクションをMarkdownに追加する() -> None:
    exp, stat, rule, decision = _make_stat_result()
    bayes = BayesResult(
        p_improve=0.90,
        p_above_tol=0.96,
        lift_mean=0.012,
        lift_ci=(-0.005, 0.030),
        tolerance=-0.005,
        params={},
    )

    report = EvidenceReport.from_result(exp, rule, decision, stat, bayes_result=bayes)
    markdown = render_markdown(exp, decision, stat, rule, bayes_result=bayes)

    assert "Bayesian Evidence" in report.markdown
    assert "Bayesian Evidence" in markdown
    assert "P(Δ>0)" in markdown
    assert "P(Δ>-0.5%)" in markdown


def test_bayes結果なしでも後方互換を保つ() -> None:
    exp, stat, rule, decision = _make_stat_result()

    report = EvidenceReport.from_result(exp, rule, decision, stat)
    markdown = render_markdown(exp, decision, stat, rule)

    assert "Bayesian Evidence" not in report.markdown
    assert "Bayesian Evidence" not in markdown
