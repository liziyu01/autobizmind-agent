"""
工具：报价核算

根据客户名称和商品名称，自动计算报价。
内部会调用客户等级和商品价格工具，组合成完整的报价单。
"""
import logging
from typing import Dict, Any, Optional

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tool_registry import register_tool, call_tool_v2
from data.init_db import get_customer_info, get_product_info

logger = logging.getLogger(__name__)

# ============================================================
# 1. 折扣规则配置
# ============================================================

DISCOUNT_RULES = {
    "金牌": 0.15,  # 15% 折扣
    "银牌": 0.10,  # 10% 折扣
    "普通": 0.05,  # 5% 折扣
    "新客户": 0.05,  # 5% 折扣
}

DEFAULT_DISCOUNT = 0.05


def get_discount_rate(tier: str) -> float:
    """根据客户等级获取折扣率"""
    return DISCOUNT_RULES.get(tier, DEFAULT_DISCOUNT)


# ============================================================
# 2. 核心函数：计算报价
# ============================================================

def calculate_quote(
        customer_name: str,
        product_name: str,
        quantity: int = 1
) -> Dict[str, Any]:
    """
    计算商品报价。

    内部流程：
    1. 查询客户等级
    2. 查询商品价格
    3. 计算折扣
    4. 生成报价单

    Args:
        customer_name: 客户姓名
        product_name: 商品名称
        quantity: 购买数量（默认 1）

    Returns:
        包含完整报价信息的字典
    """
    logger.info(f"📊 计算报价: {customer_name} → {product_name} × {quantity}")

    # 1. 查询客户信息
    customer_info = get_customer_info(customer_name)
    if not customer_info:
        return {
            "success": False,
            "error": f"未找到客户: {customer_name}",
            "error_type": "CUSTOMER_NOT_FOUND"
        }

    # 2. 查询商品信息
    product_info = get_product_info(product_name)
    if not product_info:
        return {
            "success": False,
            "error": f"未找到商品: {product_name}",
            "error_type": "PRODUCT_NOT_FOUND"
        }

    # 3. 获取客户等级和折扣率
    tier = customer_info["tier"]
    discount_rate = get_discount_rate(tier)

    # 4. 计算价格
    unit_price = product_info["price"]
    subtotal = unit_price * quantity
    discount_amount = subtotal * discount_rate
    total = subtotal - discount_amount

    # 5. 构建报价单
    quote = {
        "success": True,
        "quote_id": f"Q{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "created_at": datetime.now().isoformat(),
        "customer": {
            "name": customer_info["name"],
            "tier": tier,
            "total_spent": customer_info["total_spent"]
        },
        "product": {
            "name": product_info["name"],
            "category": product_info["category"],
            "unit_price": unit_price,
            "stock": product_info["stock"]
        },
        "quantity": quantity,
        "subtotal": round(subtotal, 2),
        "discount_rate": discount_rate,
        "discount_percent": f"{discount_rate * 100:.0f}%",
        "discount_amount": round(discount_amount, 2),
        "total": round(total, 2),
        "saved": round(discount_amount, 2),
        "valid_until": (datetime.now() + timedelta(days=3)).isoformat()
    }

    logger.info(f"✅ 报价计算完成: ￥{total} (折扣: {discount_rate * 100:.0f}%)")
    return quote

# ============================================================
# 3. MCP 元数据与注册
# ============================================================

from datetime import datetime, timedelta

TOOL_NAME = "calculate_quote"
TOOL_DESCRIPTION = """计算商品报价。
根据客户姓名和商品名称，自动查询客户等级和商品价格，计算折扣后的报价。
适用于：客户询价、销售报价、价格核算等场景。
返回完整的报价单，包含原价、折扣率、折后价和节省金额。"""

TOOL_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "customer_name": {
            "type": "string",
            "description": "客户姓名，如'张伟'"
        },
        "product_name": {
            "type": "string",
            "description": "商品名称，如'iPhone 15 Pro'"
        },
        "quantity": {
            "type": "integer",
            "description": "购买数量，默认 1",
            "default": 1
        }
    },
    "required": ["customer_name", "product_name"]
}


def register():
    return register_tool(
        name=TOOL_NAME,
        description=TOOL_DESCRIPTION,
        input_schema=TOOL_INPUT_SCHEMA,
        handler=calculate_quote
    )


register()
logger.info(f"📦 工具已注册: {TOOL_NAME}")