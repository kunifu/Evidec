"""Evidec: エビデンスベースの A/B テスト支援ライブラリ。"""

from evidec.core import (
    Decision,
    DecisionRule,
    EvidenceReport,
    Experiment,
    NonInferiorityRule,
    StatResult,
)

__all__ = [
    "__version__",
    "Decision",
    "DecisionRule",
    "NonInferiorityRule",
    "EvidenceReport",
    "Experiment",
    "StatResult",
]
__version__ = "0.1.0"
