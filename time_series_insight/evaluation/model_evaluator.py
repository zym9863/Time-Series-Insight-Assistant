"""
模型评估器

实现模型拟合、残差分析和白噪声检验功能。
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.stats.diagnostic import acorr_ljungbox, het_breuschpagan
from statsmodels.tsa.stattools import acf, pacf
from statsmodels.stats.stattools import jarque_bera
from scipy import stats
import warnings


class ModelEvaluator:
    """ARIMA模型评估器"""
    
    def __init__(self):
        """初始化模型评估器"""
        self.fitted_model = None
        self.residuals = None
        self.evaluation_results: Dict[str, Any] = {}
        
    def fit_model(self, data: pd.Series, order: Tuple[int, int, int]) -> Dict[str, Any]:
        """
        拟合ARIMA模型
        
        Args:
            data: 时间序列数据
            order: ARIMA模型阶数 (p, d, q)
            
        Returns:
            拟合结果字典
        """
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                # 拟合模型
                model = ARIMA(data, order=order)
                self.fitted_model = model.fit(method='lbfgs', maxiter=1000)
                
                # 获取残差
                self.residuals = self.fitted_model.resid
                
                # 计算拟合统计量
                fitted_values = self.fitted_model.fittedvalues
                
                # 计算拟合优度指标
                ss_res = np.sum(self.residuals ** 2)
                ss_tot = np.sum((data - data.mean()) ** 2)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                
                # 调整R平方
                n = len(data)
                p = sum(order) - order[1]  # 参数个数（不包括差分）
                adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - p - 1) if n > p + 1 else r_squared
                
                result = {
                    "success": True,
                    "order": order,
                    "aic": float(self.fitted_model.aic),
                    "bic": float(self.fitted_model.bic),
                    "hqic": float(self.fitted_model.hqic),
                    "loglikelihood": float(self.fitted_model.llf),
                    "r_squared": float(r_squared),
                    "adj_r_squared": float(adj_r_squared),
                    "sigma2": float(self.fitted_model.sigma2),
                    "n_observations": n,
                    "n_parameters": p,
                    "fitted_values": fitted_values,
                    "residuals": self.residuals,
                    "model_summary": str(self.fitted_model.summary())
                }
                
                return result
                
        except Exception as e:
            return {
                "success": False,
                "order": order,
                "error": str(e)
            }
    
    def analyze_residuals(self) -> Dict[str, Any]:
        """
        分析模型残差
        
        Returns:
            残差分析结果字典
        """
        if self.residuals is None:
            return {"error": "请先拟合模型"}
        
        try:
            residuals = self.residuals.dropna()
            
            # 基本统计量
            basic_stats = {
                "mean": float(residuals.mean()),
                "std": float(residuals.std()),
                "min": float(residuals.min()),
                "max": float(residuals.max()),
                "skewness": float(stats.skew(residuals)),
                "kurtosis": float(stats.kurtosis(residuals)),
                "n_observations": len(residuals)
            }
            
            # 正态性检验
            normality_tests = self._test_normality(residuals)
            
            # 自相关检验
            autocorr_tests = self._test_autocorrelation(residuals)
            
            # 异方差检验
            heteroskedasticity_tests = self._test_heteroskedasticity(residuals)
            
            # 残差ACF/PACF
            residual_acf_pacf = self._calculate_residual_acf_pacf(residuals)
            
            result = {
                "basic_statistics": basic_stats,
                "normality_tests": normality_tests,
                "autocorrelation_tests": autocorr_tests,
                "heteroskedasticity_tests": heteroskedasticity_tests,
                "acf_pacf": residual_acf_pacf,
                "overall_assessment": self._assess_residuals(basic_stats, normality_tests, autocorr_tests)
            }
            
            return result
            
        except Exception as e:
            return {"error": f"残差分析失败: {str(e)}"}
    
    def _test_normality(self, residuals: pd.Series) -> Dict[str, Any]:
        """正态性检验"""
        tests = {}
        
        # Jarque-Bera检验
        try:
            jb_stat, jb_pvalue = jarque_bera(residuals)
            tests["jarque_bera"] = {
                "statistic": float(jb_stat),
                "p_value": float(jb_pvalue),
                "is_normal": jb_pvalue > 0.05,
                "interpretation": "残差服从正态分布" if jb_pvalue > 0.05 else "残差不服从正态分布"
            }
        except:
            tests["jarque_bera"] = {"error": "无法进行Jarque-Bera检验"}
        
        # Shapiro-Wilk检验（适用于小样本）
        if len(residuals) <= 5000:
            try:
                sw_stat, sw_pvalue = stats.shapiro(residuals)
                tests["shapiro_wilk"] = {
                    "statistic": float(sw_stat),
                    "p_value": float(sw_pvalue),
                    "is_normal": sw_pvalue > 0.05,
                    "interpretation": "残差服从正态分布" if sw_pvalue > 0.05 else "残差不服从正态分布"
                }
            except:
                tests["shapiro_wilk"] = {"error": "无法进行Shapiro-Wilk检验"}
        
        return tests
    
    def _test_autocorrelation(self, residuals: pd.Series) -> Dict[str, Any]:
        """自相关检验"""
        tests = {}
        
        # Ljung-Box检验
        try:
            lags = min(10, len(residuals) // 4)
            lb_result = acorr_ljungbox(residuals, lags=lags, return_df=True)
            
            # 取最后一个滞后的结果作为总体检验
            last_lag = lb_result.index[-1]
            lb_stat = lb_result.loc[last_lag, 'lb_stat']
            lb_pvalue = lb_result.loc[last_lag, 'lb_pvalue']
            
            tests["ljung_box"] = {
                "statistic": float(lb_stat),
                "p_value": float(lb_pvalue),
                "lags_tested": int(last_lag),
                "is_white_noise": lb_pvalue > 0.05,
                "interpretation": "残差为白噪声" if lb_pvalue > 0.05 else "残差存在自相关",
                "detailed_results": lb_result.to_dict()
            }
        except Exception as e:
            tests["ljung_box"] = {"error": f"无法进行Ljung-Box检验: {str(e)}"}
        
        return tests
    
    def _test_heteroskedasticity(self, residuals: pd.Series) -> Dict[str, Any]:
        """异方差检验"""
        tests = {}
        
        # 简单的异方差检验：残差平方与时间的相关性
        try:
            squared_residuals = residuals ** 2
            time_index = np.arange(len(residuals))
            
            # 计算相关系数
            correlation, p_value = stats.pearsonr(time_index, squared_residuals)
            
            tests["time_correlation"] = {
                "correlation": float(correlation),
                "p_value": float(p_value),
                "is_homoskedastic": abs(correlation) < 0.1 and p_value > 0.05,
                "interpretation": "方差齐性" if abs(correlation) < 0.1 and p_value > 0.05 else "可能存在异方差"
            }
        except:
            tests["time_correlation"] = {"error": "无法进行时间相关性检验"}
        
        return tests
    
    def _calculate_residual_acf_pacf(self, residuals: pd.Series, lags: int = 20) -> Dict[str, Any]:
        """计算残差的ACF和PACF"""
        try:
            # 计算ACF
            acf_values = acf(residuals, nlags=lags, alpha=0.05, fft=False)
            if isinstance(acf_values, tuple):
                acf_vals, acf_confint = acf_values
            else:
                acf_vals = acf_values
                acf_confint = None
            
            # 计算PACF
            pacf_values = pacf(residuals, nlags=lags, alpha=0.05)
            if isinstance(pacf_values, tuple):
                pacf_vals, pacf_confint = pacf_values
            else:
                pacf_vals = pacf_values
                pacf_confint = None
            
            # 检查是否有显著的自相关
            if acf_confint is not None:
                significant_acf = np.any((acf_vals[1:] < acf_confint[1:, 0]) | 
                                       (acf_vals[1:] > acf_confint[1:, 1]))
            else:
                # 使用简单阈值
                threshold = 1.96 / np.sqrt(len(residuals))
                significant_acf = np.any(np.abs(acf_vals[1:]) > threshold)
            
            if pacf_confint is not None:
                significant_pacf = np.any((pacf_vals[1:] < pacf_confint[1:, 0]) | 
                                        (pacf_vals[1:] > pacf_confint[1:, 1]))
            else:
                threshold = 1.96 / np.sqrt(len(residuals))
                significant_pacf = np.any(np.abs(pacf_vals[1:]) > threshold)
            
            return {
                "acf_values": acf_vals.tolist(),
                "pacf_values": pacf_vals.tolist(),
                "acf_confint": acf_confint.tolist() if acf_confint is not None else None,
                "pacf_confint": pacf_confint.tolist() if pacf_confint is not None else None,
                "significant_autocorrelation": significant_acf,
                "significant_partial_autocorrelation": significant_pacf,
                "interpretation": "残差无显著自相关" if not (significant_acf or significant_pacf) else "残差存在显著自相关"
            }
            
        except Exception as e:
            return {"error": f"无法计算残差ACF/PACF: {str(e)}"}
    
    def _assess_residuals(self, basic_stats: Dict, normality_tests: Dict, autocorr_tests: Dict) -> Dict[str, Any]:
        """综合评估残差质量"""
        issues = []
        score = 100
        
        # 检查均值是否接近0
        if abs(basic_stats["mean"]) > 0.1 * basic_stats["std"]:
            issues.append("残差均值偏离0")
            score -= 10
        
        # 检查正态性
        if "jarque_bera" in normality_tests and not normality_tests["jarque_bera"].get("is_normal", True):
            issues.append("残差不服从正态分布")
            score -= 15
        
        # 检查自相关
        if "ljung_box" in autocorr_tests and not autocorr_tests["ljung_box"].get("is_white_noise", True):
            issues.append("残差存在自相关")
            score -= 20
        
        # 检查偏度和峰度
        if abs(basic_stats["skewness"]) > 1:
            issues.append("残差偏度过大")
            score -= 10
        
        if abs(basic_stats["kurtosis"]) > 3:
            issues.append("残差峰度异常")
            score -= 10
        
        # 评估等级
        if score >= 90:
            grade = "优秀"
            recommendation = "模型拟合良好，残差符合白噪声假设"
        elif score >= 75:
            grade = "良好"
            recommendation = "模型拟合较好，但存在轻微问题"
        elif score >= 60:
            grade = "一般"
            recommendation = "模型拟合一般，建议考虑调整模型"
        else:
            grade = "较差"
            recommendation = "模型拟合不佳，建议重新选择模型"
        
        return {
            "score": score,
            "grade": grade,
            "issues": issues,
            "recommendation": recommendation,
            "detailed_assessment": {
                "mean_centered": abs(basic_stats["mean"]) <= 0.1 * basic_stats["std"],
                "normal_distribution": normality_tests.get("jarque_bera", {}).get("is_normal", False),
                "no_autocorrelation": autocorr_tests.get("ljung_box", {}).get("is_white_noise", False),
                "reasonable_skewness": abs(basic_stats["skewness"]) <= 1,
                "reasonable_kurtosis": abs(basic_stats["kurtosis"]) <= 3
            }
        }
    
    def generate_evaluation_report(self, data: pd.Series, order: Tuple[int, int, int]) -> Dict[str, Any]:
        """
        生成完整的模型评估报告
        
        Args:
            data: 原始时间序列数据
            order: ARIMA模型阶数
            
        Returns:
            完整的评估报告
        """
        # 拟合模型
        fit_result = self.fit_model(data, order)
        
        if not fit_result.get("success", False):
            return {
                "success": False,
                "error": fit_result.get("error", "模型拟合失败")
            }
        
        # 残差分析
        residual_analysis = self.analyze_residuals()
        
        # 生成综合报告
        report = {
            "success": True,
            "model_info": {
                "order": order,
                "model_type": f"ARIMA{order}"
            },
            "fit_statistics": {
                "aic": fit_result["aic"],
                "bic": fit_result["bic"],
                "hqic": fit_result["hqic"],
                "loglikelihood": fit_result["loglikelihood"],
                "r_squared": fit_result["r_squared"],
                "adj_r_squared": fit_result["adj_r_squared"],
                "sigma2": fit_result["sigma2"]
            },
            "residual_analysis": residual_analysis,
            "model_adequacy": self._assess_model_adequacy(fit_result, residual_analysis),
            "recommendations": self._generate_recommendations(fit_result, residual_analysis)
        }
        
        self.evaluation_results = report
        return report
    
    def _assess_model_adequacy(self, fit_result: Dict, residual_analysis: Dict) -> Dict[str, Any]:
        """评估模型充分性"""
        adequacy_score = 0
        max_score = 100
        
        # AIC/BIC评分（相对评分，需要与其他模型比较）
        adequacy_score += 20  # 基础分
        
        # R平方评分
        r_squared = fit_result.get("r_squared", 0)
        if r_squared > 0.8:
            adequacy_score += 20
        elif r_squared > 0.6:
            adequacy_score += 15
        elif r_squared > 0.4:
            adequacy_score += 10
        else:
            adequacy_score += 5
        
        # 残差评分
        if "overall_assessment" in residual_analysis:
            residual_score = residual_analysis["overall_assessment"].get("score", 0)
            adequacy_score += int(residual_score * 0.6)  # 残差评分占60%
        
        adequacy_percentage = min(adequacy_score, max_score)
        
        if adequacy_percentage >= 85:
            adequacy_level = "高"
            interpretation = "模型非常适合数据"
        elif adequacy_percentage >= 70:
            adequacy_level = "中等"
            interpretation = "模型较好地拟合数据"
        elif adequacy_percentage >= 55:
            adequacy_level = "一般"
            interpretation = "模型基本拟合数据，但有改进空间"
        else:
            adequacy_level = "低"
            interpretation = "模型拟合不佳，建议重新选择"
        
        return {
            "score": adequacy_percentage,
            "level": adequacy_level,
            "interpretation": interpretation
        }
    
    def _generate_recommendations(self, fit_result: Dict, residual_analysis: Dict) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于残差分析的建议
        if "overall_assessment" in residual_analysis:
            issues = residual_analysis["overall_assessment"].get("issues", [])
            
            if "残差存在自相关" in issues:
                recommendations.append("考虑增加AR或MA项来消除残差自相关")
            
            if "残差不服从正态分布" in issues:
                recommendations.append("考虑对数据进行变换或使用其他分布假设")
            
            if "残差均值偏离0" in issues:
                recommendations.append("检查模型是否包含适当的常数项")
        
        # 基于拟合统计量的建议
        r_squared = fit_result.get("r_squared", 0)
        if r_squared < 0.5:
            recommendations.append("模型解释能力较低，考虑增加模型复杂度或寻找其他变量")
        
        # 基于信息准则的建议
        recommendations.append("可以尝试其他ARIMA阶数组合，比较AIC/BIC值选择最优模型")
        
        if not recommendations:
            recommendations.append("模型拟合良好，可以用于预测和分析")
        
        return recommendations
