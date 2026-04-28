# -*- coding: utf-8 -*-
import os
import sqlite3
from sqlite3 import Connection
from contextlib import contextmanager
from typing import Generator, Optional
from config import BASE_DIR


class DatabaseManager:
    """数据库管理器，负责SQLite数据库的连接和初始化"""

    def __init__(self, db_path: Optional[str] = None):
        """初始化数据库管理器

        Args:
            db_path: 数据库文件路径，如果为None则使用默认路径
        """
        if db_path is None:
            # db_path = os.path.join(BASE_DIR, "realme_customer_service.db")
            db_path = os.path.join(BASE_DIR, "realme_customer_service_backup_20260422_131018.db")

        self.db_path = db_path
        self._ensure_db_dir()

    def _ensure_db_dir(self) -> None:
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    @contextmanager
    def get_connection(self) -> Generator[Connection, None, None]:
        """获取数据库连接（使用上下文管理器自动关闭）

        Yields:
            sqlite3.Connection: 数据库连接
        """
        conn = None
        try:
            # 启用外键约束
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.row_factory = sqlite3.Row  # 返回字典格式的行
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    def get_cursor(self) -> Connection:
        """获取数据库游标（需要手动管理连接）

        Returns:
            sqlite3.Connection: 数据库连接
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_database(self) -> None:
        """初始化数据库，创建所有表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. 用户表 (users)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email VARCHAR(100) UNIQUE,
                    phone VARCHAR(20),
                    real_name VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')

            # 2. 会话表 (conversations)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES users(id),
                    thread_id VARCHAR(100) UNIQUE NOT NULL,
                    title VARCHAR(200) DEFAULT '新对话',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')

            # 3. 消息表 (messages)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER REFERENCES conversations(id),
                    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT  -- JSON字符串，存储原始API响应等额外信息
                )
            ''')

            # 4. 维修订单表 (repair_orders)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS repair_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id VARCHAR(50) NOT NULL,  -- 对应模拟数据的user_1, user_2等
                    order_id VARCHAR(50) UNIQUE NOT NULL,
                    device_model VARCHAR(100) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 5. 维修进度表 (repair_progress)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS repair_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id VARCHAR(50) REFERENCES repair_orders(order_id),
                    device_model VARCHAR(100),
                    status VARCHAR(50) NOT NULL,
                    latest_progress TEXT,
                    expected_time TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 6. 价保信息表 (price_protection)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_protection (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id VARCHAR(50) UNIQUE NOT NULL,
                    user_id VARCHAR(50) NOT NULL,
                    product_name VARCHAR(200) NOT NULL,
                    original_price DECIMAL(10,2) NOT NULL,
                    current_price DECIMAL(10,2) NOT NULL,
                    protect_amount DECIMAL(10,2) NOT NULL,
                    protect_deadline DATE NOT NULL,
                    is_protectable BOOLEAN NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 7. 用户订单表 (user_orders)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id VARCHAR(50) NOT NULL,
                    order_id VARCHAR(50) UNIQUE NOT NULL,
                    product_name VARCHAR(200) NOT NULL,
                    order_time TIMESTAMP NOT NULL,
                    price DECIMAL(10,2) NOT NULL
                )
            ''')

            # 创建索引以提高查询性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_repair_orders_user_id ON repair_orders(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_repair_progress_order_id ON repair_progress(order_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_protection_user_id ON price_protection(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_orders_user_id ON user_orders(user_id)')

            print(f"[完成] 数据库初始化完成：{self.db_path}")

    def check_database_exists(self) -> bool:
        """检查数据库文件是否存在

        Returns:
            bool: 数据库文件是否存在
        """
        return os.path.exists(self.db_path)

    def get_database_info(self) -> dict:
        """获取数据库信息

        Returns:
            dict: 数据库信息字典
        """
        info = {
            "db_path": self.db_path,
            "exists": self.check_database_exists(),
            "size": 0,
            "table_count": 0,
            "tables": []
        }

        if info["exists"]:
            # 获取文件大小
            info["size"] = os.path.getsize(self.db_path)

            # 获取表信息
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                info["table_count"] = len(tables)
                info["tables"] = [table["name"] for table in tables]

        return info

    # ====================== 【新增】查看数据库内容 ======================
    def show_all_tables(self):
        """打印所有表名"""
        info = self.get_database_info()
        print("\n📊 数据库中的所有表：")
        for table in info["tables"]:
            print(f"- {table}")
        return info["tables"]

    def show_table_data(self, table_name: str, limit: int = 50):
        """查看指定表的数据
        Args:
            table_name: 表名
            limit: 最多显示多少条
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
                rows = cursor.fetchall()

                print(f"\n📋 表：{table_name}（共 {len(rows)} 条数据）")
                if not rows:
                    print("  （空表）")
                    return

                # 打印表头
                columns = [desc[0] for desc in cursor.description]
                print("  | " + " | ".join(columns) + " |")
                print("  " + "-" * 80)

                # 打印数据
                for row in rows:
                    row_data = [str(item) if item is not None else "NULL" for item in row]
                    print("  | " + " | ".join(row_data) + " |")

        except Exception as e:
            print(f"查询表 {table_name} 失败：{e}")

    def show_all_data(self):
        """一键查看所有表的所有数据"""
        print("=" * 60)
        print("📂 查看整个数据库所有内容")
        print("=" * 60)
        tables = self.show_all_tables()
        for table in tables:
            self.show_table_data(table)

# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """获取全局数据库管理器实例

    Returns:
        DatabaseManager: 数据库管理器实例
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def initialize_database() -> None:
    """初始化数据库（创建所有表）"""
    db_manager = get_db_manager()
    db_manager.initialize_database()


def get_db_info() -> dict:
    """获取数据库信息

    Returns:
        dict: 数据库信息字典
    """
    db_manager = get_db_manager()
    return db_manager.get_database_info()


# ====================== 【查看数据库函数】 ======================
def show_all_tables():
    """显示所有表名"""
    db = get_db_manager()
    db.show_all_tables()

def show_table_data(table_name: str, limit=50):
    """显示单张表数据"""
    db = get_db_manager()
    db.show_table_data(table_name, limit)

def show_all_data():
    """显示所有表所有数据"""
    db = get_db_manager()
    db.show_all_data()


if __name__ == "__main__":
    # 1. 初始化数据库
    initialize_database()

    # 2. 查看数据库信息
    info = get_db_info()
    print("数据库信息：")
    print(f"  路径：{info['db_path']}")
    print(f"  存在：{info['exists']}")
    print(f"  大小：{info['size']} 字节")
    print(f"  表数量：{info['table_count']}")
    print(f"  表列表：{info['tables']}")

    # ====================== 在这里调用查看数据 ======================
    print("\n" + "="*50)
    show_all_data()  # 一键查看所有内容


"""
==================================================
============================================================
📂 查看整个数据库所有内容
============================================================

📊 数据库中的所有表：
- users
- sqlite_sequence
- conversations
- messages
- repair_orders
- repair_progress
- price_protection
- user_orders

📋 表：users（共 7 条数据）
  | id | username | password_hash | email | phone | real_name | created_at | last_login | is_active |
  --------------------------------------------------------------------------------
  | 1 | testuser | $pbkdf2-sha256$29000$lNJ6jzGmFGKMMSYEgHBubQ$rYxe19PijpX2davVExipbSEP/E2FruKDCNlr1b31MnM | test@example.com | 13800138000 | NULL | 2026-04-22 06:13:58 | NULL | 1 |
  | 2 | testuser2 | $pbkdf2-sha256$29000$gxACwLi3lvKeMwYAYOzdWw$GI34geINd95EeAf96hTZQUCCzAwjCtHcpPmRGUd2RBQ | test2@example.com | 13900139000 | NULL | 2026-04-22 06:18:20 | 2026-04-22 06:20:08 | 1 |
  | 3 | testuser_1776840275 | $pbkdf2-sha256$29000$fC.F8F5rLeUcQ0gppdSakw$Qi0mbDbzxzvp6IesPLKxIV2Tb6tC8a4kXrl7zWYN/z4 | test_1776840275@example.com | NULL | NULL | 2026-04-22 06:44:36 | 2026-04-22 06:44:51 | 1 |
  | 4 | test_user | $pbkdf2-sha256$29000$rxWiNKaUEqKU0hqj1BqDcA$GeRwSKZpNOznpUUUxJkmLsjNs4GUXZdLu1M7lC8xRjQ | NULL | NULL | NULL | 2026-04-22 07:27:41 | 2026-04-22 07:28:58 | 1 |
  | 5 | 江耀森 | $pbkdf2-sha256$29000$z9lbK6U0BkCIUar1PgdAiA$EpemaxSh43kRBxNrTb7ns8DreFHkNKdyxAl0qk2Kd5s | NULL | NULL | NULL | 2026-04-22 07:28:41 | 2026-04-22 08:17:21 | 1 |
  | 6 | test_empty | $pbkdf2-sha256$29000$GuMc41wrhZCS8h7jPKd0zg$092HS7PFt73LafQaNQxzEWKWdPECRVnG1ujY8kShSPs | NULL | NULL | NULL | 2026-04-22 07:33:46 | NULL | 1 |
  | 7 | 王伟伟 | $pbkdf2-sha256$29000$sNaaszYGYAzB2LvXem8NYQ$p0WcoycQu9u/uFDrFplimc5zB61w0ahG0mbAcKrmOts | NULL | NULL | NULL | 2026-04-22 07:38:00 | 2026-04-22 09:21:46 | 1 |

📋 表：sqlite_sequence（共 6 条数据）
  | name | seq |
  --------------------------------------------------------------------------------
  | repair_orders | 200 |
  | repair_progress | 100 |
  | price_protection | 6 |
  | user_orders | 6 |
  | users | 7 |
  | conversations | 2 |

📋 表：conversations（共 2 条数据）
  | id | user_id | thread_id | title | created_at | updated_at | is_active |
  --------------------------------------------------------------------------------
  | 1 | 2 | thread_1776838792_e9f75a96 | Test Conversation | 2026-04-22 06:19:52 | 2026-04-22 06:19:52 | 1 |
  | 2 | 5 | thread_1776843256_3409968b | test | 2026-04-22 07:34:16 | 2026-04-22 07:34:16 | 1 |

📋 表：messages（共 0 条数据）
  （空表）

📋 表：repair_orders（共 50 条数据）
  | id | user_id | order_id | device_model | status | created_at |
  --------------------------------------------------------------------------------
  | 101 | user_2 | RMA20260413001 | realme GT Neo2 | 维修中 | NULL |
  | 102 | user_3 | RMA20260413002 | realme GT Neo3 | 待取件 | NULL |
  | 103 | user_4 | RMA20260413003 | realme GT Neo4 | 已完成 | NULL |
  | 104 | user_5 | RMA20260413004 | realme GT Neo5 | 待检测 | NULL |
  | 105 | user_1 | RMA20260413005 | realme GT Neo6 | 维修中 | NULL |
  | 106 | user_2 | RMA20260413006 | realme GT Neo7 | 待取件 | NULL |
  | 107 | user_3 | RMA20260413007 | realme GT Neo8 | 已完成 | NULL |
  | 108 | user_4 | RMA20260413008 | realme GT Neo9 | 待检测 | NULL |
  | 109 | user_5 | RMA20260413009 | realme GT Neo10 | 维修中 | NULL |
  | 110 | user_1 | RMA20260413010 | realme GT Neo1 | 待取件 | NULL |
  | 111 | user_2 | RMA20260413011 | realme GT Neo2 | 已完成 | NULL |
  | 112 | user_3 | RMA20260413012 | realme GT Neo3 | 待检测 | NULL |
  | 113 | user_4 | RMA20260413013 | realme GT Neo4 | 维修中 | NULL |
  | 114 | user_5 | RMA20260413014 | realme GT Neo5 | 待取件 | NULL |
  | 115 | user_1 | RMA20260413015 | realme GT Neo6 | 已完成 | NULL |
  | 116 | user_2 | RMA20260413016 | realme GT Neo7 | 待检测 | NULL |
  | 117 | user_3 | RMA20260413017 | realme GT Neo8 | 维修中 | NULL |
  | 118 | user_4 | RMA20260413018 | realme GT Neo9 | 待取件 | NULL |
  | 119 | user_5 | RMA20260413019 | realme GT Neo10 | 已完成 | NULL |
  | 120 | user_1 | RMA20260413020 | realme GT Neo1 | 待检测 | NULL |
  | 121 | user_2 | RMA20260413021 | realme GT Neo2 | 维修中 | NULL |
  | 122 | user_3 | RMA20260413022 | realme GT Neo3 | 待取件 | NULL |
  | 123 | user_4 | RMA20260413023 | realme GT Neo4 | 已完成 | NULL |
  | 124 | user_5 | RMA20260413024 | realme GT Neo5 | 待检测 | NULL |
  | 125 | user_1 | RMA20260413025 | realme GT Neo6 | 维修中 | NULL |
  | 126 | user_2 | RMA20260413026 | realme GT Neo7 | 待取件 | NULL |
  | 127 | user_3 | RMA20260413027 | realme GT Neo8 | 已完成 | NULL |
  | 128 | user_4 | RMA20260413028 | realme GT Neo9 | 待检测 | NULL |
  | 129 | user_5 | RMA20260413029 | realme GT Neo10 | 维修中 | NULL |
  | 130 | user_1 | RMA20260413030 | realme GT Neo1 | 待取件 | NULL |
  | 131 | user_2 | RMA20260413031 | realme GT Neo2 | 已完成 | NULL |
  | 132 | user_3 | RMA20260413032 | realme GT Neo3 | 待检测 | NULL |
  | 133 | user_4 | RMA20260413033 | realme GT Neo4 | 维修中 | NULL |
  | 134 | user_5 | RMA20260413034 | realme GT Neo5 | 待取件 | NULL |
  | 135 | user_1 | RMA20260413035 | realme GT Neo6 | 已完成 | NULL |
  | 136 | user_2 | RMA20260413036 | realme GT Neo7 | 待检测 | NULL |
  | 137 | user_3 | RMA20260413037 | realme GT Neo8 | 维修中 | NULL |
  | 138 | user_4 | RMA20260413038 | realme GT Neo9 | 待取件 | NULL |
  | 139 | user_5 | RMA20260413039 | realme GT Neo10 | 已完成 | NULL |
  | 140 | user_1 | RMA20260413040 | realme GT Neo1 | 待检测 | NULL |
  | 141 | user_2 | RMA20260413041 | realme GT Neo2 | 维修中 | NULL |
  | 142 | user_3 | RMA20260413042 | realme GT Neo3 | 待取件 | NULL |
  | 143 | user_4 | RMA20260413043 | realme GT Neo4 | 已完成 | NULL |
  | 144 | user_5 | RMA20260413044 | realme GT Neo5 | 待检测 | NULL |
  | 145 | user_1 | RMA20260413045 | realme GT Neo6 | 维修中 | NULL |
  | 146 | user_2 | RMA20260413046 | realme GT Neo7 | 待取件 | NULL |
  | 147 | user_3 | RMA20260413047 | realme GT Neo8 | 已完成 | NULL |
  | 148 | user_4 | RMA20260413048 | realme GT Neo9 | 待检测 | NULL |
  | 149 | user_5 | RMA20260413049 | realme GT Neo10 | 维修中 | NULL |
  | 150 | user_1 | RMA20260413050 | realme GT Neo1 | 待取件 | NULL |

📋 表：repair_progress（共 50 条数据）
  | id | order_id | device_model | status | latest_progress | expected_time | updated_at |
  --------------------------------------------------------------------------------
  | 1 | RMA20260413001 | realme GT Neo2 | 维修中 | 硬件检测中 | 2026-04-14 18:00 | NULL |
  | 2 | RMA20260413002 | realme GT Neo3 | 待取件 | 配件更换中 | 2026-04-15 18:00 | NULL |
  | 3 | RMA20260413003 | realme GT Neo4 | 已完成 | 质检完成，待取件 | 2026-04-13 18:00 | NULL |
  | 4 | RMA20260413004 | realme GT Neo5 | 待检测 | 等待工程师接单 | 2026-04-14 18:00 | NULL |
  | 5 | RMA20260413005 | realme GT Neo6 | 维修中 | 硬件检测中 | 2026-04-15 18:00 | NULL |
  | 6 | RMA20260413006 | realme GT Neo7 | 待取件 | 配件更换中 | 2026-04-13 18:00 | NULL |
  | 7 | RMA20260413007 | realme GT Neo8 | 已完成 | 质检完成，待取件 | 2026-04-14 18:00 | NULL |
  | 8 | RMA20260413008 | realme GT Neo9 | 待检测 | 等待工程师接单 | 2026-04-15 18:00 | NULL |
  | 9 | RMA20260413009 | realme GT Neo10 | 维修中 | 硬件检测中 | 2026-04-13 18:00 | NULL |
  | 10 | RMA20260413010 | realme GT Neo1 | 待取件 | 配件更换中 | 2026-04-14 18:00 | NULL |
  | 11 | RMA20260413011 | realme GT Neo2 | 已完成 | 质检完成，待取件 | 2026-04-15 18:00 | NULL |
  | 12 | RMA20260413012 | realme GT Neo3 | 待检测 | 等待工程师接单 | 2026-04-13 18:00 | NULL |
  | 13 | RMA20260413013 | realme GT Neo4 | 维修中 | 硬件检测中 | 2026-04-14 18:00 | NULL |
  | 14 | RMA20260413014 | realme GT Neo5 | 待取件 | 配件更换中 | 2026-04-15 18:00 | NULL |
  | 15 | RMA20260413015 | realme GT Neo6 | 已完成 | 质检完成，待取件 | 2026-04-13 18:00 | NULL |
  | 16 | RMA20260413016 | realme GT Neo7 | 待检测 | 等待工程师接单 | 2026-04-14 18:00 | NULL |
  | 17 | RMA20260413017 | realme GT Neo8 | 维修中 | 硬件检测中 | 2026-04-15 18:00 | NULL |
  | 18 | RMA20260413018 | realme GT Neo9 | 待取件 | 配件更换中 | 2026-04-13 18:00 | NULL |
  | 19 | RMA20260413019 | realme GT Neo10 | 已完成 | 质检完成，待取件 | 2026-04-14 18:00 | NULL |
  | 20 | RMA20260413020 | realme GT Neo1 | 待检测 | 等待工程师接单 | 2026-04-15 18:00 | NULL |
  | 21 | RMA20260413021 | realme GT Neo2 | 维修中 | 硬件检测中 | 2026-04-13 18:00 | NULL |
  | 22 | RMA20260413022 | realme GT Neo3 | 待取件 | 配件更换中 | 2026-04-14 18:00 | NULL |
  | 23 | RMA20260413023 | realme GT Neo4 | 已完成 | 质检完成，待取件 | 2026-04-15 18:00 | NULL |
  | 24 | RMA20260413024 | realme GT Neo5 | 待检测 | 等待工程师接单 | 2026-04-13 18:00 | NULL |
  | 25 | RMA20260413025 | realme GT Neo6 | 维修中 | 硬件检测中 | 2026-04-14 18:00 | NULL |
  | 26 | RMA20260413026 | realme GT Neo7 | 待取件 | 配件更换中 | 2026-04-15 18:00 | NULL |
  | 27 | RMA20260413027 | realme GT Neo8 | 已完成 | 质检完成，待取件 | 2026-04-13 18:00 | NULL |
  | 28 | RMA20260413028 | realme GT Neo9 | 待检测 | 等待工程师接单 | 2026-04-14 18:00 | NULL |
  | 29 | RMA20260413029 | realme GT Neo10 | 维修中 | 硬件检测中 | 2026-04-15 18:00 | NULL |
  | 30 | RMA20260413030 | realme GT Neo1 | 待取件 | 配件更换中 | 2026-04-13 18:00 | NULL |
  | 31 | RMA20260413031 | realme GT Neo2 | 已完成 | 质检完成，待取件 | 2026-04-14 18:00 | NULL |
  | 32 | RMA20260413032 | realme GT Neo3 | 待检测 | 等待工程师接单 | 2026-04-15 18:00 | NULL |
  | 33 | RMA20260413033 | realme GT Neo4 | 维修中 | 硬件检测中 | 2026-04-13 18:00 | NULL |
  | 34 | RMA20260413034 | realme GT Neo5 | 待取件 | 配件更换中 | 2026-04-14 18:00 | NULL |
  | 35 | RMA20260413035 | realme GT Neo6 | 已完成 | 质检完成，待取件 | 2026-04-15 18:00 | NULL |
  | 36 | RMA20260413036 | realme GT Neo7 | 待检测 | 等待工程师接单 | 2026-04-13 18:00 | NULL |
  | 37 | RMA20260413037 | realme GT Neo8 | 维修中 | 硬件检测中 | 2026-04-14 18:00 | NULL |
  | 38 | RMA20260413038 | realme GT Neo9 | 待取件 | 配件更换中 | 2026-04-15 18:00 | NULL |
  | 39 | RMA20260413039 | realme GT Neo10 | 已完成 | 质检完成，待取件 | 2026-04-13 18:00 | NULL |
  | 40 | RMA20260413040 | realme GT Neo1 | 待检测 | 等待工程师接单 | 2026-04-14 18:00 | NULL |
  | 41 | RMA20260413041 | realme GT Neo2 | 维修中 | 硬件检测中 | 2026-04-15 18:00 | NULL |
  | 42 | RMA20260413042 | realme GT Neo3 | 待取件 | 配件更换中 | 2026-04-13 18:00 | NULL |
  | 43 | RMA20260413043 | realme GT Neo4 | 已完成 | 质检完成，待取件 | 2026-04-14 18:00 | NULL |
  | 44 | RMA20260413044 | realme GT Neo5 | 待检测 | 等待工程师接单 | 2026-04-15 18:00 | NULL |
  | 45 | RMA20260413045 | realme GT Neo6 | 维修中 | 硬件检测中 | 2026-04-13 18:00 | NULL |
  | 46 | RMA20260413046 | realme GT Neo7 | 待取件 | 配件更换中 | 2026-04-14 18:00 | NULL |
  | 47 | RMA20260413047 | realme GT Neo8 | 已完成 | 质检完成，待取件 | 2026-04-15 18:00 | NULL |
  | 48 | RMA20260413048 | realme GT Neo9 | 待检测 | 等待工程师接单 | 2026-04-13 18:00 | NULL |
  | 49 | RMA20260413049 | realme GT Neo10 | 维修中 | 硬件检测中 | 2026-04-14 18:00 | NULL |
  | 50 | RMA20260413050 | realme GT Neo1 | 待取件 | 配件更换中 | 2026-04-15 18:00 | NULL |

📋 表：price_protection（共 6 条数据）
  | id | order_id | user_id | product_name | original_price | current_price | protect_amount | protect_deadline | is_protectable | status | updated_at |
  --------------------------------------------------------------------------------
  | 1 | RM20250401001 | user_2 | realme GT Neo6 SE | 1999 | 1899 | 100 | 2025-05-01 | 1 | 可申请价保 | 2026-04-22T13:10:18.655883 |
  | 2 | RM20250410002 | user_2 | realme Buds Air 6 | 399 | 399 | 0 | 2025-05-10 | 0 | 不支持价保 | 2026-04-22T13:10:18.657267 |
  | 3 | RM20250315003 | user_1 | realme 12 Pro+ | 2799 | 2599 | 200 | 2025-04-15 | 1 | 可申请价保 | 2026-04-22T13:10:18.657302 |
  | 4 | RM20250201004 | user_3 | realme Pad 2 | 1499 | 1399 | 100 | 2025-03-01 | 1 | 可申请价保 | 2026-04-22T13:10:18.657317 |
  | 5 | RM20250210005 | user_3 | realme Watch 3 | 349 | 349 | 0 | 2025-03-10 | 0 | 不支持价保 | 2026-04-22T13:10:18.657330 |
  | 6 | RM20250305006 | user_3 | realme GT Neo6 SE | 1999 | 1999 | 0 | 2025-04-05 | 0 | 价保已过期 | 2026-04-22T13:10:18.657341 |

📋 表：user_orders（共 6 条数据）
  | id | user_id | order_id | product_name | order_time | price |
  --------------------------------------------------------------------------------
  | 1 | user_2 | RM20250401001 | realme GT Neo6 SE | 2025-04-01 15:30:00 | 1999 |
  | 2 | user_2 | RM20250410002 | realme Buds Air 6 | 2025-04-10 11:20:00 | 399 |
  | 3 | user_1 | RM20250315003 | realme 12 Pro+ | 2025-03-15 09:45:00 | 2799 |
  | 4 | user_3 | RM20250201004 | realme Pad 2 | 2025-02-01 16:10:00 | 1499 |
  | 5 | user_3 | RM20250210005 | realme Watch 3 | 2025-02-10 10:00:00 | 349 |
  | 6 | user_3 | RM20250305006 | realme GT Neo6 SE | 2025-03-05 18:30:00 | 1999 |
"""