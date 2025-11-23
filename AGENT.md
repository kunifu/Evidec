# AGENT: Evidec

Evidec は **A/B テストの統計評価とエビデンスレポート生成に特化した Python ライブラリ** です。
このファイルは、このリポジトリ上で動作する Agent（AI アシスタント）が守るべき「行動方針」と「コンテキストのまとめ」です。

---

## 1. プロジェクト概要
- 名前: `evidec`
- 目的: A/Bテストの結果を統計的に評価し、GO / NO-GO / INCONCLUSIVE を判定し、Markdown 形式のエビデンスレポートを生成する。
- 主な利用者: データアナリスト、プロダクトマネージャー、エンジニア。
- 想定シナリオ:
  - CTR / CVR など 0/1 指標の AB テスト
  - 売上・滞在時間など連続値指標の AB テスト

---

## 2. 技術スタックとツール
- 言語: Python 3.10+
- 主要ライブラリ: `numpy`, `scipy`, `pandas`
- 開発ツール:
  - テスト: `pytest`
  - 型チェック: `mypy`
  - Lint / Format: `ruff`
  - タスクランナー: `poethepoet`

### 開発用タスク (`pyproject.toml` の `poe` タスク)
- `poe lint`      – `ruff check .`
- `poe format`    – `ruff format .`
- `poe typecheck` – `mypy evidec`
- `poe test`      – `pytest -q`
- `poe check`     – 上記をまとめて実行

Agent がコードを変更した場合は、**可能な限り `poe check` を実行してから提案すること**。

---

## 3. ディレクトリ構成（要点）
- `evidec/`
  - `core/`
    - `experiment.py`  
      - `Experiment`, `StatResult`
      - 入力データから統計検定（z検定 / t検定）を実行し、`StatResult` を返す。
    - `decision_rule.py`  
      - `DecisionRule`, `Decision`, `DecisionStatus`
      - 統計結果 (`StatResult`) から GO / NO_GO / INCONCLUSIVE を判定する。
    - `report.py`  
      - `EvidenceReport`
      - `Experiment` + `DecisionRule` + `Decision` + `StatResult` からレポートオブジェクトと Markdown を組み立てる。
  - `stats/`
    - `ztest.py`: 比率指標向けの二群検定（two-proportion z-test）。
    - `ttest.py`: 連続値指標向けの二群検定（two-sample t-test）。
  - `report/`
    - `renderer.py`: EvidenceReport から Markdown テキストを組み立てる。
- `examples/`
  - `basic_ab.py`: ライブラリの典型的な利用例。
- `tests/`: `pytest` ベースのユニットテスト一式。

---

## 4. セットアップ
```bash
uv venv
source .venv/bin/activate
uv pip install -e '.[dev]'
# または
pip install -e '.[dev]'
```

---

## 5. 代表的な利用フロー（Agent 向け要約）
メインとなる公開 API は以下です:
- `evidec.Experiment`
- `evidec.DecisionRule`
- `evidec.EvidenceReport`

典型的なフロー:
1. `Experiment` を作成
   - 実験名 (`name`)
   - 指標名 (`metric`)
   - バリアント名 (`variant_names = ("control", "treatment")` など)
2. `exp.fit(control_data, treatment_data)` を呼び出し、`StatResult` を得る。
   - 入力は以下のいずれか:
     - 0/1 の配列（CTR, CVR など）
     - 連続値の配列（売上, 滞在時間など）
     - `(success, total)` のタプル（比率データを集計済みのケース）
3. `DecisionRule` を構成し、`rule.judge(result)` で `Decision` を得る。
4. `EvidenceReport.from_result(exp, rule, decision, result)` でレポートを生成し、
   - `report.markdown` から Markdown を取得。

Agent は、このフローを壊さない形で拡張・修正を提案すること。

---

## 6. コーディング規約・スタイル
- 型ヒント必須: `mypy` 設定で `disallow_untyped_defs = true`。
- Lint: `ruff` による `E`, `F`, `I`, `B`, `W`, `UP` チェックを通す。
- フォーマット:
  - 行長は 100 文字 (`line-length = 100`)。
  - 文字列はダブルクオート。
  - インデントはスペース。
  - 改行コードは LF。

スタイルを崩す変更を行った場合は、`poe format` を提案すること。

---

## 7. テストポリシー
- テストは `tests/` ディレクトリ配下に追加する。
- `pytest` 実行時には `--cov=evidec` によりカバレッジを計測している。
- 機能追加・バグ修正を行う場合:
  - 既存の関連テストを更新、または
  - 新しいテストケースを追加する。
- 可能であれば、変更後に `poe test` もしくは `poe check` を実行することを推奨。

---

## 8. Agent の行動方針
以下は、このリポジトリで動作する Agent が守るべきルールです。

### 8.1 安定性・互換性
- 既存の公開 API:
  - `Experiment`, `StatResult`
  - `DecisionRule`, `Decision`, `DecisionStatus`
  - `EvidenceReport`
- これらの **クラス名・メソッド名・引数シグネチャ・戻り値の意味** を、ユーザーの明示的な許可なく変更しないこと。
- 破壊的変更（シグネチャ変更・戻り値変更・挙動の大幅変更）は、
  - ユーザーが「破壊的変更 OK」と明示した場合のみ提案する。

### 8.2 変更提案の原則
- バグ修正やリファクタリングでは、以下を優先する:
  - 挙動の互換性維持
  - テストの追加・強化
  - エラーメッセージの明確化
- 新機能を追加する場合は、**少なくとも 1 つ以上のユニットテスト** を `tests/` に追加すること。
- レポート文言の変更・追加:
  - 日本語を優先しつつ、必要に応じて英語コメントで補足してよい。
  - 既存の文言トーン（事実ベース・定性的な評価のバランス）を尊重する。

### 8.3 実装上の注意
- `Experiment.fit` は、入力から自動的に
  - 比率指標 → z検定
  - 連続値指標 → t検定
  を選択している。  
  → この自動判定ロジックを壊さないこと。
- `DecisionRule.judge` は、
  - `alpha` 閾値
  - `min_lift`
  - `metric_goal` (increase / decrease)
  - `min_effect_size`
  を組み合わせて GO / NO_GO / INCONCLUSIVE を返す。  
  → ロジック変更時は、判定結果が変わりうるケースをテストで明示すること。
- `EvidenceReport` / `renderer` は、
  - 上記のオブジェクトから Markdown を組み立てる層であり、
  - 言語やフォーマットの変更は UI 層の変更扱いとして慎重に行うこと。

### 8.4 ドキュメント・例の更新
- 公開 API に変更を加えた場合や代表的な使い方が増えた場合は、
  - `README.md`
  - `examples/basic_ab.py`
  の更新も検討すること。

---

## 9. Agent への要約メッセージ
- まず `evidec/core/`・`evidec/stats/`・`evidec/report/`・`tests/` を読んでから判断すること。
- API 互換性とテストを最優先すること。
- 変更提案時は、**どのファイルのどの関数 / クラスに何を変えるか** を具体的に示すこと。
- 可能な限り `poe check` が通る状態を保つこと。
