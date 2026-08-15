"""
工具：订单查询

封装数据库查询为 MCP 风格的工具。
"""
import logging
from typing import Optional, List, Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.init_db import query_orders_sql
from app.tool_registry import register_tool

logger = logging.getLogger(__name__)

# ============================================================
# 1. 定义工具的执行函数
# ============================================================
def query_orders(
    customer_name: Optional[str] = None,
    status: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """增强版订单查询"""
    if limit < 1 or limit > 100:
        limit = 20
    return query_orders_sql(customer_name, status, min_amount, max_amount,
                           date_from, date_to, limit)

# ============================================================
# 2. 定义工具的 MCP 元数据
# ============================================================

TOOL_NAME = "query_orders"
TOOL_DESCRIPTION = """查询电商订单。可按客户姓名和订单状态筛选。
返回订单列表，包含订单编号、客户姓名、金额、状态、创建时间。
适用于：查询某个客户的订单、查询某类状态的订单、统计订单数量等场景。"""

TOOL_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "customer_name": {
            "type": "string",
            "description": "客户姓名，支持部分匹配（如'张三'）"
        },
        "status": {
            "type": "string",
            "description": "订单状态：pending（待支付）、paid（已支付）、shipped（已发货）、completed（已完成）、cancelled（已取消）",
            "enum": ["pending", "paid", "shipped", "completed", "cancelled"]
        },
        "limit": {
            "type": "integer",
            "description": "返回的最大订单数量，默认 20，最大 100"
        }
    }
}


# ============================================================
# 3. 注册工具
# ============================================================

def register():
    """注册此工具到 Redis 工具中心"""
    return register_tool(
        name=TOOL_NAME,
        description=TOOL_DESCRIPTION,
        input_schema=TOOL_INPUT_SCHEMA,
        handler=query_orders
    )


# 自动注册（导入时执行）
register()
logger.info(f"📦 工具已注册: {TOOL_NAME}")