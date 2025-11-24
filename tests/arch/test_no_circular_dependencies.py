"""内部依存が循環しないことを検証する。"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path


def _module_name_from_path(path: Path) -> str:
    rel = path.relative_to(Path("evidec"))
    parts = list(rel.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(["evidec", *parts]) if parts else "evidec"


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
    """TYPE_CHECKING ブロック内を除いて import ノードを列挙。"""
    stack = [root]
    while stack:
        node = stack.pop()
        if isinstance(node, ast.If) and _is_type_checking_guard(node):
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            yield node
        stack.extend(ast.iter_child_nodes(node))


def _get_internal_deps(path: Path, module_name: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    deps: set[str] = set()

    for node in _iter_import_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("evidec."):
                    deps.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                if node.module and node.module.startswith("evidec."):
                    deps.add(node.module)
                continue

            base_parts = module_name.split(".")
            if len(base_parts) < node.level:
                continue
            prefix = base_parts[: -node.level]

            if node.module:
                target = ".".join([*prefix, node.module])
                if target.startswith("evidec."):
                    deps.add(target)
            else:  # from . import foo, bar
                for alias in node.names:
                    target = ".".join([*prefix, alias.name])
                    if target.startswith("evidec."):
                        deps.add(target)
    return deps


def _build_dependency_graph(root: Path) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    for file_path in root.rglob("*.py"):
        module_name = _module_name_from_path(file_path)
        graph[module_name] = _get_internal_deps(file_path, module_name)
    return graph


def _find_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    visited: set[str] = set()
    stack: set[str] = set()
    path: list[str] = []

    def visit(node: str) -> bool:
        if node in stack:
            path.append(node)
            return True
        if node in visited:
            return False
        visited.add(node)
        stack.add(node)
        path.append(node)
        for dep in graph.get(node, set()):
            if dep in graph and visit(dep):
                return True
        path.pop()
        stack.remove(node)
        return False

    for n in graph:
        if visit(n):
            # cycle path ends where it started; slice for readability
            start = path[-1]
            while len(path) > 1 and path[0] != start:
                path.pop(0)
            return path + [start]
    return None


class TestNoCircularDependencies:
    def test_内部依存に循環がない(self) -> None:
        graph = _build_dependency_graph(Path("evidec"))
        cycle = _find_cycle(graph)
        assert cycle is None, f"循環依存を検出: {' -> '.join(cycle)}"
