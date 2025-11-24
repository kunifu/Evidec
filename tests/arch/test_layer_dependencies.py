"""ドメイン間依存の向きを検証する。"""

from __future__ import annotations

from pathlib import Path

from tests.arch.helpers import get_evidec_imports
from tests.arch.layers import ALLOWED_DOMAIN_DEPS, domain_of_module, domain_of_path


class TestLayeredDependencies:
    def test_許可された依存方向のみ(self) -> None:
        root = Path("evidec")
        violations: list[tuple[str, str, str]] = []  # (file, domain, imported)

        for path in root.rglob("*.py"):
            domain = domain_of_path(path)
            allowed = ALLOWED_DOMAIN_DEPS.get(domain, {domain}) | {domain}

            for imp in get_evidec_imports(path):
                dep_domain = domain_of_module(imp)
                if dep_domain not in allowed:
                    violations.append((str(path), domain, imp))

        assert not violations, (
            "ドメイン間の依存はレイヤ規則違反です（utils への横断だけ許可）: "
            f"{violations}"
        )
