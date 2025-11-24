"""AST ヘルパー: evidec.* import 抽出や __all__ 取得を担当。"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path

__all__ = [
    "get_evidec_imports",
    "get_dunder_all",
]


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
    """TYPE_CHECKING ガード内を無視しつつ import ノードを列挙。"""
    stack = [root]
    while stack:
        node = stack.pop()
        if isinstance(node, ast.If) and _is_type_checking_guard(node):
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            yield node
        stack.extend(ast.iter_child_nodes(node))


def get_evidec_imports(file_path: Path) -> set[str]:
    """evidec.* への import を抽出する（相対 import は無視）。"""
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    imports: set[str] = set()

    for node in _iter_import_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("evidec"):
                    imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level != 0:
                continue  # 相対 import はここでは扱わない
            if node.module and node.module.startswith("evidec"):
                imports.add(node.module)
    return imports


def get_dunder_all(file_path: Path) -> list[str]:
    """__all__ に定義されたシンボルを取得する。"""
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    return ast.literal_eval(node.value)
    return []
