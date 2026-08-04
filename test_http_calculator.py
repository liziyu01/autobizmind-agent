"""
HTTP 和计算器工具测试
"""
import sys


def main():
    print("=" * 50)
    print("   HTTP + 计算器 工具测试")
    print("=" * 50)

    try:
        from app.tool_registry import call_tool, get_all_tools_metadata
        import app.tools  # 导入即自动注册
    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return 1

    # 1. 查看所有工具
    print("\n[1] 已注册的工具:")
    tools = get_all_tools_metadata()
    for name in tools.keys():
        print(f"   - {name}")

    # 2. 测试计算器
    print("\n[2] 测试计算器:")
    test_exprs = [
        "2 + 3 * 4",
        "sqrt(144)",
        "pow(2, 10)",
        "100 / 0",  # 除零测试
    ]
    for expr in test_exprs:
        result = call_tool("calculator", {"expression": expr})
        print(f"   {expr} = {result}")

    # 3. 测试 HTTP（可选，需要网络）
    print("\n[3] 测试 HTTP 请求（GitHub API）:")
    try:
        result = call_tool("http_request", {
            "url": "https://api.github.com/zen",
            "method": "GET"
        })
        if result.get("status_code") == 200:
            print(f"   ✅ GitHub Zen: {result.get('data')}")
        else:
            print(f"   ⚠️ 状态码: {result.get('status_code')}")
    except Exception as e:
        print(f"   ⚠️ 测试跳过（网络可能不通）: {e}")

    # 4. 测试 HTTP POST
    print("\n[4] 测试 HTTP POST（JSONPlaceholder）:")
    try:
        result = call_tool("http_request", {
            "url": "https://jsonplaceholder.typicode.com/posts",
            "method": "POST",
            "body": {"title": "test", "body": "hello", "userId": 1}
        })
        if result.get("status_code") == 201:
            print(f"   ✅ 创建成功: {result.get('data', {}).get('id')}")
        else:
            print(f"   ⚠️ 状态码: {result.get('status_code')}")
    except Exception as e:
        print(f"   ⚠️ 测试跳过: {e}")

    print("\n" + "=" * 50)
    print("   ✅ 测试完成！")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())