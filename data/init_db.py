"""
初始化电商 Demo 数据

包含：客户、商品、订单 三张表，带关联关系。
"""
import os
import sqlite3
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 数据目录
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "ecommerce.db")


def get_connection():
    """获取数据库连接"""
    return sqlite3.connect(DB_PATH)


# ============================================================
# 1. 创建表结构
# ============================================================

def create_tables(conn: sqlite3.Connection) -> None:
    """创建三张核心表"""
    cursor = conn.cursor()

    # 客户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            tier TEXT NOT NULL DEFAULT '普通',
            register_date TEXT NOT NULL,
            total_spent REAL DEFAULT 0
        )
    """)

    # 商品表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0
        )
    """)

    # 订单表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    conn.commit()
    print("✅ 表结构创建完成")


# ============================================================
# 2. 生成模拟数据
# ============================================================

def generate_customers() -> List[Dict[str, Any]]:
    """生成 30 个客户"""
    first_names = ["张", "李", "王", "刘", "陈", "杨", "赵", "黄", "周", "吴",
                   "徐", "孙", "马", "朱", "胡", "郭", "林", "何", "高", "郑",
                   "罗", "梁", "谢", "宋", "唐", "许", "韩", "冯", "邓", "曹"]
    second_names = ["伟", "芳", "娜", "秀英", "敏", "静", "丽", "强", "磊", "军",
                    "洋", "勇", "艳", "杰", "娟", "涛", "明", "超", "秀兰", "霞",
                    "平", "刚", "桂英", "涛", "慧", "建", "文", "华", "飞", "玉兰"]

    tiers = ["普通", "普通", "普通", "银牌", "银牌", "金牌"]
    base_date = datetime(2025, 1, 1)

    customers = []
    for i in range(30):
        name = random.choice(first_names) + random.choice(second_names)
        tier = random.choice(tiers)
        days_offset = random.randint(0, 540)
        register_date = base_date + timedelta(days=days_offset)
        total_spent = round(random.uniform(100, 8000), 2)
        customers.append({
            "name": name,
            "tier": tier,
            "register_date": register_date.strftime("%Y-%m-%d"),
            "total_spent": total_spent
        })

    return customers


def generate_products() -> List[Dict[str, Any]]:
    """生成 20 个商品"""
    categories = ["电子产品", "服装", "食品", "家居"]

    product_data = [
        # 电子产品
        ("iPhone 15 Pro", "电子产品", 7999, 50),
        ("Samsung Galaxy S24", "电子产品", 6999, 35),
        ("MacBook Air M3", "电子产品", 8999, 20),
        ("iPad Pro", "电子产品", 6799, 25),
        ("Sony WH-1000XM5", "电子产品", 1999, 40),
        # 服装
        ("Levi's 牛仔裤", "服装", 599, 100),
        ("Nike 运动鞋", "服装", 899, 80),
        ("Adidas 卫衣", "服装", 499, 70),
        ("优衣库 羽绒服", "服装", 799, 50),
        ("Zara 连衣裙", "服装", 699, 60),
        # 食品
        ("五常大米 10kg", "食品", 128, 200),
        ("金龙鱼 花生油", "食品", 89, 150),
        ("三只松鼠 坚果礼盒", "食品", 168, 100),
        ("茅台 飞天", "食品", 2999, 10),
        ("星巴克 咖啡豆", "食品", 79, 120),
        # 家居
        ("宜家 沙发", "家居", 2999, 15),
        ("小米 空气净化器", "家居", 1299, 30),
        ("飞利浦 台灯", "家居", 299, 60),
        ("水星 四件套", "家居", 399, 50),
        ("双立人 刀具套装", "家居", 899, 25),
    ]

    products = []
    for name, category, price, stock in product_data:
        products.append({
            "name": name,
            "category": category,
            "price": price,
            "stock": stock
        })

    return products


def generate_orders(
        customers: List[Dict[str, Any]],
        products: List[Dict[str, Any]],
        count: int = 100
) -> List[Dict[str, Any]]:
    """
    生成订单（关联客户和商品）
    """
    statuses = ["pending", "paid", "shipped", "completed", "completed", "completed", "cancelled"]
    base_date = datetime(2026, 1, 1)

    orders = []
    customer_spent = {c["name"]: 0 for c in customers}

    for i in range(count):
        customer = random.choice(customers)
        product = random.choice(products)
        quantity = random.randint(1, 5)
        unit_price = product["price"]
        total_amount = round(unit_price * quantity, 2)
        status = random.choice(statuses)
        days_offset = random.randint(0, 200)
        created_at = base_date + timedelta(days=days_offset)

        orders.append({
            "customer_id": customers.index(customer) + 1,
            "customer_name": customer["name"],
            "product_id": products.index(product) + 1,
            "product_name": product["name"],
            "quantity": quantity,
            "unit_price": unit_price,
            "total_amount": total_amount,
            "status": status,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S")
        })

        # 累计消费（只统计已完成订单）
        if status == "completed":
            customer_spent[customer["name"]] += total_amount

    # 更新客户总消费
    for customer in customers:
        customer["total_spent"] = round(customer_spent.get(customer["name"], 0), 2)

    # 按时间排序
    orders.sort(key=lambda x: x["created_at"], reverse=True)

    return orders


# ============================================================
# 3. 插入数据
# ============================================================

def init_database():
    """初始化完整数据库"""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. 创建表
    create_tables(conn)

    # 2. 检查是否已有数据
    cursor.execute("SELECT COUNT(*) FROM customers")
    customer_count = cursor.fetchone()[0]

    if customer_count > 0:
        print(f"📊 数据库已有数据，跳过初始化")
        conn.close()
        return

    # 3. 生成数据
    print("📦 生成数据...")
    customers = generate_customers()
    products = generate_products()
    orders = generate_orders(customers, products, count=100)

    # 4. 插入客户
    cursor.executemany("""
        INSERT INTO customers (name, tier, register_date, total_spent)
        VALUES (?, ?, ?, ?)
    """, [(c["name"], c["tier"], c["register_date"], c["total_spent"]) for c in customers])
    print(f"   ✅ 插入 {len(customers)} 个客户")

    # 5. 插入商品
    cursor.executemany("""
        INSERT INTO products (name, category, price, stock)
        VALUES (?, ?, ?, ?)
    """, [(p["name"], p["category"], p["price"], p["stock"]) for p in products])
    print(f"   ✅ 插入 {len(products)} 个商品")

    # 6. 插入订单
    cursor.executemany("""
        INSERT INTO orders (customer_id, customer_name, product_id, product_name, 
                           quantity, unit_price, total_amount, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [(o["customer_id"], o["customer_name"], o["product_id"], o["product_name"],
           o["quantity"], o["unit_price"], o["total_amount"], o["status"], o["created_at"])
          for o in orders])
    print(f"   ✅ 插入 {len(orders)} 个订单")

    conn.commit()

    # 7. 统计信息
    cursor.execute("SELECT COUNT(*) FROM customers")
    print(f"\n📊 统计: {cursor.fetchone()[0]} 客户, ", end="")
    cursor.execute("SELECT COUNT(*) FROM products")
    print(f"{cursor.fetchone()[0]} 商品, ", end="")
    cursor.execute("SELECT COUNT(*) FROM orders")
    print(f"{cursor.fetchone()[0]} 订单")

    conn.close()
    print("✅ 数据库初始化完成！")


# ============================================================
# 4. 查询函数（供工具使用）
# ============================================================

def query_orders_sql(
        customer_name: str = None,
        status: str = None,
        min_amount: float = None,
        max_amount: float = None,
        date_from: str = None,
        date_to: str = None,
        limit: int = 20
) -> List[Dict[str, Any]]:
    """
    增强版订单查询（支持更多条件）
    """
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT order_id, customer_name, product_name, quantity, 
               unit_price, total_amount, status, created_at
        FROM orders WHERE 1=1
    """
    params = []

    if customer_name:
        sql += " AND customer_name LIKE ?"
        params.append(f"%{customer_name}%")

    if status:
        sql += " AND status = ?"
        params.append(status)

    if min_amount:
        sql += " AND total_amount >= ?"
        params.append(min_amount)

    if max_amount:
        sql += " AND total_amount <= ?"
        params.append(max_amount)

    if date_from:
        sql += " AND created_at >= ?"
        params.append(date_from)

    if date_to:
        sql += " AND created_at <= ?"
        params.append(date_to)

    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "order_id": row[0],
            "customer_name": row[1],
            "product_name": row[2],
            "quantity": row[3],
            "unit_price": row[4],
            "total_amount": row[5],
            "status": row[6],
            "created_at": row[7]
        }
        for row in rows
    ]


def get_customer_info(name: str) -> Dict[str, Any]:
    """根据姓名查询客户信息"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT customer_id, name, tier, register_date, total_spent
        FROM customers WHERE name LIKE ?
    """, (f"%{name}%",))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "customer_id": row[0],
            "name": row[1],
            "tier": row[2],
            "register_date": row[3],
            "total_spent": row[4]
        }
    return None


def get_product_info(name: str) -> Dict[str, Any]:
    """根据商品名查询商品信息"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT product_id, name, category, price, stock
        FROM products WHERE name LIKE ?
    """, (f"%{name}%",))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "product_id": row[0],
            "name": row[1],
            "category": row[2],
            "price": row[3],
            "stock": row[4]
        }
    return None


if __name__ == "__main__":
    init_database()