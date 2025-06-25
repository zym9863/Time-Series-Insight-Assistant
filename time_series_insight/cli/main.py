"""
时间序列洞察助手命令行接口

提供完整的命令行工具功能，支持文件输入和参数配置。
"""

import typer
import pandas as pd
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import json

from ..core.data_processor import TimeSeriesProcessor
from ..analysis.model_identifier import ModelIdentifier
from ..estimation.parameter_estimator import ParameterEstimator
from ..evaluation.model_evaluator import ModelEvaluator
from ..visualization.plotter import TimeSeriesPlotter

app = typer.Typer(
    name="tsia",
    help="时间序列洞察助手 - 智能的时间序列分析工具",
    add_completion=False
)
console = Console()


@app.command()
def analyze(
    file_path: Path = typer.Argument(..., help="时间序列数据文件路径"),
    date_column: Optional[str] = typer.Option(None, "--date-col", "-d", help="日期列名"),
    value_column: Optional[str] = typer.Option(None, "--value-col", "-v", help="数值列名"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="输出目录"),
    max_p: int = typer.Option(5, "--max-p", help="最大AR阶数"),
    max_q: int = typer.Option(5, "--max-q", help="最大MA阶数"),
    auto_diff: bool = typer.Option(True, "--auto-diff/--no-auto-diff", help="是否自动差分"),
    save_plots: bool = typer.Option(True, "--save-plots/--no-save-plots", help="是否保存图表"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出"),
):
    """
    分析时间序列数据，自动识别模型并估计参数
    """
    console.print(Panel.fit("🔍 时间序列洞察助手", style="bold blue"))
    
    # 检查文件是否存在
    if not file_path.exists():
        console.print(f"❌ 文件不存在: {file_path}", style="bold red")
        raise typer.Exit(1)
    
    # 创建输出目录
    if output_dir is None:
        output_dir = Path("tsia_output")
    output_dir.mkdir(exist_ok=True)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # 1. 加载数据
            task1 = progress.add_task("📊 加载数据...", total=None)
            processor = TimeSeriesProcessor()
            data = processor.load_data(
                file_path, 
                date_column=date_column, 
                value_column=value_column
            )
            progress.update(task1, description="✅ 数据加载完成")
            
            console.print(f"📈 数据概览: {len(data)} 个观测值")
            if verbose:
                console.print(f"   数据范围: {data.index[0]} 到 {data.index[-1]}")
                console.print(f"   数值范围: {data.min():.4f} 到 {data.max():.4f}")
            
            # 2. 平稳性检验
            task2 = progress.add_task("🔬 平稳性检验...", total=None)
            stationarity_result = processor.check_stationarity()
            progress.update(task2, description="✅ 平稳性检验完成")
            
            # 显示平稳性检验结果
            _display_stationarity_results(stationarity_result)
            
            # 3. 差分处理
            if auto_diff and not processor.is_stationary:
                task3 = progress.add_task("📉 自动差分处理...", total=None)
                diff_data, diff_order = processor.auto_difference()
                progress.update(task3, description=f"✅ 差分完成 (阶数: {diff_order})")
                console.print(f"🔄 差分阶数: {diff_order}")
            else:
                diff_data = data
                diff_order = 0
            
            # 4. 模型识别
            task4 = progress.add_task("🎯 模型识别...", total=None)
            identifier = ModelIdentifier()
            recommended_models = identifier.identify_arima_order(
                diff_data, max_p=max_p, max_q=max_q, d=diff_order
            )
            progress.update(task4, description="✅ 模型识别完成")
            
            # 显示推荐模型
            _display_recommended_models(recommended_models[:5])  # 显示前5个
            
            # 5. 参数估计和模型评估
            task5 = progress.add_task("⚙️ 参数估计和模型评估...", total=None)
            
            best_models = []
            estimator = ParameterEstimator()
            evaluator = ModelEvaluator()
            
            for i, model_info in enumerate(recommended_models[:3]):  # 评估前3个模型
                order = model_info['order']
                
                # 参数估计
                estimation_results = estimator.estimate_parameters(data, order)
                
                # 模型评估
                evaluation_result = evaluator.generate_evaluation_report(data, order)
                
                if evaluation_result.get('success', False):
                    model_result = {
                        'order': order,
                        'estimation': estimation_results,
                        'evaluation': evaluation_result,
                        'model_info': model_info
                    }
                    best_models.append(model_result)
            
            progress.update(task5, description="✅ 参数估计和评估完成")
            
            # 6. 生成可视化
            if save_plots:
                task6 = progress.add_task("📊 生成可视化图表...", total=None)
                plotter = TimeSeriesPlotter()
                
                # 原始数据图
                fig1 = plotter.plot_time_series(data, title="原始时间序列")
                fig1.savefig(output_dir / "01_original_series.png", dpi=300, bbox_inches='tight')
                
                # ACF/PACF图
                analysis_data = diff_data if diff_order > 0 else data
                fig2 = plotter.plot_acf_pacf(analysis_data, title="ACF和PACF分析")
                fig2.savefig(output_dir / "02_acf_pacf.png", dpi=300, bbox_inches='tight')
                
                # 如果有最佳模型，绘制残差诊断
                if best_models:
                    best_model = best_models[0]
                    if 'fitted_model' in best_model['estimation'].get('mle', {}):
                        fitted_model = best_model['estimation']['mle']['fitted_model']
                        residuals = fitted_model.resid
                        fitted_values = fitted_model.fittedvalues
                        
                        fig3 = plotter.plot_residual_diagnostics(
                            residuals, fitted_values, 
                            title=f"残差诊断 - ARIMA{best_model['order']}"
                        )
                        fig3.savefig(output_dir / "03_residual_diagnostics.png", dpi=300, bbox_inches='tight')
                
                progress.update(task6, description="✅ 可视化图表已保存")
                console.print(f"📊 图表已保存到: {output_dir}")
        
        # 7. 显示最终结果
        _display_final_results(best_models)
        
        # 8. 保存结果到JSON
        _save_results_to_json(
            output_dir / "analysis_results.json",
            {
                'data_summary': processor.get_summary(),
                'stationarity_test': stationarity_result,
                'recommended_models': recommended_models,
                'best_models': [
                    {
                        'order': m['order'],
                        'model_info': m['model_info'],
                        'evaluation_summary': {
                            'aic': m['evaluation']['fit_statistics']['aic'],
                            'bic': m['evaluation']['fit_statistics']['bic'],
                            'r_squared': m['evaluation']['fit_statistics']['r_squared'],
                            'adequacy_score': m['evaluation']['model_adequacy']['score']
                        }
                    } for m in best_models
                ]
            }
        )
        
        console.print(f"💾 分析结果已保存到: {output_dir / 'analysis_results.json'}")
        console.print("🎉 分析完成！", style="bold green")
        
    except Exception as e:
        console.print(f"❌ 分析过程中出现错误: {str(e)}", style="bold red")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command()
def quick_check(
    file_path: Path = typer.Argument(..., help="时间序列数据文件路径"),
    date_column: Optional[str] = typer.Option(None, "--date-col", "-d", help="日期列名"),
    value_column: Optional[str] = typer.Option(None, "--value-col", "-v", help="数值列名"),
):
    """
    快速检查时间序列数据的基本信息
    """
    console.print(Panel.fit("⚡ 快速数据检查", style="bold cyan"))
    
    try:
        # 加载数据
        processor = TimeSeriesProcessor()
        data = processor.load_data(file_path, date_column=date_column, value_column=value_column)
        
        # 基本信息
        table = Table(title="数据基本信息")
        table.add_column("项目", style="cyan")
        table.add_column("值", style="magenta")
        
        table.add_row("观测数量", str(len(data)))
        table.add_row("数据类型", str(data.dtype))
        table.add_row("缺失值", str(data.isnull().sum()))
        table.add_row("最小值", f"{data.min():.4f}")
        table.add_row("最大值", f"{data.max():.4f}")
        table.add_row("均值", f"{data.mean():.4f}")
        table.add_row("标准差", f"{data.std():.4f}")
        
        if isinstance(data.index, pd.DatetimeIndex):
            table.add_row("开始时间", str(data.index[0]))
            table.add_row("结束时间", str(data.index[-1]))
            table.add_row("频率", str(data.index.freq) if data.index.freq else "不规则")
        
        console.print(table)
        
        # 平稳性快速检查
        stationarity_result = processor.check_stationarity()
        
        status = "✅ 平稳" if stationarity_result['overall']['is_stationary'] else "❌ 非平稳"
        console.print(f"\n📊 平稳性: {status}")
        
    except Exception as e:
        console.print(f"❌ 检查失败: {str(e)}", style="bold red")
        raise typer.Exit(1)


def _display_stationarity_results(results: dict):
    """显示平稳性检验结果"""
    table = Table(title="平稳性检验结果")
    table.add_column("检验方法", style="cyan")
    table.add_column("统计量", style="magenta")
    table.add_column("p值", style="yellow")
    table.add_column("结果", style="green")
    
    if 'adf' in results:
        adf = results['adf']
        result_text = "✅ 平稳" if adf['is_stationary'] else "❌ 非平稳"
        table.add_row("ADF检验", f"{adf['statistic']:.4f}", f"{adf['p_value']:.4f}", result_text)
    
    if 'kpss' in results:
        kpss = results['kpss']
        result_text = "✅ 平稳" if kpss['is_stationary'] else "❌ 非平稳"
        table.add_row("KPSS检验", f"{kpss['statistic']:.4f}", f"{kpss['p_value']:.4f}", result_text)
    
    console.print(table)
    
    if 'overall' in results:
        overall_status = "✅ 平稳" if results['overall']['is_stationary'] else "❌ 非平稳"
        console.print(f"\n📊 综合判断: {overall_status}")


def _display_recommended_models(models: List[dict]):
    """显示推荐模型"""
    table = Table(title="推荐的ARIMA模型")
    table.add_column("排名", style="cyan")
    table.add_column("模型", style="magenta")
    table.add_column("置信度", style="yellow")
    table.add_column("推荐理由", style="green")
    
    for i, model in enumerate(models, 1):
        confidence = f"{model['confidence']:.1%}"
        table.add_row(str(i), model['type'], confidence, model['reasoning'])
    
    console.print(table)


def _display_final_results(best_models: List[dict]):
    """显示最终结果"""
    if not best_models:
        console.print("❌ 没有成功拟合的模型", style="bold red")
        return
    
    table = Table(title="模型评估结果")
    table.add_column("模型", style="cyan")
    table.add_column("AIC", style="magenta")
    table.add_column("BIC", style="yellow")
    table.add_column("R²", style="green")
    table.add_column("适合度", style="blue")
    
    for model in best_models:
        eval_result = model['evaluation']
        fit_stats = eval_result['fit_statistics']
        adequacy = eval_result['model_adequacy']
        
        table.add_row(
            f"ARIMA{model['order']}",
            f"{fit_stats['aic']:.2f}",
            f"{fit_stats['bic']:.2f}",
            f"{fit_stats['r_squared']:.3f}",
            f"{adequacy['score']:.0f}% ({adequacy['level']})"
        )
    
    console.print(table)
    
    # 显示最佳模型的详细信息
    best_model = best_models[0]
    console.print(f"\n🏆 推荐模型: ARIMA{best_model['order']}")
    console.print(f"📊 模型适合度: {best_model['evaluation']['model_adequacy']['interpretation']}")


def _save_results_to_json(file_path: Path, results: dict):
    """保存结果到JSON文件"""
    # 转换不可序列化的对象
    def convert_for_json(obj):
        if hasattr(obj, 'tolist'):
            return obj.tolist()
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif isinstance(obj, pd.Timestamp):
            return str(obj)
        elif isinstance(obj, (pd.Series, pd.DataFrame)):
            return obj.to_dict()
        return obj
    
    # 递归转换
    def clean_dict(d):
        if isinstance(d, dict):
            return {k: clean_dict(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [clean_dict(item) for item in d]
        else:
            return convert_for_json(d)
    
    cleaned_results = clean_dict(results)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_results, f, ensure_ascii=False, indent=2)


@app.command()
def version():
    """显示版本信息"""
    from .. import __version__
    console.print(f"时间序列洞察助手 v{__version__}")


if __name__ == "__main__":
    app()
