"""
工具：订单查询

封装数据库查询为 MCP 风格的工具。
"""
import logging
from typing import Optional, List, Dict, Any

# 添加父目录到路径以便导入
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
        limit: int = 20
) -> List[Dict[str, Any]]:
    """
    查询电商订单。

    Args:
        customer_name: 客户姓名（支持模糊匹配）
        status: 订单状态（pending/paid/shipped/completed/cancelled）
        limit: 返回最大数量（默认 20）

    Returns:
        订单列表，每个订单包含 order_id, customer_name, amount, status, created_at
    """
    logger.info(f"🔍 查询订单: customer_name={customer_name}, status={status}, limit={limit}")

    # 参数校验
    if status and status not in ["pending", "paid", "shipped", "completed", "cancelled"]:
        raise ValueError(f"无效的订单状态: {status}")

    if limit < 1 or limit > 100:
        limit = 20

    # 执行查询
    results = query_orders_sql(customer_name, status, limit)

    logger.info(f"✅ 查询到 {len(results)} 条订单")
    return results


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