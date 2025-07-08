"""
可视化相关API路由
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import uuid
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
from typing import List, Optional

from models.schemas import (
    VisualizationRequest,
    SuccessResponse,
    ErrorResponse
)
from routes.upload import get_data_store
from routes.analysis import analysis_results_store

router = APIRouter()


@router.post("/{file_id}/plots")
async def generate_plots(
    file_id: str,
    request: VisualizationRequest = VisualizationRequest()
):
    """
    为上传的数据生成可视化图表
    """
    try:
        # 获取上传的数据
        data_store = get_data_store()
        if file_id not in data_store:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        data_info = data_store[file_id]
        tsi = data_info["tsi"]
        
        # 创建输出目录
        output_dir = Path("outputs") / "plots" / file_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        generated_plots = []
        
        # 生成原始时间序列图
        if "original" in request.plot_types:
            plot_path = output_dir / f"original_series.{request.save_format}"
            fig = tsi.plotter.plot_time_series(
                tsi.data,
                title="原始时间序列",
                save_path=plot_path
            )
            plt.close(fig)
            generated_plots.append({
                "type": "original",
                "path": str(plot_path),
                "url": f"/outputs/plots/{file_id}/original_series.{request.save_format}"
            })
        
        # 生成ACF/PACF图
        if "acf_pacf" in request.plot_types:
            plot_path = output_dir / f"acf_pacf.{request.save_format}"
            # 需要先进行一些分析才能生成ACF/PACF图
            if hasattr(tsi, 'analysis_results') and tsi.analysis_results:
                analysis_data = tsi.analysis_results.get('differencing', {}).get('differenced_data', tsi.data)
            else:
                analysis_data = tsi.data
            
            fig = tsi.plotter.plot_acf_pacf(
                analysis_data,
                title="ACF和PACF分析",
                save_path=plot_path
            )
            plt.close(fig)
            generated_plots.append({
                "type": "acf_pacf",
                "path": str(plot_path),
                "url": f"/outputs/plots/{file_id}/acf_pacf.{request.save_format}"
            })
        
        return SuccessResponse(
            message="图表生成成功",
            data={
                "file_id": file_id,
                "plots": generated_plots,
                "output_directory": str(output_dir)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图表生成失败: {str(e)}")


@router.post("/{analysis_id}/analysis-plots")
async def generate_analysis_plots(
    analysis_id: str,
    request: VisualizationRequest = VisualizationRequest()
):
    """
    为分析结果生成完整的可视化图表
    """
    try:
        # 获取分析结果
        if analysis_id not in analysis_results_store:
            raise HTTPException(status_code=404, detail="分析结果不存在")
        
        analysis_info = analysis_results_store[analysis_id]
        tsi = analysis_info["tsi"]
        
        # 创建输出目录
        output_dir = Path("outputs") / "analysis_plots" / analysis_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成完整的分析图表
        plots_info = tsi.plot_analysis(save_dir=output_dir, show_plots=False)
        
        # 构建返回的图表信息
        generated_plots = []
        for plot_type, fig in plots_info.items():
            plot_path = output_dir / f"{plot_type}.{request.save_format}"
            if plot_path.exists():
                generated_plots.append({
                    "type": plot_type,
                    "path": str(plot_path),
                    "url": f"/outputs/analysis_plots/{analysis_id}/{plot_type}.{request.save_format}"
                })
        
        return SuccessResponse(
            message="分析图表生成成功",
            data={
                "analysis_id": analysis_id,
                "plots": generated_plots,
                "output_directory": str(output_dir)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析图表生成失败: {str(e)}")


@router.get("/plot/{file_id}/{plot_name}")
async def get_plot_file(file_id: str, plot_name: str):
    """
    获取生成的图表文件
    """
    try:
        # 构建文件路径
        plot_path = Path("outputs") / "plots" / file_id / plot_name
        
        if not plot_path.exists():
            # 尝试在分析图表目录中查找
            plot_path = Path("outputs") / "analysis_plots" / file_id / plot_name
        
        if not plot_path.exists():
            raise HTTPException(status_code=404, detail="图表文件不存在")
        
        # 确定媒体类型
        if plot_path.suffix.lower() == '.png':
            media_type = "image/png"
        elif plot_path.suffix.lower() == '.jpg' or plot_path.suffix.lower() == '.jpeg':
            media_type = "image/jpeg"
        elif plot_path.suffix.lower() == '.svg':
            media_type = "image/svg+xml"
        else:
            media_type = "application/octet-stream"
        
        return FileResponse(
            path=plot_path,
            media_type=media_type,
            filename=plot_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图表文件失败: {str(e)}")


@router.get("/list/{file_id}")
async def list_plots(file_id: str):
    """
    列出指定文件的所有图表
    """
    try:
        plots = []
        
        # 检查基本图表目录
        plots_dir = Path("outputs") / "plots" / file_id
        if plots_dir.exists():
            for plot_file in plots_dir.iterdir():
                if plot_file.is_file() and plot_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.svg']:
                    plots.append({
                        "name": plot_file.name,
                        "type": "basic",
                        "url": f"/api/v1/visualization/plot/{file_id}/{plot_file.name}",
                        "size": plot_file.stat().st_size
                    })
        
        # 检查分析图表目录
        analysis_plots_dir = Path("outputs") / "analysis_plots" / file_id
        if analysis_plots_dir.exists():
            for plot_file in analysis_plots_dir.iterdir():
                if plot_file.is_file() and plot_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.svg']:
                    plots.append({
                        "name": plot_file.name,
                        "type": "analysis",
                        "url": f"/api/v1/visualization/plot/{file_id}/{plot_file.name}",
                        "size": plot_file.stat().st_size
                    })
        
        return {"file_id": file_id, "plots": plots}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图表列表失败: {str(e)}")


@router.delete("/{file_id}/plots")
async def delete_plots(file_id: str):
    """
    删除指定文件的所有图表
    """
    try:
        import shutil
        deleted_dirs = []
        
        # 删除基本图表目录
        plots_dir = Path("outputs") / "plots" / file_id
        if plots_dir.exists():
            shutil.rmtree(plots_dir)
            deleted_dirs.append(str(plots_dir))
        
        # 删除分析图表目录
        analysis_plots_dir = Path("outputs") / "analysis_plots" / file_id
        if analysis_plots_dir.exists():
            shutil.rmtree(analysis_plots_dir)
            deleted_dirs.append(str(analysis_plots_dir))
        
        return SuccessResponse(
            message="图表删除成功",
            data={
                "file_id": file_id,
                "deleted_directories": deleted_dirs
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除图表失败: {str(e)}")


@router.get("/formats")
async def get_supported_formats():
    """
    获取支持的图表格式
    """
    return {
        "supported_formats": ["png", "jpg", "jpeg", "svg"],
        "default_format": "png",
        "recommended_dpi": [72, 150, 300, 600]
    }
