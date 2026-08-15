"""
电商工具测试
"""
import sys
import json
from langchain_core.messages import HumanMessage


def main():
    print("=" * 50)
    print("   电商工具测试")
    print("=" * 50)

    try:
        from app.tool_agent import tool_agent
        import app.tools
        from app.tool_registry import call_tool_v2, get_all_tools_metadata
    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return 1

    # 1. 查看已注册工具
    print("\n[1] 已注册工具:")
    tools = get_all_tools_metadata()
    for name in tools.keys():
        print(f"   - {name}")

    # 2. 直接调用工具（客户查询）
    print("\n[2] 直接调用: get_customer_tier")
    result = call_tool_v2("get_customer_tier", {"name": "张伟"})
    if result.success:
        print(f"   ✅ {result.data}")
    else:
        print(f"   ❌ {result.error}")

    # 3. 直接调用工具（商品查询）
    print("\n[3] 直接调用: get_product_price")
    result = call_tool_v2("get_product_price", {"name": "iPhone 15 Pro"})
    if result.success:
        print(f"   ✅ {result.data}")
    else:
        print(f"   ❌ {result.error}")

    # 4. Agent 测试：客户等级查询
    print("\n[4] Agent 测试: 查询客户等级")
    state = {"messages": [HumanMessage(content="查询张伟的客户等级")]}
    try:
        result = tool_agent.invoke(state)
        messages = result.get("messages", [])
        if messages:
            last = messages[-1]
            print(f"   🤖: {last.content[:200]}...")
    except Exception as e:
        print(f"   ❌ {e}")

    # 5. Agent 测试：商品价格查询
    print("\n[5] Agent 测试: 查询商品价格")
    state = {"messages": [HumanMessage(content="iPhone 15 Pro 多少钱？")]}
    try:
        result = tool_agent.invoke(state)
        messages = result.get("messages", [])
        if messages:
            last = messages[-1]
            print(f"   🤖: {last.content[:200]}...")
    except Exception as e:
        print(f"   ❌ {e}")

    # 6. Agent 测试：复杂场景（客户+商品组合）
    print("\n[6] Agent 测试: 组合查询")
    state = {"messages": [
        HumanMessage(content="张伟想买一个iPhone 15 Pro，帮我查一下他是什么等级的客户，以及这个商品的价格是多少？")]}
    try:
        result = tool_agent.invoke(state)
        messages = result.get("messages", [])
        if messages:
            last = messages[-1]
            print(f"   🤖: {last.content[:300]}...")
    except Exception as e:
        print(f"   ❌ {e}")

    print("\n" + "=" * 50)
    print("   ✅ 电商工具测试完成！")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())