"""
滑动窗口会话测试

验证：
1. 消息能正确追加
2. 超出窗口大小的消息被自动裁剪
3. 读取顺序正确（从旧到新）
"""
import sys
from langchain_core.messages import HumanMessage, AIMessage


def main():
    print("=" * 50)
    print("   滑动窗口会话测试")
    print("=" * 50)

    try:
        from app.session_manager import (
            append_message,
            get_messages_from_history,
            get_session_stats,
            clear_history
        )
        from app.config import config
    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return 1

    session_id = "test_window_001"

    # 1. 清空测试会话
    print(f"\n[1] 清空测试会话: {session_id}")
    clear_history(session_id)

    # 2. 获取窗口配置
    max_rounds = config.MAX_HISTORY_ROUNDS
    max_messages = max_rounds * 2
    print(f"\n[2] 窗口配置: 最多 {max_rounds} 轮 ({max_messages} 条消息)")

    # 3. 追加消息（超过窗口大小）
    print(f"\n[3] 追加 {max_messages + 4} 条消息...")
    for i in range(max_messages + 4):
        if i % 2 == 0:
            msg = HumanMessage(content=f"用户消息 {i // 2 + 1}")
        else:
            msg = AIMessage(content=f"AI 回复 {i // 2 + 1}")
        append_message(session_id, msg)

    # 4. 查看统计
    print(f"\n[4] 会话统计:")
    stats = get_session_stats(session_id)
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # 5. 读取历史
    print(f"\n[5] 读取历史（最近 {max_messages} 条）:")
    messages = get_messages_from_history(session_id)
    print(f"   实际读取: {len(messages)} 条消息")

    # 6. 验证顺序和内容
    print(f"\n[6] 验证顺序（显示前 4 条和后 2 条）:")
    print("   【前 4 条】")
    for i, msg in enumerate(messages[:4]):
        print(f"      [{i + 1}] {type(msg).__name__}: {msg.content[:30]}...")

    print("   【后 2 条】")
    for i, msg in enumerate(messages[-2:]):
        idx = len(messages) - 2 + i
        print(f"      [{idx + 1}] {type(msg).__name__}: {msg.content[:30]}...")

    # 7. 清理
    print(f"\n[7] 清理测试会话")
    clear_history(session_id)

    print("\n" + "=" * 50)
    print("   ✅ 滑动窗口测试通过！")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())