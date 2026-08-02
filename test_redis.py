"""
Redis 连接测试脚本

直接运行此文件验证 Redis 是否正常工作。
"""
import sys
import logging

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    print("=" * 50)
    print("   Redis 连接测试")
    print("=" * 50)

    try:
        # 导入封装的客户端
        from app.redis_client import redis_client

        # 1. Ping 测试
        print("\n[1] 执行 PING...")
        if redis_client.ping():
            print("✅ PONG - Redis 服务正常响应")
        else:
            print("❌ PING 失败")
            return 1

        # 2. Set/Get 测试
        print("\n[2] 测试 SET / GET...")
        test_key = "test:hello"
        test_value = {"message": "Hello AutoBizMind!", "timestamp": "2026-07-25"}

        # 写入
        success = redis_client.set(test_key, test_value, ttl=60)
        print(f"   SET {test_key} = {test_value} -> {'✅ 成功' if success else '❌ 失败'}")

        # 读取
        retrieved = redis_client.get(test_key)
        print(f"   GET {test_key} -> {retrieved}")

        # 验证一致性
        if retrieved == test_value:
            print("✅ 读写一致性验证通过")
        else:
            print("❌ 读写一致性验证失败")

        # 3. 检查 TTL
        print("\n[3] 检查过期时间 (TTL)...")
        ttl = redis_client.ttl(test_key)
        print(f"   {test_key} 剩余生存时间: {ttl} 秒")

        # 4. 删除测试
        print("\n[4] 测试 DELETE...")
        deleted = redis_client.delete(test_key)
        print(f"   删除 {test_key} -> 删除了 {deleted} 个键")

        exists = redis_client.exists(test_key)
        print(f"   再次检查存在性 -> {exists} (False 表示已删除)")

        print("\n" + "=" * 50)
        print("   ✅ 所有 Redis 测试通过！")
        print("=" * 50)
        return 0

    except ImportError as e:
        print(f"\n❌ 导入错误: {e}")
        print("   请确保在项目根目录下运行，且虚拟环境已激活。")
        return 1
    except Exception as e:
        print(f"\n❌ 测试过程发生异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())