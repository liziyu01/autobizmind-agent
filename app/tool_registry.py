"""
MCP 风格工具注册中心

基于 Redis 实现工具元数据的动态注册与发现。
"""
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

# Redis Key 前缀
TOOL_KEY_PREFIX = "tools"


def get_tool_key(tool_name: str) -> str:
    """生成工具在 Redis 中的 Key"""
    return f"{TOOL_KEY_PREFIX}:{tool_name}"

_handlers: Dict[str, Callable] = {}

def register_tool(
    name: str,
    description: str,
    input_schema: Dict[str, Any],
    handler: Callable = None
) -> bool:
    """
    注册一个工具到 Redis。

    Args:
        name: 工具名称（唯一标识）
        description: 工具功能描述（Agent 根据此描述决定是否调用）
        input_schema: 参数定义（JSON Schema 格式）
        handler: 工具的执行函数（暂存到内存中）

    Returns:
        是否注册成功
    """
    tool_meta = {
        "name": name,
        "description": description,
        "inputSchema": input_schema,
    }

    key = get_tool_key(name)
    # 存储元数据
    success = redis_client.set(key, tool_meta)

    if success:
        # 同时存储 handler 到内存字典（后续可扩展）
        if handler:
            _handlers[name] = handler
        logger.info(f"✅ 工具注册成功: {name}")
    else:
        logger.error(f"❌ 工具注册失败: {name}")

    return success


def get_tool_metadata(tool_name: str) -> Optional[Dict[str, Any]]:
    """获取单个工具的元数据"""
    key = get_tool_key(tool_name)
    return redis_client.get(key)


def get_all_tools_metadata() -> Dict[str, Dict[str, Any]]:
    """
    获取所有已注册工具的元数据。

    Returns:
        {tool_name: metadata, ...}
    """
    # 获取所有 tools:* 的 key
    keys = redis_client.client.keys(f"{TOOL_KEY_PREFIX}:*")  # 如 [tools:query_orders , tools:...]
    result = {}
    for key in keys:
        tool_name = key.replace(f"{TOOL_KEY_PREFIX}:", "")  # query_orders
        metadata = redis_client.get(key)  #  Dict[str, Any]
        if metadata:
            result[tool_name] = metadata
    return result


def get_tool_handler(tool_name: str) -> Optional[Callable]:
    """获取工具的执行函数"""
    return _handlers.get(tool_name)


def call_tool(tool_name: str, params: Dict[str, Any]) -> Any:
    """
    调用工具（根据名称和参数执行）。

    Args:
        tool_name: 工具名称
        params: 参数字典

    Returns:
        工具执行结果
    """
    handler = get_tool_handler(tool_name)
    if handler is None:
        raise ValueError(f"工具不存在或未注册: {tool_name}")

    try:
        return handler(**params)
    except Exception as e:
        logger.error(f"工具执行失败 [{tool_name}]: {e}")
        raise


def unregister_tool(tool_name: str) -> bool:
    """从 Redis 删除工具"""
    key = get_tool_key(tool_name)
    if tool_name in _handlers:
        del _handlers[tool_name]
    return redis_client.delete(key) > 0


def clear_all_tools() -> None:
    """清空所有工具（测试用）"""
    keys = redis_client.client.keys(f"{TOOL_KEY_PREFIX}:*")
    for key in keys:
        redis_client.delete(key)
    _handlers.clear()
    logger.info("🗑️ 已清空所有工具")
