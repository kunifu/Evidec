# Evidec

Python 製のエビデンスベース A/B テスト支援ライブラリ。統計検定を実行し、ルールに沿って GO/NO-GO を判定し、Markdown のエビデンスレポートを生成します。

## 動作環境
- Python 3.10+（構造的パターンマッチ・モダンな型ヒントを使用）
- 推奨インストーラ: [uv](https://github.com/astral-sh/uv)（pip 互換）

## クイックスタート
```bash
# 仮想環境を作成して有効化（uv はデフォルトで .venv を作成）
uv venv
source .venv/bin/activate

# ライブラリ + 開発ツールをインストール（ruff, mypy, pytest, poethepoet）
uv pip install -e '.[dev]'

# pip を使う場合
pip install -e '.[dev]'
```

## 使い方
```python
from evidec import DecisionRule, EvidenceReport, Experiment

exp = Experiment(name="cta_color_test", metric="ctr", variant_names=("対照群", "実験群"))
result = exp.fit(control_data, treatment_data)  # 0/1 または連続値の配列・リストなど（例: 対照群/実験群）

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

同梱のサンプルを実行する場合:
```bash
python examples/basic_ab.py
python examples/non_inferiority.py
```

## スコープ (MVP)
- 2群の比率 z 検定・平均差 t 検定（独立サンプル）
- p 値と最小リフトで GO / NO_GO / INCONCLUSIVE を判定する DecisionRule
- 悪化していないことを確認する NonInferiorityRule（非劣性判定）
- Markdown 形式の Evidence Report 生成（日本語）
- Python API のみ（CLI / GUI は未提供）

## スコープ外 (MVP)
- データクリーニング / 前処理、EDA、高度な因果推論、ダッシュボード
- サンプルサイズ・検出力・MDE 計算
- ベイズ手法、マルチアームバンディット

## 開発用タスク (poethepoet)
- `poe lint`      – ruff check
- `poe format`    – ruff format
- `poe typecheck` – mypy evidec
- `poe test`      – pytest -q
- `poe check`     – lint + typecheck + test

## プロジェクト構成
```
evidec/
  __init__.py
  core/
    experiment.py
    decision_rule.py
    report.py
  stats/
    ztest.py
    ttest.py
  report/
    renderer.py
examples/
  basic_ab.py
tests/
```

## ライセンス
MIT License（LICENSE を参照）。
