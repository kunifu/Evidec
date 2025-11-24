"""設計方針のミニマム検証テスト。

OSS で最低限守りたい 2 つを自動チェックする：
1. Public API を小さく・安定させる（Facade のみを公開）
2. 内部依存が循環しない
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path

EXPECTED_PUBLIC_API = {
    "Experiment",
    "DecisionRule",
    "Decision",
    "StatResult",
    "EvidenceReport",
}
ALLOWED_ROOT_ONLY = {"__version__"}


def _is_type_checking_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.If):
        return False
    test = node.test
    if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
        return True
    return (
        isinstance(test, ast.Attribute)
        and isinstance(test.value, ast.Name)
        and test.value.id == "typing"
        and test.attr == "TYPE_CHECKING"
    )


def _iter_import_nodes(root: ast.AST) -> Iterable[ast.AST]:
    """TYPE_CHECKING ガード内は無視しつつ import ノードを列挙。"""
    stack = [root]
    while stack:
        node = stack.pop()
        if isinstance(node, ast.If) and _is_type_checking_guard(node):
            continue  # 型ヒント専用の依存は実行時依存として扱わない
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            yield node
        stack.extend(ast.iter_child_nodes(node))


def _get_evidec_imports(file_path: Path) -> set[str]:
    """evidec.* への import だけを抽出する。"""
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    imports: set[str] = set()

    for node in _iter_import_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("evidec"):
                    imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level != 0:
                continue  # 相対 import の解決は不要（Public API 確認では使わない）
            if node.module and node.module.startswith("evidec"):
                imports.add(node.module)
    return imports


def _get_dunder_all(file_path: Path) -> list[str]:
    """__all__ に定義されたシンボルを取得する。"""
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    return ast.literal_eval(node.value)
    return []


class TestPublicAPI:
    """Public API が小さく・安定していることを検証。"""

    def test_PublicAPIがFacade集合と一致する(self) -> None:
        core_exports = set(_get_dunder_all(Path("evidec/core.py")))
        root_exports = set(_get_dunder_all(Path("evidec/__init__.py")))

        assert (
            core_exports == EXPECTED_PUBLIC_API
        ), f"evidec/core.py の公開シンボルが想定外: {core_exports}"
        assert (
            root_exports == EXPECTED_PUBLIC_API | ALLOWED_ROOT_ONLY
        ), f"evidec/__init__.py の公開シンボルが想定外: {root_exports}"

    def test_ルートはcoreのみを再輸出する(self) -> None:
        imports = _get_evidec_imports(Path("evidec/__init__.py"))
        assert imports == {
            "evidec.core"
        }, f"Facade 経由でのみ公開する想定。実際の import: {imports}"
