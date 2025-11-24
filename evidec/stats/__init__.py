"""evidec で利用する統計検定実装モジュール。"""

from evidec.stats.ttest import ttest_means
from evidec.stats.ztest import ztest_proportions

__all__ = ["ztest_proportions", "ttest_means"]
