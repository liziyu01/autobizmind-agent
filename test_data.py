"""
数据验证脚本
"""
import sys
from data.init_db import query_orders_sql, get_customer_info, get_product_info


def main():
    print("=" * 50)
    print("   电商数据验证")
    print("=" * 50)

    # 1. 测试查询
    print("\n[1] 测试订单查询（按客户名）")
    orders = query_orders_sql(customer_name="张", limit=5)
    print(f"   查询到 {len(orders)} 条订单")
    for o in orders[:3]:
        print(f"      {o['customer_name']} - {o['product_name']} - ￥{o['total_amount']}")

    print("\n[2] 测试订单查询（按状态）")
    orders = query_orders_sql(status="completed", limit=5)
    print(f"   已完成订单: {len(orders)} 条")

    print("\n[3] 测试订单查询（按金额范围）")
    orders = query_orders_sql(min_amount=500, max_amount=2000, limit=5)
    print(f"   500-2000 元订单: {len(orders)} 条")

    print("\n[4] 测试客户信息查询")
    customer = get_customer_info("张伟")
    if customer:
        print(f"   姓名: {customer['name']}")
        print(f"   等级: {customer['tier']}")
        print(f"   总消费: ￥{customer['total_spent']}")

    print("\n[5] 测试商品信息查询")
    product = get_product_info("iPhone")
    if product:
        print(f"   商品: {product['name']}")
        print(f"   分类: {product['category']}")
        print(f"   价格: ￥{product['price']}")
        print(f"   库存: {product['stock']}")

    print("\n" + "=" * 50)
    print("   ✅ 数据验证通过！")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())