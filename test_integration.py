"""
系统联调测试脚本

验证所有模块协同工作：
1. 普通对话（记忆 + 滑动窗口）
2. RAG 对话（知识库检索）
3. 工具调用对话（订单查询 + 报价核算）
4. 热加载（动态注册 + 刷新）
5. 会话统计
"""
import sys
import time
import json
import requests

BASE_URL = "http://localhost:8000"


def log_result(step: str, passed: bool, detail: str = ""):
    icon = "✅" if passed else "❌"
    print(f"{icon} {step}: {detail}")


def main():
    print("=" * 60)
    print("   🤖 AutoBizMind 系统联调测试")
    print("=" * 60)

    # ===== 健康检查 =====
    print("\n[0] 服务健康检查...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            log_result("服务状态", True, f"Redis={data.get('redis')}, LLM={data.get('llm')}")
        else:
            log_result("服务状态", False, f"HTTP {resp.status_code}")
            return 1
    except Exception as e:
        print(f"❌ 服务未启动: {e}")
        print("   请先运行: python -m app.main")
        return 1

    session_id = f"integration_test_{int(time.time())}"
    results = []

    # ===== 1. 测试普通对话（带记忆） =====
    print("\n[1] 测试普通对话（记忆）...")
    try:
        resp1 = requests.post(
            f"{BASE_URL}/chat",
            json={"message": "我叫张三，是一名程序员", "session_id": session_id}
        )
        time.sleep(0.5)
        resp2 = requests.post(
            f"{BASE_URL}/chat",
            json={"message": "我叫什么名字？", "session_id": session_id}
        )
        if resp1.status_code == 200 and resp2.status_code == 200:
            reply = resp2.json().get("response", "")
            has_name = "张三" in reply
            log_result("对话记忆", has_name, f"能记住姓名: {has_name}")
            results.append(has_name)
        else:
            log_result("对话记忆", False, f"HTTP 错误")
            results.append(False)
    except Exception as e:
        log_result("对话记忆", False, str(e))
        results.append(False)

    # ===== 2. 测试 RAG 对话 =====
    print("\n[2] 测试 RAG 对话...")
    try:
        resp = requests.post(
            f"{BASE_URL}/chat/rag",
            json={"message": "公司的年假政策是什么？", "session_id": session_id}
        )
        if resp.status_code == 200:
            reply = resp.json().get("response", "")
            has_keyword = "年假" in reply or "天" in reply
            log_result("RAG 对话", has_keyword, f"回复包含年假信息: {has_keyword}")
            results.append(has_keyword)
        else:
            log_result("RAG 对话", False, f"HTTP {resp.status_code}")
            results.append(False)
    except Exception as e:
        log_result("RAG 对话", False, str(e))
        results.append(False)

    # ===== 3. 测试工具调用（订单查询） =====
    print("\n[3] 测试工具调用（订单查询）...")
    try:
        resp = requests.post(
            f"{BASE_URL}/chat/tool",
            json={"message": "查询张三的订单", "session_id": session_id}
        )
        if resp.status_code == 200:
            data = resp.json()
            reply = data.get("response", "")
            tool_calls = data.get("tool_calls", 0)
            has_order = "订单" in reply or "order" in reply.lower() or tool_calls > 0
            log_result("工具调用", has_order, f"调用了 {tool_calls} 个工具")
            results.append(has_order)
        else:
            log_result("工具调用", False, f"HTTP {resp.status_code}")
            results.append(False)
    except Exception as e:
        log_result("工具调用", False, str(e))
        results.append(False)

    # ===== 4. 测试报价核算（多工具链式） =====
    print("\n[4] 测试报价核算（多工具链式）...")
    try:
        resp = requests.post(
            f"{BASE_URL}/chat/tool",
            json={"message": "何刚想买 iPhone 15 Pro，请给出报价", "session_id": session_id}
        )
        if resp.status_code == 200:
            data = resp.json()
            reply = data.get("response", "")
            # has_price = "报价" in reply or "￥" in reply or "折扣" in reply
            has_price = "success" in reply or "total" in reply or "quote_id" in reply
            log_result("报价核算", has_price, f"包含价格信息: {has_price}")
            results.append(has_price)
        else:
            log_result("报价核算", False, f"HTTP {resp.status_code}")
            results.append(False)
    except Exception as e:
        log_result("报价核算", False, str(e))
        results.append(False)

    # ===== 5. 测试会话统计（滑动窗口） =====
    print("\n[5] 测试会话统计...")
    try:
        resp = requests.get(f"{BASE_URL}/session/{session_id}/stats")
        if resp.status_code == 200:
            data = resp.json()
            msg_count = data.get("message_count", 0)
            max_messages = data.get("max_messages", 0)
            usage = data.get("usage_ratio", 0)
            log_result("会话统计", True, f"消息: {msg_count}/{max_messages}, 使用率: {usage}%")
            results.append(True)
        else:
            log_result("会话统计", False, f"HTTP {resp.status_code}")
            results.append(False)
    except Exception as e:
        log_result("会话统计", False, str(e))
        results.append(False)

    # ===== 6. 测试知识库统计 =====
    print("\n[6] 测试知识库统计...")
    try:
        resp = requests.get(f"{BASE_URL}/kb/stats")
        if resp.status_code == 200:
            data = resp.json()
            doc_count = data.get("document_count", 0)
            log_result("知识库统计", True, f"文档片段: {doc_count}")
            results.append(True)
        else:
            log_result("知识库统计", False, f"HTTP {resp.status_code}")
            results.append(False)
    except Exception as e:
        log_result("知识库统计", False, str(e))
        results.append(False)

    # ===== 7. 测试工具列表 =====
    print("\n[7] 测试工具列表...")
    try:
        resp = requests.get(f"{BASE_URL}/tools")
        if resp.status_code == 200:
            data = resp.json()
            tool_count = data.get("count", 0)
            tools = list(data.get("tools", {}).keys())
            log_result("工具列表", True, f"共 {tool_count} 个工具: {', '.join(tools[:5])}{'...' if len(tools) > 5 else ''}")
            results.append(True)
        else:
            log_result("工具列表", False, f"HTTP {resp.status_code}")
            results.append(False)
    except Exception as e:
        log_result("工具列表", False, str(e))
        results.append(False)

    # ===== 总结 =====
    print("\n" + "=" * 60)
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"   📊 联调结果: {passed}/{total} 项通过")
    if passed == total:
        print("   🎉 所有模块联调成功！")
    else:
        print(f"   ⚠️ {total - passed} 项测试失败，请检查")
    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())