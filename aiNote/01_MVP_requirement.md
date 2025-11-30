# Evidec MVP 要件

## ゴール
- A/Bテスト結果を「検定 → 解釈 → Go/No-Go → 証拠レポート」まで一貫処理する Python OSS の最小実装を完成させる。
- Biz / PdM / Analyst が共有できるテキスト Evidence Report を自動生成し、判断基準の再現性を担保する。

## スコープ（MVPで含める）
- 検定: 比率検定（two-proportion z-test）、平均差の t 検定（対応なし）。
- 信頼区間: 95% CI（両側）の算出。
- Decision: `DecisionRule` による Go / No-Go / Inconclusive 自動判定と判定理由の言語化。
- Reporting: テキスト/Markdown Evidence Report 自動生成。
- インタフェース: Python API のみ（CLI / Web / BI は含まない）。

## スコープ外（MVPではやらない）
- データクレンジング・前処理、EDA、高度な因果推論、GUI/ダッシュボード。
- サンプルサイズ計算（Power, MDE）、ベイズ手法、多腕バンディット。

## 主要ユースケース
- CTR の 2 群比較で、ビジネス基準を満たすか即時判定。
- 平均 CVR の 2 群比較で、効果方向と有意性を確認しレポート出力。
- 既定の DecisionRule テンプレートで複数実験に一貫した判定を適用。

## 機能要件
- `Experiment`
  - 入力: `name`, `metric`, `variant_names`, `control_data`, `treatment_data`（array-like または pandas Series）
  - メソッド: `fit(control, treatment)`, `summary()`
- 検定モジュール `frequentist/`
  - `ztest_proportions(control_success, control_total, treatment_success, treatment_total)` → `effect`, `p_value`, `ci_low`, `ci_high`, `method="two-proportion z-test"`
  - `ttest_means(control_samples, treatment_samples, equal_var=False)` → `effect`, `p_value`, `ci_low`, `ci_high`, `method="two-sample t-test"`
- `DecisionRule`
  - パラメータ: `alpha`, `min_lift`, `metric_goal` ("increase" | "decrease"), optional `min_effect_size`
  - メソッド: `judge(result)` → `Decision {status: GO | NO_GO | INCONCLUSIVE, reason: str, stats: dict}`
  - 判定ロジック:
    - p-value ≤ alpha かつ lift ≥ `min_lift` → GO（increase の場合）／ NO_GO（decrease の場合逆）
    - p-value > alpha → INCONCLUSIVE
    - 効果方向が逆 → NO_GO
    - 理由文字列に p値・CI・lift・閾値を明示
- `EvidenceReport`
  - 入力: `Experiment`, `DecisionRule`, `Decision`, `StatResult`
  - 出力: Markdown 文字列（Summary / Statistical Evidence / Decision Rule / Interpretation）
  - フォーマット: 太字・箇条書き・数値フォーマット（% は小数点 1 桁以上）
- 例示コード
  - `examples/basic_ab.py` に最小サンプルを配置し、上記 API で実行できること。

## 品質要件
- 単体テスト（pytest）で z-test, t-test, DecisionRule, EvidenceReport の主要分岐をカバー（p値境界、lift境界、効果逆転、非有意）。
- 数値検証: 既知ケースで SciPy 結果と ±1e-6 以内で一致。
- 型ヒント（PEP484）と主要パブリック API への docstring。
- 依存: `scipy`, `numpy`, `pandas`（最小限）。Python ≥ 3.10 を前提。

## フォルダ構成（MVP）
- `evidec/core/experiment.py`
- `evidec/core/decision_rule.py`
- `evidec/core/report.py`
- `evidec/frequentist/ztest.py`
- `evidec/frequentist/ttest.py`
- `evidec/report/renderer.py`
- `examples/basic_ab.py`
- `tests/` 配下に各モジュールのテスト。

## 完了の定義 (Definition of Done)
- 上記 API が import 可能で、`examples/basic_ab.py` が実行成功する。
- pytest が全件パス。
- Evidence Report が Markdown で生成され、GO / NO_GO / INCONCLUSIVE が条件通り出力される。
- README（簡易版）に利用方法・インストール・スコープ外が明記されている。
