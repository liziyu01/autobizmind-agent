"""
FastAPI 应用入口

AutoBizMind 自适应业务决策Agent
"""
import os
import shutil
import logging
from typing import Optional
import tools.query_orders

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

from app.config import config
from app.redis_client import redis_client
from app.schemas import ChatResponse, ChatRequest, UploadResponse, SearchRequest, ToolChatRequest, ToolChatResponse
from app.agent import agent, agent_rag
from app.session_manager import get_messages_from_history, append_message
from app.vectordb import add_document, search_documents, get_kb_stats
from app.tool_agent import tool_agent
from app.tool_logger import get_tool_logs, get_tool_stats
from app.session_manager import get_session_stats, clear_history


from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger(__name__)

app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="基于 MCP 协议的自适应业务决策 Agent",
    docs_url="/docs",
    redoc_url="/redos"
)

# 上传文件临时目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
async def root():
    """
    根路径健康检查

    包含 Redis 连接状态监测
    """
    # 检测 Redis 状态
    redis_status = "connected" if redis_client.ping() else "disconnected"
    return {
        "service": config.APP_NAME,
        "version": config.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """
    详细健康检查

    包含 Redis 连接状态监测
    """
    # 检测 Redis 状态
    redis_status = "connected" if redis_client.ping() else "disconnected"

    return {
        "status": "healthy" if redis_status == "connected" else "degraded",
        "redis": redis_status,
        "llm": "ready"
    }

# 普通对话接口（无 RAG + 有 Redis)
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    普通对话接口（带 Redis 会话记忆）

    - 自动从 Redis 加载 session_id 历史
    - 对话结束后自动保存到 Redis
    - 支持多轮上下文应用
    """
    session_id = request.session_id
    try:
        # 从 Redis 加载历史消息 （LangChain Message 对象列表）
        history_messages = get_messages_from_history(session_id)

        # 构造状态: 历史消息 + 当前用户消息
        state = {
            "messages": history_messages + [HumanMessage(content=request.message)]
        }

        # 调用 Agent
        result = agent.invoke(state)

        # 提取 AI 回复
        last_msg = result["messages"][-1]
        reply = last_msg.content

        # 将本轮对话（用户消息 + AI 回复）写入 Redis
        append_message(session_id, HumanMessage(content=request.message))
        append_message(session_id, AIMessage(content=reply))

        # 返回响应
        return ChatResponse(
            response=reply,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# RAG 对话接口
@app.post("/chat/rag", response_model=ChatResponse)
async def chat_rag(request: ChatRequest):
    """
    RAG 增强对话（带知识库检索 + 会话记忆）

    从知识库中检索相关文档，再生成回答。
    """
    session_id = request.session_id

    try:
        # 1. 加载历史
        history_messages = get_messages_from_history(session_id)

        # 2. 构造状态（包含用户消息）
        state = {
            "messages": history_messages + [HumanMessage(content=request.message)]
        }

        # 3. 调用 RAG Agent（自动检索 + 生成）
        result = agent_rag.invoke(state)

        # 4. 提取回复
        last_message = result["messages"][-1]
        reply = last_message.content

        # 5. 保存历史
        append_message(session_id, HumanMessage(content=request.message))
        append_message(session_id, AIMessage(content=reply))

        return ChatResponse(response=reply, session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 文档上传接口
@app.post("/upload_doc", response_model=UploadResponse)
async def upload_document(
        file: UploadFile = File(...),
        collection: str = "knowledge_base"
):
    """
    上传文档到知识库。

    支持格式: PDF, Word (.docx), TXT
    文档会被自动切片并向量化存入 ChromaDB。
    """
    # 1. 验证文件格式
    allowed_extensions = [".pdf", ".docx", ".txt"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式。支持: {', '.join(allowed_extensions)}"
        )

    # 2. 保存临时文件
    temp_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"📁 文件已保存: {temp_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {e}")

    # 3. 添加到知识库
    try:
        chunk_count = add_document(temp_path, collection_name=collection)
    except Exception as e:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"文档处理失败: {e}")

    # 4. 清理临时文件
    if os.path.exists(temp_path):
        os.remove(temp_path)

    return UploadResponse(
        filename=file.filename,
        chunk_count=chunk_count,
        message=f"文档已成功导入，共 {chunk_count} 个片段"
    )

# 知识库统计接口
@app.get("/kb/stats")
async def kb_stats(collection: str = "knowledge_base"):
    """获取知识库统计信息"""
    try:
        stats = get_kb_stats(collection)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 检索测试接口
@app.post("/kb/search")
async def kb_search(request: SearchRequest):
    """
    测试知识库检索（不调用 LLM，只返回检索结果）
    """
    try:
        docs = search_documents(request.query, top_k=request.top_k)
        results = [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
            }
            for doc in docs
        ]
        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 工具管理接口
# ============================================================

from app.tool_registry import (
    get_all_tools_metadata,
    get_tool_metadata,
    call_tool,
    register_tool,
    clear_all_tools
)
from app.schemas import ToolCallRequest, ToolCallResponse, ToolRegisterRequest


@app.get("/tools")
async def list_tools():
    """列出所有已注册的工具"""
    tools = get_all_tools_metadata()
    return {
        "count": len(tools),
        "tools": tools
    }

@app.get("/tools/version")
async def get_tools_version():
    """获取当前工具注册中心版本号"""
    return {
        "version": get_registry_version(),
        "tool_count": len(get_all_tools_metadata())
    }

# ============================================================
#  日志接口
# ============================================================
@app.get("/tools/logs")
async def get_logs(tool_name: Optional[str] = None, limit: int = 50):
    """获取工具调用日志"""
    logs = get_tool_logs(tool_name, limit)
    return {
        "count": len(logs),
        "logs": logs
    }


@app.get("/tools/stats")
async def get_stats(tool_name: Optional[str] = None):
    """获取工具调用统计"""
    return get_tool_stats(tool_name)

@app.get("/tools/{tool_name}")
async def get_tool(tool_name: str):
    """获取单个工具的元数据"""
    meta = get_tool_metadata(tool_name)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"工具不存在: {tool_name}")
    return meta


@app.post("/tools/call")
async def call_tool_api(request: ToolCallRequest):
    """调用工具（供 Agent 使用）"""
    try:
        result = call_tool(request.tool_name, request.params)
        return {
            "tool": request.tool_name,
            "result": result,
            "status": "success"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"工具执行失败: {str(e)}")


@app.post("/tools/register")
async def register_tool_api(request: ToolRegisterRequest):
    """动态注册新工具（供热加载使用）"""
    # 注意：handler 无法通过 API 传递，需要在代码中预先定义
    success = register_tool(
        name=request.name,
        description=request.description,
        input_schema=request.input_schema
    )
    if success:
        return {"message": f"工具已注册: {request.name}"}
    else:
        raise HTTPException(status_code=500, detail="工具注册失败")

# ============================================================
# 工具调用对话接口
# ============================================================
@app.post("/chat/tool", response_model=ToolChatResponse)
async def chat_with_tools(request: ToolChatRequest):
    """
    工具调用对话接口（Agent 自动调用工具）

    支持：订单查询、数学计算、HTTP 请求、多轮链式调用
    """
    session_id = request.session_id

    try:
        history_messages = get_messages_from_history(session_id)

        state = {
            "messages": history_messages + [HumanMessage(content=request.message)]
        }

        result = tool_agent.invoke(state)

        messages = result.get("messages", [])
        if not messages:
            raise ValueError("Agent 未返回任何消息")

        last_msg = messages[-1]
        reply = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

        append_message(session_id, HumanMessage(content=request.message))
        for msg in messages:
            if isinstance(msg, AIMessage):
                append_message(session_id, msg)

        return ToolChatResponse(
            response=reply,
            session_id=session_id,
            tool_calls=len([m for m in messages if "工具" in m.content])
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
#  热加载接口
# ============================================================
from app.tool_registry import (
    get_all_tools_metadata,
    get_tool_metadata,
    call_tool,
    register_tool_dynamic,
    refresh_tools,
    get_registry_version,
    unregister_tool,
    clear_all_tools,
)
from app.schemas import ToolRegisterRequest, ToolRefreshResponse


@app.post("/tools/refresh")
async def refresh_tools_api():
    """
    刷新工具列表。

    重新从 Redis 加载工具元数据，让 Agent 感知新注册的工具。
    """
    result = refresh_tools()
    return {
        "message": "工具列表已刷新",
        "version": result["version"],
        "tool_count": result["tool_count"],
        "tools": result["tools"],
        "missing_handlers": result["missing_handlers"]
    }


@app.post("/tools/register_dynamic")
async def register_tool_dynamic_api(request: ToolRegisterRequest):
    """
    动态注册工具（元数据存入 Redis）。

    注意：handler 需要另外注入。如果提供 handler_code，
    会在当前进程中动态创建 handler（仅限开发环境）。
    """
    success = register_tool_dynamic(
        name=request.name,
        description=request.description,
        input_schema=request.input_schema,
        handler_code=request.handler_code
    )

    if success:
        return {
            "message": f"工具已注册: {request.name}",
            "name": request.name
        }
    else:
        raise HTTPException(status_code=500, detail="工具注册失败")


@app.delete("/tools/{tool_name}")
async def unregister_tool_api(tool_name: str):
    """删除已注册的工具"""
    success = unregister_tool(tool_name)
    if success:
        return {"message": f"工具已删除: {tool_name}"}
    else:
        raise HTTPException(status_code=404, detail=f"工具不存在: {tool_name}")

# ============================================================
#   会话统计接口
# ============================================================

@app.get("/session/{session_id}/stats")
async def session_stats(session_id: str):
    """获取会话统计信息（消息数、窗口使用率等）"""
    stats = get_session_stats(session_id)
    return stats


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """清空会话历史"""
    success = clear_history(session_id)
    if success:
        return {"message": f"会话 {session_id} 已清空"}
    else:
        raise HTTPException(status_code=500, detail="清空会话失败")

# 启动入口
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

