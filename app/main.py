"""
FastAPI 应用入口

AutoBizMind 自适应业务决策Agent
"""
from fastapi import FastAPI, HTTPException
from langchain_core.messages import HumanMessage, AIMessage
from fastapi.responses import JSONResponse


from app.config import config
from app.redis_client import redis_client
from app.scheme import ChatResponse, ChatRequest
from app.agent import agent
from app.session_manager import get_messages_from_history, append_message

app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="基于 MCP 协议的自适应业务决策 Agent",
    docs_url="/docs",
    redoc_url="/redos"
)

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

# 对话接口
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    对话接口（带 Redis 会话记忆）

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

