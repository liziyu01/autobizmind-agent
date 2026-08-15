"""
工具：商品查询
"""
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.init_db import get_product_info
from app.tool_registry import register_tool

logger = logging.getLogger(__name__)


def get_product_price(name: str) -> dict:
    """
    查询商品价格和库存。

    Args:
        name: 商品名称

    Returns:
        商品信息字典，包含 name, price, stock, category
    """
    logger.info(f"🔍 查询商品: {name}")

    if not name or not name.strip():
        return {"error": "请提供商品名称"}

    info = get_product_info(name)
    if info:
        return {
            "name": info["name"],
            "price": info["price"],
            "stock": info["stock"],
            "category": info["category"]
        }
    return {"error": f"未找到商品: {name}"}


# ============================================================
# 注册工具
# ============================================================

TOOL_NAME = "get_product_price"
TOOL_DESCRIPTION = """查询商品价格和库存信息。
适用于：商品询价、库存查询、价格对比等场景。"""

TOOL_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "商品名称，如'iPhone 15 Pro'"
        }
    },
    "required": ["name"]
}


def register():
    return register_tool(
        name=TOOL_NAME,
        description=TOOL_DESCRIPTION,
        input_schema=TOOL_INPUT_SCHEMA,
        handler=get_product_price
    )


# 自动注册（导入时执行）
register()
logger.info(f"📦 工具已注册: {TOOL_NAME}")