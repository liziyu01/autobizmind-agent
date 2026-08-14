"""
MCP 风格工具注册中心

基于 Redis 实现工具元数据的动态注册与发现
热加载支持（工具刷新、动态注册）
"""
import json
import time
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List, Union

from app.redis_client import redis_client
from app.tool_logger import log_tool_call

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

# ============================================================
# 升级函数 -> 升级后  call_tool_v2
# ============================================================
# def call_tool(tool_name: str, params: Dict[str, Any]) -> Any:
#     """调用工具"""
#     handler = get_tool_handler(tool_name)
#     if handler is None:
#         raise ValueError(f"工具不存在或未注册: {tool_name}")
#
#     try:
#         return handler(**params)
#     except Exception as e:
#         logger.error(f"工具执行失败 [{tool_name}]: {e}")
#         raise

# ============================================================
# 增强：工具调用（支持结构化错误返回）
# ============================================================

class ToolCallResult:
    """
    工具调用结果封装。

    统一工具调用的返回格式，让 Agent 能区分「成功」和「失败」。
    """

    def __init__(
            self,
            success: bool,
            data: Any = None,
            error: Optional[str] = None,
            error_type: Optional[str] = None,
            duration_ms: float = 0
    ):
        self.success = success
        self.data = data
        self.error = error
        self.error_type = error_type
        self.duration_ms = duration_ms

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，便于 JSON 序列化和 Agent 理解"""
        return {
            "success": self.success,
            "data": self.data if self.success else None,
            "error": self.error if not self.success else None,
            "error_type": self.error_type if not self.success else None,
            "duration_ms": round(self.duration_ms, 2)
        }

    def __repr__(self):
        if self.success:
            return f"ToolCallResult(success=True, data={self.data})"
        else:
            return f"ToolCallResult(success=False, error={self.error})"


def call_tool_v2(
        tool_name: str,
        params: Dict[str, Any],
        max_retries: int = 2,
        retry_delay: float = 0.5
) -> ToolCallResult:
    """
    增强版工具调用（支持重试 + 结构化错误返回）。

    Args:
        tool_name: 工具名称
        params: 参数字典
        max_retries: 最大重试次数（临时性错误自动重试）
        retry_delay: 重试间隔（秒）

    Returns:
        ToolCallResult 对象（包含成功/失败状态和数据/错误信息）
    """
    start_time = time.time()
    handler = get_tool_handler(tool_name)  # 注意：这里用的是 get_tool_handler

    if handler is None:
        duration_ms = (time.time() - start_time) * 1000
        log_tool_call(
            tool_name=tool_name,
            params=params,
            success=False,
            result=None,
            error=f"工具 '{tool_name}' 不存在或未注册",
            error_type="NOT_FOUND",
            duration_ms=duration_ms
        )
        return ToolCallResult(
            success=False,
            error=f"工具 '{tool_name}' 不存在或未注册",
            error_type="NOT_FOUND",
            duration_ms=(time.time() - start_time) * 1000
        )

    last_error = None
    last_error_type = None

    for attempt in range(max_retries + 1):
        try:
            # 执行工具
            result = handler(**params)

            duration_ms = (time.time() - start_time) * 1000

            # 如果工具本身返回了错误格式（业务错误）
            if isinstance(result, dict) and result.get("_error"):
                log_tool_call(
                    tool_name=tool_name,
                    params=params,
                    success=False,
                    result=None,
                    error=result.get("_error"),
                    error_type="BUSINESS_ERROR",
                    duration_ms=duration_ms
                )
                return ToolCallResult(
                    success=False,
                    error=result.get("_error"),
                    error_type="BUSINESS_ERROR",
                    duration_ms=duration_ms
                )

            log_tool_call(
                tool_name=tool_name,
                params=params,
                success=True,
                result=result,
                error=None,
                error_type=None,
                duration_ms=duration_ms
            )

            return ToolCallResult(
                success=True,
                data=result,
                duration_ms=duration_ms
            )

        except ValueError as e:
            # 参数错误 → 不重试
            last_error = str(e)
            last_error_type = "PARAM_ERROR"
            break

        except (ConnectionError, TimeoutError) as e:
            # 网络/超时错误 → 可重试
            last_error = str(e)
            last_error_type = "NETWORK_ERROR"
            if attempt < max_retries:
                logger.warning(f"⏳ 工具 {tool_name} 第 {attempt + 1} 次重试: {e}")
                time.sleep(retry_delay)
                continue
            break

        except Exception as e:
            # 其他未知错误 → 不重试
            last_error = str(e)
            last_error_type = "UNKNOWN_ERROR"
            logger.error(f"❌ 工具 {tool_name} 执行异常: {e}\n{traceback.format_exc()}")
            break

    duration_ms = (time.time() - start_time) * 1000

    # 记录日志
    log_tool_call(
        tool_name=tool_name,
        params=params,
        success=False,
        result=None,
        error=last_error or "未知错误",
        error_type=last_error_type or "UNKNOWN_ERROR",
        duration_ms=duration_ms
    )

    return  ToolCallResult(
        success=False,
        error=last_error or "未知错误",
        error_type=last_error_type or "UNKNOWN_ERROR",
        duration_ms=duration_ms
    )

# 兼容旧接口
def call_tool(tool_name: str, params: Dict[str, Any]) -> Any:
    """
    兼容旧版调用接口（直接返回数据或抛出异常）。
    新代码使用 call_tool_v2。
    """
    result = call_tool_v2(tool_name, params)
    if result.success:
        return result.data
    else:
        raise RuntimeError(f"工具调用失败 [{result.error_type}]: {result.error}")


def unregister_tool(tool_name: str) -> bool:
    """从 Redis 删除工具"""
    key = get_tool_key(tool_name)
    if tool_name in _handlers:
        del _handlers[tool_name]
    global _handler_registry_version
    _handler_registry_version += 1
    return redis_client.delete(key) > 0


# ============================================================
# 热加载核心功能
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
# 动态注册工具（通过 API 调用）
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