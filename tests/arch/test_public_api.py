"""Public API の最小性と Facade ポリシーを検証する。"""

from __future__ import annotations

from pathlib import Path

from tests.arch.helpers import get_dunder_all, get_evidec_imports

EXPECTED_PUBLIC_API = {
    "Experiment",
    "DecisionRule",
    "Decision",
    "StatResult",
    "EvidenceReport",
}
ALLOWED_ROOT_ONLY = {"__version__"}


class TestPublicAPI:
    def test_PublicAPIがFacade集合と一致する(self) -> None:
        core_exports = set(get_dunder_all(Path("evidec/core.py")))
        root_exports = set(get_dunder_all(Path("evidec/__init__.py")))

        assert (
            core_exports == EXPECTED_PUBLIC_API
        ), f"evidec/core.py の公開シンボルが想定外: {core_exports}"
        assert (
            root_exports == EXPECTED_PUBLIC_API | ALLOWED_ROOT_ONLY
        ), f"evidec/__init__.py の公開シンボルが想定外: {root_exports}"

    def test_ルートはcoreのみを再輸出する(self) -> None:
        imports = get_evidec_imports(Path("evidec/__init__.py"))
        assert imports == {
            "evidec.core"
        }, f"Facade 経由でのみ公開する想定。実際の import: {imports}"
