[English](README_EN.md) | [中文](README.md)

# 时间序列洞察助手 (Time Series Insight Assistant)

🔍 **智能的时间序列分析工具** - 提供自动模型识别、参数估计和可视化诊断功能

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/yourusername/time-series-insight-assistant)

## ✨ 特性

- 🤖 **自动模型识别**: 基于ACF/PACF分析自动推荐最适合的ARIMA模型
- 📊 **智能数据处理**: 自动平稳性检验、差分处理和数据清洗
- ⚙️ **多种参数估计**: 支持矩估计法和最大似然估计，提供参数对比
- 🔬 **全面模型评估**: 残差分析、白噪声检验和模型适合度评估
- 📈 **丰富可视化**: ACF/PACF图、残差诊断图、预测图等
- 🖥️ **双重接口**: 命令行工具和Python库，满足不同使用场景
- 📋 **详细报告**: 生成完整的分析报告和模型推荐

## 🚀 快速开始

### 安装

使用uv包管理器安装（推荐）：

```bash
uv add time-series-insight-assistant
```

或使用pip安装：

```bash
pip install time-series-insight-assistant
```

### 命令行使用

```bash
# 分析CSV文件中的时间序列数据
tsia analyze data.csv --date-col date --value-col value

# 快速检查数据
tsia quick-check data.csv

# 查看帮助
tsia --help
```

### FastAPI服务使用

```bash
# 启动开发服务器
python scripts/start_dev.py
# 或使用
./scripts/start.sh

# 启动生产服务器
python scripts/start_prod.py
# 或使用
./scripts/start.sh prod

# 访问API文档
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### Python API使用

```python
import pandas as pd
from time_series_insight import analyze_time_series

# 一键分析
tsi = analyze_time_series('data.csv', date_column='date', value_column='value')

# 查看分析摘要
summary = tsi.get_summary()
print(f"推荐模型: {summary['best_model']['type']}")

# 生成预测
forecast = tsi.predict(steps=10)
print(forecast['forecast'])

# 生成可视化图表
tsi.plot_analysis(save_dir='output/')
```

### FastAPI服务API使用

```python
import requests

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

# 上传数据文件
with open('data.csv', 'rb') as f:
    files = {'file': f}
    data = {'date_column': 'date', 'value_column': 'value'}
    response = requests.post(f"{BASE_URL}/upload/file", files=files, data=data)
    upload_result = response.json()
    file_id = upload_result["file_id"]

# 执行分析
analysis_request = {
    "auto_diff": True,
    "max_p": 5,
    "max_q": 5,
    "n_models": 3
}
response = requests.post(f"{BASE_URL}/analysis/{file_id}", json=analysis_request)
analysis_result = response.json()
analysis_id = analysis_result["analysis_id"]

# 进行预测
prediction_request = {"steps": 10, "alpha": 0.05}
response = requests.post(f"{BASE_URL}/analysis/{analysis_id}/predict", json=prediction_request)
prediction_result = response.json()
print(f"预测值: {prediction_result['forecast_values']}")
```

## � Docker 部署

### 快速部署

使用Docker可以快速部署FastAPI服务，无需复杂的环境配置：

```bash
# 方法一：使用部署脚本（推荐）
chmod +x scripts/docker-deploy.sh
./scripts/docker-deploy.sh --build --run

# 方法二：使用Docker Compose
docker-compose up --build -d

# Windows PowerShell
.\scripts\docker-deploy.ps1 -Build -Run
```

### 验证部署

```bash
# 检查服务状态
curl http://localhost:8000/health

# 访问API文档
open http://localhost:8000/docs
```

### 高级部署选项

```bash
# 包含Redis缓存
./scripts/docker-deploy.sh --run --with-redis

# 包含PostgreSQL数据库
./scripts/docker-deploy.sh --run --with-db

# 查看日志
./scripts/docker-deploy.sh --logs

# 停止服务
./scripts/docker-deploy.sh --stop
```

详细的Docker部署指南请参考：[Docker部署文档](docs/DOCKER_DEPLOYMENT.md)

## �📖 核心功能

### 1. 模型自动识别与可视化诊断

- **平稳性检验**: ADF检验和KPSS检验
- **自动差分**: 根据检验结果自动确定差分阶数
- **ACF/PACF分析**: 计算并可视化自相关和偏自相关函数
- **模式识别**: 自动识别截尾和拖尾模式
- **模型推荐**: 基于统计特征推荐最适合的ARIMA模型

### 2. 参数快速估计与模型评估

- **矩估计法**: 快速计算模型参数的初始估计
- **最大似然估计**: 提供更精确的参数估计
- **参数对比**: 比较不同估计方法的结果
- **模型评估**: AIC/BIC信息准则、R²、残差分析
- **白噪声检验**: Ljung-Box检验验证模型充分性

## 📊 使用示例

### 基本分析流程

```python
from time_series_insight import TimeSeriesInsight
import pandas as pd

# 创建分析器
tsi = TimeSeriesInsight()

# 加载数据
data = pd.read_csv('your_data.csv')
tsi.load_data(data, date_column='date', value_column='value')

# 执行完整分析
results = tsi.analyze()

# 查看推荐模型
best_model = tsi.get_best_model()
print(f"推荐模型: ARIMA{best_model['order']}")
print(f"AIC: {best_model['evaluation']['fit_statistics']['aic']:.2f}")

# 生成预测
forecast_result = tsi.predict(steps=12)
forecast = forecast_result['forecast']

# 可视化分析
tsi.plot_analysis(save_dir='analysis_output/')
```

### 模型比较

```python
# 分析多个候选模型
results = tsi.analyze(n_models=5)

# 查看所有评估的模型
for model in results['model_evaluation']:
    order = model['order']
    aic = model['evaluation']['fit_statistics']['aic']
    r2 = model['evaluation']['fit_statistics']['r_squared']
    print(f"ARIMA{order}: AIC={aic:.2f}, R²={r2:.3f}")
```

### 导出结果

```python
# 导出完整分析结果
tsi.export_results('analysis_results.json', format='json')
tsi.export_results('analysis_results.xlsx', format='excel')

# 获取分析摘要
summary = tsi.get_summary()
```

## 🛠️ 技术栈

- **Python 3.9+**: 现代Python特性支持
- **pandas**: 数据处理和时间序列操作
- **numpy**: 数值计算
- **scipy**: 科学计算和统计检验
- **statsmodels**: 时间序列分析和ARIMA建模
- **matplotlib/seaborn**: 数据可视化
- **typer**: 现代命令行接口
- **rich**: 美观的终端输出

## 📁 项目结构

```
time-series-insight-assistant/
├── time_series_insight/          # 主包
│   ├── core/                     # 核心数据处理
│   ├── analysis/                 # 统计分析
│   ├── estimation/               # 参数估计
│   ├── evaluation/               # 模型评估
│   ├── visualization/            # 可视化
│   ├── cli/                      # 命令行接口
│   └── api.py                    # 高级API
├── tests/                        # 测试文件
├── examples/                     # 使用示例
└── docs/                         # 文档
```

## 🧪 运行测试

```bash
# 安装开发依赖
uv sync --dev

# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_api.py

# 运行测试并生成覆盖率报告
pytest --cov=time_series_insight --cov-report=html
```

## 📚 示例和教程

### 生成示例数据

```bash
cd examples
python sample_data.py
```

### 运行基本示例

```bash
cd examples
python basic_usage.py
```

### 命令行示例

```bash
# 分析ARIMA示例数据
tsia analyze examples/data/arima_sample.csv

# 分析季节性数据
tsia analyze examples/data/seasonal_sample.csv

# 分析股价数据
tsia analyze examples/data/stock_sample.csv --value-col price

# 保存分析结果到指定目录
tsia analyze data.csv --output results/ --save-plots
```

## 🔧 开发

### 环境设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/time-series-insight-assistant.git
cd time-series-insight-assistant

# 使用uv创建虚拟环境并安装依赖
uv sync --dev

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows
```

### 代码质量

```bash
# 代码格式化
black time_series_insight/
isort time_series_insight/

# 代码检查
flake8 time_series_insight/
mypy time_series_insight/

# 运行所有质量检查
pre-commit run --all-files
```

## 📈 性能特点

- **快速分析**: 优化的算法确保快速处理中等规模数据集（< 10,000点）
- **内存效率**: 流式处理大型数据集，避免内存溢出
- **并行计算**: 支持多模型并行评估
- **缓存机制**: 智能缓存中间结果，避免重复计算

## 🤝 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 贡献指南

- 遵循现有代码风格
- 添加适当的测试
- 更新相关文档
- 确保所有测试通过

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [statsmodels](https://www.statsmodels.org/) - 提供强大的统计建模功能
- [pandas](https://pandas.pydata.org/) - 优秀的数据处理库
- [matplotlib](https://matplotlib.org/) - 灵活的可视化工具
- [typer](https://typer.tiangolo.com/) - 现代命令行接口框架

## 📞 联系方式

- 项目主页: [https://github.com/zym9863/time-series-insight-assistant](https://github.com/zym9863/time-series-insight-assistant)
- 问题反馈: [Issues](https://github.com/zym9863/time-series-insight-assistant/issues)

## 🔮 路线图

- [ ] 支持更多时间序列模型（SARIMA、VAR等）
- [ ] 添加机器学习方法（LSTM、Prophet等）
- [ ] Web界面支持
- [ ] 实时数据流处理
- [ ] 多变量时间序列分析
- [ ] 异常检测功能

---

**如果这个项目对您有帮助，请给个 ⭐ Star！**