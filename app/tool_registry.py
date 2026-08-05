"""
MCP 风格工具注册中心

基于 Redis 实现工具元数据的动态注册与发现
热加载支持（工具刷新、动态注册）
"""
import json
import logging
from typing import Dict, Any, Optional, Callable, List

from app.redis_client import redis_client

logger = logging.getLogger(__name__)

TOOL_KEY_PREFIX = "tools"

# ============================================================
# 内存存储（工具执行函数 + 工具注册时间戳）
# ============================================================

_handlers: Dict[str, Callable] = {}
_handler_registry_version: int = 0  # 版本号，用于检测变更


def get_tool_key(tool_name: str) -> str:
    return f"{TOOL_KEY_PREFIX}:{tool_name}"


def register_tool(
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable = None
) -> bool:
    """注册工具到 Redis（已存在则覆盖）"""
    tool_meta = {
        "name": name,
        "description": description,
        "inputSchema": input_schema,
    }

    key = get_tool_key(name)
    success = redis_client.set(key, tool_meta)

    if success and handler:
        _handlers[name] = handler
        # 版本号递增，触发刷新
        global _handler_registry_version
        _handler_registry_version += 1
        logger.info(f"✅ 工具注册成功: {name} (版本: {_handler_registry_version})")

    return success


def get_tool_metadata(tool_name: str) -> Optional[Dict[str, Any]]:
    """获取单个工具元数据（实时从 Redis 读取）"""
    key = get_tool_key(tool_name)
    return redis_client.get(key)


def get_all_tools_metadata() -> Dict[str, Dict[str, Any]]:
    """获取所有工具元数据（实时从 Redis 读取）"""
    keys = redis_client.client.keys(f"{TOOL_KEY_PREFIX}:*")
    result = {}
    for key in keys:
        tool_name = key.replace(f"{TOOL_KEY_PREFIX}:", "")
        metadata = redis_client.get(key)
        if metadata:
            result[tool_name] = metadata
    return result


def get_tool_handler(tool_name: str) -> Optional[Callable]:
    """获取工具执行函数"""
    return _handlers.get(tool_name)


def call_tool(tool_name: str, params: Dict[str, Any]) -> Any:
    """调用工具"""
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
    global _handler_registry_version
    _handler_registry_version += 1
    return redis_client.delete(key) > 0


# ============================================================
# 新增：热加载核心功能（Day 12）
# ============================================================

def refresh_tools() -> Dict[str, Any]:
    """
    刷新工具注册中心。

    功能：
    1. 检查版本号，判断是否有变更
    2. 重新从 Redis 加载工具元数据（元数据本身是实时读取的）
    3. 返回当前状态供调用方确认

    Returns:
        {
            "version": 当前版本号,
            "tool_count": 工具数量,
            "tools": 工具名称列表
        }
    """
    global _handler_registry_version

    tools = get_all_tools_metadata()

    # 检查是否有 handler 缺失（注册了新工具但 handler 还没注册）
    # 注意：handler 需要通过代码或动态注册方式添加
    missing_handlers = []
    for name in tools.keys():
        if name not in _handlers:
            missing_handlers.append(name)

    logger.info(f"🔄 刷新工具列表: 共 {len(tools)} 个工具")
    if missing_handlers:
        logger.warning(f"⚠️ 以下工具缺少 handler: {missing_handlers}")

    return {
        "version": _handler_registry_version,
        "tool_count": len(tools),
        "tools": list(tools.keys()),
        "missing_handlers": missing_handlers
    }


def get_registry_version() -> int:
    """获取当前注册中心版本号"""
    return _handler_registry_version


# ============================================================
# 新增：动态注册工具（通过 API 调用）
# ============================================================

def register_tool_dynamic(
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler_code: Optional[str] = None
) -> bool:
    """
    动态注册工具（用于热加载 API）。

    注意：handler 需要通过代码方式预先定义，或通过其他机制注入。
    如果 handler_code 提供，会尝试 eval 执行（仅限信任环境）。
    """
    # 元数据写入 Redis
    tool_meta = {
        "name": name,
        "description": description,
        "inputSchema": input_schema,
    }

    key = get_tool_key(name)
    success = redis_client.set(key, tool_meta)

    if success:
        global _handler_registry_version
        _handler_registry_version += 1
        logger.info(f"📦 动态注册工具元数据: {name}")

        # 如果有 handler_code，尝试注入（仅限开发环境）
        if handler_code:
            try:
                # 创建安全环境执行 handler 定义
                # ⚠️ 仅用于开发/信任环境，生产环境需严格限制
                local_ns = {}
                exec(handler_code, {"__builtins__": {}}, local_ns)
                if name in local_ns:
                    _handlers[name] = local_ns[name]
                    logger.info(f"✅ 动态注册 handler: {name}")
            except Exception as e:
                logger.error(f"❌ 动态 handler 注入失败: {e}")

    return success


def clear_all_tools() -> None:
    """清空所有工具"""
    keys = redis_client.client.keys(f"{TOOL_KEY_PREFIX}:*")
    for key in keys:
        redis_client.delete(key)
    _handlers.clear()
    global _handler_registry_version
    _handler_registry_version += 1
    logger.info("🗑️ 已清空所有工具")