"""
数据模型

用于校验 Fast API接口请求/响应校验
"""
from pydantic import BaseModel

class ChatRequest(BaseModel):
    """对话请求"""
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    """对话响应"""
    response: str
    session_id: str

class UploadResponse(BaseModel):
    """文档上传响应"""
    filename: str
    chunk_count: int          # 存入的文档片段数
    message: str


class SearchRequest(BaseModel):
    """检索测试请求"""
    query: str
    top_k: int = 3