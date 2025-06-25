"""
时间序列数据处理器

提供时间序列数据的加载、预处理、平稳性检验和差分功能。
"""

import pandas as pd
import numpy as np
from typing import Union, Tuple, Optional, Dict, Any
from pathlib import Path
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.tsa.seasonal import seasonal_decompose
import warnings


class TimeSeriesProcessor:
    """时间序列数据处理器"""
    
    def __init__(self):
        """初始化处理器"""
        self.data: Optional[pd.Series] = None
        self.original_data: Optional[pd.Series] = None
        self.differenced_data: Optional[pd.Series] = None
        self.diff_order: int = 0
        self.is_stationary: bool = False
        self.stationarity_tests: Dict[str, Any] = {}
        
    def load_data(self, 
                  data: Union[str, Path, pd.Series, pd.DataFrame, np.ndarray],
                  date_column: Optional[str] = None,
                  value_column: Optional[str] = None,
                  date_format: Optional[str] = None) -> pd.Series:
        """
        加载时间序列数据
        
        Args:
            data: 数据源，可以是文件路径、pandas Series/DataFrame或numpy数组
            date_column: 日期列名（当data为DataFrame时）
            value_column: 数值列名（当data为DataFrame时）
            date_format: 日期格式
            
        Returns:
            处理后的时间序列数据
        """
        if isinstance(data, (str, Path)):
            # 从文件加载
            file_path = Path(data)
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"不支持的文件格式: {file_path.suffix}")
                
            # 处理DataFrame
            if date_column and value_column:
                df[date_column] = pd.to_datetime(df[date_column], format=date_format)
                df.set_index(date_column, inplace=True)
                self.data = df[value_column]
            elif len(df.columns) == 2:
                # 假设第一列是日期，第二列是数值
                df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], format=date_format)
                df.set_index(df.columns[0], inplace=True)
                self.data = df.iloc[:, 0]
            elif len(df.columns) == 1:
                # 只有一列数值，使用默认索引
                self.data = df.iloc[:, 0]
            else:
                raise ValueError("无法自动识别数据格式，请指定date_column和value_column")
                
        elif isinstance(data, pd.DataFrame):
            if value_column:
                if date_column:
                    data[date_column] = pd.to_datetime(data[date_column], format=date_format)
                    data.set_index(date_column, inplace=True)
                self.data = data[value_column]
            else:
                # 假设第一列是数值
                self.data = data.iloc[:, 0]
                
        elif isinstance(data, pd.Series):
            self.data = data.copy()
            
        elif isinstance(data, np.ndarray):
            self.data = pd.Series(data)
            
        else:
            raise ValueError(f"不支持的数据类型: {type(data)}")
        
        # 保存原始数据
        self.original_data = self.data.copy()
        
        # 基本数据清理
        self.data = self._clean_data(self.data)
        
        return self.data
    
    def _clean_data(self, data: pd.Series) -> pd.Series:
        """清理数据"""
        # 移除缺失值
        data = data.dropna()
        
        # 确保数据类型为数值型
        if not pd.api.types.is_numeric_dtype(data):
            try:
                data = pd.to_numeric(data, errors='coerce')
                data = data.dropna()
            except:
                raise ValueError("无法将数据转换为数值型")
        
        return data
    
    def check_stationarity(self, 
                          alpha: float = 0.05,
                          method: str = 'both') -> Dict[str, Any]:
        """
        检验时间序列的平稳性
        
        Args:
            alpha: 显著性水平
            method: 检验方法 ('adf', 'kpss', 'both')
            
        Returns:
            检验结果字典
        """
        if self.data is None:
            raise ValueError("请先加载数据")
        
        results = {}
        
        if method in ['adf', 'both']:
            # ADF检验 (原假设：存在单位根，即非平稳)
            adf_result = adfuller(self.data, autolag='AIC')
            results['adf'] = {
                'statistic': adf_result[0],
                'p_value': adf_result[1],
                'critical_values': adf_result[4],
                'is_stationary': adf_result[1] < alpha,
                'interpretation': 'ADF检验：' + ('平稳' if adf_result[1] < alpha else '非平稳')
            }
        
        if method in ['kpss', 'both']:
            # KPSS检验 (原假设：平稳)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                kpss_result = kpss(self.data, regression='c')
            results['kpss'] = {
                'statistic': kpss_result[0],
                'p_value': kpss_result[1],
                'critical_values': kpss_result[3],
                'is_stationary': kpss_result[1] > alpha,
                'interpretation': 'KPSS检验：' + ('平稳' if kpss_result[1] > alpha else '非平稳')
            }
        
        # 综合判断
        if method == 'both':
            adf_stationary = results['adf']['is_stationary']
            kpss_stationary = results['kpss']['is_stationary']
            
            if adf_stationary and kpss_stationary:
                overall_result = '平稳'
                self.is_stationary = True
            elif not adf_stationary and not kpss_stationary:
                overall_result = '非平稳'
                self.is_stationary = False
            else:
                overall_result = '结果不一致，建议进一步分析'
                self.is_stationary = False
                
            results['overall'] = {
                'is_stationary': self.is_stationary,
                'interpretation': f'综合判断：{overall_result}'
            }
        else:
            test_key = 'adf' if method == 'adf' else 'kpss'
            self.is_stationary = results[test_key]['is_stationary']
            results['overall'] = {
                'is_stationary': self.is_stationary,
                'interpretation': results[test_key]['interpretation']
            }
        
        self.stationarity_tests = results
        return results
    
    def difference(self, order: int = 1, seasonal_order: int = 0) -> pd.Series:
        """
        对时间序列进行差分
        
        Args:
            order: 差分阶数
            seasonal_order: 季节差分阶数
            
        Returns:
            差分后的时间序列
        """
        if self.data is None:
            raise ValueError("请先加载数据")
        
        differenced = self.data.copy()
        
        # 季节差分
        if seasonal_order > 0:
            for _ in range(seasonal_order):
                differenced = differenced.diff(periods=12).dropna()  # 假设季节周期为12
        
        # 普通差分
        for _ in range(order):
            differenced = differenced.diff().dropna()
        
        self.differenced_data = differenced
        self.diff_order = order
        
        return differenced
    
    def auto_difference(self, max_order: int = 3, alpha: float = 0.05) -> Tuple[pd.Series, int]:
        """
        自动确定差分阶数并进行差分
        
        Args:
            max_order: 最大差分阶数
            alpha: 显著性水平
            
        Returns:
            差分后的序列和差分阶数
        """
        if self.data is None:
            raise ValueError("请先加载数据")
        
        current_data = self.data.copy()
        diff_order = 0
        
        # 检查原始数据是否平稳
        stationarity_result = self.check_stationarity(alpha=alpha)
        
        if stationarity_result['overall']['is_stationary']:
            self.differenced_data = current_data
            self.diff_order = 0
            return current_data, 0
        
        # 逐步差分直到平稳
        for order in range(1, max_order + 1):
            current_data = current_data.diff().dropna()
            
            # 检验差分后的平稳性
            try:
                adf_result = adfuller(current_data, autolag='AIC')
                if adf_result[1] < alpha:  # 平稳
                    diff_order = order
                    break
            except:
                continue
        
        if diff_order == 0:
            print(f"警告：在{max_order}阶差分内未能达到平稳，使用1阶差分")
            current_data = self.data.diff().dropna()
            diff_order = 1
        
        self.differenced_data = current_data
        self.diff_order = diff_order
        
        return current_data, diff_order
    
    def get_processed_data(self) -> pd.Series:
        """获取处理后的数据（差分后或原始数据）"""
        if self.differenced_data is not None:
            return self.differenced_data
        elif self.data is not None:
            return self.data
        else:
            raise ValueError("没有可用的数据")
    
    def get_summary(self) -> Dict[str, Any]:
        """获取数据处理摘要"""
        if self.data is None:
            return {"error": "没有加载数据"}
        
        summary = {
            "原始数据长度": len(self.original_data) if self.original_data is not None else 0,
            "处理后数据长度": len(self.data),
            "差分阶数": self.diff_order,
            "是否平稳": self.is_stationary,
            "平稳性检验结果": self.stationarity_tests,
            "数据统计": {
                "均值": float(self.data.mean()),
                "标准差": float(self.data.std()),
                "最小值": float(self.data.min()),
                "最大值": float(self.data.max()),
            }
        }
        
        if self.differenced_data is not None:
            summary["差分后数据长度"] = len(self.differenced_data)
            summary["差分后数据统计"] = {
                "均值": float(self.differenced_data.mean()),
                "标准差": float(self.differenced_data.std()),
                "最小值": float(self.differenced_data.min()),
                "最大值": float(self.differenced_data.max()),
            }
        
        return summary
