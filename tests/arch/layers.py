"""ドメイン階層ルールを一元管理するモジュール。"""

from __future__ import annotations

from pathlib import Path

# ドメイン間の許可依存マトリクス
ALLOWED_DOMAIN_DEPS: dict[str, set[str]] = {
    # ルートは Facade(core) のみを再輸出
    "root": {"core"},
    # Facade は全ドメインを束ねてよい
    "core": {"report", "decision", "experiment", "stats", "utils"},
    # UI 層
    "report": {"report", "decision", "experiment", "stats", "utils"},
    # 判定層
    "decision": {"decision", "experiment", "stats", "utils"},
    # 実験層
    "experiment": {"experiment", "stats", "utils"},
    # 統計層
    "stats": {"stats", "utils"},
    # 横断ユーティリティ
    "utils": {"utils"},
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
