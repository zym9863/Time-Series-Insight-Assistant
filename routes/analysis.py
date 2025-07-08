"""
时间序列分析相关API路由
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from models.schemas import (
    AnalysisRequest,
    AnalysisResult,
    PredictionRequest,
    PredictionResult,
    ErrorResponse,
    SuccessResponse,
    ExportRequest,
    ModelOrder,
    StatisticsInfo,
    ModelInfo,
    StationarityResult,
    DifferencingInfo,
    ModelEvaluation
)
from routes.upload import get_data_store
from time_series_insight import TimeSeriesInsight

router = APIRouter()

# 存储分析结果
analysis_results_store: Dict[str, Dict[str, Any]] = {}


@router.post("/{file_id}", response_model=AnalysisResult)
async def analyze_time_series(
    file_id: str,
    request: AnalysisRequest = AnalysisRequest()
):
    """
    对上传的时间序列数据进行完整分析
    """
    try:
        # 获取上传的数据
        data_store = get_data_store()
        if file_id not in data_store:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        data_info = data_store[file_id]
        tsi = data_info["tsi"]
        
        # 执行分析
        analysis_params = {
            "auto_diff": request.auto_diff,
            "max_p": request.max_p,
            "max_q": request.max_q,
            "n_models": request.n_models
        }
        
        results = tsi.analyze(**analysis_params)
        
        # 生成分析ID
        analysis_id = str(uuid.uuid4())
        
        # 转换结果格式
        analysis_result = _convert_analysis_results(results, analysis_id, tsi)
        
        # 存储分析结果
        analysis_results_store[analysis_id] = {
            "file_id": file_id,
            "tsi": tsi,
            "results": results,
            "analysis_params": analysis_params,
            "timestamp": datetime.now()
        }
        
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/{analysis_id}/summary")
async def get_analysis_summary(analysis_id: str):
    """获取分析摘要"""
    if analysis_id not in analysis_results_store:
        raise HTTPException(status_code=404, detail="分析结果不存在")
    
    try:
        analysis_info = analysis_results_store[analysis_id]
        tsi = analysis_info["tsi"]
        summary = tsi.get_summary()
        
        return {"summary": summary, "analysis_id": analysis_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取摘要失败: {str(e)}")


@router.post("/{analysis_id}/predict", response_model=PredictionResult)
async def predict_time_series(
    analysis_id: str,
    request: PredictionRequest = PredictionRequest()
):
    """
    使用分析结果进行时间序列预测
    """
    if analysis_id not in analysis_results_store:
        raise HTTPException(status_code=404, detail="分析结果不存在")
    
    try:
        analysis_info = analysis_results_store[analysis_id]
        tsi = analysis_info["tsi"]
        
        # 执行预测
        prediction_result = tsi.predict(steps=request.steps, alpha=request.alpha)
        
        # 转换预测结果格式
        forecast_values = prediction_result["forecast"].tolist()
        forecast_index = [str(idx) for idx in prediction_result["forecast"].index]
        
        confidence_intervals = None
        if prediction_result.get("confidence_intervals") is not None:
            confidence_intervals = prediction_result["confidence_intervals"].tolist()
        
        return PredictionResult(
            forecast_values=forecast_values,
            forecast_index=forecast_index,
            confidence_intervals=confidence_intervals,
            model_order=prediction_result["model_order"],
            forecast_steps=prediction_result["forecast_steps"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预测失败: {str(e)}")


@router.post("/{analysis_id}/export")
async def export_analysis_results(
    analysis_id: str,
    request: ExportRequest = ExportRequest()
):
    """
    导出分析结果
    """
    if analysis_id not in analysis_results_store:
        raise HTTPException(status_code=404, detail="分析结果不存在")
    
    try:
        analysis_info = analysis_results_store[analysis_id]
        tsi = analysis_info["tsi"]
        
        # 创建导出目录
        export_dir = Path("outputs") / analysis_id
        export_dir.mkdir(exist_ok=True)
        
        # 导出文件路径
        file_extension = request.format.value
        export_file = export_dir / f"analysis_results.{file_extension}"
        
        # 导出结果
        tsi.export_results(export_file, format=file_extension)
        
        # 如果需要包含图表
        if request.include_plots:
            plot_dir = export_dir / "plots"
            plot_dir.mkdir(exist_ok=True)
            tsi.plot_analysis(save_dir=plot_dir, show_plots=False)
        
        return SuccessResponse(
            message="导出成功",
            data={
                "export_path": str(export_file),
                "analysis_id": analysis_id,
                "format": file_extension,
                "include_plots": request.include_plots
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/list")
async def list_analysis_results():
    """获取所有分析结果列表"""
    results_list = []
    for analysis_id, info in analysis_results_store.items():
        results_list.append({
            "analysis_id": analysis_id,
            "file_id": info["file_id"],
            "timestamp": info["timestamp"].isoformat(),
            "analysis_params": info["analysis_params"]
        })
    
    return {"analyses": results_list}


@router.delete("/{analysis_id}")
async def delete_analysis_result(analysis_id: str):
    """删除分析结果"""
    if analysis_id not in analysis_results_store:
        raise HTTPException(status_code=404, detail="分析结果不存在")
    
    # 删除存储的结果
    del analysis_results_store[analysis_id]
    
    # 删除导出文件（如果存在）
    export_dir = Path("outputs") / analysis_id
    if export_dir.exists():
        import shutil
        shutil.rmtree(export_dir, ignore_errors=True)
    
    return SuccessResponse(message=f"分析结果 {analysis_id} 已删除")


def _convert_analysis_results(results: Dict[str, Any], analysis_id: str, tsi: TimeSeriesInsight) -> AnalysisResult:
    """转换分析结果格式"""
    
    # 数据信息
    data_info = {
        "length": len(tsi.data),
        "start": str(tsi.data.index[0]) if len(tsi.data) > 0 else None,
        "end": str(tsi.data.index[-1]) if len(tsi.data) > 0 else None,
        "mean": float(tsi.data.mean()),
        "std": float(tsi.data.std()),
        "min": float(tsi.data.min()),
        "max": float(tsi.data.max())
    }
    
    # 平稳性结果
    stationarity_info = results.get("stationarity", {}).get("overall", {})
    stationarity = StationarityResult(
        is_stationary=stationarity_info.get("is_stationary", False),
        interpretation=stationarity_info.get("interpretation", ""),
        adf_pvalue=results.get("stationarity", {}).get("adf", {}).get("p_value"),
        kpss_pvalue=results.get("stationarity", {}).get("kpss", {}).get("p_value")
    )
    
    # 差分信息
    diff_info = results.get("differencing", {})
    differencing = DifferencingInfo(
        applied=diff_info.get("applied", False),
        order=diff_info.get("order", 0)
    )
    
    # 推荐模型
    recommended_models = []
    for model in results.get("model_identification", {}).get("recommended_models", []):
        recommended_models.append(ModelInfo(
            order=model["order"],
            type=model.get("type", f"ARIMA{model['order']}"),
            reasoning=model.get("reasoning"),
            confidence=model.get("confidence")
        ))
    
    # 最佳模型
    best_model = None
    if "best_model" in results:
        best_model_info = results["best_model"]
        eval_stats = best_model_info["evaluation"]["fit_statistics"]
        adequacy = best_model_info["evaluation"]["model_adequacy"]
        
        best_model = ModelEvaluation(
            order=best_model_info["order"],
            statistics=StatisticsInfo(
                aic=eval_stats["aic"],
                bic=eval_stats["bic"],
                hqic=eval_stats.get("hqic"),
                r_squared=eval_stats.get("r_squared"),
                log_likelihood=eval_stats.get("log_likelihood")
            ),
            adequacy_score=adequacy.get("score"),
            adequacy_level=adequacy.get("level")
        )
    
    return AnalysisResult(
        data_info=data_info,
        stationarity=stationarity,
        differencing=differencing,
        recommended_models=recommended_models,
        best_model=best_model,
        analysis_id=analysis_id
    )
