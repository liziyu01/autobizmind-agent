"""
数据模型

用于校验 Fast API接口请求/响应校验
"""
from pydantic import BaseModel
from typing import Any, Dict, List, Optional


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

# ============================================================
# 工具相关数据模型
# ============================================================
class SearchRequest(BaseModel):
    """检索测试请求"""
    query: str
    top_k: int = 3

class ToolCallRequest(BaseModel):
    """工具调用请求"""
    tool_name: str
    params: Dict[str, Any] = {}


class ToolCallResponse(BaseModel):
    """工具调用响应"""
    tool: str
    result: Any
    status: str


class ToolRegisterRequest(BaseModel):
    """工具注册请求"""
    name: str
    description: str
    input_schema: Dict[str, Any]

class ToolChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ToolChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls: int = 0

class ToolRegisterRequest(BaseModel):
    """工具注册   请求（热加载用）"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler_code: Optional[str] = None  # Python 代码字符串（仅开发环境）


class ToolRefreshResponse(BaseModel):
    """工具刷新响应"""
    message: str
    version: int
    tool_count: int
    tools: List[str]
    missing_handlers: List[str]