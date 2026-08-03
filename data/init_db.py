"""
初始化模拟数据

创建 SQLite 数据库，生成电商订单测试数据。
"""
import os
import sqlite3
from datetime import datetime, timedelta
import random

# 数据目录
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "orders.db")


def get_connection():
    """获取数据库连接"""
    return sqlite3.connect(DB_PATH)


def init_database():
    """初始化数据库：创建表并插入测试数据"""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. 创建订单表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_id TEXT,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # 2. 检查是否已有数据
    cursor.execute("SELECT COUNT(*) FROM orders")
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"📊 数据库已有 {count} 条订单记录，跳过初始化")
        conn.close()
        return

    # 3. 生成模拟数据
    customers = [
        ("张三", "C001"),
        ("李四", "C002"),
        ("王五", "C003"),
        ("赵六", "C004"),
        ("孙七", "C005"),
        ("周八", "C006"),
    ]

    statuses = ["pending", "paid", "shipped", "completed", "cancelled"]
    status_cn = {
        "pending": "待支付",
        "paid": "已支付",
        "shipped": "已发货",
        "completed": "已完成",
        "cancelled": "已取消"
    }

    orders = []
    base_date = datetime(2026, 7, 1)

    for i in range(100):
        customer = random.choice(customers)
        status = random.choice(statuses)
        amount = round(random.uniform(50, 5000), 2)
        days_offset = random.randint(0, 28)
        created_at = base_date + timedelta(days=days_offset)

        orders.append((
            customer[0],
            customer[1],
            amount,
            status,
            created_at.strftime("%Y-%m-%d %H:%M:%S")
        ))

    # 按时间排序（最新的在前）
    orders.sort(key=lambda x: x[4], reverse=True)

    # 4. 插入数据
    cursor.executemany("""
        INSERT INTO orders (customer_name, customer_id, amount, status, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, orders)

    conn.commit()

    # 5. 统计
    cursor.execute("SELECT COUNT(*) FROM orders")
    total = cursor.fetchone()[0]
    print(f"✅ 数据库初始化完成，共 {total} 条订单记录")

    conn.close()


def query_orders_sql(
        customer_name: str = None,
        status: str = None,
        limit: int = 20
) -> list:
    """
    查询订单（SQL 实现）。

    这是工具的内部实现，供 tool_registry 注册时使用。
    """
    conn = get_connection()
    cursor = conn.cursor()

    sql = "SELECT order_id, customer_name, amount, status, created_at FROM orders WHERE 1=1"
    params = []

    if customer_name:
        sql += " AND customer_name LIKE ?"
        params.append(f"%{customer_name}%")

    if status:
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "order_id": row[0],
            "customer_name": row[1],
            "amount": row[2],
            "status": row[3],
            "created_at": row[4]
        }
        for row in rows
    ]


if __name__ == "__main__":
    init_database()