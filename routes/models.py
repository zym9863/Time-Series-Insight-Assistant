"""
模型相关API路由
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Tuple, Dict, Any
import uuid

from models.schemas import (
    ModelOrder,
    AnalysisRequest,
    SuccessResponse,
    ErrorResponse,
    StatisticsInfo,
    ModelInfo
)
from routes.upload import get_data_store
from routes.analysis import analysis_results_store
from time_series_insight import TimeSeriesInsight

router = APIRouter()


@router.post("/{file_id}/identify")
async def identify_models(
    file_id: str,
    max_p: int = Query(5, ge=1, le=10, description="最大AR阶数"),
    max_q: int = Query(5, ge=1, le=10, description="最大MA阶数"),
    max_d: int = Query(2, ge=0, le=3, description="最大差分阶数")
):
    """
    为指定数据识别推荐的ARIMA模型
    """
    try:
        # 获取上传的数据
        data_store = get_data_store()
        if file_id not in data_store:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        data_info = data_store[file_id]
        tsi = data_info["tsi"]
        
        # 检查平稳性并确定差分阶数
        stationarity_result = tsi.processor.check_stationarity()
        
        if not tsi.processor.is_stationary:
            # 自动差分
            diff_data, diff_order = tsi.processor.auto_difference()
            d = min(diff_order, max_d)
        else:
            diff_data = tsi.data
            d = 0
        
        # 识别模型
        recommended_models = tsi.identifier.identify_arima_order(
            diff_data, max_p=max_p, max_q=max_q, d=d
        )
        
        # 转换格式
        models_list = []
        for model in recommended_models:
            models_list.append({
                "order": model["order"],
                "type": model.get("type", f"ARIMA{model['order']}"),
                "reasoning": model.get("reasoning", ""),
                "confidence": model.get("confidence", 0.0)
            })
        
        return {
            "file_id": file_id,
            "stationarity": {
                "is_stationary": stationarity_result["overall"]["is_stationary"],
                "interpretation": stationarity_result["overall"]["interpretation"]
            },
            "differencing_order": d,
            "recommended_models": models_list,
            "search_parameters": {
                "max_p": max_p,
                "max_q": max_q,
                "max_d": max_d
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型识别失败: {str(e)}")


@router.post("/{file_id}/estimate")
async def estimate_parameters(
    file_id: str,
    p: int = Query(description="AR阶数"),
    d: int = Query(description="差分阶数"),
    q: int = Query(description="MA阶数"),
    methods: List[str] = Query(["mle"], description="估计方法")
):
    """
    为指定模型估计参数
    """
    try:
        # 获取上传的数据
        data_store = get_data_store()
        if file_id not in data_store:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        data_info = data_store[file_id]
        tsi = data_info["tsi"]
        
        # 验证参数
        if p < 0 or d < 0 or q < 0:
            raise HTTPException(status_code=400, detail="模型阶数不能为负数")
        
        if p > 10 or d > 3 or q > 10:
            raise HTTPException(status_code=400, detail="模型阶数过大")
        
        # 估计参数
        order = (p, d, q)
        estimation_results = tsi.estimator.estimate_parameters(
            tsi.data, order, methods=methods
        )
        
        # 转换结果格式
        formatted_results = {}
        for method, result in estimation_results.items():
            if result.get("success", False):
                formatted_results[method] = {
                    "success": True,
                    "parameters": result.get("parameters", {}),
                    "standard_errors": result.get("standard_errors", {}),
                    "statistics": result.get("statistics", {}),
                    "method_info": result.get("method", "")
                }
            else:
                formatted_results[method] = {
                    "success": False,
                    "error": result.get("error", "估计失败")
                }
        
        return {
            "file_id": file_id,
            "model_order": order,
            "estimation_results": formatted_results,
            "methods_used": methods
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"参数估计失败: {str(e)}")


@router.post("/{file_id}/evaluate")
async def evaluate_model(
    file_id: str,
    p: int = Query(description="AR阶数"),
    d: int = Query(description="差分阶数"),
    q: int = Query(description="MA阶数")
):
    """
    评估指定模型的性能
    """
    try:
        # 获取上传的数据
        data_store = get_data_store()
        if file_id not in data_store:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        data_info = data_store[file_id]
        tsi = data_info["tsi"]
        
        # 验证参数
        if p < 0 or d < 0 or q < 0:
            raise HTTPException(status_code=400, detail="模型阶数不能为负数")
        
        order = (p, d, q)
        
        # 评估模型
        evaluation_result = tsi.evaluator.generate_evaluation_report(tsi.data, order)
        
        if not evaluation_result.get("success", False):
            raise HTTPException(
                status_code=400, 
                detail=f"模型评估失败: {evaluation_result.get('error', '未知错误')}"
            )
        
        # 格式化结果
        fit_stats = evaluation_result["fit_statistics"]
        adequacy = evaluation_result["model_adequacy"]
        
        return {
            "file_id": file_id,
            "model_order": order,
            "evaluation": {
                "fit_statistics": {
                    "aic": fit_stats["aic"],
                    "bic": fit_stats["bic"],
                    "hqic": fit_stats.get("hqic"),
                    "r_squared": fit_stats.get("r_squared"),
                    "log_likelihood": fit_stats.get("log_likelihood"),
                    "mse": fit_stats.get("mse"),
                    "rmse": fit_stats.get("rmse")
                },
                "model_adequacy": {
                    "score": adequacy["score"],
                    "level": adequacy["level"],
                    "ljung_box_pvalue": adequacy.get("ljung_box_pvalue"),
                    "interpretation": adequacy.get("interpretation")
                },
                "residual_analysis": evaluation_result.get("residual_analysis", {}),
                "success": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型评估失败: {str(e)}")


@router.post("/{file_id}/compare")
async def compare_models(
    file_id: str,
    models: List[Dict[str, int]]
):
    """
    比较多个模型的性能
    
    models格式: [{"p": 1, "d": 1, "q": 1}, {"p": 2, "d": 1, "q": 0}, ...]
    """
    try:
        # 获取上传的数据
        data_store = get_data_store()
        if file_id not in data_store:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        data_info = data_store[file_id]
        tsi = data_info["tsi"]
        
        if len(models) > 10:
            raise HTTPException(status_code=400, detail="最多只能比较10个模型")
        
        comparison_results = []
        
        for model_spec in models:
            try:
                p = model_spec.get("p", 0)
                d = model_spec.get("d", 0)
                q = model_spec.get("q", 0)
                order = (p, d, q)
                
                # 评估模型
                evaluation_result = tsi.evaluator.generate_evaluation_report(tsi.data, order)
                
                if evaluation_result.get("success", False):
                    fit_stats = evaluation_result["fit_statistics"]
                    adequacy = evaluation_result["model_adequacy"]
                    
                    comparison_results.append({
                        "order": order,
                        "model_type": f"ARIMA{order}",
                        "aic": fit_stats["aic"],
                        "bic": fit_stats["bic"],
                        "r_squared": fit_stats.get("r_squared"),
                        "adequacy_score": adequacy["score"],
                        "adequacy_level": adequacy["level"],
                        "success": True
                    })
                else:
                    comparison_results.append({
                        "order": order,
                        "model_type": f"ARIMA{order}",
                        "success": False,
                        "error": evaluation_result.get("error", "评估失败")
                    })
                    
            except Exception as e:
                comparison_results.append({
                    "order": (model_spec.get("p", 0), model_spec.get("d", 0), model_spec.get("q", 0)),
                    "success": False,
                    "error": str(e)
                })
        
        # 找出最佳模型（基于AIC）
        successful_models = [m for m in comparison_results if m.get("success", False)]
        best_model = None
        if successful_models:
            best_model = min(successful_models, key=lambda x: x["aic"])
        
        return {
            "file_id": file_id,
            "comparison_results": comparison_results,
            "best_model": best_model,
            "total_models": len(models),
            "successful_evaluations": len(successful_models)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型比较失败: {str(e)}")


@router.get("/info")
async def get_model_info():
    """
    获取支持的模型信息
    """
    return {
        "supported_models": ["ARIMA", "AR", "MA"],
        "parameter_ranges": {
            "p": {"min": 0, "max": 10, "description": "AR阶数"},
            "d": {"min": 0, "max": 3, "description": "差分阶数"},
            "q": {"min": 0, "max": 10, "description": "MA阶数"}
        },
        "estimation_methods": ["moments", "mle"],
        "evaluation_criteria": ["AIC", "BIC", "HQIC", "R²", "Ljung-Box检验"]
    }
