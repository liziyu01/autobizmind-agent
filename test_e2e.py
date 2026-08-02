"""
端到端测试脚本

模拟完整用户流程：
1. 上传文档 → 2. 普通对话（无知识库）→ 3. RAG 对话（有知识库）→ 4. 验证记忆
"""
import sys
import os
import time
import json
import requests

# 服务地址
BASE_URL = "http://localhost:8000"


def log_step(step: str, success: bool, detail: str = ""):
    """格式化输出测试步骤"""
    icon = "✅" if success else "❌"
    print(f"{icon} {step}: {detail}")


def main():
    print("=" * 60)
    print("   端到端测试")
    print("=" * 60)

    # ===== Step 0: 健康检查 =====
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

    session_id = f"e2e_test_{int(time.time())}"

    # ===== Step 1: 创建测试文档 =====
    print("\n[1] 准备测试文档...")
    test_content = """
    公司内部员工手册

    第一章：考勤制度
    1. 工作时间：周一至周五 9:00-18:00，午休 12:00-13:00
    2. 迟到：每月累计迟到超过 30 分钟，扣除全勤奖
    3. 请假：需提前 1 天在 OA 系统提交申请

    第二章：福利待遇
    1. 年假：入职满 1 年享有 5 天年假，满 3 年 10 天
    2. 公积金：按 12% 比例缴纳
    3. 餐补：每日 30 元

    第三章：报销流程
    1. 提交发票 → 部门主管审批 → 财务审核 → 打款
    2. 报销周期：提交后 5-10 个工作日到账
    """

    test_file = "test_employee_handbook.txt"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_content)
    log_step("测试文档创建", True, test_file)

    # ===== Step 2: 上传文档 =====
    print("\n[2] 上传文档到知识库...")
    try:
        with open(test_file, "rb") as f:
            files = {"file": (test_file, f, "text/plain")}
            resp = requests.post(f"{BASE_URL}/upload_doc", files=files, params={"collection": "knowledge_base"})

        if resp.status_code == 200:
            data = resp.json()
            log_step("文档上传", True, f"片段数: {data.get('chunk_count')}, {data.get('message')}")
        else:
            log_step("文档上传", False, f"HTTP {resp.status_code}: {resp.text}")
            # 继续执行，不退出（可能已有同名文档）
    except Exception as e:
        log_step("文档上传", False, str(e))
        return 1

    # ===== Step 3: 普通对话（无知识库） =====
    print("\n[3] 普通对话测试（无知识库）...")
    try:
        resp = requests.post(
            f"{BASE_URL}/chat",
            json={"message": "公司年假有多少天？", "session_id": session_id}
        )
        if resp.status_code == 200:
            data = resp.json()
            reply = data.get("response", "")
            # 普通模式下，LLM 可能给出通用回答，不一定是文档中的信息
            log_step("普通对话", True, f"回复长度: {len(reply)} 字符")
            print(f"   🤖: {reply[:100]}...")
        else:
            log_step("普通对话", False, f"HTTP {resp.status_code}")
    except Exception as e:
        log_step("普通对话", False, str(e))

    # ===== Step 4: RAG 对话（有知识库） =====
    print("\n[4] RAG 对话测试（有知识库）...")
    try:
        resp = requests.post(
            f"{BASE_URL}/chat/rag",
            json={"message": "公司年假有多少天？", "session_id": session_id}
        )
        if resp.status_code == 200:
            data = resp.json()
            reply = data.get("response", "")
            # RAG 模式下，应该基于文档内容回答（包含"5天"或"年假"等关键词）
            has_keyword = "5" in reply or "年假" in reply or "10" in reply
            log_step("RAG 对话", True, f"回复长度: {len(reply)} 字符")
            print(f"   🤖: {reply[:150]}...")
            if has_keyword:
                print("   ✅ 回复包含文档中的关键信息（年假天数）")
            else:
                print("   ⚠️ 回复可能未基于文档内容，请检查 RAG 检索是否生效")
        else:
            log_step("RAG 对话", False, f"HTTP {resp.status_code}")
    except Exception as e:
        log_step("RAG 对话", False, str(e))

    # ===== Step 5: 多轮对话记忆测试 =====
    print("\n[5] 会话记忆测试（多轮对话）...")
    try:
        # 第一轮：问一个问题
        resp1 = requests.post(
            f"{BASE_URL}/chat/rag",
            json={"message": "我叫张三，是公司新员工", "session_id": session_id}
        )
        # 第二轮：问一个需要记住上下文的问题
        time.sleep(0.5)
        resp2 = requests.post(
            f"{BASE_URL}/chat/rag",
            json={"message": "我叫什么名字？", "session_id": session_id}
        )

        if resp1.status_code == 200 and resp2.status_code == 200:
            reply1 = resp1.json().get("response", "")
            reply2 = resp2.json().get("response", "")
            # 检查第二轮回复是否包含"张三"
            has_name = "张三" in reply2
            log_step("会话记忆", has_name, f"第一轮已告知姓名，第二轮{'能' if has_name else '不能'}记住")
            if not has_name:
                print(f"   ⚠️ 第二轮回复: {reply2[:100]}...")
        else:
            log_step("会话记忆", False, "多轮对话请求失败")
    except Exception as e:
        log_step("会话记忆", False, str(e))

    # ===== Step 6: 知识库统计 =====
    print("\n[6] 知识库统计...")
    try:
        resp = requests.get(f"{BASE_URL}/kb/stats", params={"collection": "knowledge_base"})
        if resp.status_code == 200:
            data = resp.json()
            log_step("知识库统计", True, f"文档片段数: {data.get('document_count', 0)}")
        else:
            log_step("知识库统计", False, f"HTTP {resp.status_code}")
    except Exception as e:
        log_step("知识库统计", False, str(e))

    # ===== Step 7: 清理测试文件 =====
    print("\n[7] 清理测试文件...")
    if os.path.exists(test_file):
        os.remove(test_file)
        log_step("清理", True, f"已删除 {test_file}")

    # ===== 测试总结 =====
    print("\n" + "=" * 60)
    print("   端到端测试完成！")
    print("=" * 60)
    print("\n📊 测试说明：")
    print("  - 步骤 3 和 4 对比了普通对话 vs RAG 对话")
    print("  - 步骤 5 验证了 Redis 会话记忆")
    print("  - 所有数据均通过 API 验证，无人工干预")
    print("\n📁 查看 Swagger API 文档: http://localhost:8000/docs")
    return 0


if __name__ == "__main__":
    sys.exit(main())