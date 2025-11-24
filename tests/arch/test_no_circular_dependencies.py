"""循環依存の検証テスト。"""

from __future__ import annotations

from pathlib import Path


def _get_module_dependencies(file_path: Path) -> set[str]:
    """モジュールが依存する evidec 内部モジュールのリストを取得する。"""
    content = file_path.read_text(encoding="utf-8")
    dependencies: set[str] = set()

    lines = content.split("\n")
    for line in lines:
        if line.strip().startswith("from evidec.") or line.strip().startswith("import evidec."):
            parts = line.split()
            if "from" in parts:
                idx = parts.index("from")
                if idx + 1 < len(parts):
                    module = parts[idx + 1]
                    if module.startswith("evidec."):
                        dependencies.add(module)

    return dependencies


class TestNoCircularDependencies:
    """循環依存がないことを検証する。"""

    def test_experiment_does_not_depend_on_decision_or_report(self):
        """experiment モジュールは decision や report に依存しない。"""
        experiment_file = Path("evidec/experiment/experiment.py")
        deps = _get_module_dependencies(experiment_file)

        forbidden = {"evidec.decision", "evidec.report"}
        for dep in deps:
            assert not any(
                dep.startswith(f) for f in forbidden
            ), f"experiment.py は {forbidden} に依存すべきではない。実際: {dep}"

    def test_decision_does_not_depend_on_report_schema(self):
        """decision モジュールは report.schema に依存しない。"""
        decision_file = Path("evidec/decision/rule.py")
        deps = _get_module_dependencies(decision_file)

        forbidden = {"evidec.report.schema"}
        for dep in deps:
            assert dep not in forbidden, (
                f"decision/rule.py は {forbidden} に依存すべきではない。実際: {dep}"
            )

    def test_report_formatters_has_no_evidec_dependencies(self):
        """report/formatters.py は他の evidec モジュールに依存しない。"""
        formatters_file = Path("evidec/report/formatters.py")
        deps = _get_module_dependencies(formatters_file)

        assert (
            len(deps) == 0
        ), f"report/formatters.py は他の evidec モジュールに依存すべきではない。実際: {deps}"

