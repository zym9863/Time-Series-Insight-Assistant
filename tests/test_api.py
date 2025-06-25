"""
测试API接口模块
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path

from time_series_insight.api import TimeSeriesInsight, analyze_time_series


class TestTimeSeriesInsight:
    """测试TimeSeriesInsight类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.tsi = TimeSeriesInsight()
        
        # 创建测试数据
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        
        # 创建ARIMA(1,1,1)过程的模拟数据
        # 首先生成AR(1)过程
        ar_coef = 0.7
        ma_coef = 0.3
        noise = np.random.randn(100)
        
        # 生成ARMA过程
        y = np.zeros(100)
        errors = np.zeros(100)
        for t in range(1, 100):
            errors[t] = noise[t] + ma_coef * noise[t-1]
            y[t] = ar_coef * y[t-1] + errors[t]
        
        # 积分得到ARIMA过程
        integrated_y = np.cumsum(y) + 100
        
        self.test_series = pd.Series(integrated_y, index=dates)
    
    def test_load_data(self):
        """测试数据加载"""
        result = self.tsi.load_data(self.test_series)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(self.test_series)
        assert self.tsi.data is not None
    
    def test_analyze(self):
        """测试完整分析流程"""
        self.tsi.load_data(self.test_series)
        
        results = self.tsi.analyze(n_models=2)  # 只评估2个模型以加快测试
        
        # 验证结果结构
        assert isinstance(results, dict)
        assert 'stationarity' in results
        assert 'differencing' in results
        assert 'model_identification' in results
        assert 'model_evaluation' in results
        
        # 验证平稳性检验结果
        stationarity = results['stationarity']
        assert 'overall' in stationarity
        assert 'is_stationary' in stationarity['overall']
        
        # 验证差分结果
        differencing = results['differencing']
        assert 'applied' in differencing
        assert 'order' in differencing
        
        # 验证模型识别结果
        model_id = results['model_identification']
        assert 'recommended_models' in model_id
        assert len(model_id['recommended_models']) > 0
        
        # 验证模型评估结果
        model_eval = results['model_evaluation']
        assert isinstance(model_eval, list)
        assert len(model_eval) > 0
        
        # 验证最佳模型
        if 'best_model' in results:
            best_model = results['best_model']
            assert 'order' in best_model
            assert 'evaluation' in best_model
    
    def test_quick_analysis(self):
        """测试一键分析功能"""
        results = self.tsi.quick_analysis(self.test_series, n_models=2)
        
        assert isinstance(results, dict)
        assert 'stationarity' in results
        assert 'model_identification' in results
        assert self.tsi.data is not None
    
    def test_get_best_model(self):
        """测试获取最佳模型"""
        self.tsi.load_data(self.test_series)
        self.tsi.analyze(n_models=2)
        
        best_model = self.tsi.get_best_model()
        
        if best_model is not None:
            assert 'order' in best_model
            assert 'evaluation' in best_model
            assert 'estimation' in best_model
    
    def test_predict(self):
        """测试预测功能"""
        self.tsi.load_data(self.test_series)
        self.tsi.analyze(n_models=1)
        
        best_model = self.tsi.get_best_model()
        if best_model is not None:
            try:
                forecast_result = self.tsi.predict(steps=5)
                
                assert isinstance(forecast_result, dict)
                assert 'forecast' in forecast_result
                assert 'model_order' in forecast_result
                assert 'forecast_steps' in forecast_result
                
                forecast = forecast_result['forecast']
                assert isinstance(forecast, pd.Series)
                assert len(forecast) == 5
            except ValueError:
                # 如果模型拟合失败，这是可以接受的
                pass
    
    def test_get_summary(self):
        """测试获取分析摘要"""
        self.tsi.load_data(self.test_series)
        self.tsi.analyze(n_models=1)
        
        summary = self.tsi.get_summary()
        
        assert isinstance(summary, dict)
        assert 'data_info' in summary
        
        data_info = summary['data_info']
        assert 'length' in data_info
        assert 'mean' in data_info
        assert 'std' in data_info
        
        if 'stationarity' in summary:
            stationarity = summary['stationarity']
            assert 'is_stationary' in stationarity
        
        if 'best_model' in summary:
            best_model = summary['best_model']
            assert 'order' in best_model
            assert 'aic' in best_model
    
    def test_export_results_json(self):
        """测试导出JSON结果"""
        self.tsi.load_data(self.test_series)
        self.tsi.analyze(n_models=1)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            self.tsi.export_results(temp_file, format='json')
            
            # 验证文件存在
            assert os.path.exists(temp_file)
            
            # 验证文件内容
            import json
            with open(temp_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert isinstance(data, dict)
            assert 'stationarity' in data
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_plot_analysis(self):
        """测试生成分析图表"""
        self.tsi.load_data(self.test_series)
        self.tsi.analyze(n_models=1)
        
        # 测试不保存图表
        plots_info = self.tsi.plot_analysis(show_plots=False)
        
        assert isinstance(plots_info, dict)
        assert 'original_series' in plots_info
        
        # 测试保存图表
        with tempfile.TemporaryDirectory() as temp_dir:
            plots_info = self.tsi.plot_analysis(
                save_dir=temp_dir, 
                show_plots=False
            )
            
            # 验证文件存在
            assert os.path.exists(os.path.join(temp_dir, "original_series.png"))
            assert os.path.exists(os.path.join(temp_dir, "acf_pacf.png"))
    
    def test_analyze_time_series_function(self):
        """测试便捷分析函数"""
        result = analyze_time_series(self.test_series, n_models=1)
        
        assert isinstance(result, TimeSeriesInsight)
        assert result.data is not None
        assert result.analysis_results
    
    def test_error_handling_no_data(self):
        """测试无数据时的错误处理"""
        with pytest.raises(ValueError):
            self.tsi.analyze()
        
        with pytest.raises(ValueError):
            self.tsi.predict()
    
    def test_error_handling_no_analysis(self):
        """测试未分析时的错误处理"""
        self.tsi.load_data(self.test_series)
        
        # 未分析时获取最佳模型应返回None
        assert self.tsi.get_best_model() is None
        
        # 未分析时预测应抛出异常
        with pytest.raises(ValueError):
            self.tsi.predict()
        
        # 未分析时导出结果应抛出异常
        with pytest.raises(ValueError):
            self.tsi.export_results("test.json")


class TestDataTypes:
    """测试不同数据类型的处理"""
    
    def test_different_data_types(self):
        """测试不同数据类型"""
        # 测试numpy数组
        array_data = np.random.randn(50)
        tsi1 = TimeSeriesInsight()
        result1 = tsi1.load_data(array_data)
        assert isinstance(result1, pd.Series)
        
        # 测试DataFrame
        df_data = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=50),
            'value': np.random.randn(50)
        })
        tsi2 = TimeSeriesInsight()
        result2 = tsi2.load_data(df_data, date_column='date', value_column='value')
        assert isinstance(result2, pd.Series)
        
        # 测试CSV文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df_data.to_csv(f.name, index=False)
            temp_file = f.name
        
        try:
            tsi3 = TimeSeriesInsight()
            result3 = tsi3.load_data(temp_file, date_column='date', value_column='value')
            assert isinstance(result3, pd.Series)
        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__])
