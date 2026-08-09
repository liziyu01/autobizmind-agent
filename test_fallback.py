"""
异常降级测试
"""
import sys
import json

def main():
    print("=" * 50)
    print("   异常降级测试")
    print("=" * 50)

    try:
        from app.tool_registry import call_tool_v2
        from app.tool_agent import tool_agent
        import app.tools
        from langchain_core.messages import HumanMessage
    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return 1

    # 1. 测试正常调用
    print("\n[1] 测试正常调用: query_orders")
    result = call_tool_v2("query_orders", {"customer_name": "张三"})
    print(f"   成功: {result.success}, 数据条数: {len(result.data) if result.data else 0}")

    # 2. 测试参数错误
    print("\n[2] 测试参数错误: query_orders 缺少必填参数")
    result = call_tool_v2("query_orders", {})
    print(f"   成功: {result.success}")
    print(f"   错误类型: {result.error_type}")
    print(f"   错误信息: {result.error}")

    # 3. 测试不存在的工具
    print("\n[3] 测试不存在的工具: non_existent_tool")
    result = call_tool_v2("non_existent_tool", {})
    print(f"   成功: {result.success}")
    print(f"   错误类型: {result.error_type}")
    print(f"   错误信息: {result.error}")

    # 4. 测试 Agent 的降级响应
    print("\n[4] 测试 Agent 降级响应")
    state = {"messages": [HumanMessage(content="查询一个不存在的客户：赵钱")]}
    result = tool_agent.invoke(state)
    messages = result.get("messages", [])
    if messages:
        last = messages[-1]
        print(f"   Agent 回复: {last.content[:200]}...")

    # 5. 查看统计
    print("\n[5] 测试统计接口")
    from app.tool_logger import get_tool_stats
    stats = get_tool_stats()
    print(f"   总调用: {stats['total_calls']}")
    print(f"   成功率: {stats['success_rate']}%")
    print(f"   错误类型: {stats['error_types']}")

    print("\n" + "=" * 50)
    print("   ✅ 异常降级测试完成！")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())