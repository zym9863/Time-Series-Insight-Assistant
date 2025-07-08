"""
数据上传相关API路由
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
import uuid
import json
from pathlib import Path
from typing import Optional, Dict, Any
import tempfile
import os

from models.schemas import (
    FileUploadResponse, 
    DataUploadRequest, 
    ErrorResponse,
    SuccessResponse
)
from time_series_insight import TimeSeriesInsight

router = APIRouter()

# 存储上传的数据
uploaded_data_store: Dict[str, Dict[str, Any]] = {}


@router.post("/file", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    date_column: Optional[str] = Form(None),
    value_column: Optional[str] = Form(None),
    date_format: Optional[str] = Form(None)
):
    """
    上传时间序列数据文件
    
    支持的文件格式：
    - CSV (.csv)
    - Excel (.xlsx, .xls)
    """
    try:
        # 验证文件格式
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ['.csv', '.xlsx', '.xls']:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件格式: {file_extension}。支持的格式: .csv, .xlsx, .xls"
            )
        
        # 生成文件ID
        file_id = str(uuid.uuid4())
        
        # 创建临时文件
        temp_dir = Path("temp_files")
        temp_dir.mkdir(exist_ok=True)
        temp_file_path = temp_dir / f"{file_id}{file_extension}"
        
        # 保存上传的文件
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 读取数据
        try:
            if file_extension == '.csv':
                df = pd.read_csv(temp_file_path)
            else:
                df = pd.read_excel(temp_file_path)
        except Exception as e:
            # 清理临时文件
            if temp_file_path.exists():
                temp_file_path.unlink()
            raise HTTPException(status_code=400, detail=f"文件读取失败: {str(e)}")
        
        # 数据预处理和验证
        tsi = TimeSeriesInsight()
        try:
            # 尝试加载数据
            series_data = tsi.load_data(
                df, 
                date_column=date_column,
                value_column=value_column,
                date_format=date_format
            )
            
            # 生成数据预览
            data_preview = {
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "head": df.head().to_dict('records'),
                "data_types": df.dtypes.astype(str).to_dict(),
                "series_info": {
                    "length": len(series_data),
                    "start": str(series_data.index[0]) if len(series_data) > 0 else None,
                    "end": str(series_data.index[-1]) if len(series_data) > 0 else None,
                    "mean": float(series_data.mean()),
                    "std": float(series_data.std()),
                    "min": float(series_data.min()),
                    "max": float(series_data.max())
                }
            }
            
            # 存储数据和TSI实例
            uploaded_data_store[file_id] = {
                "filename": file.filename,
                "file_path": str(temp_file_path),
                "tsi": tsi,
                "data": series_data,
                "original_df": df,
                "upload_params": {
                    "date_column": date_column,
                    "value_column": value_column,
                    "date_format": date_format
                }
            }
            
            return FileUploadResponse(
                filename=file.filename,
                file_id=file_id,
                data_preview=data_preview
            )
            
        except Exception as e:
            # 清理临时文件
            if temp_file_path.exists():
                temp_file_path.unlink()
            raise HTTPException(status_code=400, detail=f"数据处理失败: {str(e)}")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@router.post("/json", response_model=FileUploadResponse)
async def upload_json_data(
    data: Dict[str, Any],
    date_column: Optional[str] = None,
    value_column: Optional[str] = None,
    date_format: Optional[str] = None
):
    """
    上传JSON格式的时间序列数据
    """
    try:
        # 生成文件ID
        file_id = str(uuid.uuid4())
        
        # 将JSON数据转换为DataFrame
        if isinstance(data.get('data'), list):
            df = pd.DataFrame(data['data'])
        elif isinstance(data.get('data'), dict):
            df = pd.DataFrame([data['data']])
        else:
            df = pd.DataFrame(data)
        
        # 数据预处理
        tsi = TimeSeriesInsight()
        try:
            series_data = tsi.load_data(
                df,
                date_column=date_column,
                value_column=value_column,
                date_format=date_format
            )
            
            # 生成数据预览
            data_preview = {
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "head": df.head().to_dict('records'),
                "data_types": df.dtypes.astype(str).to_dict(),
                "series_info": {
                    "length": len(series_data),
                    "start": str(series_data.index[0]) if len(series_data) > 0 else None,
                    "end": str(series_data.index[-1]) if len(series_data) > 0 else None,
                    "mean": float(series_data.mean()),
                    "std": float(series_data.std()),
                    "min": float(series_data.min()),
                    "max": float(series_data.max())
                }
            }
            
            # 存储数据
            uploaded_data_store[file_id] = {
                "filename": "json_data.json",
                "file_path": None,
                "tsi": tsi,
                "data": series_data,
                "original_df": df,
                "upload_params": {
                    "date_column": date_column,
                    "value_column": value_column,
                    "date_format": date_format
                }
            }
            
            return FileUploadResponse(
                filename="json_data.json",
                file_id=file_id,
                data_preview=data_preview
            )
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"数据处理失败: {str(e)}")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@router.get("/list")
async def list_uploaded_files():
    """获取已上传文件列表"""
    files_info = []
    for file_id, info in uploaded_data_store.items():
        files_info.append({
            "file_id": file_id,
            "filename": info["filename"],
            "data_length": len(info["data"]),
            "upload_params": info["upload_params"]
        })
    
    return {"files": files_info}


@router.delete("/{file_id}")
async def delete_uploaded_file(file_id: str):
    """删除已上传的文件"""
    if file_id not in uploaded_data_store:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 删除临时文件
    file_info = uploaded_data_store[file_id]
    if file_info["file_path"] and Path(file_info["file_path"]).exists():
        Path(file_info["file_path"]).unlink()
    
    # 从存储中删除
    del uploaded_data_store[file_id]
    
    return SuccessResponse(message=f"文件 {file_id} 已删除")


def get_uploaded_data(file_id: str) -> Dict[str, Any]:
    """获取上传的数据（依赖注入函数）"""
    if file_id not in uploaded_data_store:
        raise HTTPException(status_code=404, detail="文件不存在")
    return uploaded_data_store[file_id]


# 导出数据存储，供其他模块使用
def get_data_store():
    """获取数据存储"""
    return uploaded_data_store
