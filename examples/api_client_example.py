"""
时间序列洞察助手 API 客户端示例

演示如何使用Python客户端调用API服务
"""

import requests
import pandas as pd
import numpy as np
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

class TSIAClient:
    """时间序列洞察助手API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        """
        初始化客户端
        
        Args:
            base_url: API基础URL
        """
        self.base_url = base_url
        self.session = requests.Session()
        
    def upload_file(self, 
                   file_path: str,
                   date_column: Optional[str] = None,
                   value_column: Optional[str] = None,
                   date_format: Optional[str] = None) -> Dict[str, Any]:
        """
        上传文件
        
        Args:
            file_path: 文件路径
            date_column: 日期列名
            value_column: 数值列名
            date_format: 日期格式
            
        Returns:
            上传结果
        """
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {}
            if date_column:
                data['date_column'] = date_column
            if value_column:
                data['value_column'] = value_column
            if date_format:
                data['date_format'] = date_format
                
            response = self.session.post(f"{self.base_url}/upload/file", files=files, data=data)
            response.raise_for_status()
            return response.json()
    
    def upload_json_data(self, 
                        data: Dict[str, Any],
                        date_column: Optional[str] = None,
                        value_column: Optional[str] = None) -> Dict[str, Any]:
        """
        上传JSON数据
        
        Args:
            data: JSON数据
            date_column: 日期列名
            value_column: 数值列名
            
        Returns:
            上传结果
        """
        payload = {"data": data}
        if date_column:
            payload["date_column"] = date_column
        if value_column:
            payload["value_column"] = value_column
            
        response = self.session.post(f"{self.base_url}/upload/json", json=payload)
        response.raise_for_status()
        return response.json()
    
    def analyze_data(self, 
                    file_id: str,
                    auto_diff: bool = True,
                    max_p: int = 5,
                    max_q: int = 5,
                    n_models: int = 3) -> Dict[str, Any]:
        """
        执行时间序列分析
        
        Args:
            file_id: 文件ID
            auto_diff: 是否自动差分
            max_p: 最大AR阶数
            max_q: 最大MA阶数
            n_models: 评估的模型数量
            
        Returns:
            分析结果
        """
        analysis_request = {
            "auto_diff": auto_diff,
            "max_p": max_p,
            "max_q": max_q,
            "n_models": n_models
        }
        
        response = self.session.post(f"{self.base_url}/analysis/{file_id}", json=analysis_request)
        response.raise_for_status()
        return response.json()
    
    def get_analysis_summary(self, analysis_id: str) -> Dict[str, Any]:
        """获取分析摘要"""
        response = self.session.get(f"{self.base_url}/analysis/{analysis_id}/summary")
        response.raise_for_status()
        return response.json()
    
    def predict(self, 
               analysis_id: str,
               steps: int = 10,
               alpha: float = 0.05) -> Dict[str, Any]:
        """
        进行预测
        
        Args:
            analysis_id: 分析ID
            steps: 预测步数
            alpha: 置信水平
            
        Returns:
            预测结果
        """
        prediction_request = {
            "steps": steps,
            "alpha": alpha
        }
        
        response = self.session.post(f"{self.base_url}/analysis/{analysis_id}/predict", json=prediction_request)
        response.raise_for_status()
        return response.json()
    
    def generate_plots(self, 
                      file_id: str,
                      plot_types: list = None,
                      save_format: str = "png") -> Dict[str, Any]:
        """
        生成图表
        
        Args:
            file_id: 文件ID
            plot_types: 图表类型列表
            save_format: 保存格式
            
        Returns:
            图表生成结果
        """
        if plot_types is None:
            plot_types = ["original", "acf_pacf"]
            
        plot_request = {
            "plot_types": plot_types,
            "save_format": save_format
        }
        
        response = self.session.post(f"{self.base_url}/visualization/{file_id}/plots", json=plot_request)
        response.raise_for_status()
        return response.json()
    
    def identify_models(self, 
                       file_id: str,
                       max_p: int = 5,
                       max_q: int = 5,
                       max_d: int = 2) -> Dict[str, Any]:
        """识别推荐模型"""
        params = {
            "max_p": max_p,
            "max_q": max_q,
            "max_d": max_d
        }
        
        response = self.session.post(f"{self.base_url}/models/{file_id}/identify", params=params)
        response.raise_for_status()
        return response.json()
    
    def evaluate_model(self, 
                      file_id: str,
                      p: int,
                      d: int,
                      q: int) -> Dict[str, Any]:
        """评估模型"""
        params = {"p": p, "d": d, "q": q}
        
        response = self.session.post(f"{self.base_url}/models/{file_id}/evaluate", params=params)
        response.raise_for_status()
        return response.json()


def create_sample_data():
    """创建示例数据"""
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=200, freq='D')
    
    # 生成ARIMA(1,1,1)过程
    noise = np.random.randn(200)
    y = np.zeros(200)
    errors = np.zeros(200)
    
    for t in range(1, 200):
        errors[t] = noise[t] + 0.3 * noise[t-1]  # MA(1)
        y[t] = 0.7 * y[t-1] + errors[t]  # AR(1)
    
    # 添加趋势
    trend = np.linspace(0, 50, 200)
    y = y + trend
    
    df = pd.DataFrame({
        'date': dates,
        'value': y
    })
    
    return df


def main():
    """主函数 - 完整的API使用示例"""
    
    print("🚀 时间序列洞察助手 API 客户端示例")
    print("=" * 50)
    
    # 创建客户端
    client = TSIAClient()
    
    try:
        # 1. 创建示例数据
        print("📊 创建示例数据...")
        sample_data = create_sample_data()
        sample_file = "sample_data.csv"
        sample_data.to_csv(sample_file, index=False)
        print(f"✅ 示例数据已保存到 {sample_file}")
        
        # 2. 上传数据
        print("\n📤 上传数据...")
        upload_result = client.upload_file(
            sample_file,
            date_column="date",
            value_column="value"
        )
        file_id = upload_result["file_id"]
        print(f"✅ 文件上传成功，ID: {file_id}")
        print(f"   数据长度: {upload_result['data_preview']['series_info']['length']}")
        
        # 3. 识别推荐模型
        print("\n🔍 识别推荐模型...")
        model_identification = client.identify_models(file_id)
        print(f"✅ 模型识别完成")
        print(f"   平稳性: {model_identification['stationarity']['interpretation']}")
        print(f"   推荐模型数量: {len(model_identification['recommended_models'])}")
        
        # 4. 执行完整分析
        print("\n🔬 执行完整分析...")
        analysis_result = client.analyze_data(file_id)
        analysis_id = analysis_result["analysis_id"]
        print(f"✅ 分析完成，ID: {analysis_id}")
        
        if analysis_result.get("best_model"):
            best_model = analysis_result["best_model"]
            print(f"   最佳模型: ARIMA{best_model['order']}")
            print(f"   AIC: {best_model['statistics']['aic']:.2f}")
        
        # 5. 获取分析摘要
        print("\n📋 获取分析摘要...")
        summary = client.get_analysis_summary(analysis_id)
        print("✅ 摘要获取成功")
        
        # 6. 进行预测
        print("\n🔮 进行预测...")
        prediction_result = client.predict(analysis_id, steps=10)
        forecast_values = prediction_result["forecast_values"]
        print(f"✅ 预测完成")
        print(f"   预测步数: {len(forecast_values)}")
        print(f"   前5个预测值: {[f'{v:.2f}' for v in forecast_values[:5]]}")
        
        # 7. 生成图表
        print("\n📈 生成图表...")
        plot_result = client.generate_plots(file_id)
        print(f"✅ 图表生成完成")
        print(f"   生成的图表: {len(plot_result['data']['plots'])}")
        
        # 8. 评估特定模型
        print("\n⚖️ 评估特定模型...")
        evaluation_result = client.evaluate_model(file_id, p=1, d=1, q=1)
        print(f"✅ 模型评估完成")
        eval_stats = evaluation_result["evaluation"]["fit_statistics"]
        print(f"   ARIMA(1,1,1) - AIC: {eval_stats['aic']:.2f}, R²: {eval_stats.get('r_squared', 'N/A')}")
        
        print("\n🎉 所有API功能测试完成！")
        
        # 清理示例文件
        Path(sample_file).unlink(missing_ok=True)
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务，请确保服务已启动")
        print("   启动命令: python scripts/start_dev.py")
    except requests.exceptions.HTTPError as e:
        print(f"❌ API请求失败: {e}")
        if hasattr(e.response, 'text'):
            print(f"   错误详情: {e.response.text}")
    except Exception as e:
        print(f"❌ 发生错误: {e}")


if __name__ == "__main__":
    main()
