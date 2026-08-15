"""
工具：商品查询
"""
import logging
from data.init_db import get_product_info
from app.tool_registry import register_tool


def get_product_price(name: str) -> dict:
    """查询商品价格和库存"""
    info = get_product_info(name)
    if info:
        return {"name": info["name"], "price": info["price"], "stock": info["stock"]}
    return {"error": f"未找到商品: {name}"}


# 注册为工具
register_tool(
    name="get_product_price",
    description="查询商品价格和库存",
    input_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "商品名称"}
        },
        "required": ["name"]
    },
    handler=get_product_price
)