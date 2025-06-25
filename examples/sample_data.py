"""
生成示例时间序列数据

用于演示时间序列洞察助手的功能。
"""

import pandas as pd
import numpy as np
from pathlib import Path


def generate_arima_data(n=200, ar_params=None, ma_params=None, d=1, noise_std=1.0, seed=42):
    """
    生成ARIMA模型的模拟数据
    
    Args:
        n: 数据点数量
        ar_params: AR参数列表
        ma_params: MA参数列表  
        d: 差分阶数
        noise_std: 噪声标准差
        seed: 随机种子
        
    Returns:
        pandas Series: 生成的时间序列数据
    """
    np.random.seed(seed)
    
    if ar_params is None:
        ar_params = [0.7, -0.2]  # AR(2)
    if ma_params is None:
        ma_params = [0.3]  # MA(1)
    
    # 生成白噪声
    noise = np.random.normal(0, noise_std, n + 50)  # 多生成一些用于预热
    
    # 生成ARMA过程
    p = len(ar_params)
    q = len(ma_params)
    
    y = np.zeros(n + 50)
    errors = np.zeros(n + 50)
    
    for t in range(max(p, q), n + 50):
        # MA部分
        ma_term = noise[t]
        for j in range(q):
            ma_term += ma_params[j] * noise[t-j-1]
        errors[t] = ma_term
        
        # AR部分
        ar_term = errors[t]
        for i in range(p):
            ar_term += ar_params[i] * y[t-i-1]
        y[t] = ar_term
    
    # 取后n个点（去掉预热期）
    arma_series = y[-n:]
    
    # 进行积分（差分的逆操作）
    if d > 0:
        integrated_series = arma_series.copy()
        for _ in range(d):
            integrated_series = np.cumsum(integrated_series)
        # 添加常数项使数据更现实
        integrated_series += 100
    else:
        integrated_series = arma_series + 100
    
    # 创建时间索引
    dates = pd.date_range('2020-01-01', periods=n, freq='D')
    
    return pd.Series(integrated_series, index=dates, name='value')


def generate_seasonal_data(n=365, trend=0.1, seasonal_amplitude=10, noise_std=2.0, seed=42):
    """
    生成带季节性的时间序列数据
    
    Args:
        n: 数据点数量
        trend: 趋势斜率
        seasonal_amplitude: 季节性振幅
        noise_std: 噪声标准差
        seed: 随机种子
        
    Returns:
        pandas Series: 生成的时间序列数据
    """
    np.random.seed(seed)
    
    # 时间索引
    dates = pd.date_range('2020-01-01', periods=n, freq='D')
    t = np.arange(n)
    
    # 趋势项
    trend_component = trend * t
    
    # 季节性项（年度周期）
    seasonal_component = seasonal_amplitude * np.sin(2 * np.pi * t / 365.25)
    
    # 噪声项
    noise = np.random.normal(0, noise_std, n)
    
    # 组合
    values = 100 + trend_component + seasonal_component + noise
    
    return pd.Series(values, index=dates, name='value')


def generate_stock_like_data(n=252, initial_price=100, volatility=0.02, drift=0.0005, seed=42):
    """
    生成类似股价的随机游走数据
    
    Args:
        n: 数据点数量
        initial_price: 初始价格
        volatility: 波动率
        drift: 漂移率
        seed: 随机种子
        
    Returns:
        pandas Series: 生成的时间序列数据
    """
    np.random.seed(seed)
    
    # 生成对数收益率
    returns = np.random.normal(drift, volatility, n)
    
    # 计算价格
    log_prices = np.log(initial_price) + np.cumsum(returns)
    prices = np.exp(log_prices)
    
    # 创建时间索引（工作日）
    dates = pd.bdate_range('2020-01-01', periods=n)
    
    return pd.Series(prices, index=dates, name='price')


def save_sample_datasets():
    """保存示例数据集到CSV文件"""
    output_dir = Path("examples/data")
    output_dir.mkdir(exist_ok=True)
    
    # 1. ARIMA数据
    arima_data = generate_arima_data(n=200, ar_params=[0.7, -0.2], ma_params=[0.3], d=1)
    arima_df = pd.DataFrame({
        'date': arima_data.index,
        'value': arima_data.values
    })
    arima_df.to_csv(output_dir / "arima_sample.csv", index=False)
    print(f"已保存ARIMA示例数据: {output_dir / 'arima_sample.csv'}")
    
    # 2. 季节性数据
    seasonal_data = generate_seasonal_data(n=365, trend=0.1, seasonal_amplitude=10)
    seasonal_df = pd.DataFrame({
        'date': seasonal_data.index,
        'value': seasonal_data.values
    })
    seasonal_df.to_csv(output_dir / "seasonal_sample.csv", index=False)
    print(f"已保存季节性示例数据: {output_dir / 'seasonal_sample.csv'}")
    
    # 3. 股价类数据
    stock_data = generate_stock_like_data(n=252, initial_price=100, volatility=0.02)
    stock_df = pd.DataFrame({
        'date': stock_data.index,
        'price': stock_data.values
    })
    stock_df.to_csv(output_dir / "stock_sample.csv", index=False)
    print(f"已保存股价类示例数据: {output_dir / 'stock_sample.csv'}")
    
    # 4. 简单趋势数据
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    trend_values = 50 + 0.5 * np.arange(100) + np.random.normal(0, 2, 100)
    trend_df = pd.DataFrame({
        'date': dates,
        'value': trend_values
    })
    trend_df.to_csv(output_dir / "trend_sample.csv", index=False)
    print(f"已保存趋势示例数据: {output_dir / 'trend_sample.csv'}")
    
    return {
        'arima': output_dir / "arima_sample.csv",
        'seasonal': output_dir / "seasonal_sample.csv", 
        'stock': output_dir / "stock_sample.csv",
        'trend': output_dir / "trend_sample.csv"
    }


if __name__ == "__main__":
    # 创建示例数据目录
    Path("examples/data").mkdir(parents=True, exist_ok=True)
    
    # 生成并保存示例数据
    files = save_sample_datasets()
    
    print("\n示例数据生成完成！")
    print("可以使用以下命令测试：")
    print(f"tsia analyze {files['arima']}")
    print(f"tsia analyze {files['seasonal']}")
    print(f"tsia analyze {files['stock']} --value-col price")
    print(f"tsia analyze {files['trend']}")
