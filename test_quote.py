"""
报价核算工具测试
"""
import sys
import json


def main():
    print("=" * 50)
    print("   报价核算工具测试")
    print("=" * 50)

    try:
        from app.tool_registry import call_tool_v2, get_all_tools_metadata
        import app.tools
    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return 1

    # 1. 查看所有工具
    print("\n[1] 已注册工具:")
    tools = get_all_tools_metadata()
    for name in tools.keys():
        print(f"   - {name}")

    # 2. 测试报价（金牌客户）
    print("\n[2] 测试报价: 何刚（金牌客户）→ iPhone 15 Pro")
    result = call_tool_v2("calculate_quote", {
        "customer_name": "何刚",
        "product_name": "iPhone 15 Pro",
        "quantity": 1
    })

    if result.success:
        data = result.data
        print(f"   ✅ 报价生成成功")
        print(f"   📋 报价单:")
        print(f"      客户: {data['customer']['name']}（{data['customer']['tier']}）")
        print(f"      商品: {data['product']['name']}")
        print(f"      原价: ￥{data['subtotal']}")
        print(f"      折扣: {data['discount_percent']}")
        print(f"      折后价: ￥{data['total']}")
        print(f"      节省: ￥{data['saved']}")
    else:
        print(f"   ❌ {result.error}")

    # 3. 测试报价（普通客户）
    print("\n[3] 测试报价: 孙华（普通客户）→ 小米空气净化器")
    result = call_tool_v2("calculate_quote", {
        "customer_name": "孙华",
        "product_name": "小米 空气净化器",
        "quantity": 2
    })

    if result.success:
        data = result.data
        print(f"   ✅ 报价生成成功")
        print(f"   📋 报价单:")
        print(f"      客户: {data['customer']['name']}（{data['customer']['tier']}）")
        print(f"      商品: {data['product']['name']}")
        print(f"      数量: {data['quantity']}")
        print(f"      原价: ￥{data['subtotal']}")
        print(f"      折扣: {data['discount_percent']}")
        print(f"      折后价: ￥{data['total']}")
    else:
        print(f"   ❌ {result.error}")

    # 4. 测试不存在的客户
    print("\n[4] 测试异常: 不存在的客户")
    result = call_tool_v2("calculate_quote", {
        "customer_name": "奥特曼",
        "product_name": "iPhone 15 Pro"
    })
    if result.success:
        print("   ⚠️ 预期失败，但成功了")
    else:
        print(f"   ✅ 正确返回错误: {result.error}")

    print("\n" + "=" * 50)
    print("   ✅ 报价核算测试完成！")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())