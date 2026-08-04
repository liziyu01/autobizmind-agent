"""
工具调用 Agent 测试
"""
import sys
from langchain_core.messages import HumanMessage


def main():
    print("=" * 50)
    print("   工具调用 Agent 测试（输入 quit 退出）")
    print("=" * 50)

    try:
        from app.tool_agent import tool_agent
        import app.tools
    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return 1

    print("\n💬 可以开始对话了（支持：查询订单、计算、HTTP 请求）")

    while True:
        user_input = input("\n你：").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            print("👋 再见！")
            break

        if not user_input:
            continue

        state = {"messages": [HumanMessage(content=user_input)]}

        try:
            result = tool_agent.invoke(state)
            messages = result.get("messages", [])
            if messages:
                last = messages[-1]
                content = last.content if hasattr(last, "content") else str(last)
                print(f"🤖：{content}")
            else:
                print("🤖：（无响应）")
        except Exception as e:
            print(f"❌ 错误: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())