"""
工具：客户查询
"""
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.init_db import get_customer_info
from app.tool_registry import register_tool

logger = logging.getLogger(__name__)


def get_customer_tier(name: str) -> dict:
    """
    查询客户等级和累计消费。

    Args:
        name: 客户姓名

    Returns:
        客户信息字典，包含 name, tier, total_spent
    """
    logger.info(f"🔍 查询客户: {name}")

    if not name or not name.strip():
        return {"error": "请提供客户姓名"}

    info = get_customer_info(name)
    if info:
        return {
            "name": info["name"],
            "tier": info["tier"],
            "total_spent": info["total_spent"]
        }
    return {"error": f"未找到客户: {name}"}


# ============================================================
# 注册工具
# ============================================================

TOOL_NAME = "get_customer_tier"
TOOL_DESCRIPTION = """查询客户等级和累计消费金额。
客户等级分为：普通（消费<1000）、银牌（1000-5000）、金牌（>5000）。
适用于：客户身份识别、会员权益判断、客户画像分析等场景。"""

TOOL_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "客户姓名，如'张三'"
        }
    },
    "required": ["name"]
}


def register():
    return register_tool(
        name=TOOL_NAME,
        description=TOOL_DESCRIPTION,
        input_schema=TOOL_INPUT_SCHEMA,
        handler=get_customer_tier
    )


# 自动注册（导入时执行）
register()
logger.info(f"📦 工具已注册: {TOOL_NAME}")