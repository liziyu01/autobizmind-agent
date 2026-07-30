"""
Agent 核心模块

使用 LangGraph 构建单 Agent 对话引擎。
"""
import logging
from typing import Dict, Any, List

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict, Annotated

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.config import config

logger = logging.getLogger(__name__)

# 定义状态 State
class AgentState(TypedDict):
    messages: Annotated[List[Dict[str, Any]], add_messages]

# 初始化 LLM
llm = ChatOpenAI(
    model=config.MODEL_NAME,
    api_key=config.OPENAI_API_KEY,
    base_url=config.OPENAI_BASE_RUL,
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
        return {"messages": response}
    except Exception as e:
        logger.error(f"LLM 调用失败：{e}")
        error_msg = AIMessage(content="抱歉，我遇到了技术问题，请稍后再试。")
        return {"messages": [error_msg]}

# 构件图 Graph
def build_agent():
    """构建并编译 Agent 图"""
    graph_buider = StateGraph(AgentState)

    graph_buider.add_node("chat", chat_node)

    graph_buider.add_edge(START, "chat")
    graph_buider.add_edge("chat", END)

    return graph_buider.compile()

# 创建 Agent 实例
agent = build_agent()
logger.info("Agent 已初始化完成")