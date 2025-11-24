"""フォーマット関連の共通ユーティリティ。

report/decision など複数ドメインから参照される軽量関数を配置する。
"""

from __future__ import annotations

__all__ = ["_fmt_p", "_fmt_numeric", "_fmt_ci"]


def _fmt_p(p_value: float) -> str:
    """p値を表示用文字列にフォーマットする。"""

    return "<0.0001" if p_value < 0.0001 else f"{p_value:.4f}"


def _fmt_numeric(value: float, as_percent: bool) -> str:
    """数値をパーセントまたは小数点表記でフォーマットする。"""

    if as_percent:
        return f"{value:+.1%}"
    return f"{value:+.3f}"


def _fmt_ci(ci_low: float, ci_high: float, as_percent: bool) -> str:
    """信頼区間をフォーマットする。"""

    return f"[{_fmt_numeric(ci_low, as_percent)}, {_fmt_numeric(ci_high, as_percent)}]"
