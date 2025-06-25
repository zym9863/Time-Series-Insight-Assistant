"""
时间序列可视化器

实现ACF/PACF图表绘制、时间序列可视化和诊断图表功能。
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.seasonal import seasonal_decompose
import warnings

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class TimeSeriesPlotter:
    """时间序列可视化器"""
    
    def __init__(self, figsize: Tuple[int, int] = (12, 8), style: str = 'seaborn-v0_8'):
        """
        初始化可视化器
        
        Args:
            figsize: 图形大小
            style: 绘图风格
        """
        self.figsize = figsize
        try:
            plt.style.use(style)
        except:
            plt.style.use('default')
        
        # 设置seaborn样式
        sns.set_palette("husl")
        
    def plot_time_series(self, 
                        data: pd.Series, 
                        title: str = "时间序列图",
                        show_trend: bool = False,
                        save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制时间序列图
        
        Args:
            data: 时间序列数据
            title: 图表标题
            show_trend: 是否显示趋势线
            save_path: 保存路径
            
        Returns:
            matplotlib图形对象
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # 绘制时间序列
        ax.plot(data.index, data.values, linewidth=1.5, alpha=0.8, label='原始数据')
        
        # 添加趋势线
        if show_trend:
            z = np.polyfit(range(len(data)), data.values, 1)
            p = np.poly1d(z)
            ax.plot(data.index, p(range(len(data))), "r--", alpha=0.8, label='趋势线')
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel('时间', fontsize=12)
        ax.set_ylabel('数值', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # 格式化x轴日期（如果是日期索引）
        if isinstance(data.index, pd.DatetimeIndex):
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=max(1, len(data)//10)))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def plot_acf_pacf(self, 
                     data: pd.Series,
                     lags: int = 20,
                     alpha: float = 0.05,
                     title: str = "ACF和PACF图",
                     save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制ACF和PACF图
        
        Args:
            data: 时间序列数据
            lags: 滞后阶数
            alpha: 置信水平
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            matplotlib图形对象
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(self.figsize[0], self.figsize[1]*1.2))
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            # 绘制ACF
            plot_acf(data, lags=lags, alpha=alpha, ax=ax1, title='自相关函数 (ACF)')
            ax1.set_xlabel('滞后阶数')
            ax1.set_ylabel('自相关系数')
            ax1.grid(True, alpha=0.3)
            
            # 绘制PACF
            plot_pacf(data, lags=lags, alpha=alpha, ax=ax2, title='偏自相关函数 (PACF)')
            ax2.set_xlabel('滞后阶数')
            ax2.set_ylabel('偏自相关系数')
            ax2.grid(True, alpha=0.3)
        
        fig.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def plot_decomposition(self, 
                          data: pd.Series,
                          model: str = 'additive',
                          period: Optional[int] = None,
                          title: str = "时间序列分解",
                          save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制时间序列分解图
        
        Args:
            data: 时间序列数据
            model: 分解模型 ('additive' 或 'multiplicative')
            period: 季节周期
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            matplotlib图形对象
        """
        try:
            # 自动检测周期
            if period is None:
                period = min(12, len(data) // 2)
            
            # 进行分解
            decomposition = seasonal_decompose(data, model=model, period=period)
            
            # 创建图形
            fig, axes = plt.subplots(4, 1, figsize=(self.figsize[0], self.figsize[1]*1.5))
            
            # 原始数据
            axes[0].plot(data.index, data.values, linewidth=1.5)
            axes[0].set_title('原始数据')
            axes[0].grid(True, alpha=0.3)
            
            # 趋势
            axes[1].plot(decomposition.trend.index, decomposition.trend.values, linewidth=1.5, color='orange')
            axes[1].set_title('趋势')
            axes[1].grid(True, alpha=0.3)
            
            # 季节性
            axes[2].plot(decomposition.seasonal.index, decomposition.seasonal.values, linewidth=1.5, color='green')
            axes[2].set_title('季节性')
            axes[2].grid(True, alpha=0.3)
            
            # 残差
            axes[3].plot(decomposition.resid.index, decomposition.resid.values, linewidth=1.5, color='red')
            axes[3].set_title('残差')
            axes[3].grid(True, alpha=0.3)
            axes[3].set_xlabel('时间')
            
            fig.suptitle(title, fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
            
            return fig
            
        except Exception as e:
            # 如果分解失败，返回简单的时间序列图
            print(f"分解失败: {e}")
            return self.plot_time_series(data, title="时间序列图（分解失败）")
    
    def plot_residual_diagnostics(self, 
                                 residuals: pd.Series,
                                 fitted_values: pd.Series,
                                 title: str = "残差诊断图",
                                 save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制残差诊断图
        
        Args:
            residuals: 残差序列
            fitted_values: 拟合值序列
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            matplotlib图形对象
        """
        fig, axes = plt.subplots(2, 2, figsize=(self.figsize[0]*1.2, self.figsize[1]))
        
        # 1. 残差vs拟合值
        axes[0, 0].scatter(fitted_values, residuals, alpha=0.6)
        axes[0, 0].axhline(y=0, color='r', linestyle='--', alpha=0.8)
        axes[0, 0].set_xlabel('拟合值')
        axes[0, 0].set_ylabel('残差')
        axes[0, 0].set_title('残差 vs 拟合值')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. 残差时间序列图
        axes[0, 1].plot(residuals.index, residuals.values, linewidth=1)
        axes[0, 1].axhline(y=0, color='r', linestyle='--', alpha=0.8)
        axes[0, 1].set_xlabel('时间')
        axes[0, 1].set_ylabel('残差')
        axes[0, 1].set_title('残差时间序列')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 残差直方图
        axes[1, 0].hist(residuals.dropna(), bins=30, density=True, alpha=0.7, edgecolor='black')
        
        # 添加正态分布曲线
        mu, sigma = residuals.mean(), residuals.std()
        x = np.linspace(residuals.min(), residuals.max(), 100)
        axes[1, 0].plot(x, (1/(sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2), 
                       'r-', linewidth=2, label='正态分布')
        axes[1, 0].set_xlabel('残差值')
        axes[1, 0].set_ylabel('密度')
        axes[1, 0].set_title('残差分布')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Q-Q图
        from scipy import stats
        stats.probplot(residuals.dropna(), dist="norm", plot=axes[1, 1])
        axes[1, 1].set_title('Q-Q图')
        axes[1, 1].grid(True, alpha=0.3)
        
        fig.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def plot_model_comparison(self, 
                             models_results: List[Dict[str, Any]],
                             criteria: str = 'aic',
                             title: str = "模型比较",
                             save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制模型比较图
        
        Args:
            models_results: 模型结果列表
            criteria: 比较准则 ('aic', 'bic', 'hqic')
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            matplotlib图形对象
        """
        if not models_results:
            raise ValueError("没有模型结果可供比较")
        
        # 提取模型信息
        model_names = []
        criteria_values = []
        
        for result in models_results:
            if 'order' in result and criteria in result:
                order = result['order']
                model_names.append(f"ARIMA{order}")
                criteria_values.append(result[criteria])
        
        if not model_names:
            raise ValueError(f"没有找到有效的{criteria}值")
        
        # 创建图形
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # 绘制条形图
        bars = ax.bar(range(len(model_names)), criteria_values, alpha=0.7)
        
        # 标记最优模型
        best_idx = np.argmin(criteria_values)
        bars[best_idx].set_color('red')
        bars[best_idx].set_alpha(0.9)
        
        ax.set_xlabel('模型')
        ax.set_ylabel(criteria.upper())
        ax.set_title(f'{title} - {criteria.upper()}比较')
        ax.set_xticks(range(len(model_names)))
        ax.set_xticklabels(model_names, rotation=45)
        ax.grid(True, alpha=0.3, axis='y')
        
        # 添加数值标签
        for i, v in enumerate(criteria_values):
            ax.text(i, v + max(criteria_values) * 0.01, f'{v:.2f}', 
                   ha='center', va='bottom', fontweight='bold' if i == best_idx else 'normal')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def plot_forecast(self, 
                     original_data: pd.Series,
                     forecast: pd.Series,
                     confidence_intervals: Optional[pd.DataFrame] = None,
                     title: str = "预测结果",
                     save_path: Optional[str] = None) -> plt.Figure:
        """
        绘制预测结果图
        
        Args:
            original_data: 原始数据
            forecast: 预测值
            confidence_intervals: 置信区间
            title: 图表标题
            save_path: 保存路径
            
        Returns:
            matplotlib图形对象
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # 绘制原始数据
        ax.plot(original_data.index, original_data.values, 
               label='历史数据', linewidth=1.5, alpha=0.8)
        
        # 绘制预测值
        ax.plot(forecast.index, forecast.values, 
               label='预测值', linewidth=2, color='red', alpha=0.8)
        
        # 绘制置信区间
        if confidence_intervals is not None:
            ax.fill_between(forecast.index, 
                           confidence_intervals.iloc[:, 0], 
                           confidence_intervals.iloc[:, 1],
                           alpha=0.3, color='red', label='95%置信区间')
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel('时间')
        ax.set_ylabel('数值')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 添加分割线
        if len(original_data) > 0:
            ax.axvline(x=original_data.index[-1], color='gray', 
                      linestyle='--', alpha=0.7, label='预测起点')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
    
    def create_comprehensive_report(self, 
                                   data: pd.Series,
                                   acf_pacf_data: Optional[pd.Series] = None,
                                   residuals: Optional[pd.Series] = None,
                                   fitted_values: Optional[pd.Series] = None,
                                   save_path: Optional[str] = None) -> plt.Figure:
        """
        创建综合分析报告图
        
        Args:
            data: 原始时间序列数据
            acf_pacf_data: 用于ACF/PACF分析的数据（通常是差分后的数据）
            residuals: 残差
            fitted_values: 拟合值
            save_path: 保存路径
            
        Returns:
            matplotlib图形对象
        """
        # 确定子图数量
        n_plots = 2  # 原始数据 + ACF/PACF
        if residuals is not None and fitted_values is not None:
            n_plots += 1  # 残差诊断
        
        fig = plt.figure(figsize=(self.figsize[0]*1.5, self.figsize[1]*n_plots*0.8))
        
        # 1. 原始时间序列
        ax1 = plt.subplot(n_plots, 1, 1)
        ax1.plot(data.index, data.values, linewidth=1.5, alpha=0.8)
        ax1.set_title('原始时间序列', fontsize=14, fontweight='bold')
        ax1.set_ylabel('数值')
        ax1.grid(True, alpha=0.3)
        
        # 2. ACF/PACF（如果提供了数据）
        if acf_pacf_data is not None:
            ax2 = plt.subplot(n_plots, 2, 3)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                plot_acf(acf_pacf_data, lags=20, ax=ax2, title='ACF')
                ax2.grid(True, alpha=0.3)
            
            ax3 = plt.subplot(n_plots, 2, 4)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                plot_pacf(acf_pacf_data, lags=20, ax=ax3, title='PACF')
                ax3.grid(True, alpha=0.3)
        
        # 3. 残差诊断（如果提供了残差）
        if residuals is not None and fitted_values is not None:
            start_row = 3 if acf_pacf_data is not None else 2
            
            # 残差时间序列
            ax4 = plt.subplot(n_plots, 2, start_row*2-1)
            ax4.plot(residuals.index, residuals.values, linewidth=1)
            ax4.axhline(y=0, color='r', linestyle='--', alpha=0.8)
            ax4.set_title('残差时间序列')
            ax4.set_ylabel('残差')
            ax4.grid(True, alpha=0.3)
            
            # 残差直方图
            ax5 = plt.subplot(n_plots, 2, start_row*2)
            ax5.hist(residuals.dropna(), bins=20, density=True, alpha=0.7, edgecolor='black')
            ax5.set_title('残差分布')
            ax5.set_xlabel('残差值')
            ax5.set_ylabel('密度')
            ax5.grid(True, alpha=0.3)
        
        plt.suptitle('时间序列分析综合报告', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        return fig
