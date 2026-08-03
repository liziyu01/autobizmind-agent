"""
工具系统测试

测试工具注册、元数据读取和工具调用。
"""
import sys
import json


def main():
    print("=" * 50)
    print("   工具系统测试")
    print("=" * 50)

    try:
        from app.tool_registry import (
            get_tool_metadata,
            get_all_tools_metadata,
            call_tool,
            clear_all_tools
        )
        from app.tools import query_orders  # 导入即自动注册
    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return 1

    # 1. 查看已注册的工具
    print("\n[1] 已注册的工具:")
    all_tools = get_all_tools_metadata()
    for name, meta in all_tools.items():
        print(f"   - {name}: {meta.get('description', '')[:50]}...")

    # 2. 获取单个工具元数据
    print("\n[2] 工具详情: query_orders")
    meta = get_tool_metadata("query_orders")
    if meta:
        print(f"   名称: {meta['name']}")
        print(f"   描述: {meta['description']}")
        print(f"   参数: {json.dumps(meta['inputSchema'], ensure_ascii=False, indent=2)}")

    # 3. 调用工具测试
    print("\n[3] 调用工具: 查询张三的订单")
    try:
        result = call_tool("query_orders", {"customer_name": "张三", "limit": 5})
        print(f"   ✅ 查询成功，返回 {len(result)} 条记录:")
        for order in result[:3]:
            print(f"      - 订单#{order['order_id']}: {order['customer_name']} ￥{order['amount']} {order['status']}")
    except Exception as e:
        print(f"   ❌ 调用失败: {e}")

    # 4. 调用工具：按状态筛选
    print("\n[4] 调用工具: 查询已完成订单")
    try:
        result = call_tool("query_orders", {"status": "completed", "limit": 3})
        print(f"   ✅ 查询成功，返回 {len(result)} 条记录:")
        for order in result:
            print(f"      - 订单#{order['order_id']}: {order['customer_name']} ￥{order['amount']}")
    except Exception as e:
        print(f"   ❌ 调用失败: {e}")

    print("\n" + "=" * 50)
    print("   ✅ 工具系统测试完成！")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())