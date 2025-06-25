"""
时间序列洞察助手 - 高级API接口

提供简化的API接口，方便程序化调用和集成。
"""

import pandas as pd
import numpy as np
from typing import Union, Dict, Any, Optional, Tuple, List
from pathlib import Path

from .core.data_processor import TimeSeriesProcessor
from .analysis.model_identifier import ModelIdentifier
from .estimation.parameter_estimator import ParameterEstimator
from .evaluation.model_evaluator import ModelEvaluator
from .visualization.plotter import TimeSeriesPlotter


class TimeSeriesInsight:
    """
    时间序列洞察助手主类
    
    提供完整的时间序列分析功能，包括：
    - 数据加载和预处理
    - 平稳性检验和差分
    - 模型自动识别
    - 参数估计
    - 模型评估
    - 可视化
    """
    
    def __init__(self):
        """初始化时间序列洞察助手"""
        self.processor = TimeSeriesProcessor()
        self.identifier = ModelIdentifier()
        self.estimator = ParameterEstimator()
        self.evaluator = ModelEvaluator()
        self.plotter = TimeSeriesPlotter()
        
        # 存储分析结果
        self.data = None
        self.analysis_results = {}
        
    def load_data(self, 
                  data: Union[str, Path, pd.Series, pd.DataFrame, np.ndarray],
                  date_column: Optional[str] = None,
                  value_column: Optional[str] = None,
                  date_format: Optional[str] = None) -> pd.Series:
        """
        加载时间序列数据
        
        Args:
            data: 数据源
            date_column: 日期列名
            value_column: 数值列名
            date_format: 日期格式
            
        Returns:
            加载的时间序列数据
        """
        self.data = self.processor.load_data(
            data, date_column=date_column, 
            value_column=value_column, date_format=date_format
        )
        return self.data
    
    def analyze(self, 
                auto_diff: bool = True,
                max_p: int = 5,
                max_q: int = 5,
                n_models: int = 3) -> Dict[str, Any]:
        """
        执行完整的时间序列分析
        
        Args:
            auto_diff: 是否自动差分
            max_p: 最大AR阶数
            max_q: 最大MA阶数
            n_models: 评估的模型数量
            
        Returns:
            完整的分析结果
        """
        if self.data is None:
            raise ValueError("请先加载数据")
        
        results = {}
        
        # 1. 平稳性检验
        stationarity_result = self.processor.check_stationarity()
        results['stationarity'] = stationarity_result
        
        # 2. 差分处理
        if auto_diff and not self.processor.is_stationary:
            diff_data, diff_order = self.processor.auto_difference()
            results['differencing'] = {
                'applied': True,
                'order': diff_order,
                'differenced_data': diff_data
            }
        else:
            diff_data = self.data
            diff_order = 0
            results['differencing'] = {
                'applied': False,
                'order': 0,
                'differenced_data': diff_data
            }
        
        # 3. 模型识别
        recommended_models = self.identifier.identify_arima_order(
            diff_data, max_p=max_p, max_q=max_q, d=diff_order
        )
        results['model_identification'] = {
            'recommended_models': recommended_models,
            'acf_pacf_analysis': self.identifier.get_analysis_summary()
        }
        
        # 4. 参数估计和模型评估
        evaluated_models = []
        for i, model_info in enumerate(recommended_models[:n_models]):
            order = model_info['order']
            
            # 参数估计
            estimation_results = self.estimator.estimate_parameters(self.data, order)
            
            # 模型评估
            evaluation_result = self.evaluator.generate_evaluation_report(self.data, order)
            
            if evaluation_result.get('success', False):
                model_result = {
                    'order': order,
                    'model_info': model_info,
                    'estimation': estimation_results,
                    'evaluation': evaluation_result
                }
                evaluated_models.append(model_result)
        
        results['model_evaluation'] = evaluated_models
        
        # 5. 选择最佳模型
        if evaluated_models:
            # 根据AIC选择最佳模型
            best_model = min(evaluated_models, 
                           key=lambda x: x['evaluation']['fit_statistics']['aic'])
            results['best_model'] = best_model
        
        # 保存结果
        self.analysis_results = results
        return results
    
    def quick_analysis(self, 
                      data: Union[str, Path, pd.Series, pd.DataFrame, np.ndarray],
                      **kwargs) -> Dict[str, Any]:
        """
        一键分析：加载数据并执行完整分析
        
        Args:
            data: 数据源
            **kwargs: 其他参数
            
        Returns:
            分析结果
        """
        # 提取加载数据的参数
        load_params = {k: v for k, v in kwargs.items() 
                      if k in ['date_column', 'value_column', 'date_format']}
        
        # 提取分析参数
        analyze_params = {k: v for k, v in kwargs.items() 
                         if k in ['auto_diff', 'max_p', 'max_q', 'n_models']}
        
        # 加载数据
        self.load_data(data, **load_params)
        
        # 执行分析
        return self.analyze(**analyze_params)
    
    def get_best_model(self) -> Optional[Dict[str, Any]]:
        """获取最佳模型"""
        if 'best_model' in self.analysis_results:
            return self.analysis_results['best_model']
        return None
    
    def predict(self, 
                steps: int = 10,
                alpha: float = 0.05) -> Dict[str, Any]:
        """
        使用最佳模型进行预测
        
        Args:
            steps: 预测步数
            alpha: 置信水平
            
        Returns:
            预测结果
        """
        best_model = self.get_best_model()
        if best_model is None:
            raise ValueError("没有可用的模型，请先执行分析")
        
        # 获取拟合的模型
        if 'fitted_model' in best_model['estimation'].get('mle', {}):
            fitted_model = best_model['estimation']['mle']['fitted_model']
            
            # 进行预测
            forecast_result = fitted_model.forecast(steps=steps, alpha=alpha)
            
            if isinstance(forecast_result, tuple):
                forecast, conf_int = forecast_result
            else:
                forecast = forecast_result
                conf_int = None
            
            # 创建预测索引
            if isinstance(self.data.index, pd.DatetimeIndex):
                # 尝试推断频率
                freq = self.data.index.freq
                if freq is None:
                    # 估算频率
                    time_diff = self.data.index[-1] - self.data.index[-2]
                    freq = time_diff
                
                forecast_index = pd.date_range(
                    start=self.data.index[-1] + freq,
                    periods=steps,
                    freq=freq
                )
            else:
                forecast_index = range(len(self.data), len(self.data) + steps)
            
            forecast_series = pd.Series(forecast, index=forecast_index)
            
            result = {
                'forecast': forecast_series,
                'confidence_intervals': conf_int,
                'model_order': best_model['order'],
                'forecast_steps': steps
            }
            
            return result
        else:
            raise ValueError("最佳模型没有拟合结果")
    
    def plot_analysis(self, 
                     save_dir: Optional[Union[str, Path]] = None,
                     show_plots: bool = True) -> Dict[str, Any]:
        """
        生成分析图表
        
        Args:
            save_dir: 保存目录
            show_plots: 是否显示图表
            
        Returns:
            生成的图表信息
        """
        if self.data is None:
            raise ValueError("请先加载数据")
        
        plots_info = {}
        
        # 创建保存目录
        if save_dir:
            save_dir = Path(save_dir)
            save_dir.mkdir(exist_ok=True)
        
        # 1. 原始时间序列图
        fig1 = self.plotter.plot_time_series(
            self.data, 
            title="原始时间序列",
            save_path=save_dir / "original_series.png" if save_dir else None
        )
        plots_info['original_series'] = fig1
        
        # 2. ACF/PACF图
        if 'differencing' in self.analysis_results:
            analysis_data = self.analysis_results['differencing']['differenced_data']
            fig2 = self.plotter.plot_acf_pacf(
                analysis_data,
                title="ACF和PACF分析",
                save_path=save_dir / "acf_pacf.png" if save_dir else None
            )
            plots_info['acf_pacf'] = fig2
        
        # 3. 残差诊断图
        best_model = self.get_best_model()
        if best_model and 'fitted_model' in best_model['estimation'].get('mle', {}):
            fitted_model = best_model['estimation']['mle']['fitted_model']
            residuals = fitted_model.resid
            fitted_values = fitted_model.fittedvalues
            
            fig3 = self.plotter.plot_residual_diagnostics(
                residuals, fitted_values,
                title=f"残差诊断 - ARIMA{best_model['order']}",
                save_path=save_dir / "residual_diagnostics.png" if save_dir else None
            )
            plots_info['residual_diagnostics'] = fig3
        
        # 4. 模型比较图
        if 'model_evaluation' in self.analysis_results:
            models = self.analysis_results['model_evaluation']
            if len(models) > 1:
                model_results = []
                for model in models:
                    eval_stats = model['evaluation']['fit_statistics']
                    model_results.append({
                        'order': model['order'],
                        'aic': eval_stats['aic'],
                        'bic': eval_stats['bic'],
                        'hqic': eval_stats['hqic']
                    })
                
                fig4 = self.plotter.plot_model_comparison(
                    model_results,
                    title="模型比较",
                    save_path=save_dir / "model_comparison.png" if save_dir else None
                )
                plots_info['model_comparison'] = fig4
        
        if not show_plots:
            import matplotlib.pyplot as plt
            plt.close('all')
        
        return plots_info
    
    def get_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        if not self.analysis_results:
            return {"error": "请先执行分析"}
        
        summary = {
            "data_info": {
                "length": len(self.data),
                "start": str(self.data.index[0]) if len(self.data) > 0 else None,
                "end": str(self.data.index[-1]) if len(self.data) > 0 else None,
                "mean": float(self.data.mean()),
                "std": float(self.data.std())
            }
        }
        
        # 平稳性信息
        if 'stationarity' in self.analysis_results:
            stationarity = self.analysis_results['stationarity']
            summary["stationarity"] = {
                "is_stationary": stationarity['overall']['is_stationary'],
                "interpretation": stationarity['overall']['interpretation']
            }
        
        # 差分信息
        if 'differencing' in self.analysis_results:
            diff_info = self.analysis_results['differencing']
            summary["differencing"] = {
                "applied": diff_info['applied'],
                "order": diff_info['order']
            }
        
        # 最佳模型信息
        best_model = self.get_best_model()
        if best_model:
            eval_stats = best_model['evaluation']['fit_statistics']
            adequacy = best_model['evaluation']['model_adequacy']
            
            summary["best_model"] = {
                "order": best_model['order'],
                "type": f"ARIMA{best_model['order']}",
                "aic": eval_stats['aic'],
                "bic": eval_stats['bic'],
                "r_squared": eval_stats['r_squared'],
                "adequacy_score": adequacy['score'],
                "adequacy_level": adequacy['level']
            }
        
        return summary
    
    def export_results(self, 
                      file_path: Union[str, Path],
                      format: str = 'json') -> None:
        """
        导出分析结果
        
        Args:
            file_path: 导出文件路径
            format: 导出格式 ('json', 'csv', 'excel')
        """
        if not self.analysis_results:
            raise ValueError("没有分析结果可导出")
        
        file_path = Path(file_path)
        
        if format.lower() == 'json':
            import json
            
            # 转换不可序列化的对象
            def convert_for_json(obj):
                if hasattr(obj, 'tolist'):
                    return obj.tolist()
                elif isinstance(obj, pd.Timestamp):
                    return str(obj)
                elif isinstance(obj, (pd.Series, pd.DataFrame)):
                    return obj.to_dict()
                return obj
            
            def clean_dict(d):
                if isinstance(d, dict):
                    return {k: clean_dict(v) for k, v in d.items()}
                elif isinstance(d, list):
                    return [clean_dict(item) for item in d]
                else:
                    return convert_for_json(d)
            
            cleaned_results = clean_dict(self.analysis_results)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_results, f, ensure_ascii=False, indent=2)
        
        elif format.lower() == 'csv':
            # 导出摘要信息到CSV
            summary = self.get_summary()
            df = pd.DataFrame([summary])
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        elif format.lower() == 'excel':
            # 导出到Excel，包含多个工作表
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # 摘要信息
                summary = self.get_summary()
                summary_df = pd.DataFrame([summary])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # 原始数据
                self.data.to_excel(writer, sheet_name='Data')
                
                # 模型比较
                if 'model_evaluation' in self.analysis_results:
                    models_data = []
                    for model in self.analysis_results['model_evaluation']:
                        eval_stats = model['evaluation']['fit_statistics']
                        models_data.append({
                            'Model': f"ARIMA{model['order']}",
                            'AIC': eval_stats['aic'],
                            'BIC': eval_stats['bic'],
                            'R_squared': eval_stats['r_squared'],
                            'Adequacy_Score': model['evaluation']['model_adequacy']['score']
                        })
                    
                    models_df = pd.DataFrame(models_data)
                    models_df.to_excel(writer, sheet_name='Model_Comparison', index=False)
        
        else:
            raise ValueError(f"不支持的导出格式: {format}")


# 便捷函数
def analyze_time_series(data: Union[str, Path, pd.Series, pd.DataFrame, np.ndarray],
                       **kwargs) -> TimeSeriesInsight:
    """
    便捷函数：一键分析时间序列
    
    Args:
        data: 时间序列数据
        **kwargs: 其他参数
        
    Returns:
        TimeSeriesInsight实例，包含完整分析结果
    """
    tsi = TimeSeriesInsight()
    tsi.quick_analysis(data, **kwargs)
    return tsi
