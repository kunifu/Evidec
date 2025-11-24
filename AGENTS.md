# AGENTS.md

Evidec は **A/B テスト結果を統計評価し、Markdown エビデンスを生成する Python ライブラリ**。

## 主要ポイント
- 目的: CTR/CVR など 0/1 指標と連続値指標の 2 群比較を評価し、GO / NO_GO / INCONCLUSIVE を判定。
- 公開 API: `Experiment`, `StatResult`, `DecisionRule`, `Decision`, `DecisionStatus`, `EvidenceReport`（すべて `evidec.core` 経由）。
- 対応データ: 0/1 配列・連続値配列・集計済み `(success, total)` タプル。

## 設計原則（tests/arch/ が監視）
- Facade: 公開は `evidec/core.py` のみ。`evidec/__init__.py` は core から import するだけ。`evidec/core/` ディレクトリを作らない。
- 責務分離: `experiment`(実行・結果), `decision`(判定), `report`(レポート生成), `stats`(検定)。
- 依存: 循環禁止。
- 互換性: 公開クラスのシグネチャ・挙動を勝手に変えない。

## 使い方フロー（最小）
1) `Experiment(name, metric, variant_names)` を用意。  
2) `result = exp.fit(control, treatment)` で `StatResult`。比率→`stats/ztest.py`、連続→`stats/ttest.py` を自動選択。  
3) `rule = DecisionRule(alpha, min_lift, metric_goal="increase"/"decrease", min_effect_size=None)`。  
4) `decision = rule.judge(result)` で GO/NO_GO/INCONCLUSIVE。  
5) `report = EvidenceReport.from_result(exp, rule, decision, result)` → `report.markdown`。

## 開発コマンド（poethepoet）
- `poe lint` / `poe format` / `poe typecheck` / `poe test` / `poe check`（推奨: 変更後はまず `poe check`）。

## 実装メモ
- `DecisionRule.judge`: p 値 + `min_lift` + `metric_goal` + `min_effect_size` で判定。ロジック変更はテストで明示。  
- `EvidenceReport` / `renderer` は UI 層。文言変更は慎重に。  
- コメント・エラーメッセージは日本語優先。

## テスト方針
- 新機能やバグ修正では `tests/` にケースを追加/更新。`pytest` は `--cov=evidec`。  
- アーキテクチャ違反は `tests/arch/` が検出。

## Agent チェックリスト
- まず `evidec/core.py`, `stats/`, `report/`, `tests/` を確認。  
- 変更箇所（ファイル・関数・クラス）を明示して提案。  
- API 互換とテストを最優先し、`poe check` が通る状態を目指す。
