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
            db_path = os.path.join(BASE_DIR, "realme_customer_service.db")

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


if __name__ == "__main__":
    # 测试数据库初始化
    initialize_database()
    info = get_db_info()
    print(f"数据库信息：")
    print(f"  路径：{info['db_path']}")
    print(f"  存在：{info['exists']}")
    print(f"  大小：{info['size']} 字节")
    print(f"  表数量：{info['table_count']}")
    print(f"  表列表：{info['tables']}")