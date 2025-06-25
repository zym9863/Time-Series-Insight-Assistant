"""
时间序列洞察助手 (Time Series Insight Assistant)

一个智能的时间序列分析库，提供自动模型识别、参数估计和可视化诊断功能。

主要功能：
- 自动平稳性检验和差分
- ACF/PACF分析和可视化
- 自动ARIMA模型识别
- 参数估计（矩估计法和最大似然估计）
- 模型评估和诊断
"""

__version__ = "0.1.0"
__author__ = "Time Series Insight Assistant"
__email__ = "contact@example.com"

from .core.data_processor import TimeSeriesProcessor
from .analysis.model_identifier import ModelIdentifier
from .estimation.parameter_estimator import ParameterEstimator
from .evaluation.model_evaluator import ModelEvaluator
from .visualization.plotter import TimeSeriesPlotter
from .api import TimeSeriesInsight, analyze_time_series

__all__ = [
    "TimeSeriesProcessor",
    "ModelIdentifier",
    "ParameterEstimator",
    "ModelEvaluator",
    "TimeSeriesPlotter",
    "TimeSeriesInsight",
    "analyze_time_series",
]
