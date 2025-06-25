"""
时间序列洞察助手基本使用示例

演示如何使用Python API进行时间序列分析。
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# 导入时间序列洞察助手
from time_series_insight import TimeSeriesInsight, analyze_time_series


def example_1_basic_analysis():
    """示例1：基本分析流程"""
    print("=" * 50)
    print("示例1：基本分析流程")
    print("=" * 50)
    
    # 创建示例数据
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=200, freq='D')
    
    # 生成ARIMA(1,1,1)过程
    noise = np.random.randn(200)
    y = np.zeros(200)
    errors = np.zeros(200)
    
    for t in range(1, 200):
        errors[t] = noise[t] + 0.3 * noise[t-1]  # MA(1)
        y[t] = 0.7 * y[t-1] + errors[t]  # AR(1)
    
    # 积分得到I(1)过程
    integrated_y = np.cumsum(y) + 100
    data = pd.Series(integrated_y, index=dates)
    
    # 创建分析器实例
    tsi = TimeSeriesInsight()
    
    # 加载数据
    print("1. 加载数据...")
    tsi.load_data(data)
    print(f"   数据长度: {len(tsi.data)}")
    print(f"   数据范围: {tsi.data.min():.2f} 到 {tsi.data.max():.2f}")
    
    # 执行分析
    print("\n2. 执行分析...")
    results = tsi.analyze(n_models=3)
    
    # 显示分析结果
    print("\n3. 分析结果:")
    
    # 平稳性检验结果
    stationarity = results['stationarity']['overall']
    print(f"   平稳性: {'是' if stationarity['is_stationary'] else '否'}")
    
    # 差分结果
    differencing = results['differencing']
    if differencing['applied']:
        print(f"   差分阶数: {differencing['order']}")
    else:
        print("   无需差分")
    
    # 推荐模型
    best_model = tsi.get_best_model()
    if best_model:
        order = best_model['order']
        aic = best_model['evaluation']['fit_statistics']['aic']
        print(f"   推荐模型: ARIMA{order}")
        print(f"   AIC: {aic:.2f}")
    
    # 生成预测
    print("\n4. 生成预测...")
    try:
        forecast_result = tsi.predict(steps=10)
        forecast = forecast_result['forecast']
        print(f"   预测未来10期，预测值范围: {forecast.min():.2f} 到 {forecast.max():.2f}")
    except Exception as e:
        print(f"   预测失败: {e}")
    
    # 获取摘要
    print("\n5. 分析摘要:")
    summary = tsi.get_summary()
    if 'best_model' in summary:
        model_info = summary['best_model']
        print(f"   最佳模型: {model_info['type']}")
        print(f"   R²: {model_info['r_squared']:.3f}")
        print(f"   适合度: {model_info['adequacy_score']:.0f}% ({model_info['adequacy_level']})")
    
    return tsi


def example_2_file_analysis():
    """示例2：从文件分析数据"""
    print("\n" + "=" * 50)
    print("示例2：从文件分析数据")
    print("=" * 50)
    
    # 首先生成示例数据文件
    from sample_data import generate_arima_data
    
    # 创建数据目录
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # 生成数据
    data = generate_arima_data(n=150, ar_params=[0.6], ma_params=[0.4], d=1)
    
    # 保存到CSV
    df = pd.DataFrame({
        'date': data.index,
        'value': data.values
    })
    file_path = data_dir / "example_data.csv"
    df.to_csv(file_path, index=False)
    print(f"1. 已生成示例数据文件: {file_path}")
    
    # 从文件分析
    print("\n2. 从文件加载并分析...")
    tsi = analyze_time_series(
        file_path,
        date_column='date',
        value_column='value',
        n_models=2
    )
    
    # 显示结果
    summary = tsi.get_summary()
    print(f"   数据长度: {summary['data_info']['length']}")
    print(f"   数据均值: {summary['data_info']['mean']:.2f}")
    
    if 'best_model' in summary:
        print(f"   推荐模型: {summary['best_model']['type']}")
        print(f"   AIC: {summary['best_model']['aic']:.2f}")
    
    return tsi


def example_3_visualization():
    """示例3：可视化分析"""
    print("\n" + "=" * 50)
    print("示例3：可视化分析")
    print("=" * 50)
    
    # 使用示例1的结果
    tsi = example_1_basic_analysis()
    
    # 生成图表
    print("\n1. 生成可视化图表...")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    plots_info = tsi.plot_analysis(
        save_dir=output_dir,
        show_plots=False  # 不显示图表，只保存
    )
    
    print(f"   图表已保存到: {output_dir}")
    for plot_name in plots_info.keys():
        print(f"   - {plot_name}.png")
    
    return plots_info


def example_4_model_comparison():
    """示例4：模型比较"""
    print("\n" + "=" * 50)
    print("示例4：模型比较")
    print("=" * 50)
    
    # 生成数据
    from sample_data import generate_seasonal_data
    data = generate_seasonal_data(n=200, trend=0.05, seasonal_amplitude=5)
    
    # 分析
    tsi = TimeSeriesInsight()
    tsi.load_data(data)
    results = tsi.analyze(n_models=5)  # 评估更多模型
    
    # 显示模型比较
    print("1. 模型比较结果:")
    print(f"{'模型':<15} {'AIC':<10} {'BIC':<10} {'R²':<8} {'适合度':<10}")
    print("-" * 60)
    
    for model in results['model_evaluation']:
        order = model['order']
        eval_stats = model['evaluation']['fit_statistics']
        adequacy = model['evaluation']['model_adequacy']
        
        print(f"ARIMA{order:<8} {eval_stats['aic']:<10.2f} "
              f"{eval_stats['bic']:<10.2f} {eval_stats['r_squared']:<8.3f} "
              f"{adequacy['score']:<10.0f}")
    
    # 显示最佳模型详情
    best_model = tsi.get_best_model()
    if best_model:
        print(f"\n2. 最佳模型详情:")
        print(f"   模型: ARIMA{best_model['order']}")
        
        # 参数估计结果
        if 'mle' in best_model['estimation']:
            mle_result = best_model['estimation']['mle']
            if mle_result.get('success', False):
                print(f"   AR参数: {mle_result.get('ar_params', [])}")
                print(f"   MA参数: {mle_result.get('ma_params', [])}")
                print(f"   噪声方差: {mle_result.get('sigma2', 0):.4f}")
    
    return tsi


def example_5_export_results():
    """示例5：导出结果"""
    print("\n" + "=" * 50)
    print("示例5：导出分析结果")
    print("=" * 50)
    
    # 使用之前的分析结果
    tsi = example_1_basic_analysis()
    
    # 创建输出目录
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # 导出JSON格式
    json_file = output_dir / "analysis_results.json"
    tsi.export_results(json_file, format='json')
    print(f"1. JSON结果已导出到: {json_file}")
    
    # 导出Excel格式
    try:
        excel_file = output_dir / "analysis_results.xlsx"
        tsi.export_results(excel_file, format='excel')
        print(f"2. Excel结果已导出到: {excel_file}")
    except ImportError:
        print("2. Excel导出需要安装openpyxl: pip install openpyxl")
    
    # 导出CSV格式
    csv_file = output_dir / "analysis_summary.csv"
    tsi.export_results(csv_file, format='csv')
    print(f"3. CSV摘要已导出到: {csv_file}")


def main():
    """运行所有示例"""
    print("时间序列洞察助手 - 使用示例")
    print("=" * 60)
    
    try:
        # 运行示例
        example_1_basic_analysis()
        example_2_file_analysis()
        example_3_visualization()
        example_4_model_comparison()
        example_5_export_results()
        
        print("\n" + "=" * 60)
        print("所有示例运行完成！")
        print("请查看 examples/output 目录中的输出文件。")
        
    except Exception as e:
        print(f"\n运行示例时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
