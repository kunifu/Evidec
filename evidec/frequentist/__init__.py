"""頻度論ベースの検定実装。"""

from evidec.frequentist.ttest import ttest_means
from evidec.frequentist.ztest import ztest_proportions

__all__ = ["ztest_proportions", "ttest_means"]
