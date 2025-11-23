# Evidec MVP 技術設計書 (WIP)

## 1. 目的と対象
- 01_MVP要件.md の機能要件を実装するための技術方針・設計を定義する。
- スコープ: Python API による検定・判定・Markdown Evidence Report 生成まで（CLI/GUI は対象外）。
- 非スコープ: データクレンジング、サンプルサイズ計算、ベイズ手法、ダッシュボード等は含めない。

## 2. 技術選定
- 言語・ランタイム: Python ≥ 3.10（パターンマッチング、型ヒントの充実を活用）。
- パッケージ管理: `pyproject.toml` を基盤とし、インストールは **uv** を推奨（`uv pip install -e '.[dev]'`）。pip も互換維持。
- タスクランナー: **poethepoet** を採用し、`poe lint|format|typecheck|test|check` を定義。
- コア依存: `numpy`, `scipy`（z-test, t-test）, `pandas`（Series 入力サポート）。
- 開発用依存: `pytest`, `pytest-cov`, `mypy`, `ruff`, `poethepoet`。
- 配布形態: PyPI 配布を前提に `evidec` パッケージを PEP517 ビルド（hatchling）。
- ドキュメント: README + `examples/basic_ab.py`。後続で `docs/` に拡張可能。

## 3. アーキテクチャ概要
```
evidec/
├─ core/
│   ├─ experiment.py      # 入力検証・実行オーケストレーション
│   ├─ decision_rule.py   # 判定ロジック
│   └─ report.py          # EvidenceReport モデル
├─ stats/
│   ├─ ztest.py           # 比率検定
│   └─ ttest.py           # 平均差 t 検定
└─ report/
    └─ renderer.py        # Markdown 生成
```
- `stats` は純計算レイヤ。`core` はドメインロジック。`report` はプレゼンテーションに限定。
- 依存方向: `core` → `stats` / `report`。`stats` と `report` 間に依存を持たない。
- 単体テストはレイヤ単位（`tests/stats/test_ztest.py` など）で分割。

## 4. データモデル
- `StatResult`（dataclass）
  - `effect: float`（treatment - control または lift）
  - `p_value: float`
  - `ci_low: float`, `ci_high: float`
  - `method: Literal["two-proportion z-test", "two-sample t-test"]`
  - `metric: str`（例: "ctr", "cvr"）
  - `baseline: float | None`（比率なら control 比率、平均なら control 平均）
- `Decision`
  - `status: Literal["GO", "NO_GO", "INCONCLUSIVE"]`
  - `reason: str`（閾値・p値・CI を含む自然文）
  - `stats: dict[str, float]`（`p_value`, `lift`, `alpha`, `min_lift` 等）
- `DecisionRule`
  - `alpha: float`, `min_lift: float`, `metric_goal: Literal["increase","decrease"]`, `min_effect_size: float | None`
- `Experiment`
  - `name: str`, `metric: str`, `variant_names: tuple[str,str]`
  - `fit(control, treatment) -> StatResult`
  - `judge(rule: DecisionRule) -> Decision`
- `EvidenceReport`
  - `summary`, `statistical_evidence`, `decision_rule`, `interpretation` の各セクション文字列を保持。

## 5. モジュール設計詳細
- `stats/ztest.py`
  - `ztest_proportions(control_success, control_total, treatment_success, treatment_total, correction=False)` を提供。
  - 入力は int または array-like。array の場合は success=1/0 としてカウントするユーティリティを内部に持つ。
  - 正規近似前提を明記し、サンプルが少ない場合は警告（`RuntimeWarning`）を発生させる。
- `stats/ttest.py`
  - `ttest_means(control_samples, treatment_samples, equal_var=False)` を提供。scipy.stats.ttest_ind を呼び出し、効果量を treatment - control で算出。
  - CI 計算は Welch/Student の df に応じて `stats.t.interval` を使用。
- `core/experiment.py`
  - 入力検証（NaN 除去、空配列チェック、型正規化）を行い、メトリック種別を選択して `stats` を呼び出す。
  - `summary()` は `StatResult` を辞書化し、小数/百分率の整形を統一する。
- `core/decision_rule.py`
  - `judge(result: StatResult) -> Decision`。`metric_goal` に基づき効果方向を評価。`p_value` と `alpha`、`min_lift` を順序立てて判定。
  - 理由文はテンプレートベースで生成し、閾値と実測値を明示（例: `"p=0.012 ≤ α=0.05 かつ lift=2.3% ≥ min_lift=1.0% → GO"`）。
- `report/renderer.py`
  - Markdown を組み立てる純関数 `render_markdown(experiment, decision, stat_result, rule) -> str`。
  - 数値フォーマット: 比率・lift は `:+.1%`, p値は `:.3f`（0.000 未満は `<0.001` 表記）。
  - 英語/日本語混在を避け、MVP では日本語テンプレートを固定。将来ローカライズ用にテンプレート分離を検討。
- `core/report.py`
  - `EvidenceReport` dataclass とファクトリ関数を置き、`renderer` を呼び出すだけに留める（プレゼン層との結合を薄く）。

## 6. API サーフェス（想定）
```python
from evidec.core.experiment import Experiment
from evidec.core.decision_rule import DecisionRule
from evidec.core.report import EvidenceReport

exp = Experiment(
    name="cta_color_test",
    metric="ctr",
    variant_names=("control", "treatment")
)
result = exp.fit(control_data, treatment_data)

rule = DecisionRule(alpha=0.05, min_lift=0.01, metric_goal="increase")
decision = rule.judge(result)

report = EvidenceReport.from_result(exp, rule, decision, result)
print(report.markdown)
```

## 7. エラーハンドリング & バリデーション
- 入力長が 2 未満、全て同一値などで検定が不可能な場合は `ValueError` を送出。
- NaN/inf は事前に除去・警告。比率データで分母=0 の場合は例外。
- `metric_goal` が `increase|decrease` 以外の場合は即時例外。
- 検定での数値不安定（極端な p値）は `RuntimeWarning` で通知しつつ値は返す。

## 8. テスト戦略
- `stats`：scipy 既知ケースとの一致を ±1e-6 以内で検証（比率・平均双方）。
- `decision_rule`：p値境界、lift 境界、効果逆転、非有意の4系統で表形式テスト。
- `report`：レンダリング結果に GO/NO_GO/INCONCLUSIVE の各文言と主要数値が含まれることをスナップショットテスト。
- `examples/basic_ab.py`：最小実行例。pytest で smoke テストとしても実行。
- カバレッジ目標: lines 80% 以上、分岐 70% 以上（MVP）。

## 9. 数値フォーマット・国際化方針（MVP）
- 内部計算は全て浮動小数（倍精度）。出力は用途に応じ丸め:
  - lift/比率: `round(value, 4)` を計算保持、表示は `:.1%`。
  - p値: `:.4f`、0.00005 未満は `<0.0001`。
- 言語は日本語固定。将来は `renderer` をテンプレート単位で差し替え可能にする。

## 10. パフォーマンス・拡張性
- ベクトル演算を優先し、ループを避ける（`numpy` 依存で十分）。
- 入力サイズは典型的な A/B テスト（〜百万行）を想定し、データは配列/Series のみ扱い、DataFrame 全体の複製を避ける。
- 将来拡張: 事前に `StatResult` に `effect_size`（Cohen's d 等）フィールドを追加できる余白を確保。

## 11. 開発フロー
- uv 推奨: `uv pip install -e '.[dev]'`
- poe タスク（pyproject定義）:
  - `poe lint` → `ruff check .`
  - `poe format` → `ruff format .`
  - `poe typecheck` → `mypy evidec`
  - `poe test` → `pytest -q`
  - `poe check` → 上記 lint+type+test を連鎖
- CI（後続）：GitHub Actions で `uv pip install -e '.[dev]'` → `poe check` → `poe test examples/basic_ab.py` 実行を組み合わせる。

## 12. リスクと対応
- **正規近似の妥当性**: サンプル小時の z-test 精度低下 → サンプル条件をドキュメントに明記し警告を出す。
- **データ型のばらつき**: list/ndarray/Series 混在 → 入力正規化ユーティリティを `core` に用意。
- **浮動小数誤差**: 1e-6 の許容差でテスト、表示丸めと内部計算を分離。
- **判定ロジックの誤用**: `metric_goal` が逆指定されるリスク → docstring と例示で強調、判定理由文に方向性を含める。

## 13. 実装タスクリスト（MVP）
- [ ] `StatResult`, `Decision`, `DecisionRule`, `Experiment`, `EvidenceReport` の dataclass 実装
- [ ] `ztest_proportions`, `ttest_means` の計算関数 + テスト
- [ ] `DecisionRule.judge` の判定ロジック + テスト
- [ ] `renderer.render_markdown` と `EvidenceReport.from_result`
- [ ] `examples/basic_ab.py` の動作確認
- [ ] README にスコープ/使い方/制約を追記
