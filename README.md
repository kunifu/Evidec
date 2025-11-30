# Evidec

Python 製の A/B テスト評価ライブラリ。2 群の統計検定を行い、ルールに沿って GO / NO_GO / INCONCLUSIVE を判定し、Markdown レポートを生成します。

## インストール
```bash
uv venv && source .venv/bin/activate
uv pip install -e '.[dev]'   # または pip install -e '.[dev]'
```

## 最小サンプル
```python
from evidec import DecisionRule, EvidenceReport, Experiment

exp = Experiment(name="cta_color", metric="ctr", variant_names=("対照群", "実験群"))
result = exp.fit(control_data, treatment_data)  # 0/1 配列・連続値・(success, total) に対応
rule = DecisionRule(alpha=0.05, min_lift=0.01, metric_goal="increase")
decision = rule.judge(result)
report = EvidenceReport.from_result(exp, rule, decision, result)
print(report.markdown)
```

### 悪化していないことを確認する（非劣性テスト）
```python
from evidec import EvidenceReport, Experiment, NonInferiorityRule

exp = Experiment(name="variant_check", metric="cvr", variant_names=("original", "new"))
result = exp.fit(control_data, treatment_data)

# margin は「許容する悪化幅 (絶対差)」を表す。0.01 = 1pp まで悪化を許容。
rule = NonInferiorityRule(alpha=0.05, margin=0.01, metric_goal="increase")
decision = rule.judge(result)

report = EvidenceReport.from_result(exp, rule, decision, result)
print(report.markdown)
```

サンプル実行: 
```bash
python examples/basic_ab.py
python examples/non_inferiority.py
```

## 提供するもの
- 比率 z 検定 / 平均差 t 検定（指標タイプに応じて自動選択）
- `DecisionRule` による p 値・リフト・方向性 (`metric_goal`)・最小効果量による判定
- `NonInferiorityRule` による悪化検証（非劣性判定）
- 日本語 Markdown の Evidence Report

## 開発コマンド
- `poe lint` / `poe format` / `poe typecheck` / `poe test` / `poe check`（推奨）

## ディレクトリ概要
```
evidec/
  core/            # Experiment, DecisionRule, EvidenceReport を束ねるドメインロジック
  report/          # renderer (Markdown組み立て)
  frequentist/     # ztest, ttest（頻度論）
  utils/           # 共通ユーティリティ
  bayesian/        # Beta-Binomial など拡張
tests/             # ユニット & アーキテクチャテスト
examples/          # basic_ab.py
```

詳細と開発方針は `AGENTS.md` を参照してください。

## ライセンス
MIT License。
