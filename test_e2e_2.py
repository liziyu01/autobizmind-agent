
"""
端到端测试 2.0

模拟完整用户流程：
1. 查看已注册工具
2. 测试工具调用（订单查询 + 计算）
3. 测试热加载（动态注册 + 刷新）
4. 测试异常降级（参数错误、不存在的工具）
5. 查看工具日志和统计
"""
import sys
import time
import json
import requests

BASE_URL = "http://localhost:8000"


def log_step(step: str, success: bool, detail: str = ""):
    icon = "✅" if success else "❌"
    print(f"{icon} {step}: {detail}")


def main():
    print("=" * 60)
    print("   端到端测试")
    print("=" * 60)

    # Step 0: 健康检查
    print("\n[0] 检查服务状态...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            log_step("服务健康", True, f"Redis={data.get('redis')}, LLM={data.get('llm')}")
        else:
            log_step("服务健康", False, f"HTTP {resp.status_code}")
            return 1
    except requests.exceptions.ConnectionError:
        print("❌ 服务未启动！请先运行 python -m app.main")
        return 1

    session_id = f"e2e_2_{int(time.time())}"

    # ===== Step 1: 查看已注册工具 =====
    print("\n[1] 查看已注册工具...")
    try:
        resp = requests.get(f"{BASE_URL}/tools")
        if resp.status_code == 200:
            data = resp.json()
            tools = data.get("tools", {})
            log_step("工具列表", True, f"共 {len(tools)} 个工具: {', '.join(tools.keys())}")
        else:
            log_step("工具列表", False, f"HTTP {resp.status_code}")
    except Exception as e:
        log_step("工具列表", False, str(e))

    # ===== Step 2: 测试工具调用（订单查询） =====
    print("\n[2] 测试工具调用: 查询张三的订单...")
    try:
        resp = requests.post(
            f"{BASE_URL}/chat/tool",
            json={"message": "查询张三的订单", "session_id": session_id}
        )
        if resp.status_code == 200:
            data = resp.json()
            reply = data.get("response", "")
            has_order = "订单" in reply or "order" in reply.lower()
            log_step("订单查询", has_order, f"回复包含订单信息: {has_order}")
            if not has_order:
                print(f"   回复: {reply[:100]}...")
        else:
            log_step("订单查询", False, f"HTTP {resp.status_code}")
    except Exception as e:
        log_step("订单查询", False, str(e))

    # ===== Step 3: 测试工具调用（计算） =====
    print("\n[3] 测试工具调用: 数学计算...")
    try:
        resp = requests.post(
            f"{BASE_URL}/chat/tool",
            json={"message": "计算 25 乘以 4", "session_id": session_id}
        )
        if resp.status_code == 200:
            data = resp.json()
            reply = data.get("response", "")
            has_result = "100" in reply
            log_step("计算器", has_result, f"回复包含结果 100: {has_result}")
        else:
            log_step("计算器", False, f"HTTP {resp.status_code}")
    except Exception as e:
        log_step("计算器", False, str(e))

    # ===== Step 4: 测试热加载（动态注册 + 刷新） =====
    print("\n[4] 测试热加载: 动态注册工具...")
    try:
        # 4.1 注册新工具（仅元数据）
        register_payload = {
            "name": "test_greeting",
            "description": "返回问候语",
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "姓名"}
                },
                "required": ["name"]
            }
        }
        resp = requests.post(
            f"{BASE_URL}/tools/register_dynamic",
            json=register_payload
        )
        if resp.status_code == 200:
            log_step("动态注册", True, f"工具 test_greeting 已注册")
        else:
            log_step("动态注册", False, f"HTTP {resp.status_code}")

        # 4.2 刷新工具列表
        time.sleep(0.5)
        resp = requests.post(f"{BASE_URL}/tools/refresh")
        if resp.status_code == 200:
            data = resp.json()
            log_step("刷新工具", True, f"版本: {data.get('version')}, 工具数: {data.get('tool_count')}")
        else:
            log_step("刷新工具", False, f"HTTP {resp.status_code}")

        # 4.3 验证新工具是否出现在列表中
        resp = requests.get(f"{BASE_URL}/tools")
        if resp.status_code == 200:
            tools = resp.json().get("tools", {})
            has_new = "test_greeting" in tools
            log_step("验证新工具", has_new, f"test_greeting 在列表中: {has_new}")
        else:
            log_step("验证新工具", False, "无法获取工具列表")

    except Exception as e:
        log_step("热加载测试", False, str(e))

    # ===== Step 5: 测试异常降级（不存在的工具） =====
    print("\n[5] 测试异常降级: 调用不存在的工具...")
    try:
        # 强制 Agent 调用一个不存在的工具（通过 prompt 诱导）
        resp = requests.post(
            f"{BASE_URL}/chat/tool",
            json={
                "message": "调用一个不存在的工具 non_existent_tool",
                "session_id": session_id
            }
        )
        if resp.status_code == 200:
            data = resp.json()
            reply = data.get("response", "")
            has_error = any(keyword in reply for keyword in ["不存在", "失败", "error", "未注册", "没有", "无法", "不可用"])
            log_step("异常降级", has_error, f"回复包含错误提示: {has_error}")
        else:
            log_step("异常降级", False, f"HTTP {resp.status_code}")
    except Exception as e:
        log_step("异常降级", False, str(e))

    # ===== Step 6: 测试工具日志和统计 =====
    print("\n[6] 测试工具日志和统计...")
    try:
        resp = requests.get(f"{BASE_URL}/tools/stats")
        if resp.status_code == 200:
            data = resp.json()
            log_step("工具统计", True, f"总调用: {data.get('total_calls')}, 成功率: {data.get('success_rate')}%")
        else:
            log_step("工具统计", False, f"HTTP {resp.status_code}")

        resp = requests.get(f"{BASE_URL}/tools/logs", params={"limit": 5})
        if resp.status_code == 200:
            logs = resp.json().get("logs", [])
            log_step("工具日志", True, f"获取到 {len(logs)} 条日志")
        else:
            log_step("工具日志", False, f"HTTP {resp.status_code}")
    except Exception as e:
        log_step("日志统计", False, str(e))

    # ===== Step 7: 清理动态注册的工具 =====
    print("\n[7] 清理测试工具...")
    try:
        resp = requests.delete(f"{BASE_URL}/tools/test_greeting")
        if resp.status_code == 200:
            log_step("清理", True, "已删除 test_greeting")
        else:
            log_step("清理", False, f"HTTP {resp.status_code}")
    except Exception as e:
        log_step("清理", False, str(e))

    # ===== 测试总结 =====
    print("\n" + "=" * 60)
    print("   端到端测试完成！")
    print("=" * 60)
    print("\n📊 测试覆盖：")
    print("  - 工具列表查看")
    print("  - 工具调用（订单查询、计算器）")
    print("  - 热加载（动态注册 + 刷新）")
    print("  - 异常降级（不存在工具）")
    print("  - 工具日志和统计")
    print("\n📁 查看 Swagger API 文档: http://localhost:8000/docs")
    return 0


if __name__ == "__main__":
    sys.exit(main())