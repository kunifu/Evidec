# Evidec — Evidence Engine for Decision Making
> データを、意思決定の「確かな証拠」へ。  
> *Turn Data into Decision.*

---

## 1. プロジェクト概要（What is Evidec?）

**Evidec** は、A/B テストや実験データをもとに  
**「計算 → 解釈 → 判断（Go/No-Go） → 証拠提示」までを一貫処理する Python OSS** です。

多くの OSS が統計計算で止まる一方、Evidec は **意思決定そのものを扱う** 点に特徴があります。  
Analyst / PdM / Biz が共通の “Evidence” を元に迅速かつ納得感のある判断を下せる世界を目指します。

---

## 2. 解決したい課題（Problem）

実務の現場では、実験フローがしばしば分断されています：

```
実験設計 → 検定 → 結果解釈 → Go/No-Go → 証拠レポート作成
```

この結果、次のような問題が起きます。

### ● 分析はできるが意思決定につながらない
- p値やグラフはあるが「結局どうすべきか？」が不明確
- 結論の根拠がドキュメント化されず、再利用できない

### ● A/B テストごとにスクリプトをスクラッチで作る非効率
- 実装が属人化し、手法や前提の一貫性が保てない
- 「とりあえずt検定」など統計的な誤用が頻発

### ● 判断基準が属人化し、組織として標準化されていない
- メール・口頭・Excel などに基準が散在
- 「p値 0.06 だけど今回はGO」など暗黙知がコード化されない

---

## 3. Evidec が提供する解決（Value Proposition）

Evidec は上記の断絶を埋め、**実験結果を組織的な意思決定へ変換する “Evidence Engine”** を提供します。

### 1. 設計 → 統計検証 → 判定 → レポート を一貫提供
統計計算で終わらず、判断可能な「証拠レポート」まで自動生成。

### 2. 意思決定の再現性と品質を向上
判断基準を **DecisionRule** としてコード化し、誰が分析しても同じルールが適用されます。

### 3. Evidence Report による共通言語化
Biz / PdM でも読める形式で要点だけを抽出したレポートを自動生成。

### 4. 確率分布（Assumptions）への厳格な準拠
メトリクスの性質に応じて適切な検定手法・前提を扱い、誤った意思決定を防ぐ。

---

## 4. 既存 OSS との差別化

| ツール | 守備範囲 | Evidec との違い |
| :--- | :--- | :--- |
| scipy / statsmodels | 統計計算 | 計算のみ。判断や証拠化は対象外。 |
| scikit-learn | 予測モデル | A/B テストや意思決定の文脈は持たない。 |
| CausalImpact / DoWhy | 因果推論 | 効果推定に特化。「判断」までは扱わない。 |
| **Evidec** | **意思決定・証拠化** | **計算結果を Go/No-Go に変換し、証拠レポートまで提供。** |

---

## 5. Evidec の守備範囲（Scope）

初期MVPは最も需要が高く、汎用性が高い以下にフォーカス：

### Design（実験設計）
- メトリクス定義
- [Future] サンプルサイズ計算（Power, MDE）

### Validation（統計検証）
- **比率検定（z-test） / t検定** [MVP]
- 信頼区間計算

### Decision（意思決定）
- **DecisionRule** による Go / No-Go / Inconclusive 自動判定
- 判定理由の言語化
- ルールのテンプレート化

### Reporting（証拠化）
- **Evidence Report** 自動生成（Markdown/Text）
- 統計結果と解釈の要約
- 組織判断に必要な根拠の明文化

---

## 6. Evidence Report の例（イメージ）

```
# Evidence Report — CTA Color Test

## Summary
- 判定: **GO**
- 改善度: +2.3%（基準 +1.0%）
- 有意差あり (p=0.012)

## Statistical Evidence
- Method: Two-proportion z-test
- 95% CI: [1.1%, 3.5%]

## Decision Rule
- α = 0.05
- min_lift = 1%
- metric_goal = increase

## Interpretation
基準を満たし、改善幅も事業的に十分であるため、Treatment を採用。
```

---

## 7. Before / After（導入効果）

### Before
- スクリプトが毎回スクラッチ
- 結果解釈が人によって異なる
- レポート作成に時間がかかる
- 過去の判断ロジックが資産化されない

### After（Evidec導入）
- 実験 → 検定 → 判定 → レポートが数行のコードで再現可能
- 一貫した DecisionRule により意思決定の再現性が向上
- Biz / PdM がそのまま読める Evidence が自動生成
- 過去の判断基準が組織資産として蓄積される

---

## 8. Evidec が自動化する領域 / しない領域

**Evidec が自動化する：**
- 適切な統計手法の選択
- 結果解釈（効果の方向性 / 信頼性）
- Go/No-Go 判定
- 証拠レポート生成

**Evidec が扱わない：**
- データクレンジング / 前処理
- 探索的データ分析（EDA）
- 高度な因果推論
- BI / GUI ダッシュボード

---

## 9. 初期 API イメージ

```python
from evidec import Experiment, DecisionRule

exp = Experiment(
    name="cta_color_test",
    metric="ctr",
    variant_names=["control", "treatment"]
)

rule = DecisionRule(
    alpha=0.05,
    min_lift=0.01,
    metric_goal="increase"
)

exp.fit(control_data, treatment_data)
decision = exp.judge(rule)

print(decision.summary())
```

---

## 10. アーキテクチャ構想（概要）

```
evidec/
├─ core/
│   ├─ experiment.py
│   ├─ decision_rule.py
│   └─ report.py
├─ stats/
│   ├─ ztest.py
│   └─ ttest.py
└─ report/
    └─ renderer.py
```

---

## 11. 今後のステップ

- [ ] **MVP**：比率検定 + DecisionRule + Textレポート
- [ ] Experiment / DecisionRule の詳細設計
- [ ] DDD を意識したパッケージ構成の確立
- [ ] README（OSS向け）作成

---
