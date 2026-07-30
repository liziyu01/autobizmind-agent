"""
会话管理模块

负责从 Redis 中读取对话历史，实现多轮对话记忆功能。
"""
import json
import logging

from typing import List, Dict, Any

from certifi import contents
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

# Redis Key 前缀
SESSION_KEY_PREFIX = "session"

def get_session_key(session_id: str) -> str:
    """生成 Redis Key"""
    return f"{SESSION_KEY_PREFIX}:{session_id}:history"

# ============================================================
# 消息转换函数（LangChain Message ↔ 字典）
# ============================================================

# 消息转换（LangChain Message -> dict）
def message_to_dict(msg: BaseMessage) -> Dict[str, Any]:
    """
    将 LangChain Message 对象转为可 JSON 序列化的字典。

    HumanMessage(content="你好") → {"role": "user", "content": "你好"}
    """
    role_map = {
        "HumanMessage": "user",
        "AIMessage": "assistant",
        "SystemMessage": "system",
    }
    return {
        "role": role_map.get(type(msg).__name__, "unknown"),
        "content": msg.content
    }

# 消息转换（dict -> LangChain Message）
def dict_to_message(data: Dict[str, Any]) -> BaseMessage:
    """
    将字典恢复为 LangChain Message 对象。

    {"role": "user", "content": "你好"} → HumanMessage(content="你好")
    """
    role = data.get("role")
    content = data.get("content", "")

    if role == "user":
        return HumanMessage(content=content)
    elif role == "assistant":
        return AIMessage(content=content)
    elif role == "system":
        return SystemMessage(content=content)
    else:
        # 默认作 HumanMessage
        return HumanMessage(content=content)

# ============================================================
# 核心会话函数
# ============================================================
def get_history(session_id: str) -> List[Dict[str, Any]]:
    """
    从 Redis 读取某个会话的历史记录

    返回格式： 字典列表
    无历史，则返回空列表
    """
    key = get_session_key(session_id)
    raw = redis_client.get(key)

    if raw is None:
        return []

    # 如果存的是 JSON 字符串，尝试解析
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(f"会话历史格式异常：{session_id}")
            return []
    return []

def save_history(session_id: str, history: List[Dict[str, Any]]) -> bool:
    """
    将会话历史写入 Redis

    覆盖写入
    """
    key = get_session_key(session_id)
    # 转 JSON 字符串存储
    data = json.dumps(history, ensure_ascii=False)
    return redis_client.set(key, data)

def append_message(session_id: str, msg: BaseMessage) -> bool:
    """
    向会话历史中追加一条消息。

    流程： 读取历史 -> 追加新消息 -> 写回 Redis
    """
    history = get_history(session_id)
    history.append(message_to_dict(msg))
    return save_history(session_id, history)

def get_messages_from_history(session_id: str) -> List[BaseMessage]:
    """
    从 Redis 读取历史，转换为 LangChain Message 对象列表。

    方便直接注入 Agent 的 State
    """
    history = get_history(session_id)
    return [dict_to_message(item) for item in history]

def clear_history(session_id: str) -> bool:
    """清空会话历史"""
    key = get_session_key(session_id)
    return redis_client.delete(key) > 0

