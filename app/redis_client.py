"""
Redis 客户端封装模块

提供统一的 Redis 连接管理和基础操作接口。
使用单例模式避免重复创建连接，提高性能。
"""
import json
import logging
from typing import Optional, Any, Dict

import redis
from redis.exceptions import RedisError, ConnectionError, TimeoutError

from app.config import config

# 配置日志
logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis 客户端单例类

    特性：
    - 连接池管理，自动重连
    - 支持 String、Hash、List 等基础数据结构
    - 序列化/反序列化 JSON 自动处理
    - 异常捕获并降级，不中断主业务
    """

    _instance: Optional["RedisClient"] = None
    _client: Optional[redis.Redis] = None

    def __new__(cls) -> "RedisClient":
        """单例模式：确保全局只有一个实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化连接池（只执行一次）"""
        if self._client is not None:
            return

        try:
            # 创建 Redis 连接池
            pool = redis.ConnectionPool(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                decode_responses=True,  # 自动将返回的 bytes 转为 str
                max_connections=10,  # 连接池大小
                socket_timeout=5,  # 读写超时 5 秒
                socket_connect_timeout=3,  # 连接超时 3 秒
                retry_on_timeout=True,  # 超时自动重试
            )

            self._client = redis.Redis(connection_pool=pool)

            # 测试连接
            self._client.ping()
            logger.info(f"✅ 成功连接到 Redis: {config.REDIS_HOST}:{config.REDIS_PORT}")

        except (ConnectionError, TimeoutError) as e:
            logger.error(f"❌ Redis 连接失败: {e}")
            self._client = None
            raise RuntimeError("Redis 服务不可用，请检查服务是否启动") from e
        except Exception as e:
            logger.error(f"❌ Redis 初始化异常: {e}")
            self._client = None
            raise

    @property
    def client(self) -> redis.Redis:
        """获取原始 Redis 客户端（用于高级操作）"""
        if self._client is None:
            raise RuntimeError("Redis 客户端未初始化")
        return self._client


    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置键值对

        Args:
            key: 键名
            value: 值（会自动序列化为 JSON 字符串）
            ttl: 过期时间（秒），None 表示永不过期

        Returns:
            是否设置成功
        """
        try:
            serialized = json.dumps(value, ensure_ascii=False)
            if ttl:
                return self.client.setex(key, ttl, serialized)
            return self.client.set(key, serialized)
        except (RedisError, TypeError) as e:
            logger.error(f"Redis SET 失败 [{key}]: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """
        获取键对应的值

        Args:
            key: 键名

        Returns:
            反序列化后的 Python 对象，不存在时返回 None
        """
        try:
            raw = self.client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except json.JSONDecodeError:
            # 如果不是 JSON 格式，直接返回原始字符串
            return raw
        except RedisError as e:
            logger.error(f"Redis GET 失败 [{key}]: {e}")
            return None

    def delete(self, *keys: str) -> int:
        """
        删除一个或多个键

        Returns:
            成功删除的键数量
        """
        if not keys:
            return 0
        try:
            return self.client.delete(*keys)
        except RedisError as e:
            logger.error(f"Redis DELETE 失败 {keys}: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return self.client.exists(key) > 0
        except RedisError as e:
            logger.error(f"Redis EXISTS 失败 [{key}]: {e}")
            return False

    def expire(self, key: str, ttl: int) -> bool:
        """设置键的过期时间（秒）"""
        try:
            return self.client.expire(key, ttl)
        except RedisError as e:
            logger.error(f"Redis EXPIRE 失败 [{key}]: {e}")
            return False

    def ttl(self, key: str) -> int:
        """获取键的剩余生存时间（秒），-1 表示永久，-2 表示不存在"""
        try:
            return self.client.ttl(key)
        except RedisError as e:
            logger.error(f"Redis TTL 失败 [{key}]: {e}")
            return -2

    # ========== Hash 操作（用于工具注册） ==========

    def hset(self, name: str, key: str, value: Any) -> bool:
        """设置 Hash 表中指定字段的值"""
        try:
            serialized = json.dumps(value, ensure_ascii=False)
            self.client.hset(name, key, serialized)
            return True
        except (RedisError, TypeError) as e:
            logger.error(f"Redis HSET 失败 [{name}:{key}]: {e}")
            return False

    def hget(self, name: str, key: str) -> Optional[Any]:
        """获取 Hash 表中指定字段的值"""
        try:
            raw = self.client.hget(name, key)
            if raw is None:
                return None
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
        except RedisError as e:
            logger.error(f"Redis HGET 失败 [{name}:{key}]: {e}")
            return None

    def hgetall(self, name: str) -> Dict[str, Any]:
        """获取 Hash 表中所有字段和值"""
        try:
            raw_data = self.client.hgetall(name)
            result = {}
            for k, v in raw_data.items():
                try:
                    result[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    result[k] = v
            return result
        except RedisError as e:
            logger.error(f"Redis HGETALL 失败 [{name}]: {e}")
            return {}

    # ========== 健康检查 ==========

    def ping(self) -> bool:
        """检查 Redis 服务是否可达"""
        try:
            return self.client.ping()
        except RedisError:
            return False


# 创建全局单例实例
redis_client = RedisClient()