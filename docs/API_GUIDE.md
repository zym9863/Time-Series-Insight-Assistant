# 时间序列洞察助手 API 使用指南

## 概述

时间序列洞察助手 FastAPI 服务提供了完整的时间序列分析功能，包括数据上传、模型识别、参数估计、预测和可视化等功能。

## 快速开始

### 启动服务

#### 开发环境
```bash
# 使用Python脚本启动
python scripts/start_dev.py

# 或使用uv运行
uv run python scripts/start_dev.py

# 或使用脚本命令
./scripts/start.sh

# Windows用户
scripts/start.bat
```

#### 生产环境
```bash
# 使用Python脚本启动
python scripts/start_prod.py

# 或使用脚本启动
./scripts/start.sh prod
```

### 访问API文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API 端点概览

### 1. 数据上传 (`/api/v1/upload`)

#### 上传文件
```http
POST /api/v1/upload/file
Content-Type: multipart/form-data

file: [CSV/Excel文件]
date_column: "date" (可选)
value_column: "value" (可选)
date_format: "%Y-%m-%d" (可选)
```

#### 上传JSON数据
```http
POST /api/v1/upload/json
Content-Type: application/json

{
  "data": [
    {"date": "2023-01-01", "value": 100},
    {"date": "2023-01-02", "value": 105}
  ]
}
```

### 2. 时间序列分析 (`/api/v1/analysis`)

#### 执行完整分析
```http
POST /api/v1/analysis/{file_id}
Content-Type: application/json

{
  "auto_diff": true,
  "max_p": 5,
  "max_q": 5,
  "n_models": 3
}
```

#### 获取分析摘要
```http
GET /api/v1/analysis/{analysis_id}/summary
```

#### 进行预测
```http
POST /api/v1/analysis/{analysis_id}/predict
Content-Type: application/json

{
  "steps": 10,
  "alpha": 0.05
}
```

### 3. 模型操作 (`/api/v1/models`)

#### 识别推荐模型
```http
POST /api/v1/models/{file_id}/identify?max_p=5&max_q=5&max_d=2
```

#### 估计模型参数
```http
POST /api/v1/models/{file_id}/estimate?p=1&d=1&q=1&methods=mle
```

#### 评估模型性能
```http
POST /api/v1/models/{file_id}/evaluate?p=1&d=1&q=1
```

### 4. 可视化 (`/api/v1/visualization`)

#### 生成基础图表
```http
POST /api/v1/visualization/{file_id}/plots
Content-Type: application/json

{
  "plot_types": ["original", "acf_pacf"],
  "save_format": "png",
  "dpi": 300
}
```

#### 生成分析图表
```http
POST /api/v1/visualization/{analysis_id}/analysis-plots
```

## 使用示例

### Python客户端示例

```python
import requests
import pandas as pd
import json

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

# 1. 上传数据
def upload_data(file_path):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'date_column': 'date',
            'value_column': 'value'
        }
        response = requests.post(f"{BASE_URL}/upload/file", files=files, data=data)
    return response.json()

# 2. 执行分析
def analyze_data(file_id):
    analysis_request = {
        "auto_diff": True,
        "max_p": 5,
        "max_q": 5,
        "n_models": 3
    }
    response = requests.post(f"{BASE_URL}/analysis/{file_id}", json=analysis_request)
    return response.json()

# 3. 进行预测
def predict(analysis_id, steps=10):
    prediction_request = {
        "steps": steps,
        "alpha": 0.05
    }
    response = requests.post(f"{BASE_URL}/analysis/{analysis_id}/predict", json=prediction_request)
    return response.json()

# 4. 生成图表
def generate_plots(file_id):
    plot_request = {
        "plot_types": ["original", "acf_pacf"],
        "save_format": "png"
    }
    response = requests.post(f"{BASE_URL}/visualization/{file_id}/plots", json=plot_request)
    return response.json()

# 完整使用流程
if __name__ == "__main__":
    # 上传数据
    upload_result = upload_data("data.csv")
    file_id = upload_result["file_id"]
    print(f"文件上传成功，ID: {file_id}")
    
    # 执行分析
    analysis_result = analyze_data(file_id)
    analysis_id = analysis_result["analysis_id"]
    print(f"分析完成，ID: {analysis_id}")
    
    # 进行预测
    prediction_result = predict(analysis_id)
    print(f"预测完成，预测值: {prediction_result['forecast_values'][:5]}...")
    
    # 生成图表
    plot_result = generate_plots(file_id)
    print(f"图表生成完成: {plot_result['data']['plots']}")
```

### JavaScript客户端示例

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';

// 上传文件
async function uploadFile(file, dateColumn = 'date', valueColumn = 'value') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('date_column', dateColumn);
    formData.append('value_column', valueColumn);
    
    const response = await fetch(`${BASE_URL}/upload/file`, {
        method: 'POST',
        body: formData
    });
    
    return await response.json();
}

// 执行分析
async function analyzeData(fileId) {
    const analysisRequest = {
        auto_diff: true,
        max_p: 5,
        max_q: 5,
        n_models: 3
    };
    
    const response = await fetch(`${BASE_URL}/analysis/${fileId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(analysisRequest)
    });
    
    return await response.json();
}

// 进行预测
async function predict(analysisId, steps = 10) {
    const predictionRequest = {
        steps: steps,
        alpha: 0.05
    };
    
    const response = await fetch(`${BASE_URL}/analysis/${analysisId}/predict`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(predictionRequest)
    });
    
    return await response.json();
}
```

## 错误处理

API使用标准的HTTP状态码：

- `200`: 成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `422`: 请求验证失败
- `429`: 请求过于频繁
- `500`: 服务器内部错误

错误响应格式：
```json
{
  "error": "错误类型",
  "detail": "详细错误信息",
  "timestamp": "2024-01-01T12:00:00",
  "path": "/api/v1/analysis/123"
}
```

## 速率限制

API实施了速率限制：
- 默认：每分钟100次请求
- 响应头包含限制信息：
  - `X-RateLimit-Limit`: 限制次数
  - `X-RateLimit-Remaining`: 剩余次数
  - `X-RateLimit-Reset`: 重置时间

## 最佳实践

1. **数据格式**: 确保时间序列数据格式正确，包含日期和数值列
2. **文件大小**: 建议单个文件不超过10MB
3. **参数选择**: 根据数据特点选择合适的模型参数范围
4. **错误处理**: 始终检查API响应状态和错误信息
5. **资源清理**: 及时删除不需要的文件和分析结果

## 支持的文件格式

- **CSV**: `.csv`
- **Excel**: `.xlsx`, `.xls`
- **JSON**: 通过API直接上传

## 环境变量配置

```bash
# 服务配置
HOST=0.0.0.0
PORT=8000
WORKERS=4

# 环境设置
ENVIRONMENT=development  # 或 production

# 日志配置
LOG_LEVEL=INFO
```

## 部署说明

### Docker部署

创建 `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装uv
RUN pip install uv

# 复制项目文件
COPY . .

# 安装依赖
RUN uv sync

# 创建必要目录
RUN mkdir -p temp_files outputs logs

# 暴露端口
EXPOSE 8000

# 启动服务
CMD ["uv", "run", "python", "scripts/start_prod.py"]
```

### 使用Docker Compose

创建 `docker-compose.yml`:
```yaml
version: '3.8'
services:
  tsia-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - HOST=0.0.0.0
      - PORT=8000
    volumes:
      - ./outputs:/app/outputs
      - ./logs:/app/logs
```
