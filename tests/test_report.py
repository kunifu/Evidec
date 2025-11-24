import numpy as np

from evidec.core import DecisionRule, EvidenceReport, Experiment


def test_レポートに主要セクションが含まれる():
    # Arrange
    exp = Experiment(name="ctr_report", metric="ctr", variant_names=("control", "treatment"))
    control = np.concatenate([np.zeros(70), np.ones(30)])
    treatment = np.concatenate([np.zeros(60), np.ones(40)])
    rule = DecisionRule(alpha=0.05, min_lift=0.01, metric_goal="increase")

    # Act
    result = exp.fit(control, treatment)
    decision = rule.judge(result)
    report = EvidenceReport.from_result(exp, rule, decision, result)

    # Assert
    assert "## 主要結果" in report.markdown
    assert f"**判定**: ⚠️ **{decision.status}**" in report.markdown
    assert report.summary.startswith(exp.name)


def test_簡易セクション構成でも必要項目を含む():
    # Arrange
    exp = Experiment(name="ctr_report", metric="ctr", variant_names=("control", "treatment"))
    control = np.concatenate([np.zeros(70), np.ones(30)])
    treatment = np.concatenate([np.zeros(60), np.ones(40)])
    rule = DecisionRule(alpha=0.05, min_lift=0.01, metric_goal="increase")

    # Act
    result = exp.fit(control, treatment)
    decision = rule.judge(result)
    report = EvidenceReport.from_result(exp, rule, decision, result)

    # Assert
    assert "## 結論" in report.markdown
    assert "## 実験詳細" in report.markdown
    assert "> **注記**" in report.markdown
    assert "変化率 (相対)" in report.markdown


def test_GOの場合に有意差と段階的ロールアウトを記述する():
    # Arrange
    exp = Experiment(
        name="ctr_significant_go", metric="ctr", variant_names=("control", "treatment")
    )
    rule = DecisionRule(alpha=0.05, min_lift=0.01, metric_goal="increase")

    # Act
    result = exp.fit((60, 200), (80, 200))
    decision = rule.judge(result)
    report = EvidenceReport.from_result(exp, rule, decision, result)

    # Assert
    assert decision.status == "GO"
    # p値が0.036なので参考として表示されているか確認
    assert "p=0.03" in report.markdown
    assert "段階的ロールアウトを推奨" in report.markdown


def test_NO_GOの場合にロールアウト非推奨を記述する():
    # Arrange
    exp = Experiment(name="ctr_negative", metric="ctr", variant_names=("control", "treatment"))
    rule = DecisionRule(alpha=0.05, metric_goal="increase")

    # Act
    result = exp.fit((80, 100), (50, 100))
    decision = rule.judge(result)
    report = EvidenceReport.from_result(exp, rule, decision, result)

    # Assert
    assert decision.status == "NO_GO"
    assert "ロールアウト非推奨" in report.markdown


def test_ベースラインゼロ時に相対リフトをn_a表示する():
    # Arrange
    exp = Experiment(name="ctr_zero_baseline", metric="ctr", variant_names=("control", "treatment"))
    rule = DecisionRule(alpha=0.05, metric_goal="increase")

    # Act
    result = exp.fit((0, 50), (5, 50))
    decision = rule.judge(result)
    report = EvidenceReport.from_result(exp, rule, decision, result)

    # Assert
    assert decision.status == "INCONCLUSIVE"
    # ベースライン0の場合は相対リフトが計算できず "n/a" になる
    assert "**変化率 (相対)**: n/a" in report.markdown


def test_絶対変化と相対変化をわかりやすく表示する():
    # Arrange
    exp = Experiment(name="ctr_clear_labels", metric="ctr", variant_names=("control", "treatment"))
    rule = DecisionRule(alpha=0.05, min_lift=0.01, metric_goal="increase")

    # Act
    result = exp.fit((30, 100), (40, 100))
    decision = rule.judge(result)
    report = EvidenceReport.from_result(exp, rule, decision, result)

    # Assert
    assert "**変化量 (絶対)**: +10.0pp" in report.markdown
    assert "**変化率 (相対)**: +33.3%" in report.markdown
