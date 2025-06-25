"""
模型识别器

实现ACF/PACF计算、截尾拖尾模式识别和ARIMA模型自动推荐功能。
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, List, Any, Optional
from statsmodels.tsa.stattools import acf, pacf
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.stats.diagnostic import acorr_ljungbox
import warnings


class ModelIdentifier:
    """ARIMA模型识别器"""
    
    def __init__(self):
        """初始化模型识别器"""
        self.acf_values: Optional[np.ndarray] = None
        self.pacf_values: Optional[np.ndarray] = None
        self.acf_confint: Optional[np.ndarray] = None
        self.pacf_confint: Optional[np.ndarray] = None
        self.recommended_models: List[Dict[str, Any]] = []
        
    def calculate_acf_pacf(self, 
                          data: pd.Series, 
                          lags: int = 20,
                          alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        计算ACF和PACF
        
        Args:
            data: 时间序列数据
            lags: 滞后阶数
            alpha: 置信水平
            
        Returns:
            (acf_values, pacf_values, acf_confint, pacf_confint)
        """
        # 计算ACF
        acf_result = acf(data, nlags=lags, alpha=alpha, fft=False)
        if isinstance(acf_result, tuple):
            self.acf_values, self.acf_confint = acf_result
        else:
            self.acf_values = acf_result
            self.acf_confint = None
        
        # 计算PACF
        pacf_result = pacf(data, nlags=lags, alpha=alpha)
        if isinstance(pacf_result, tuple):
            self.pacf_values, self.pacf_confint = pacf_result
        else:
            self.pacf_values = pacf_result
            self.pacf_confint = None
        
        return self.acf_values, self.pacf_values, self.acf_confint, self.pacf_confint
    
    def _identify_cutoff_pattern(self, 
                                values: np.ndarray, 
                                confint: Optional[np.ndarray] = None,
                                significance_level: float = 0.05) -> Dict[str, Any]:
        """
        识别截尾或拖尾模式
        
        Args:
            values: ACF或PACF值
            confint: 置信区间
            significance_level: 显著性水平
            
        Returns:
            模式识别结果
        """
        if confint is not None:
            # 使用置信区间判断显著性
            lower_bound = confint[:, 0]
            upper_bound = confint[:, 1]
            significant = (values < lower_bound) | (values > upper_bound)
        else:
            # 使用简单的阈值判断（约等于1.96/sqrt(n)的近似）
            n = len(values) * 10  # 假设样本大小
            threshold = 1.96 / np.sqrt(n)
            significant = np.abs(values) > threshold
        
        # 跳过第0个滞后（总是1）
        significant = significant[1:]
        values_no_zero = values[1:]
        
        # 找到最后一个显著的滞后
        last_significant = -1
        for i in range(len(significant)):
            if significant[i]:
                last_significant = i
        
        # 判断模式
        if last_significant == -1:
            pattern_type = "白噪声"
            cutoff_lag = 0
        elif last_significant < 3:
            pattern_type = "截尾"
            cutoff_lag = last_significant + 1
        else:
            # 检查是否为拖尾（逐渐衰减）
            if last_significant >= 5:
                # 计算衰减趋势
                recent_values = np.abs(values_no_zero[max(0, last_significant-3):last_significant+1])
                if len(recent_values) > 1:
                    trend = np.polyfit(range(len(recent_values)), recent_values, 1)[0]
                    if trend < -0.01:  # 负趋势表示衰减
                        pattern_type = "拖尾"
                        cutoff_lag = last_significant + 1
                    else:
                        pattern_type = "截尾"
                        cutoff_lag = last_significant + 1
                else:
                    pattern_type = "截尾"
                    cutoff_lag = last_significant + 1
            else:
                pattern_type = "截尾"
                cutoff_lag = last_significant + 1
        
        return {
            "pattern_type": pattern_type,
            "cutoff_lag": cutoff_lag,
            "last_significant_lag": last_significant + 1 if last_significant >= 0 else 0,
            "significant_lags": np.where(significant)[0] + 1,
            "max_significant_value": float(np.max(np.abs(values_no_zero[significant]))) if np.any(significant) else 0.0
        }
    
    def identify_arima_order(self, 
                           data: pd.Series,
                           max_p: int = 5,
                           max_q: int = 5,
                           d: int = 0) -> List[Dict[str, Any]]:
        """
        基于ACF/PACF模式识别ARIMA模型阶数
        
        Args:
            data: 时间序列数据
            max_p: 最大AR阶数
            max_q: 最大MA阶数
            d: 差分阶数
            
        Returns:
            推荐的模型列表
        """
        # 计算ACF和PACF
        lags = min(len(data) // 4, 20)  # 动态确定滞后数
        self.calculate_acf_pacf(data, lags=lags)
        
        # 分析ACF和PACF模式
        acf_pattern = self._identify_cutoff_pattern(self.acf_values, self.acf_confint)
        pacf_pattern = self._identify_cutoff_pattern(self.pacf_values, self.pacf_confint)
        
        models = []
        
        # 基于经典的Box-Jenkins方法推荐模型
        
        # 1. 如果ACF截尾，PACF拖尾 -> MA模型
        if acf_pattern["pattern_type"] == "截尾" and pacf_pattern["pattern_type"] == "拖尾":
            q = min(acf_pattern["cutoff_lag"], max_q)
            if q > 0:
                models.append({
                    "order": (0, d, q),
                    "type": f"MA({q})",
                    "reasoning": f"ACF在滞后{q}处截尾，PACF拖尾",
                    "confidence": 0.8
                })
        
        # 2. 如果PACF截尾，ACF拖尾 -> AR模型
        elif pacf_pattern["pattern_type"] == "截尾" and acf_pattern["pattern_type"] == "拖尾":
            p = min(pacf_pattern["cutoff_lag"], max_p)
            if p > 0:
                models.append({
                    "order": (p, d, 0),
                    "type": f"AR({p})",
                    "reasoning": f"PACF在滞后{p}处截尾，ACF拖尾",
                    "confidence": 0.8
                })
        
        # 3. 如果ACF和PACF都拖尾 -> ARMA模型
        elif acf_pattern["pattern_type"] == "拖尾" and pacf_pattern["pattern_type"] == "拖尾":
            # 尝试几个小的p和q组合
            for p in range(1, min(4, max_p + 1)):
                for q in range(1, min(4, max_q + 1)):
                    models.append({
                        "order": (p, d, q),
                        "type": f"ARMA({p},{q})",
                        "reasoning": "ACF和PACF都呈拖尾模式",
                        "confidence": 0.6
                    })
        
        # 4. 如果都截尾或者模式不明确，尝试低阶模型
        else:
            # 基于显著滞后推荐
            acf_lags = acf_pattern["significant_lags"]
            pacf_lags = pacf_pattern["significant_lags"]
            
            if len(pacf_lags) > 0:
                p = min(max(pacf_lags), max_p)
                models.append({
                    "order": (p, d, 0),
                    "type": f"AR({p})",
                    "reasoning": f"基于PACF显著滞后推荐",
                    "confidence": 0.5
                })
            
            if len(acf_lags) > 0:
                q = min(max(acf_lags), max_q)
                models.append({
                    "order": (0, d, q),
                    "type": f"MA({q})",
                    "reasoning": f"基于ACF显著滞后推荐",
                    "confidence": 0.5
                })
        
        # 5. 总是包含一些常用的低阶模型作为备选
        common_models = [
            (1, d, 0), (0, d, 1), (1, d, 1),
            (2, d, 0), (0, d, 2), (2, d, 1), (1, d, 2)
        ]
        
        for order in common_models:
            if order not in [m["order"] for m in models]:
                models.append({
                    "order": order,
                    "type": f"ARIMA{order}",
                    "reasoning": "常用低阶模型",
                    "confidence": 0.3
                })
        
        # 按置信度排序
        models.sort(key=lambda x: x["confidence"], reverse=True)
        
        self.recommended_models = models[:10]  # 保留前10个推荐
        return self.recommended_models
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        if self.acf_values is None or self.pacf_values is None:
            return {"error": "请先进行ACF/PACF分析"}
        
        acf_pattern = self._identify_cutoff_pattern(self.acf_values, self.acf_confint)
        pacf_pattern = self._identify_cutoff_pattern(self.pacf_values, self.pacf_confint)
        
        return {
            "acf_analysis": acf_pattern,
            "pacf_analysis": pacf_pattern,
            "recommended_models": self.recommended_models,
            "interpretation": self._generate_interpretation(acf_pattern, pacf_pattern)
        }
    
    def _generate_interpretation(self, acf_pattern: Dict, pacf_pattern: Dict) -> str:
        """生成分析解释"""
        interpretation = []
        
        interpretation.append(f"ACF分析：{acf_pattern['pattern_type']}")
        if acf_pattern['pattern_type'] == '截尾':
            interpretation.append(f"  - ACF在滞后{acf_pattern['cutoff_lag']}处截尾")
        elif acf_pattern['pattern_type'] == '拖尾':
            interpretation.append(f"  - ACF呈拖尾模式，逐渐衰减")
        
        interpretation.append(f"PACF分析：{pacf_pattern['pattern_type']}")
        if pacf_pattern['pattern_type'] == '截尾':
            interpretation.append(f"  - PACF在滞后{pacf_pattern['cutoff_lag']}处截尾")
        elif pacf_pattern['pattern_type'] == '拖尾':
            interpretation.append(f"  - PACF呈拖尾模式，逐渐衰减")
        
        # 模型推荐解释
        if self.recommended_models:
            top_model = self.recommended_models[0]
            interpretation.append(f"推荐模型：{top_model['type']}")
            interpretation.append(f"推荐理由：{top_model['reasoning']}")
        
        return "\n".join(interpretation)
