"""
Agent 核心模块

使用 LangGraph 构建单 Agent 对话引擎。
使用 RAG 检索增强生成节点。
"""
import logging
from typing import Dict, Any, List, Optional

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict, Annotated

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.config import config
from app.vectordb import search_documents

logger = logging.getLogger(__name__)

# 定义状态 State
class AgentState(TypedDict):
    messages: Annotated[List[Dict[str, Any]], add_messages]
    retrieved_context: Optional[str]

# 初始化 LLM
llm = ChatOpenAI(
    model=config.MODEL_NAME,
    api_key=config.OPENAI_API_KEY,
    base_url=config.OPENAI_BASE_URL,
    temperature=0.7
)

# 定义节点函数 Node
def chat_node(state: AgentState) -> Dict[str, Any]:
    """
    对话节点：从状态中读取消息，调用 LLM, 将回复追加到 messages。
    """
    messages = state.get("messages", [])

    # system tip
    if not messages or not isinstance(messages[0], SystemMessage):
        system_prompt = SystemMessage(
            content="你是一个智能助手，名叫 AutoBizMind Agent, 请用中文友好地回答问题。"
        )
        messages = [system_prompt] + messages

    try:
        response = llm.invoke(messages)
        logger.info(f"LLM 响应成功，长度：{len(response.content)}")
        return {"messages": [response]}
    except Exception as e:
        logger.error(f"LLM 调用失败：{e}")
        error_msg = AIMessage(content="抱歉，我遇到了技术问题，请稍后再试。")
        return {"messages": [error_msg]}

# RAG 检索节点
def rag_retrieval_node(state: AgentState) -> Dict[str, Any]:
    """
        RAG 检索节点：根据用户问题从知识库检索相关文档。
    """

    # 从状态中读取当前消息列表
    messages = state.get("messages", [])
    user_query = ""

    # 找到最后一条用户消息
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_query = msg.content
            break

    if not user_query:
        return {"retrieved_context": ""}

    # 从知识库检索
    try:
        docs = search_documents(user_query, top_k=3)

        if docs:
            context_parts = []
            for i, doc in enumerate(docs):
                context_parts.append(f"【文档片段 {i+1}】\n{doc.page_content}")

            context = "\n\n".join(context_parts)
            logger.info(f"📚 RAG 检索到 {len(docs)} 个片段")

            # 检检索结果存入状态
            return {"retrieved_context": context}
        else:
            return {"retrieved_context": ""}

    except Exception as e:
        logger.error(f"RAG 检索失败: {e}")
        return {"retrieved_context": ""}

# RAG 增强对话节点
def rag_chat_node(state: AgentState) -> Dict[str, Any]:
    messages = state.get("messages", [])
    context = state.get("retrieved_context", "")

    system_content ="""
你是一个智能助手，名叫 AutoBizMind。请基于以下参考资料回答问题。

【参考资料】
{context}

注意：
1. 如果参考资料中有相关信息，请基于参考资料回答
2. 如果参考资料中没有相关信息，请如实地说"资料库中没有相关信息"
3. 不要编造参考资料中没有的内容
"""
    system_prompt = SystemMessage(
        content=system_content.format(context=context or "（暂无参考资料）")
    )

    # 过滤原有的 SystemMessage，用新的替换
    filtered_messages = [msg for msg in messages if not isinstance(msg, SystemMessage)]
    messages_with_context = [system_prompt] + filtered_messages

    try:
        response = llm.invoke(messages_with_context)
        logger.info(f"RAG LLM 响应成功，长度: {len(response.content)} 字符")
        return {"messages": [response]}
    except Exception as e:
        logger.error(f"RAG LLM 调用失败: {e}")
        error_msg = AIMessage(content="抱歉，我遇到了技术问题，请稍后再试。")
        return {"messages": [error_msg]}

# 构建图 Graph （支持 RAG 模式）
def build_agent(use_rag: bool = False):
    """
    构建并编译 Agent 图

    use_rag: 是否启用 RAG 模式
    """
    graph_builder = StateGraph(AgentState)

    if use_rag:
        # RAG 模式
        graph_builder.add_node("retrieve", rag_retrieval_node)
        graph_builder.add_node("chat", rag_chat_node)
        graph_builder.add_edge(START, "retrieve")
        graph_builder.add_edge("retrieve", "chat")
        graph_builder.add_edge("chat", END)

    else:
        # 普通模式：直接对话
        graph_builder.add_node("chat", chat_node)
        graph_builder.add_edge(START, "chat")
        graph_builder.add_edge("chat", END)

    return graph_builder.compile()

# 创建 Agent 实例（普通模式 + RAG 模式）
agent = build_agent(use_rag=False)
agent_rag = build_agent(use_rag=True)

logger.info("✅ Agent 已初始化完成（普通模式 + RAG 模式）")