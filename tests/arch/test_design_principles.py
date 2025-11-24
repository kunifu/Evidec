"""設計原則の自動検証テスト。

Facade パターン、責務分離、依存関係の制約を検証します。
"""

from __future__ import annotations

import ast
from pathlib import Path


def _get_imports_from_file(file_path: Path) -> list[tuple[str, str]]:
    """ファイル内の import 文を抽出する。

    Returns:
        (module_name, alias) のタプルのリスト
    """
    with open(file_path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))

    imports: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, alias.asname or alias.name.split(".")[-1]))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for alias in node.names:
                    imports.append((node.module, alias.asname or alias.name))
    return imports


def _get_evidec_imports(file_path: Path) -> list[str]:
    """evidec 関連の import のみを抽出する。"""
    imports = _get_imports_from_file(file_path)
    return [mod for mod, _ in imports if mod and mod.startswith("evidec")]


class TestFacadePattern:
    """Facade パターンの検証。"""

    def test_root_init_only_imports_from_core(self):
        """evidec/__init__.py は evidec.core からのみ import すべき。"""
        root_init = Path("evidec/__init__.py")
        imports = _get_evidec_imports(root_init)

        assert len(imports) > 0, "evidec/__init__.py は evidec.core から import すべき"
        assert all(
            imp == "evidec.core" for imp in imports
        ), f"evidec/__init__.py は evidec.core からのみ import すべき。実際: {imports}"

    def test_core_py_imports_from_internal_modules(self):
        """evidec/core.py は内部モジュールから import すべき。"""
        core_py = Path("evidec/core.py")
        imports = _get_evidec_imports(core_py)

        expected_modules = {
            "evidec.decision.rule",
            "evidec.experiment.experiment",
            "evidec.experiment.result",
            "evidec.report.schema",
        }
        actual_modules = set(imports)

        assert (
            actual_modules == expected_modules
        ), f"evidec/core.py は {expected_modules} から import すべき。実際: {actual_modules}"

    def test_no_direct_imports_from_internal_modules_in_root(self):
        """evidec/__init__.py は内部モジュールを直接 import しない。"""
        root_init = Path("evidec/__init__.py")
        imports = _get_evidec_imports(root_init)

        forbidden_prefixes = [
            "evidec.experiment",
            "evidec.decision",
            "evidec.report",
            "evidec.stats",
        ]
        for imp in imports:
            assert not any(
                imp.startswith(prefix) for prefix in forbidden_prefixes
            ), f"evidec/__init__.py は内部モジュール ({imp}) を直接 import すべきではない"


class TestModuleSeparation:
    """モジュールの責務分離の検証。"""

    def test_experiment_module_structure(self):
        """experiment モジュールは適切に分離されている。"""
        experiment_dir = Path("evidec/experiment")
        files = {
            f.name
            for f in experiment_dir.iterdir()
            if f.suffix == ".py" and f.name != "__init__.py"
        }

        expected_files = {"experiment.py", "result.py"}
        assert (
            files == expected_files
        ), f"experiment モジュールは {expected_files} を含むべき。実際: {files}"

    def test_decision_module_structure(self):
        """decision モジュールは適切に分離されている。"""
        decision_dir = Path("evidec/decision")
        files = {
            f.name
            for f in decision_dir.iterdir()
            if f.suffix == ".py" and f.name != "__init__.py"
        }

        expected_files = {"rule.py"}
        assert (
            files == expected_files
        ), f"decision モジュールは {expected_files} を含むべき。実際: {files}"

    def test_report_module_structure(self):
        """report モジュールは適切に分離されている。"""
        report_dir = Path("evidec/report")
        files = {
            f.name
            for f in report_dir.iterdir()
            if f.suffix == ".py" and f.name != "__init__.py"
        }

        expected_files = {"schema.py", "renderer.py", "formatters.py"}
        assert (
            files == expected_files
        ), f"report モジュールは {expected_files} を含むべき。実際: {files}"

    def test_no_core_directory_exists(self):
        """evidec/core/ ディレクトリは存在しない（core.py のみ）。"""
        core_dir = Path("evidec/core")
        core_file = Path("evidec/core.py")

        assert not core_dir.exists(), (
            "evidec/core/ ディレクトリは存在すべきではない（Facade は core.py ファイル）"
        )
        assert core_file.exists(), "evidec/core.py ファイルは存在すべき"


class TestDependencyRules:
    """依存関係の制約検証。"""

    def test_experiment_imports_only_stats(self):
        """experiment モジュールは stats のみを import すべき。"""
        experiment_file = Path("evidec/experiment/experiment.py")
        imports = _get_evidec_imports(experiment_file)

        allowed = {"evidec.stats", "evidec.experiment.result"}
        for imp in imports:
            assert imp in allowed or imp.startswith(
                "evidec.experiment"
            ), f"experiment.py は {allowed} からのみ import すべき。実際: {imp}"

    def test_decision_imports_from_experiment_and_report(self):
        """decision モジュールは experiment.result と report.formatters を import すべき。"""
        decision_file = Path("evidec/decision/rule.py")
        imports = set(_get_evidec_imports(decision_file))

        expected = {"evidec.experiment.result", "evidec.report.formatters"}
        assert (
            expected.issubset(imports)
        ), f"decision/rule.py は {expected} を import すべき。実際: {imports}"

    def test_report_schema_imports_from_other_modules(self):
        """report/schema.py は他のモジュールから適切に import する。"""
        schema_file = Path("evidec/report/schema.py")
        imports = set(_get_evidec_imports(schema_file))

        expected = {"evidec.report.formatters", "evidec.report.renderer"}
        assert (
            expected.issubset(imports)
        ), f"report/schema.py は {expected} を import すべき。実際: {imports}"

    def test_report_renderer_imports_formatters(self):
        """report/renderer.py は report.formatters を import すべき。"""
        renderer_file = Path("evidec/report/renderer.py")
        imports = set(_get_evidec_imports(renderer_file))

        expected = {"evidec.report.formatters"}
        assert (
            expected.issubset(imports)
        ), f"report/renderer.py は {expected} を import すべき。実際: {imports}"


class TestPublicAPI:
    """公開 API の整合性検証。"""

    def test_core_exports_all_public_classes(self):
        """evidec/core.py はすべての公開クラスを export している。"""
        core_py = Path("evidec/core.py")
        content = core_py.read_text(encoding="utf-8")

        expected_exports = [
            "Experiment",
            "DecisionRule",
            "Decision",
            "StatResult",
            "EvidenceReport",
        ]
        for export in expected_exports:
            assert (
                export in content
            ), f"evidec/core.py は {export} を export すべき"

    def test_root_init_exports_match_core(self):
        """evidec/__init__.py の export は evidec/core.py と一致すべき。"""
        root_init = Path("evidec/__init__.py")
        root_content = root_init.read_text(encoding="utf-8")

        core_py = Path("evidec/core.py")
        core_content = core_py.read_text(encoding="utf-8")

        expected_exports = [
            "Experiment",
            "DecisionRule",
            "Decision",
            "StatResult",
            "EvidenceReport",
        ]
        for export in expected_exports:
            assert (
                export in root_content
            ), f"evidec/__init__.py は {export} を export すべき"
            assert (
                export in core_content
            ), f"evidec/core.py は {export} を export すべき"

