"""
Agent本地测试脚本
"""
import sys
from langchain_core.messages import HumanMessage

def main():
    print("=" * 50)
    print("   Agent 本地测试（输入 quit 退出）")
    print("=" * 50)

    try:
        from app.agent import agent
    except ImportError as e:
        print(f"\n 导入失败：{e}")
        print("请确保在项目根目录下运行，且虚拟环境已激活。")
        return 1

    print("\n💬 你好，我们可以开始对话了：")

    # 初始化状态
    state = {"messages": []}

    while True:
        user_input = input("👤 用户：").strip()
        quit = ["quit", "exit", "q"]
        if user_input.lower() in quit:
            print("再见")
            break
        if not user_input:
            continue

        # 将用户消息加入状态
        state["messages"].append(HumanMessage(content=user_input))

        # 调用 Agent
        try:
            result = agent.invoke(state)
            last_msg = result["messages"][-1]
            print(f"🤖 系统：{last_msg.content}")

            state = result
        except Exception as e:
            print(f"❌ 错误: {e}")
    return 0

if __name__ == "__main__":
    sys.exit(main())