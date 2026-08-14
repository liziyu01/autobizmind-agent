"""
会话管理模块

使用 Redis List 实现滑动窗口会话存储。
- 每条消息作为一个独立元素存储
- 自动裁剪，只保留最近 N 轮
- 支持高效的范围读取
"""
import json
import logging
from typing import List, Dict, Any

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from app.redis_client import redis_client
from app.config import config

logger = logging.getLogger(__name__)

# Redis Key 前缀
SESSION_KEY_PREFIX = "session"

# 窗口大小（轮数）
# 每轮包含 1 条用户消息 + 1 条 AI 消息 = 2 条消息
MAX_ROUNDS = config.MAX_HISTORY_ROUNDS
MAX_MESSAGES = MAX_ROUNDS * 2


def get_session_key(session_id: str) -> str:
    """生成会话在 Redis 中的 Key"""
    return f"{SESSION_KEY_PREFIX}:{session_id}:messages"


# ============================================================
# 消息序列化
# ============================================================

def message_to_dict(msg: BaseMessage) -> Dict[str, Any]:
    role_map = {
        "HumanMessage": "user",
        "AIMessage": "assistant",
        "SystemMessage": "system",
    }
    return {
        "role": role_map.get(type(msg).__name__, "unknown"),
        "content": msg.content
    }


def dict_to_message(data: Dict[str, Any]) -> BaseMessage:
    role = data.get("role")
    content = data.get("content", "")

    if role == "user":
        return HumanMessage(content=content)
    elif role == "assistant":
        return AIMessage(content=content)
    elif role == "system":
        return SystemMessage(content=content)
    else:
        return HumanMessage(content=content)


# ============================================================
# 核心：使用 Redis List 实现滑动窗口
# ============================================================

def append_message(session_id: str, msg: BaseMessage) -> bool:
    """
    向会话中追加一条消息（自动裁剪到窗口大小）。

    使用 Redis List 结构：
    - LPUSH: 将新消息插入列表头部（最新消息在最前）
    - LTRIM: 保留最近 N 条，删除超出部分
    - 读取时用 LRANGE 0 -1 获取全部，再反转（或直接按顺序）

    存储格式：列表中的每个元素是 JSON 序列化的消息字典。
    """
    key = get_session_key(session_id)

    # 将消息转为 JSON 字符串
    msg_dict = message_to_dict(msg)
    msg_json = json.dumps(msg_dict, ensure_ascii=False)

    try:
        # LPUSH: 将新消息插入列表头部（索引 0 是最新的）
        redis_client.client.lpush(key, msg_json)

        # LTRIM: 只保留列表前 MAX_MESSAGES 条（0 到 MAX_MESSAGES-1）
        # 超出部分自动删除
        redis_client.client.ltrim(key, 0, MAX_MESSAGES - 1)

        logger.info(f"💾 会话 {session_id} 追加消息，窗口大小: {MAX_MESSAGES} 条")
        return True

    except Exception as e:
        logger.error(f"❌ 会话追加失败 [{session_id}]: {e}")
        return False


def get_messages_from_history(session_id: str) -> List[BaseMessage]:
    """
    从 Redis 读取会话历史，转为 LangChain Message 对象列表。

    返回顺序：从旧到新（符合 LLM 的输入顺序）。
    Redis List 中索引 0 是最新消息，所以需要反转。
    """
    key = get_session_key(session_id)

    try:
        # LRANGE 0 -1 获取列表所有元素
        # 结果顺序：最新 → 最旧（因为 LPUSH 插入头部）
        raw_messages = redis_client.client.lrange(key, 0, -1)

        # 反转：最旧 → 最新
        raw_messages.reverse()

        result = []
        for raw in raw_messages:
            try:
                msg_dict = json.loads(raw)
                result.append(dict_to_message(msg_dict))
            except json.JSONDecodeError:
                logger.warning(f"跳过无效消息: {raw}")
                continue

        logger.info(f"📖 会话 {session_id} 加载 {len(result)} 条消息")
        return result

    except Exception as e:
        logger.error(f"❌ 会话读取失败 [{session_id}]: {e}")
        return []


def get_history(session_id: str) -> List[Dict[str, Any]]:
    """获取会话历史（字典列表格式，兼容旧接口）"""
    messages = get_messages_from_history(session_id)
    return [message_to_dict(msg) for msg in messages]


def get_session_stats(session_id: str) -> Dict[str, Any]:
    """获取会话统计信息"""
    key = get_session_key(session_id)
    try:
        count = redis_client.client.llen(key)
        return {
            "session_id": session_id,
            "message_count": count,
            "max_messages": MAX_MESSAGES,
            "max_rounds": MAX_ROUNDS,
            "usage_ratio": round(count / MAX_MESSAGES * 100, 2) if MAX_MESSAGES > 0 else 0
        }
    except Exception as e:
        return {"session_id": session_id, "error": str(e)}


def clear_history(session_id: str) -> bool:
    """清空会话历史"""
    key = get_session_key(session_id)
    try:
        redis_client.client.delete(key)
        logger.info(f"🗑️ 已清空会话: {session_id}")
        return True
    except Exception as e:
        logger.error(f"❌ 清空会话失败 [{session_id}]: {e}")
        return False