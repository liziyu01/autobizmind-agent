"""
AutoBizMind Streamlit 前端

提供可视化界面，支持：
1. 三种对话模式（普通 / RAG / 工具调用）
2. 文档上传到知识库
3. 会话管理（session_id）
4. 工具调用过程可视化
"""
import streamlit as st
import requests
import json
import time
from datetime import datetime

# ============================================================
# 页面配置
# ============================================================

st.set_page_config(
    page_title="AutoBizMind - AI Agent 助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 后端 API 地址
# ============================================================

API_BASE = "http://localhost:8000"

# ============================================================
# 侧边栏
# ============================================================

with st.sidebar:
    st.title("🤖 AutoBizMind")
    st.caption("自适应业务决策 Agent · 核心版 MVP")

    st.divider()

    # 会话管理
    st.subheader("📋 会话管理")

    # 生成或输入 session_id
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"web_{int(time.time())}"

    session_id = st.text_input(
        "Session ID",
        value=st.session_state.session_id,
        help="相同 ID 的对话共享历史记忆"
    )
    st.session_state.session_id = session_id

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆕 新建会话", use_container_width=True):
            st.session_state.session_id = f"web_{int(time.time())}"
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🗑️ 清空会话", use_container_width=True):
            try:
                requests.delete(f"{API_BASE}/session/{st.session_state.session_id}")
                st.session_state.messages = []
                st.success("已清空")
            except:
                st.error("清空失败")

    st.divider()

    # 模式选择
    st.subheader("🎯 对话模式")
    mode = st.radio(
        "选择 Agent 模式",
        options=["💬 普通对话", "📚 RAG 对话", "🔧 工具调用"],
        index=2,
        help="普通: 带记忆对话 | RAG: 检索知识库 | 工具: 自动调用工具"
    )

    mode_map = {
        "💬 普通对话": "/chat",
        "📚 RAG 对话": "/chat/rag",
        "🔧 工具调用": "/chat/tool"
    }
    api_endpoint = mode_map[mode]

    st.divider()

    # 系统状态
    st.subheader("📊 系统状态")
    try:
        health = requests.get(f"{API_BASE}/health", timeout=2)
        if health.status_code == 200:
            data = health.json()
            st.success(f"✅ 服务正常\nRedis: {data.get('redis')}")
        else:
            st.error("❌ 服务不可用")
    except:
        st.error("❌ 无法连接后端服务")
        st.info("请先启动: python -m app.main")

    # 工具统计（仅工具模式显示）
    if "工具" in mode:
        try:
            stats = requests.get(f"{API_BASE}/tools/stats", timeout=2)
            if stats.status_code == 200:
                data = stats.json()
                st.metric("工具调用", data.get("total_calls", 0))
                st.metric("成功率", f"{data.get('success_rate', 0)}%")
        except:
            pass

    st.divider()

    # 工具列表
    st.subheader("🔧 可用工具")
    try:
        tools_resp = requests.get(f"{API_BASE}/tools", timeout=2)
        if tools_resp.status_code == 200:
            tools = tools_resp.json().get("tools", {})
            for name, meta in list(tools.items())[:5]:
                desc = meta.get("description", "")[:40]
                st.caption(f"• {name}: {desc}...")
            if len(tools) > 5:
                st.caption(f"... 共 {len(tools)} 个工具")
    except:
        st.caption("无法获取工具列表")

    st.divider()

    st.caption(f"v0.2.0 · {datetime.now().strftime('%Y-%m-%d')}")

# ============================================================
# 主界面
# ============================================================

st.title("🤖 AutoBizMind 智能助手")
st.caption(f"会话 ID: `{st.session_state.session_id}` · 模式: {mode}")

# ============================================================
# 文档上传区域（RAG 模式显示）
# ============================================================

if "📚" in mode:
    with st.expander("📄 上传文档到知识库", expanded=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            uploaded_file = st.file_uploader(
                "选择文件 (PDF / Word / TXT)",
                type=["pdf", "docx", "txt"],
                label_visibility="collapsed"
            )
        with col2:
            if uploaded_file and st.button("📤 上传", use_container_width=True):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                try:
                    resp = requests.post(
                        f"{API_BASE}/upload_doc",
                        files=files,
                        params={"collection": "knowledge_base"}
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        st.success(f"✅ 已上传! 片段数: {data.get('chunk_count', 0)}")
                    else:
                        st.error(f"❌ 上传失败: {resp.text}")
                except Exception as e:
                    st.error(f"❌ 请求失败: {e}")

        # 显示知识库统计
        try:
            stats = requests.get(f"{API_BASE}/kb/stats", timeout=2)
            if stats.status_code == 200:
                data = stats.json()
                st.info(f"📊 知识库: {data.get('document_count', 0)} 个文档片段")
        except:
            pass

# ============================================================
# 聊天历史
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # 如果是工具调用，额外显示工具信息
        if message.get("tool_calls"):
            st.caption(f"🔧 调用了 {message['tool_calls']} 个工具")

# ============================================================
# 聊天输入
# ============================================================

if prompt := st.chat_input("输入你的问题..."):
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 调用后端 API
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                payload = {
                    "message": prompt,
                    "session_id": st.session_state.session_id
                }
                resp = requests.post(
                    f"{API_BASE}{api_endpoint}",
                    json=payload,
                    timeout=60
                )

                if resp.status_code == 200:
                    data = resp.json()
                    reply = data.get("response", "(无回复)")
                    tool_calls = data.get("tool_calls", 0)

                    st.markdown(reply)

                    # 显示工具调用信息
                    if tool_calls > 0:
                        st.caption(f"🔧 调用了 {tool_calls} 个工具")

                    # 保存消息
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": reply,
                        "tool_calls": tool_calls
                    })
                else:
                    st.error(f"❌ 请求失败: HTTP {resp.status_code}")
                    st.code(resp.text[:500] if resp.text else "无响应")

            except requests.exceptions.Timeout:
                st.error("⏰ 请求超时，请稍后重试")
            except requests.exceptions.ConnectionError:
                st.error("🔌 无法连接后端服务，请确认服务已启动")
            except Exception as e:
                st.error(f"❌ 错误: {e}")
                import traceback

                st.code(traceback.format_exc())