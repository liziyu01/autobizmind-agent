"""
向量数据库测试脚本

测试文档加载、切片、存储和检索功能。
"""
import os
import sys


def main():
    print("=" * 50)
    print("   向量数据库测试")
    print("=" * 50)

    try:
        from app.vectordb import add_document, search_documents, get_kb_stats
    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        return 1

    # 1. 创建测试文档
    print("\n[1] 准备测试文档...")
    test_content = """
    电商退货政策

    1. 退货条件
    用户签收商品后7天内，商品未经使用、包装完好、不影响二次销售，可申请无理由退货。

    2. 退货流程
    用户需在订单页面提交退货申请，上传商品照片，等待客服审核。
    审核通过后，用户需将商品寄回指定仓库。

    3. 退款方式
    退货审核通过后，退款将在3-5个工作日内原路退回支付账户。

    4. 特殊情况
    生鲜食品、定制商品、贴身衣物等特殊商品不支持7天无理由退货。
    """

    # 写入临时文件
    test_file = "test_policy.txt"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_content)

    print(f"   ✅ 已创建测试文档: {test_file}")

    # 2. 添加文档到知识库
    print("\n[2] 添加文档到知识库...")
    try:
        count = add_document(test_file)
        print(f"   ✅ 已存入 {count} 个片段")
    except Exception as e:
        print(f"   ❌ 添加失败: {e}")
        return 1

    # 3. 查看统计信息
    print("\n[3] 知识库统计:")
    stats = get_kb_stats()
    print(f"   集合: {stats['collection_name']}")
    print(f"   文档数: {stats['document_count']}")
    print(f"   存储路径: {stats['persist_dir']}")

    # 4. 测试检索
    print("\n[4] 测试检索（相关问题）:")
    test_queries = [
        "退货条件是什么？",
        "怎么申请退货？",
        "食品能退货吗？",
        "退款要多久？",
        "今天天气怎么样？",  # 不相关的问题
    ]

    for query in test_queries:
        print(f"\n   问题: {query}")
        results = search_documents(query, top_k=2)
        if results:
            for i, doc in enumerate(results):
                # 只显示前 100 个字符
                preview = doc.page_content[:100].replace("\n", " ")
                print(f"      [{i + 1}] {preview}...")
        else:
            print("      (无相关结果)")

    # 5. 清理
    print("\n[5] 清理测试文件...")
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"   ✅ 已删除 {test_file}")

    print("\n" + "=" * 50)
    print("   ✅ 向量数据库测试通过！")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())