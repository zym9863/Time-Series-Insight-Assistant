"""
参数估计器

实现矩估计法和最大似然估计的参数计算功能。
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import acf, pacf
from scipy.optimize import minimize
import warnings


class ParameterEstimator:
    """ARIMA模型参数估计器"""
    
    def __init__(self):
        """初始化参数估计器"""
        self.moment_estimates: Dict[str, Any] = {}
        self.mle_estimates: Dict[str, Any] = {}
        self.comparison_results: Dict[str, Any] = {}
        
    def estimate_ar_moments(self, data: pd.Series, p: int) -> Dict[str, Any]:
        """
        使用矩估计法估计AR模型参数
        
        Args:
            data: 时间序列数据
            p: AR阶数
            
        Returns:
            估计结果字典
        """
        if p <= 0:
            return {"error": "AR阶数必须大于0"}
        
        try:
            # 计算样本自协方差
            n = len(data)
            mean = data.mean()
            centered_data = data - mean
            
            # 计算自协方差函数
            gamma = np.zeros(p + 1)
            for k in range(p + 1):
                if k == 0:
                    gamma[k] = np.var(centered_data, ddof=1)
                else:
                    gamma[k] = np.mean(centered_data[:-k] * centered_data[k:])
            
            # 构建Yule-Walker方程组
            # gamma[0] = phi[0]*gamma[0] + phi[1]*gamma[1] + ... + phi[p-1]*gamma[p-1] + sigma^2
            # gamma[1] = phi[0]*gamma[1] + phi[1]*gamma[0] + ... + phi[p-1]*gamma[p-2]
            # ...
            
            if p == 1:
                # AR(1)的简单情况
                phi1 = gamma[1] / gamma[0] if gamma[0] != 0 else 0
                sigma2 = gamma[0] * (1 - phi1**2)
                phi = [phi1]
            else:
                # 一般情况：解Yule-Walker方程
                R = np.zeros((p, p))
                r = np.zeros(p)
                
                for i in range(p):
                    r[i] = gamma[i + 1]
                    for j in range(p):
                        R[i, j] = gamma[abs(i - j)]
                
                # 解线性方程组 R * phi = r
                try:
                    phi = np.linalg.solve(R, r)
                    # 计算噪声方差
                    sigma2 = gamma[0] - np.sum(phi * r)
                except np.linalg.LinAlgError:
                    # 如果矩阵奇异，使用最小二乘解
                    phi = np.linalg.lstsq(R, r, rcond=None)[0]
                    sigma2 = gamma[0] - np.sum(phi * r)
            
            # 确保噪声方差为正
            sigma2 = max(sigma2, 0.001)
            
            return {
                "method": "矩估计法",
                "order": (p, 0, 0),
                "ar_params": phi.tolist(),
                "ma_params": [],
                "sigma2": float(sigma2),
                "const": float(mean),
                "success": True,
                "details": {
                    "autocovariances": gamma.tolist(),
                    "yule_walker_matrix": R.tolist() if p > 1 else [[gamma[0]]],
                    "yule_walker_vector": r.tolist() if p > 1 else [gamma[1]]
                }
            }
            
        except Exception as e:
            return {
                "method": "矩估计法",
                "order": (p, 0, 0),
                "success": False,
                "error": str(e)
            }
    
    def estimate_ma_moments(self, data: pd.Series, q: int) -> Dict[str, Any]:
        """
        使用矩估计法估计MA模型参数
        
        Args:
            data: 时间序列数据
            q: MA阶数
            
        Returns:
            估计结果字典
        """
        if q <= 0:
            return {"error": "MA阶数必须大于0"}
        
        try:
            # MA模型的矩估计比较复杂，这里使用简化的方法
            # 基于ACF的性质进行估计
            
            mean = data.mean()
            var = data.var(ddof=1)
            
            # 计算样本ACF
            acf_values = acf(data, nlags=q, fft=False)
            
            if q == 1:
                # MA(1)的简单情况
                # rho[1] = theta / (1 + theta^2)
                # 解二次方程
                rho1 = acf_values[1]
                if abs(rho1) < 0.5:  # 确保有解
                    # theta^2 - (1/rho1)*theta + 1 = 0
                    if rho1 != 0:
                        discriminant = (1/rho1)**2 - 4
                        if discriminant >= 0:
                            theta1 = ((1/rho1) - np.sqrt(discriminant)) / 2
                            theta2 = ((1/rho1) + np.sqrt(discriminant)) / 2
                            # 选择绝对值较小的解（可逆性）
                            theta = theta1 if abs(theta1) < abs(theta2) else theta2
                        else:
                            theta = 0.5 * np.sign(rho1)  # 近似解
                    else:
                        theta = 0
                else:
                    theta = 0.5 * np.sign(rho1)  # 边界情况
                
                sigma2 = var / (1 + theta**2)
                ma_params = [theta]
            else:
                # 高阶MA模型使用数值方法
                def ma_objective(theta):
                    # 计算理论ACF并与样本ACF比较
                    theoretical_acf = self._ma_theoretical_acf(theta, q)
                    sample_acf = acf_values[1:q+1]
                    return np.sum((theoretical_acf - sample_acf)**2)
                
                # 初始猜测
                initial_theta = np.random.uniform(-0.5, 0.5, q)
                
                # 优化
                result = minimize(ma_objective, initial_theta, method='L-BFGS-B',
                                bounds=[(-0.99, 0.99)] * q)
                
                if result.success:
                    ma_params = result.x.tolist()
                    # 计算噪声方差
                    sigma2 = var / (1 + np.sum(np.array(ma_params)**2))
                else:
                    # 如果优化失败，使用简单估计
                    ma_params = [0.1] * q
                    sigma2 = var * 0.8
            
            return {
                "method": "矩估计法",
                "order": (0, 0, q),
                "ar_params": [],
                "ma_params": ma_params,
                "sigma2": float(max(sigma2, 0.001)),
                "const": float(mean),
                "success": True,
                "details": {
                    "sample_acf": acf_values.tolist(),
                    "estimated_variance": float(var)
                }
            }
            
        except Exception as e:
            return {
                "method": "矩估计法",
                "order": (0, 0, q),
                "success": False,
                "error": str(e)
            }
    
    def _ma_theoretical_acf(self, theta: np.ndarray, q: int) -> np.ndarray:
        """计算MA模型的理论ACF"""
        acf_values = np.zeros(q)
        for k in range(1, q + 1):
            if k <= q:
                numerator = 0
                for j in range(q - k + 1):
                    numerator += theta[j] * theta[j + k - 1]
                denominator = 1 + np.sum(theta**2)
                acf_values[k - 1] = numerator / denominator
            else:
                acf_values[k - 1] = 0
        return acf_values
    
    def estimate_mle(self, data: pd.Series, order: Tuple[int, int, int]) -> Dict[str, Any]:
        """
        使用最大似然估计法估计ARIMA模型参数
        
        Args:
            data: 时间序列数据
            order: ARIMA模型阶数 (p, d, q)
            
        Returns:
            估计结果字典
        """
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                # 拟合ARIMA模型
                model = ARIMA(data, order=order)
                fitted_model = model.fit(method='lbfgs', maxiter=1000)
                
                # 提取参数
                params = fitted_model.params
                param_names = fitted_model.param_names
                
                # 分离AR、MA参数
                ar_params = []
                ma_params = []
                const = 0
                sigma2 = fitted_model.sigma2
                
                for i, name in enumerate(param_names):
                    if 'ar.L' in name:
                        ar_params.append(float(params[i]))
                    elif 'ma.L' in name:
                        ma_params.append(float(params[i]))
                    elif 'const' in name or 'intercept' in name:
                        const = float(params[i])
                
                # 计算标准误
                try:
                    std_errors = fitted_model.bse
                    param_std_errors = {}
                    for i, name in enumerate(param_names):
                        param_std_errors[name] = float(std_errors[i])
                except:
                    param_std_errors = {}
                
                return {
                    "method": "最大似然估计",
                    "order": order,
                    "ar_params": ar_params,
                    "ma_params": ma_params,
                    "sigma2": float(sigma2),
                    "const": float(const),
                    "success": True,
                    "loglikelihood": float(fitted_model.llf),
                    "aic": float(fitted_model.aic),
                    "bic": float(fitted_model.bic),
                    "std_errors": param_std_errors,
                    "fitted_model": fitted_model,
                    "details": {
                        "convergence": fitted_model.mle_retvals['converged'] if hasattr(fitted_model, 'mle_retvals') else True,
                        "iterations": fitted_model.mle_retvals.get('iterations', 'N/A') if hasattr(fitted_model, 'mle_retvals') else 'N/A',
                        "param_names": param_names
                    }
                }
                
        except Exception as e:
            return {
                "method": "最大似然估计",
                "order": order,
                "success": False,
                "error": str(e)
            }
    
    def estimate_parameters(self, 
                          data: pd.Series, 
                          order: Tuple[int, int, int],
                          methods: List[str] = ['moments', 'mle']) -> Dict[str, Any]:
        """
        使用多种方法估计参数
        
        Args:
            data: 时间序列数据
            order: ARIMA模型阶数 (p, d, q)
            methods: 估计方法列表
            
        Returns:
            所有方法的估计结果
        """
        p, d, q = order
        results = {}
        
        # 如果需要差分，先进行差分
        if d > 0:
            diff_data = data.copy()
            for _ in range(d):
                diff_data = diff_data.diff().dropna()
        else:
            diff_data = data.copy()
        
        # 矩估计法
        if 'moments' in methods:
            if p > 0 and q == 0:
                # AR模型
                results['moments'] = self.estimate_ar_moments(diff_data, p)
            elif p == 0 and q > 0:
                # MA模型
                results['moments'] = self.estimate_ma_moments(diff_data, q)
            elif p > 0 and q > 0:
                # ARMA模型 - 矩估计较复杂，这里给出提示
                results['moments'] = {
                    "method": "矩估计法",
                    "order": order,
                    "success": False,
                    "error": "ARMA模型的矩估计较为复杂，建议使用最大似然估计"
                }
            else:
                results['moments'] = {
                    "method": "矩估计法",
                    "order": order,
                    "success": False,
                    "error": "无效的模型阶数"
                }
        
        # 最大似然估计
        if 'mle' in methods:
            results['mle'] = self.estimate_mle(data, order)
        
        # 保存结果
        self.moment_estimates = results.get('moments', {})
        self.mle_estimates = results.get('mle', {})
        
        return results
    
    def compare_estimates(self) -> Dict[str, Any]:
        """比较不同估计方法的结果"""
        if not self.moment_estimates or not self.mle_estimates:
            return {"error": "需要先进行参数估计"}
        
        comparison = {
            "methods_compared": ["矩估计法", "最大似然估计"],
            "parameter_comparison": {},
            "summary": {}
        }
        
        # 比较AR参数
        if (self.moment_estimates.get('success') and self.mle_estimates.get('success')):
            moment_ar = self.moment_estimates.get('ar_params', [])
            mle_ar = self.mle_estimates.get('ar_params', [])
            
            if len(moment_ar) == len(mle_ar) and len(moment_ar) > 0:
                ar_diff = [abs(m - ml) for m, ml in zip(moment_ar, mle_ar)]
                comparison["parameter_comparison"]["ar_params"] = {
                    "moments": moment_ar,
                    "mle": mle_ar,
                    "absolute_differences": ar_diff,
                    "max_difference": max(ar_diff) if ar_diff else 0
                }
            
            # 比较MA参数
            moment_ma = self.moment_estimates.get('ma_params', [])
            mle_ma = self.mle_estimates.get('ma_params', [])
            
            if len(moment_ma) == len(mle_ma) and len(moment_ma) > 0:
                ma_diff = [abs(m - ml) for m, ml in zip(moment_ma, mle_ma)]
                comparison["parameter_comparison"]["ma_params"] = {
                    "moments": moment_ma,
                    "mle": mle_ma,
                    "absolute_differences": ma_diff,
                    "max_difference": max(ma_diff) if ma_diff else 0
                }
            
            # 比较噪声方差
            moment_sigma2 = self.moment_estimates.get('sigma2', 0)
            mle_sigma2 = self.mle_estimates.get('sigma2', 0)
            
            comparison["parameter_comparison"]["sigma2"] = {
                "moments": moment_sigma2,
                "mle": mle_sigma2,
                "absolute_difference": abs(moment_sigma2 - mle_sigma2),
                "relative_difference": abs(moment_sigma2 - mle_sigma2) / max(moment_sigma2, mle_sigma2) if max(moment_sigma2, mle_sigma2) > 0 else 0
            }
        
        # 生成总结
        if self.mle_estimates.get('success'):
            comparison["summary"]["recommended_method"] = "最大似然估计"
            comparison["summary"]["reason"] = "MLE通常提供更准确和稳定的估计"
            if 'aic' in self.mle_estimates:
                comparison["summary"]["model_selection_criteria"] = {
                    "AIC": self.mle_estimates['aic'],
                    "BIC": self.mle_estimates['bic'],
                    "Log-likelihood": self.mle_estimates['loglikelihood']
                }
        
        self.comparison_results = comparison
        return comparison
