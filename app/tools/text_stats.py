"""
工具：文本统计

统计文本的字数、字符数、句数等信息。
（用于演示热加载功能）
"""
import logging

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tool_registry import register_tool

logger = logging.getLogger(__name__)


# ============================================================
# 1. 工具执行函数
# ============================================================

def text_stats(text: str, include_spaces: bool = True) -> dict:
    """
    统计文本信息。

    Args:
        text: 要统计的文本
        include_spaces: 是否包含空格（字符数统计）

    Returns:
        {
            "char_count": 字符数,
            "word_count": 单词数（中文按字算）,
            "sentence_count": 句数,
            "line_count": 行数,
            "has_chinese": 是否包含中文
        }
    """
    logger.info(f"📊 文本统计: 长度 {len(text)}")

    if not text:
        return {
            "char_count": 0,
            "word_count": 0,
            "sentence_count": 0,
            "line_count": 0,
            "has_chinese": False
        }

    # 字符数
    char_count = len(text) if include_spaces else len(text.replace(" ", ""))

    # 单词数（按空格分割，中文按字符数）
    word_count = len(text.split())
    # 如果全是中文或中英混合，大致统计
    if word_count < 10 and len(text) > 10:
        word_count = len([c for c in text if c.isalnum() or c.isalpha()])

    # 句数（按 。！？.\n 分割）
    sentence_count = 0
    for sep in ["。", "！", "？", ".", "!", "?"]:
        sentence_count += text.count(sep)
    if sentence_count == 0 and text.strip():
        sentence_count = 1

    # 行数
    line_count = text.count("\n") + 1

    # 是否包含中文
    has_chinese = any("\u4e00" <= c <= "\u9fff" for c in text)

    return {
        "char_count": char_count,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "line_count": line_count,
        "has_chinese": has_chinese
    }


# ============================================================
# 2. MCP 元数据
# ============================================================

TOOL_NAME = "text_stats"
TOOL_DESCRIPTION = """统计文本信息，包括字符数、单词数、句数等。
适用于：统计文章长度、分析文本特征、文档信息提取等场景。"""

TOOL_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {
            "type": "string",
            "description": "要统计的文本内容"
        },
        "include_spaces": {
            "type": "boolean",
            "description": "是否包含空格统计，默认 True",
            "default": True
        }
    },
    "required": ["text"]
}


# ============================================================
# 3. 注册工具
# ============================================================

def register():
    return register_tool(
        name=TOOL_NAME,
        description=TOOL_DESCRIPTION,
        input_schema=TOOL_INPUT_SCHEMA,
        handler=text_stats
    )


register()
logger.info(f"📦 工具已注册: {TOOL_NAME}")