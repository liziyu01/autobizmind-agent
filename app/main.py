"""
FastAPI 应用入口

AutoBizMind 自适应业务决策Agent
"""
from fastapi import FastAPI
from app.config import config

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
    """
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
    """
    return {
        "status": "healthy",
        "redis": "",
        "llm": ""
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )