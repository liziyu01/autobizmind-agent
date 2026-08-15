"""
工具包

所有 MCP 风格的工具。
"""
from app.tools import query_orders
from app.tools import http_request
from app.tools import calculator
from app.tools import text_stats
from app.tools import customer_tools
from app.tools import product_tools
from app.tools import quote_calculator

# 所有工具列表
ALL_TOOLS = [
    query_orders,
    http_request,
    calculator,
    text_stats,
    customer_tools,
    product_tools,
    quote_calculator,
]


def register_all():
    """批量注册所有工具（导入时已自动注册，此函数主要用于显式调用）"""
    for tool in ALL_TOOLS:
        if hasattr(tool, 'register'):
            try:
                tool.register()
            except Exception as e:
                print(f"⚠️ 注册工具失败: {tool.__name__ if hasattr(tool, '__name__') else tool} - {e}")
    print("✅ 所有工具已注册")