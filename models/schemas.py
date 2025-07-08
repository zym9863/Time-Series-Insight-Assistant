"""
Pydantic数据模型定义

定义API请求和响应的数据结构
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union, Tuple
from datetime import datetime
from enum import Enum


class AnalysisMethod(str, Enum):
    """分析方法枚举"""
    MOMENTS = "moments"
    MLE = "mle"
    BOTH = "both"


class FileFormat(str, Enum):
    """文件格式枚举"""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"


class AnalysisRequest(BaseModel):
    """分析请求模型"""
    auto_diff: bool = Field(True, description="是否自动差分")
    max_p: int = Field(5, ge=1, le=10, description="最大AR阶数")
    max_q: int = Field(5, ge=1, le=10, description="最大MA阶数")
    n_models: int = Field(3, ge=1, le=10, description="评估的模型数量")
    methods: List[AnalysisMethod] = Field([AnalysisMethod.BOTH], description="参数估计方法")


class DataUploadRequest(BaseModel):
    """数据上传请求模型"""
    date_column: Optional[str] = Field(None, description="日期列名")
    value_column: Optional[str] = Field(None, description="数值列名")
    date_format: Optional[str] = Field(None, description="日期格式")


class PredictionRequest(BaseModel):
    """预测请求模型"""
    steps: int = Field(10, ge=1, le=100, description="预测步数")
    alpha: float = Field(0.05, ge=0.01, le=0.5, description="置信水平")


class ModelOrder(BaseModel):
    """模型阶数"""
    p: int = Field(description="AR阶数")
    d: int = Field(description="差分阶数")
    q: int = Field(description="MA阶数")


class StatisticsInfo(BaseModel):
    """统计信息"""
    aic: float = Field(description="AIC信息准则")
    bic: float = Field(description="BIC信息准则")
    hqic: Optional[float] = Field(None, description="HQIC信息准则")
    r_squared: Optional[float] = Field(None, description="R平方")
    log_likelihood: Optional[float] = Field(None, description="对数似然")


class ModelInfo(BaseModel):
    """模型信息"""
    order: Tuple[int, int, int] = Field(description="模型阶数(p,d,q)")
    type: str = Field(description="模型类型")
    reasoning: Optional[str] = Field(None, description="推荐理由")
    confidence: Optional[float] = Field(None, description="置信度")


class StationarityResult(BaseModel):
    """平稳性检验结果"""
    is_stationary: bool = Field(description="是否平稳")
    interpretation: str = Field(description="结果解释")
    adf_pvalue: Optional[float] = Field(None, description="ADF检验p值")
    kpss_pvalue: Optional[float] = Field(None, description="KPSS检验p值")


class DifferencingInfo(BaseModel):
    """差分信息"""
    applied: bool = Field(description="是否应用差分")
    order: int = Field(description="差分阶数")


class ModelEvaluation(BaseModel):
    """模型评估结果"""
    order: Tuple[int, int, int] = Field(description="模型阶数")
    statistics: StatisticsInfo = Field(description="统计信息")
    adequacy_score: Optional[float] = Field(None, description="充分性得分")
    adequacy_level: Optional[str] = Field(None, description="充分性等级")


class AnalysisResult(BaseModel):
    """分析结果"""
    data_info: Dict[str, Any] = Field(description="数据信息")
    stationarity: StationarityResult = Field(description="平稳性检验结果")
    differencing: DifferencingInfo = Field(description="差分信息")
    recommended_models: List[ModelInfo] = Field(description="推荐模型列表")
    best_model: Optional[ModelEvaluation] = Field(None, description="最佳模型")
    analysis_id: str = Field(description="分析ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="分析时间")


class PredictionResult(BaseModel):
    """预测结果"""
    forecast_values: List[float] = Field(description="预测值")
    forecast_index: List[str] = Field(description="预测时间索引")
    confidence_intervals: Optional[List[List[float]]] = Field(None, description="置信区间")
    model_order: Tuple[int, int, int] = Field(description="使用的模型阶数")
    forecast_steps: int = Field(description="预测步数")


class VisualizationRequest(BaseModel):
    """可视化请求"""
    plot_types: List[str] = Field(
        ["original", "acf_pacf", "residuals"], 
        description="图表类型列表"
    )
    save_format: str = Field("png", description="保存格式")
    dpi: int = Field(300, ge=72, le=600, description="图像分辨率")


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(description="错误类型")
    detail: str = Field(description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误时间")


class SuccessResponse(BaseModel):
    """成功响应"""
    message: str = Field(description="成功消息")
    data: Optional[Dict[str, Any]] = Field(None, description="返回数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    filename: str = Field(description="文件名")
    file_id: str = Field(description="文件ID")
    data_preview: Dict[str, Any] = Field(description="数据预览")
    upload_time: datetime = Field(default_factory=datetime.now, description="上传时间")


class ExportRequest(BaseModel):
    """导出请求"""
    format: FileFormat = Field(FileFormat.JSON, description="导出格式")
    include_plots: bool = Field(True, description="是否包含图表")


# 响应模型的配置
class Config:
    """Pydantic配置"""
    json_encoders = {
        datetime: lambda v: v.isoformat()
    }
    schema_extra = {
        "example": {
            "message": "操作成功",
            "timestamp": "2024-01-01T12:00:00"
        }
    }
