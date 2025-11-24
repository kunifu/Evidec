"""報告用フォーマッタの互換モジュール。

内部共有ユーティリティ ``evidec.utils.formatting`` に実体を移し、
既存の import パスとの後方互換だけを提供する。
"""

from __future__ import annotations

from evidec.utils.formatting import _fmt_ci, _fmt_numeric, _fmt_p

__all__ = ["_fmt_p", "_fmt_numeric", "_fmt_ci"]
