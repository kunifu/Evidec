# ベイズ推論モジュール 設計書

## 1. モジュール構成
`evidec` パッケージ直下に `bayesian` サブパッケージを新設する。

```
evidec/
  bayesian/
    __init__.py
    beta_binomial.py      # Beta-Binomial モデルの実装
    decision_rule.py      # ベイズ判定ルール (GO/SAFE/NO-GO)
    adapters.py           # 配列→集計のヘルパー（必要に応じて）
```

## 2. データ構造

### 2.1 BayesResult
ベイズ推論の結果を保持する不変データクラス。レポート出力と判定で共通利用する。

```python
# evidec/bayesian/beta_binomial.py

@dataclass(frozen=True)
class BayesResult:
    p_improve: float
    p_above_tol: float
    lift_mean: float
    lift_ci: tuple[float, float]
    tolerance: float
    method: str = "beta-binomial"
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "p_improve": self.p_improve,
            "p_above_tol": self.p_above_tol,
            "lift_mean": self.lift_mean,
            "lift_ci": self.lift_ci,
            "tolerance": self.tolerance,
            "method": self.method,
            "params": self.params,
        }
```

- `params` には事前分布 `alpha0`, `beta0`, サンプリング設定 `n_draws`, `seed`, 入力サマリ（成功数/試行数）を格納し、レンダラー側で辞書アクセス時に欠損しないようにする。

## 3. API 設計

### 3.1 fit_beta_binomial

```python
# evidec/bayesian/beta_binomial.py

def fit_beta_binomial(
    control_success: int,
    control_total: int,
    treatment_success: int,
    treatment_total: int,
    *,
    alpha0: float = 1.0,
    beta0: float = 1.0,
    n_draws: int = 20000,
    tolerance: float = -0.005,
    seed: int | None = None
) -> BayesResult:
    ...
```

- **入力**: 整数型の成功数・試行数を受け取る。配列入力の正規化は呼び出し元で行うか、ヘルパー関数を用意する（今回はシンプルに整数入力を基本とする）。
- **計算ロジック**:
    1.  事後分布パラメータ計算:
        - `alpha_c = alpha0 + control_success`
        - `beta_c = beta0 + (control_total - control_success)`
        - `alpha_t = alpha0 + treatment_success`
        - `beta_t = beta0 + (treatment_total - treatment_success)`
    2.  乱数生成:
        - `rng = np.random.default_rng(seed)`
        - `sample_c = rng.beta(alpha_c, beta_c, size=n_draws)`
        - `sample_t = rng.beta(alpha_t, beta_t, size=n_draws)`
    3.  リフト計算:
        - `lift = sample_t - sample_c`
    4.  統計量算出:
        - `p_improve = np.mean(lift > 0)`
        - `p_above_tol = np.mean(lift > tolerance)`  # 許容下限（例: -0.5pp）を超える確率
        - `lift_mean = np.mean(lift)`
        - `lift_ci = np.percentile(lift, [2.5, 97.5])`
    5.  `BayesResult` に格納:
        - `params` に `alpha0`, `beta0`, `n_draws`, `tolerance`, `seed`, `control_success`, `control_total`, `treatment_success`, `treatment_total` を保存し、レンダラーが安全に参照できるようにする。

### 3.2 配列入力ヘルパー（任意）

集計済みデータを持たない利用者向けに、0/1 配列を受け取り集計してから `fit_beta_binomial` を呼ぶ薄いヘルパーを用意してもよい。

```python
# evidec/bayesian/adapters.py

def fit_beta_binomial_from_arrays(
    control: ArrayLike,
    treatment: ArrayLike,
    **kwargs: Any,
) -> BayesResult:
    control_success = int(np.sum(control))
    control_total = int(len(control))
    treatment_success = int(np.sum(treatment))
    treatment_total = int(len(treatment))
    return fit_beta_binomial(
        control_success,
        control_total,
        treatment_success,
        treatment_total,
        **kwargs,
    )
```

## 4. 既存コンポーネントの拡張

### 4.1 EvidenceReport (evidec/core/report.py)
`BayesResult` を保持できるように拡張する。

```python
@dataclass(frozen=True)
class EvidenceReport:
    # ... existing fields ...
    bayes_result: BayesResult | None = None  # 追加

    @classmethod
    def from_result(
        cls,
        experiment: Experiment,
        rule: RuleDisplayContext,
        decision: Decision,
        stat_result: StatResult,
        bayes_result: BayesResult | None = None,  # 追加
    ) -> EvidenceReport:
        # ...
        markdown = render_markdown(experiment, decision, stat_result, rule, bayes_result)
        return cls(..., bayes_result=bayes_result)
```

### 4.2 Renderer (evidec/report/renderer.py)
`render_markdown` 関数に `bayes_result` 引数を追加し、存在する場合にセクションを追記する。

```python
def render_markdown(
    experiment: Experiment,
    decision: Decision,
    stat_result: StatResult,
    rule: RuleDisplayContext,
    bayes_result: BayesResult | None = None,  # 追加
) -> str:
    # ... 既存の処理 ...
    
    if bayes_result:
        lines.extend([
            "",
            "## Bayesian Evidence (Beta-Binomial)",
            f"- **改善確率 (P(Δ>0))**: {bayes_result.p_improve:.1%}",
            f"- **非劣性確率 (P(Δ>{bayes_result.tolerance:+.1%}))**: {bayes_result.p_above_tol:.1%}",
            f"- **推定リフト**: {bayes_result.lift_mean:+.2%} (95% CI: {bayes_result.lift_ci[0]:+.2%} ~ {bayes_result.lift_ci[1]:+.2%})",
        ])
    
    return "\n".join(lines)
```

## 5. ベイズ判定ロジック

頻度論的 DecisionRule を置き換えず、ベイズ専用の軽量ルールを追加する。

```python
# evidec/bayesian/decision_rule.py

@dataclass(frozen=True)
class BayesDecisionRule:
    p_improve_go: float = 0.95   # 改善確率がこの値以上なら「改善とみなす」
    p_safe: float = 0.975        # 非劣性確率（悪化しない確率）がこの値以上で安全圏
    p_improve_safe: float = 0.80 # SAFE 判定の下限（改善期待の弱いが悪化は低い）
    min_lift: float = 0.0        # リフト期待値の下限（任意）

    def judge(self, bayes: BayesResult) -> Decision:
        # status は既存の DecisionStatus を流用
        if (
            bayes.p_improve >= self.p_improve_go
            and bayes.p_above_tol >= self.p_safe
            and bayes.lift_mean >= self.min_lift
        ):
            status: DecisionStatus = "GO"
            reason = (
                f"P(Δ>0)={bayes.p_improve:.1%}≥{self.p_improve_go:.0%}, "
                f"P(Δ>{bayes.tolerance:+.1%})={bayes.p_above_tol:.1%}≥{self.p_safe:.0%}"
            )
        elif bayes.p_above_tol >= self.p_safe and bayes.p_improve >= self.p_improve_safe:
            status = "SAFE"
            reason = "悪化リスクは低いが改善確率が基準未満 → SAFE"
        elif bayes.p_above_tol < self.p_safe:
            status = "NO_GO"
            reason = "悪化リスクが許容を超過 → NO_GO"
        else:
            status = "INCONCLUSIVE"
            reason = "確率指標が閾値に達していない → INCONCLUSIVE"

        return Decision(status=status, reason=reason, stats={
            "p_improve": bayes.p_improve,
            "p_above_tol": bayes.p_above_tol,
            "lift_mean": bayes.lift_mean,
            "tolerance": bayes.tolerance,
            "p_improve_go": self.p_improve_go,
            "p_safe": self.p_safe,
            "p_improve_safe": self.p_improve_safe,
            "min_lift": self.min_lift,
        })
```

- 既存の `DecisionRule` を変更せず、ベイズ判定が必要な場合のみ利用者がこのルールを選択する。
- SAFE を追加するが `DecisionStatus` を拡張しないため、SAFE は `Decision` の `reason` と `stats` に表示し、ステータス自体は `GO/NO_GO/INCONCLUSIVE` のままとする案と、`DecisionStatus` を拡張する案の2択がある。破壊的変更を避けるため前者（INCONCLUSIVE として扱い、reason に SAFE を明記）を推奨する。

## 6. テスト計画

- `tests/bayesian/test_beta_binomial.py`
  - 改善確率・非劣性確率の計算が期待通り（簡単な手計算ケース）
  - `tolerance` 符号の解釈確認（負の許容下限で `p_above_tol` が増えること）
  - `seed` による再現性（同じ seed で結果が一致）
  - 大規模サンプルで計算が秒オーダーで完了すること（性能回帰テストは time 上限付き）
- `tests/bayesian/test_decision_rule.py`
  - GO/SAFE/NO-GO/INCONCLUSIVE の各分岐をカバー
  - SAFE 判定が `DecisionStatus` を拡張しない場合の表示確認
- `tests/report/test_renderer_bayesian.py`
  - `bayes_result` あり/なしで Markdown が後方互換で生成される
  - `params` 辞書が空でも KeyError にならないこと

## 7. パフォーマンス・再現性

- `n_draws` のデフォルト 20,000 は通常の AB テスト規模で数秒以内を想定。必要に応じて `n_draws` を増減可能とし、ドキュメントで計算コストの目安を記載する。
- `numpy.random.default_rng(seed)` で擬似乱数を制御し、シード指定時は完全再現を保証する。

## 8. 互換性・後方対応

- 既存 API (`Experiment`, `StatResult`, `DecisionRule`, `EvidenceReport`) のシグネチャは変更しない。ベイズ関連はオプション引数・新規モジュール追加で提供。
- `bayes_result` が渡されない場合は従来通りのレポートを返し、既存の利用コードは無変更で動作する。
- SAFE ステータス表示は非破壊的に扱う（理由文に明記しつつ `DecisionStatus` は維持）。必要に応じて今後のメジャーアップデートで拡張を検討する。

## 9. 実装ステップ
1. `evidec/bayesianian/beta_binomial.py` に `BayesResult`・`fit_beta_binomial` を実装し、`params` に必要メタ情報を格納する。
2. `evidec/bayesianian/adapters.py`（任意）で配列入力ヘルパーを実装する。
3. `evidec/bayesianian/decision_rule.py` にベイズ判定ロジックを実装し、既存 `Decision` を返す形にする。
4. `evidec/core/report.py` を拡張して `bayes_result` を受け取れるようにする。
5. `evidec/report/renderer.py` を拡張し、ベイズセクションを条件付きでレンダリングする。
6. `evidec/__init__.py` で公開範囲を整理（必要であれば）。
7. テスト追加：`tests/bayesian/` 配下とレンダラー周りを新設し、決定木と再現性をカバーする。
