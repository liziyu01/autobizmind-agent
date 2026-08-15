"""
Agent 报价核算测试（多工具链式调用）
"""
import sys
from langchain_core.messages import HumanMessage


def main():
    print("=" * 50)
    print("   Agent 报价核算测试（多工具链式调用）")
    print("=" * 50)

    try:
        from app.tool_agent import tool_agent
        import app.tools
    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return 1

    # 测试场景列表
    test_scenarios = [
        {
            "name": "场景1: 金牌客户询价",
            "message": "何刚想买一个iPhone 15 Pro，帮他算一下报价"
        },
        {
            "name": "场景2: 普通客户询价",
            "message": "孙华想买两个 小米 空气净化器，给个报价"
        },
        {
            "name": "场景3: 客户不存在",
            "message": "李四想买五常大米，帮我算报价"
        },
        {
            "name": "场景4: 查询客户等级后报价（间接推理）",
            "message": "查询一下何刚的客户等级，然后根据等级给出iPhone 15 Pro的报价"
        }
    ]

    for scenario in test_scenarios:
        print(f"\n[📋 {scenario['name']}]")
        print(f"   用户: {scenario['message']}")

        state = {"messages": [HumanMessage(content=scenario['message'])]}
        try:
            result = tool_agent.invoke(state)
            messages = result.get("messages", [])
            if messages:
                last = messages[-1]
                print(f"   🤖: {last.content[:300]}")
                if len(last.content) > 300:
                    print("   ...")
        except Exception as e:
            print(f"   ❌ 错误: {e}")

    print("\n" + "=" * 50)
    print("   ✅ Agent 报价核算测试完成！")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())