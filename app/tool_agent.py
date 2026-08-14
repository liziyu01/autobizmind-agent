"""
工具调用 Agent

基于 LangGraph 实现「自主决策 → 调用工具 → 返回结果」的完整链路。
"""
import json
import logging
from typing import Dict, Any, List, Literal, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from app.config import config
from app.tool_registry import get_all_tools_metadata, call_tool, call_tool_v2, ToolCallResult

logger = logging.getLogger(__name__)


# ============================================================
# 1. 定义状态（扩展支持工具调用）
# ============================================================

class ToolAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    tool_results: List[Dict[str, Any]]
    execution_summary: List[Dict[str, Any]] # 执行摘要（用于路由决策）

# ============================================================
# 2. 初始化 LLM
# ============================================================

llm = ChatOpenAI(
    model=config.MODEL_NAME,
    api_key=config.OPENAI_API_KEY,
    base_url=config.OPENAI_BASE_URL,
    temperature=0.3,
)

# ============================================================
# 3. 构建工具列表描述（注入 System Prompt）
# ============================================================

def build_tools_description() -> str:
    """从 Redis 读取所有已注册工具的元数据，生成文本描述。"""
    tools = get_all_tools_metadata()

    if not tools:
        return "（当前没有可用工具）"

    lines = []
    for name, meta in tools.items():
        lines.append(f"工具名称: {name}")
        lines.append(f"功能描述: {meta.get('description', '无描述')}")
        lines.append(f"参数: {json.dumps(meta.get('inputSchema', {}), ensure_ascii=False)}")
        lines.append("---")

    return "\n".join(lines)


def build_tool_system_prompt() -> SystemMessage:
    """生成包含工具列表的 System Prompt。"""
    tools_desc = build_tools_description()

    content = f"""你是一个智能助手，名叫 AutoBizMind。你可以使用工具来完成用户的任务。

【可用工具】
{tools_desc}

【工具调用规则】
当用户的问题需要工具辅助时，你必须输出以下格式的 JSON：
```json
{{"action": "工具名称", "params": {{"参数名": "参数值"}}}}
```

【重要】
1. 如果你认为不需要调用工具就能回答，直接输出回答内容（不要用 JSON 格式）
2. 如果工具执行后还需要进一步操作，可以继续调用工具
3. 所有输出必须用中文（工具参数除外）

【示例】
用户：「查询张三的订单」
输出：
```json
{{"action": "query_orders", "params": {{"customer_name": "张三"}}}}
```

用户：「你好」
输出：你好！我是 AutoBizMind，有什么可以帮你的吗？
"""
    return SystemMessage(content=content)


# ============================================================
# 4. 节点函数：决定是否调用工具
# ============================================================
def should_use_tool(state: ToolAgentState) -> Dict[str, Any]:
    """
    决策节点：判断是否需要调用工具。

    1.如果 LLM 返回 JSON 格式的 tool call → 进入工具执行节点
	2.如果 LLM 返回普通文本 → 直接输出（进入 END）
    """
    messages = state.get("messages", [])

    # 注入 System Prompt
    system_prompt = build_tool_system_prompt()
    messages_with_system = [system_prompt] + messages

    try:
        response = llm.invoke(messages_with_system)
        content = response.content

        # 尝试解析 JSON，提取 JSON（处理 markdown 代码块）
        json_str = content.strip()

        if "```json" in json_str:  # 提取 json ... 中的内容
            start = json_str.find("```json") + 7
            end = json_str.find("```", start)
            json_str = json_str[start:end].strip()
        elif "```" in json_str:
            start = json_str.find("```") + 3
            end = json_str.find("```", start)
            json_str = json_str[start:end].strip()

        # 尝试解析为 JSON
        try:
            data = json.loads(json_str)
            if "action" in data and "params" in data:  # 这是一个工具调用指令
                logger.info(f"🔧 Agent 决定调用工具: {data['action']}")
                return {
                    "messages": [response],
                    "tool_results": [{"action": data["action"], "params": data["params"]}]
                }

        # 不是 JSON，直接作为普通回答
        except json.JSONDecodeError:
            logger.info("💬 Agent 直接回答（无需工具）")

        # 普通回答
        return {
            "messages": [response],
            "tool_results": []
        }

    except Exception as e:
        logger.error(f"❌ 决策节点出错: {e}")
        error_msg = AIMessage(content="抱歉，我在处理时遇到了问题，请稍后再试。")
        return {
            "messages": [error_msg],
            "tool_results": []
        }


# ============================================================
# 5. 节点函数：执行工具(弃用 -> 转升级版 execute_tool
# ============================================================
# def execute_tool(state: ToolAgentState) -> Dict[str, Any]:
#     """工具执行节点：根据决策结果调用工具。"""
#     tool_results = state.get("tool_results", [])
#     if not tool_results:  # 没有工具要执行，直接返回
#         return {}
#
#     result_messages = []
#
#     for tool_call in tool_results:
#         action = tool_call.get("action")
#         params = tool_call.get("params", {})
#
#         logger.info(f"⚙️ 执行工具: {action} 参数: {params}")
#
#         try:
#             result = call_tool(action, params)
#
#             # 将结果转为字符串，方便 LLM 理解
#             result_str = json.dumps(result, ensure_ascii=False, indent=2)
#             logger.info(f"✅ 工具执行成功: {action}")
#
#             # 把工具执行结果作为 AI 消息返回，追加到对话中
#             result_msg = AIMessage(
#                 content=f"工具 {action} 执行结果：\n{result_str}"
#             )
#             result_messages.append(result_msg)
#
#         except Exception as e:
#             logger.error(f"❌ 工具执行失败 {action}: {e}")
#             error_msg = AIMessage(
#                 content=f"工具 {action} 执行失败：{str(e)}"
#             )
#             result_messages.append(error_msg)
#
#     # 返回结果消息（追加到 messages）
#     return {
#         "messages": result_messages,
#         "tool_results": []
#     }

# ============================================================
# 5. 升级：execute_tool 节点（支持结构化错误）
# ============================================================
def execute_tool(state: ToolAgentState) -> Dict[str, Any]:
    """
    工具执行节点（增强版）：支持结构化错误返回。

    执行结果会以结构化的方式返回给 Agent，让 Agent 能：
    1. 识别成功/失败
    2. 理解错误类型
    3. 根据错误做出下一步决策
    """
    tool_results = state.get("tool_results", [])

    if not tool_results:
        return {}

    result_messages = []
    execution_summary = []

    for tool_call in tool_results:
        action = tool_call.get("action")
        params = tool_call.get("params", {})

        logger.info(f"⚙️ 执行工具: {action} 参数: {params}")

        # 使用增强版调用
        result: ToolCallResult = call_tool_v2(action, params, max_retries=2)

        if result.success:
            logger.info(f"✅ 工具执行成功: {action} (耗时: {result.duration_ms}ms)")

            # 格式化成功结果
            data_str = json.dumps(result.data, ensure_ascii=False, indent=2)
            # 如果结果太长，截断
            if len(data_str) > 2000:
                data_str = data_str[:2000] + "...(截断)"

            result_msg = AIMessage(
                content=f"✅ 工具 {action} 执行成功：\n{data_str}"
            )

            result_messages.append(result_msg)

            execution_summary.append({
                "tool": action,
                "success": True,
                "duration_ms": result.duration_ms
            })

        else:
            logger.warning(f"⚠️ 工具执行失败: {action} [{result.error_type}]: {result.error}")

            # 根据错误类型生成不同的提示
            error_hint = _get_error_hint(result.error_type)

            result_msg = AIMessage(
                content=f"❌ 工具 {action} 执行失败：{result.error}\n{error_hint}"
            )

            execution_summary.append({
                "tool": action,
                "success": False,
                "error": result.error,
                "error_type": result.error_type,
                "duration_ms": result.duration_ms
            })

        result_messages.append(result_msg)

    # 在状态中记录执行摘要（可用于后续决策）
    return {
        "messages": result_messages,
        "tool_results": [],
        "execution_summary": execution_summary  # 新增
    }


def _get_error_hint(error_type: str) -> str:
    """根据错误类型生成友好的提示"""
    hints = {
        "NOT_FOUND": "提示：工具可能未注册，请检查工具名称是否正确。",
        "PARAM_ERROR": "提示：请检查参数格式是否正确。",
        "NETWORK_ERROR": "提示：网络可能不稳定，请稍后重试。",
        "BUSINESS_ERROR": "提示：业务逻辑执行失败，请检查输入数据。",
        "UNKNOWN_ERROR": "提示：发生了未知错误，请查看日志。",
    }
    return hints.get(error_type, "提示：请检查输入或稍后重试。")

# ============================================================
# 6. 条件边函数：判断下一步走向
# ============================================================
def route_after_decision(state: ToolAgentState) -> Literal["execute_tool", "END"]:
    """
    根据决策结果路由。
    """
    tool_results = state.get("tool_results", [])
    if tool_results:
        return "execute_tool"
    return "END"

# ============================================================
# 转 -> 升级版 route_after_execution
# ============================================================
# def route_after_execution(state: ToolAgentState) -> Literal["should_use_tool", "END"]:
#     """
#     工具执行后，判断是否需要继续调用工具。
#     """
#
#     # 检查最后一条消息是否为错误，或是否包含工具执行结果
#     messages = state.get("messages", [])
#     if not messages:
#         return "END"
#
#
#     last_msg = messages[-1]
#     content = last_msg.content if hasattr(last_msg, "content") else ""
#
#     # 如果执行结果包含错误，或者只有工具结果，都回到决策节点让 Agent 决定是继续调用工具还是结束
#     if "工具" in content and ("执行结果" in content or "执行失败" in content):
#         return "should_use_tool"
#
#     return "END"

# ============================================================
# 升级：条件边函数（支持错误后的重试）
# ============================================================

def route_after_execution(state: ToolAgentState) -> Literal["should_use_tool", "END"]:
    """
    工具执行后的路由（增强版）。

    即使工具执行失败，也回到决策节点，让 Agent 决定：
    1. 重试（修改参数后重试）
    2. 换一个工具
    3. 告诉用户失败信息并结束
    """
    messages = state.get("messages", [])
    execution_summary = state.get("execution_summary", [])

    if not messages:
        return "END"

    # 检查执行摘要，如果有任何工具执行，都回到决策节点
    # 让 Agent 有机会处理结果（成功或失败）
    if execution_summary:
        # 检查是否所有工具都执行成功了
        all_success = all(item.get("success", False) for item in execution_summary)
        if all_success:
            # ✅ 全部成功 → 直接结束，不再循环
            return "should_use_tool"
        else:
            # ❌ 有失败 → 回到决策节点，让 Agent 决定是重试还是放弃
            return "should_use_tool"
    return "END"

# ============================================================
# 7. 构建图
# ============================================================
def build_tool_agent():
    """
    构建工具调用 Agent 图。
结构：
START → should_use_tool（决策）
            ├→ 无工具调用 → END
            └→ 有工具调用 → execute_tool → should_use_tool（循环）
"""
    graph_builder = StateGraph(ToolAgentState)

    # 添加节点
    graph_builder.add_node("should_use_tool", should_use_tool)
    graph_builder.add_node("execute_tool", execute_tool)

    # 起始边
    graph_builder.add_edge(START, "should_use_tool")

    # 条件边（决策后路由）
    graph_builder.add_conditional_edges(
        "should_use_tool",
        route_after_decision,
        {
            "execute_tool": "execute_tool",
            "END": END
        }
    )

    # 条件边（工具执行后路由）
    graph_builder.add_conditional_edges(
        "execute_tool",
        route_after_execution,
        {
            "should_use_tool": "should_use_tool",
            "END": END
        }
    )

    return graph_builder.compile()


# ============================================================
# 8. 创建全局实例
# ============================================================
tool_agent = build_tool_agent()
logger.info("✅ 工具调用 Agent 已初始化完成")