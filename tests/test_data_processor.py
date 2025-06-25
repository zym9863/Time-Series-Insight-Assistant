"""
测试数据处理器模块
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from time_series_insight.core.data_processor import TimeSeriesProcessor


class TestTimeSeriesProcessor:
    """测试TimeSeriesProcessor类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.processor = TimeSeriesProcessor()
        
        # 创建测试数据
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        values = np.cumsum(np.random.randn(100)) + 100
        self.test_series = pd.Series(values, index=dates)
        
        # 创建非平稳数据（带趋势）
        trend = np.linspace(0, 50, 100)
        self.non_stationary_series = pd.Series(values + trend, index=dates)
    
    def test_load_series_data(self):
        """测试加载Series数据"""
        result = self.processor.load_data(self.test_series)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(self.test_series)
        assert result.equals(self.test_series)
    
    def test_load_array_data(self):
        """测试加载numpy数组数据"""
        array_data = self.test_series.values
        result = self.processor.load_data(array_data)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(array_data)
        np.testing.assert_array_equal(result.values, array_data)
    
    def test_load_dataframe_data(self):
        """测试加载DataFrame数据"""
        df = pd.DataFrame({
            'date': self.test_series.index,
            'value': self.test_series.values
        })
        
        result = self.processor.load_data(df, date_column='date', value_column='value')
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(self.test_series)
        np.testing.assert_array_almost_equal(result.values, self.test_series.values)
    
    def test_load_csv_file(self):
        """测试加载CSV文件"""
        # 创建临时CSV文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'date': self.test_series.index,
                'value': self.test_series.values
            })
            df.to_csv(f.name, index=False)
            temp_file = f.name
        
        try:
            result = self.processor.load_data(temp_file, date_column='date', value_column='value')
            
            assert isinstance(result, pd.Series)
            assert len(result) == len(self.test_series)
            np.testing.assert_array_almost_equal(result.values, self.test_series.values)
        finally:
            os.unlink(temp_file)
    
    def test_check_stationarity_stationary(self):
        """测试平稳序列的平稳性检验"""
        # 创建平稳序列（白噪声）
        stationary_data = pd.Series(np.random.randn(100))
        self.processor.load_data(stationary_data)
        
        result = self.processor.check_stationarity()
        
        assert 'adf' in result
        assert 'kpss' in result
        assert 'overall' in result
        assert isinstance(result['overall']['is_stationary'], bool)
    
    def test_check_stationarity_non_stationary(self):
        """测试非平稳序列的平稳性检验"""
        self.processor.load_data(self.non_stationary_series)
        
        result = self.processor.check_stationarity()
        
        assert 'adf' in result
        assert 'kpss' in result
        assert 'overall' in result
        # 非平稳序列应该被检测为非平稳
        assert not result['overall']['is_stationary']
    
    def test_difference(self):
        """测试差分功能"""
        self.processor.load_data(self.test_series)
        
        # 一阶差分
        diff_result = self.processor.difference(order=1)
        
        assert isinstance(diff_result, pd.Series)
        assert len(diff_result) == len(self.test_series) - 1
        assert self.processor.diff_order == 1
        
        # 验证差分计算正确性
        expected_diff = self.test_series.diff().dropna()
        np.testing.assert_array_almost_equal(diff_result.values, expected_diff.values)
    
    def test_auto_difference(self):
        """测试自动差分功能"""
        self.processor.load_data(self.non_stationary_series)
        
        diff_result, diff_order = self.processor.auto_difference()
        
        assert isinstance(diff_result, pd.Series)
        assert isinstance(diff_order, int)
        assert diff_order >= 0
        assert self.processor.diff_order == diff_order
    
    def test_get_processed_data(self):
        """测试获取处理后数据"""
        self.processor.load_data(self.test_series)
        
        # 未差分时应返回原始数据
        result = self.processor.get_processed_data()
        assert result.equals(self.test_series)
        
        # 差分后应返回差分数据
        self.processor.difference(order=1)
        result = self.processor.get_processed_data()
        assert len(result) == len(self.test_series) - 1
    
    def test_get_summary(self):
        """测试获取数据摘要"""
        self.processor.load_data(self.test_series)
        self.processor.check_stationarity()
        
        summary = self.processor.get_summary()
        
        assert isinstance(summary, dict)
        assert '原始数据长度' in summary
        assert '处理后数据长度' in summary
        assert '差分阶数' in summary
        assert '是否平稳' in summary
        assert '数据统计' in summary
        
        # 验证统计信息
        stats = summary['数据统计']
        assert '均值' in stats
        assert '标准差' in stats
        assert '最小值' in stats
        assert '最大值' in stats
    
    def test_clean_data_with_missing_values(self):
        """测试清理包含缺失值的数据"""
        # 创建包含缺失值的数据
        data_with_nan = self.test_series.copy()
        data_with_nan.iloc[10:15] = np.nan
        
        result = self.processor.load_data(data_with_nan)
        
        # 应该自动移除缺失值
        assert not result.isnull().any()
        assert len(result) == len(self.test_series) - 5
    
    def test_invalid_data_type(self):
        """测试无效数据类型"""
        with pytest.raises(ValueError):
            self.processor.load_data("invalid_string_data")
    
    def test_empty_data(self):
        """测试空数据"""
        empty_series = pd.Series([], dtype=float)
        
        with pytest.raises(Exception):  # 应该抛出异常
            self.processor.load_data(empty_series)
            self.processor.check_stationarity()


if __name__ == "__main__":
    pytest.main([__file__])
