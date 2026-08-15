"""
完整端到端测试（模拟前端调用）
"""
import sys
import time
import requests

BASE_URL = "http://localhost:8000"


def main():
    print("=" * 60)
    print("   🚀 完整端到端测试")
    print("=" * 60)

    session_id = f"e2e_full_{int(time.time())}"

    # 测试场景列表
    tests = [
        ("普通对话", "/chat", "我叫何刚，是产品经理"),
        ("普通对话（记忆）", "/chat", "我的职位是什么？"),
        ("工具调用", "/chat/tool", "查询何刚的订单"),
        ("报价核算", "/chat/tool", "何刚想买一个MacBook Air M3，请给出报价"),
    ]

    passed = 0
    total = len(tests)

    for name, endpoint, message in tests:
        print(f"\n[{name}]")
        print(f"  请求: {message}")

        try:
            resp = requests.post(
                f"{BASE_URL}{endpoint}",
                json={"message": message, "session_id": session_id},
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                reply = data.get("response", "")[:100]
                print(f"  ✅ 响应: {reply}...")
                passed += 1
            else:
                print(f"  ❌ HTTP {resp.status_code}")
        except Exception as e:
            print(f"  ❌ {e}")

        time.sleep(0.5)

    print("\n" + "=" * 60)
    print(f"   📊 结果: {passed}/{total} 通过")
    print("=" * 60)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())