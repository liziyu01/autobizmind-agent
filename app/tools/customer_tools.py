"""
工具：客户查询
"""
import logging
from data.init_db import get_customer_info
from app.tool_registry import register_tool


def get_customer_tier(name: str) -> dict:
    """查询客户等级"""
    info = get_customer_info(name)
    if info:
        return {"name": info["name"], "tier": info["tier"], "total_spent": info["total_spent"]}
    return {"error": f"未找到客户: {name}"}


# 注册为工具
register_tool(
    name="get_customer_tier",
    description="查询客户等级和累计消费",
    input_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "客户姓名"}
        },
        "required": ["name"]
    },
    handler=get_customer_tier
)