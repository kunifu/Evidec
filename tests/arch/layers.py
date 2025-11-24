"""ドメイン階層ルールを一元管理するモジュール。"""

from __future__ import annotations

from pathlib import Path

# ドメイン間の許可依存マトリクス
ALLOWED_DOMAIN_DEPS: dict[str, set[str]] = {
    # ルートは Facade(core) のみを再輸出
    "root": {"core"},
    # Facade は公開オブジェクトが属するドメインのみ束ねる
    "core": {"report", "decision", "experiment"},
    # ベイズ拡張は判定ロジックに依存
    "bayes": {"decision"},
    # UI 層: レポート生成に必要なドメインだけ
    "report": {"decision", "experiment", "utils"},
    # 判定層: 実験結果と共有ユーティリティに依存
    "decision": {"experiment", "utils"},
    # 実験層: 統計計算のみを利用
    "experiment": {"stats"},
    # 統計層: 他ドメインに依存しない
    "stats": set(),
    # 横断ユーティリティ: 自己完結
    "utils": set(),
}


def domain_of_path(path: Path) -> str:
    """ファイルパスからドメイン名を推定する。"""

    rel_parts = path.relative_to(Path("evidec")).parts
    if not rel_parts:
        return "root"
    if rel_parts[0] in {"__init__.py", "__pycache__"}:
        return "root"
    if len(rel_parts) == 1:
        stem = Path(rel_parts[0]).stem
        return stem if stem else "root"
    return rel_parts[0]


def domain_of_module(module: str) -> str:
    """モジュール名からドメイン名を取得する。"""

    parts = module.split(".")
    if len(parts) < 2:
        return "root"
    return parts[1]
