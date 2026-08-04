"""
工具：HTTP 请求

封装通用 HTTP 请求，让 Agent 能调用公开 API。
"""
import logging
import requests
from typing import Optional, Dict, Any

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tool_registry import register_tool

logger = logging.getLogger(__name__)


# ============================================================
# 1. 工具执行函数
# ============================================================

def http_request(
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None,
        timeout: int = 10
) -> Dict[str, Any]:
    """
    发送 HTTP 请求到指定 URL。

    Args:
        url: 请求地址（完整 URL）
        method: HTTP 方法（GET/POST/PUT/DELETE）
        headers: 请求头字典
        body: 请求体（POST/PUT 时使用，JSON 格式）
        timeout: 超时时间（秒）

    Returns:
        {
            "status_code": 200,
            "headers": {...},
            "data": {...}  # JSON 响应自动解析
        }
    """
    logger.info(f"🌐 HTTP {method} {url}")

    # 安全检查：只允许 HTTP/HTTPS
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"不支持的协议: {url}")

    # 默认 headers
    default_headers = {"User-Agent": "AutoBizMind/1.0"}
    if headers:
        default_headers.update(headers)

    try:
        # 根据方法发送请求
        if method.upper() == "GET":
            resp = requests.get(url, headers=default_headers, timeout=timeout)
        elif method.upper() == "POST":
            resp = requests.post(url, headers=default_headers, json=body, timeout=timeout)
        elif method.upper() == "PUT":
            resp = requests.put(url, headers=default_headers, json=body, timeout=timeout)
        elif method.upper() == "DELETE":
            resp = requests.delete(url, headers=default_headers, timeout=timeout)
        else:
            raise ValueError(f"不支持的 HTTP 方法: {method}")

        # 解析响应
        try:
            data = resp.json()
        except:
            data = resp.text

        logger.info(f"✅ HTTP {method} {url} -> {resp.status_code}")

        return {
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "data": data
        }

    except requests.exceptions.Timeout:
        logger.error(f"⏰ HTTP 请求超时: {url}")
        return {"status_code": 408, "data": "请求超时"}
    except requests.exceptions.ConnectionError:
        logger.error(f"🔗 连接失败: {url}")
        return {"status_code": 503, "data": "无法连接到服务器"}
    except Exception as e:
        logger.error(f"❌ HTTP 请求失败: {e}")
        raise


# ============================================================
# 2. MCP 元数据
# ============================================================

TOOL_NAME = "http_request"
TOOL_DESCRIPTION = """发送 HTTP 请求获取外部数据。
支持 GET/POST/PUT/DELETE 方法。
适用于：查询天气、获取新闻、调用公开 API 等场景。
返回状态码和响应数据。"""

TOOL_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "url": {
            "type": "string",
            "description": "完整的请求 URL，如 https://api.example.com/data"
        },
        "method": {
            "type": "string",
            "description": "HTTP 方法：GET（默认）、POST、PUT、DELETE",
            "enum": ["GET", "POST", "PUT", "DELETE"],
            "default": "GET"
        },
        "headers": {
            "type": "object",
            "description": "请求头，如 {'Authorization': 'Bearer token'}"
        },
        "body": {
            "type": "object",
            "description": "请求体（POST/PUT 时使用），JSON 格式"
        },
        "timeout": {
            "type": "integer",
            "description": "超时时间（秒），默认 10",
            "default": 10
        }
    },
    "required": ["url"]
}


# ============================================================
# 3. 注册工具
# ============================================================

def register():
    return register_tool(
        name=TOOL_NAME,
        description=TOOL_DESCRIPTION,
        input_schema=TOOL_INPUT_SCHEMA,
        handler=http_request
    )


register()
logger.info(f"📦 工具已注册: {TOOL_NAME}")