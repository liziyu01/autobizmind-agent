"""
工具：计算器

安全地执行数学表达式求值。
"""
import logging
import math
from typing import Union, Optional

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tool_registry import register_tool

logger = logging.getLogger(__name__)

# ============================================================
# 1. 安全表达式求值
# ============================================================
# 为什么不用 eval？
# - eval 可以执行任意 Python 代码，有安全风险
# - 但我们可以限制 eval 可用的函数和变量（受限环境）
# - 或者使用 ast.literal_eval 只支持字面量（不支持表达式）
#
# 方案：使用受限的 eval，只暴露数学函数和安全操作符

# 白名单：允许的数学函数和常量
_SAFE_NAMESPACE = {
    # 数学函数
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    # 常量
    "pi": math.pi,
    "e": math.e,
    # 类型转换
    "int": int,
    "float": float,
}

# 允许的数学函数（从 math 模块导入）
for name in [
    "sqrt", "pow", "sin", "cos", "tan", "log", "log10",
    "exp", "floor", "ceil", "radians", "degrees"
]:
    if hasattr(math, name):
        _SAFE_NAMESPACE[name] = getattr(math, name)


def _is_safe_expression(expr: str) -> bool:
    """
    检查表达式是否安全（不含危险字符）。

    禁止：
    - __（双下划线，可访问私有属性）
    - import（导入模块）
    - exec / eval（递归调用）
    - .（点号，可访问对象属性）
    """
    dangerous_patterns = ["__", "import", "exec", "eval", "globals", "locals"]
    expr_lower = expr.lower()
    for pattern in dangerous_patterns:
        if pattern in expr_lower:
            return False
    # 检查括号是否匹配
    if expr.count("(") != expr.count(")"):
        return False
    return True


def calculate(expression: str) -> Union[float, int, str]:
    """
    计算数学表达式。

    Args:
        expression: 数学表达式，如 "2 + 3 * 4" 或 "sqrt(16) + pi"

    Returns:
        计算结果（数字）或错误信息
    """
    logger.info(f"🧮 计算: {expression}")

    # 去除空白
    expression = expression.strip()

    if not expression:
        return "表达式为空"

    # 安全检查
    if not _is_safe_expression(expression):
        logger.warning(f"⚠️ 表达式包含危险字符: {expression}")
        return "表达式包含不安全的字符，请重试"

    try:
        # 在受限环境中执行计算
        result = eval(expression, {"__builtins__": {}}, _SAFE_NAMESPACE)

        # 处理结果格式
        if isinstance(result, float):
            # 如果是整数，转成 int 显示
            if result.is_integer():
                result = int(result)
            else:
                result = round(result, 6)  # 保留 6 位小数

        logger.info(f"✅ 计算结果: {expression} = {result}")
        return result

    except ZeroDivisionError:
        return "错误：除零操作"
    except SyntaxError:
        return "错误：表达式语法不正确"
    except NameError:
        return "错误：使用了未定义的函数或变量"
    except Exception as e:
        logger.error(f"❌ 计算失败: {e}")
        return f"计算错误: {str(e)}"


# ============================================================
# 2. MCP 元数据
# ============================================================

TOOL_NAME = "calculator"
TOOL_DESCRIPTION = """执行数学表达式计算。
支持四则运算、括号、数学函数（sqrt, sin, cos, log, pow 等）。
适用于：数值计算、百分比计算、统计计算等场景。"""

TOOL_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "expression": {
            "type": "string",
            "description": "数学表达式，如 '2 + 3 * 4' 或 'sqrt(16) * 10'",
            "examples": ["2 + 3", "100 * 0.8", "sqrt(144)", "pow(2, 10)"]
        }
    },
    "required": ["expression"]
}


# ============================================================
# 3. 注册工具
# ============================================================

def register():
    return register_tool(
        name=TOOL_NAME,
        description=TOOL_DESCRIPTION,
        input_schema=TOOL_INPUT_SCHEMA,
        handler=calculate
    )


register()
logger.info(f"📦 工具已注册: {TOOL_NAME}")