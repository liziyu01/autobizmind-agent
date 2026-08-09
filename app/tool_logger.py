"""
工具调用日志模块

记录每次工具调用的请求、响应、耗时等信息。
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

LOG_KEY_PREFIX = "tool_logs"


def log_tool_call(
        tool_name: str,
        params: Dict[str, Any],
        success: bool,
        result: Any = None,
        error: Optional[str] = None,
        error_type: Optional[str] = None,
        duration_ms: float = 0,
        session_id: Optional[str] = None
) -> None:
    """
    记录工具调用日志到 Redis（带 TTL，自动清理）。
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "tool_name": tool_name,
        "params": params,
        "success": success,
        "duration_ms": round(duration_ms, 2),
        "session_id": session_id or "unknown"
    }

    if success:
        # 结果可能很大，截断
        result_str = json.dumps(result, ensure_ascii=False)[:500]
        log_entry["result_preview"] = result_str
    else:
        log_entry["error"] = error
        log_entry["error_type"] = error_type

    # 存入 Redis（带 7 天 TTL）
    key = f"{LOG_KEY_PREFIX}:{tool_name}:{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    redis_client.set(key, log_entry, ttl=60 * 60 * 24 * 7)

    # 同时记录到本地日志
    status = "✅" if success else "❌"
    logger.info(f"{status} 工具调用日志: {tool_name} duration={duration_ms}ms success={success}")


def get_tool_logs(
        tool_name: Optional[str] = None,
        limit: int = 50
) -> List[Dict[str, Any]]:
    """
    获取工具调用日志。

    Args:
        tool_name: 筛选特定工具（可选）
        limit: 返回条数
    """
    pattern = f"{LOG_KEY_PREFIX}:*" if not tool_name else f"{LOG_KEY_PREFIX}:{tool_name}:*"
    keys = redis_client.client.keys(pattern)

    # 按时间排序（最新的在前）
    keys = sorted(keys, reverse=True)[:limit]

    logs = []
    for key in keys:
        log = redis_client.get(key)
        if log:
            logs.append(log)

    return logs


def get_tool_stats(tool_name: Optional[str] = None) -> Dict[str, Any]:
    """
    获取工具调用统计信息。
    """
    logs = get_tool_logs(tool_name, limit=1000)

    total = len(logs)
    success_count = sum(1 for log in logs if log.get("success", False))

    # 按错误类型分组
    error_types = {}
    for log in logs:
        if not log.get("success"):
            et = log.get("error_type", "UNKNOWN")
            error_types[et] = error_types.get(et, 0) + 1

    # 平均耗时
    durations = [log.get("duration_ms", 0) for log in logs if log.get("duration_ms")]
    avg_duration = sum(durations) / len(durations) if durations else 0

    return {
        "total_calls": total,
        "success_rate": round(success_count / total * 100, 2) if total > 0 else 0,
        "success_count": success_count,
        "failure_count": total - success_count,
        "error_types": error_types,
        "avg_duration_ms": round(avg_duration, 2),
        "tool_name": tool_name or "all"
    }