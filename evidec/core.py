"""Public API Facade for evidec.

このモジュールは evidec の公開 API を提供します。
内部実装の詳細は隠蔽され、安定した API を保証します。
"""

from evidec.decision.rule import Decision, DecisionRule
from evidec.experiment.experiment import Experiment
from evidec.experiment.result import StatResult
from evidec.report.schema import EvidenceReport

__all__ = ["Experiment", "DecisionRule", "Decision", "StatResult", "EvidenceReport"]

