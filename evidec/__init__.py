"""Evidec: エビデンスベースの A/B テスト支援ライブラリ。"""

from evidec.bayes import (
    BayesDecisionRule,
    BayesResult,
    fit_beta_binomial,
    fit_beta_binomial_from_arrays,
    fit_beta_binomial_from_prior,
)
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
    "BayesResult",
    "BayesDecisionRule",
    "fit_beta_binomial",
    "fit_beta_binomial_from_arrays",
    "fit_beta_binomial_from_prior",
]
__version__ = "0.1.0"
