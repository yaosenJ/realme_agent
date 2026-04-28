# -*- coding: utf-8 -*-
import json
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
from .db import get_db_manager


class UserCRUD:
    """用户CRUD操作"""

    @staticmethod
    def create_user(
        username: str,
        password_hash: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        real_name: Optional[str] = None,
    ) -> Optional[int]:
        """创建用户

        Args:
            username: 用户名
            password_hash: 密码哈希值
            email: 邮箱
            phone: 手机号
            real_name: 真实姓名

        Returns:
            Optional[int]: 用户ID，如果创建失败返回None
        """
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, email, phone, real_name)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (username, password_hash, email, phone, real_name)
                )
                return cursor.lastrowid
            except sqlite3.IntegrityError as e:
                # 用户名或邮箱已存在
                print(f"创建用户失败：{e}")
                return None

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户

        Args:
            user_id: 用户ID

        Returns:
            Optional[Dict[str, Any]]: 用户信息字典，如果不存在返回None
        """
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户

        Args:
            username: 用户名

        Returns:
            Optional[Dict[str, Any]]: 用户信息字典，如果不存在返回None
        """
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱获取用户

        Args:
            email: 邮箱

        Returns:
            Optional[Dict[str, Any]]: 用户信息字典，如果不存在返回None
        """
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def update_user_last_login(user_id: int) -> bool:
        """更新用户最后登录时间

        Args:
            user_id: 用户ID

        Returns:
            bool: 是否更新成功
        """
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,)
            )
            return cursor.rowcount > 0

    @staticmethod
    def verify_user_credentials(username: str, password_hash: str) -> Optional[Dict[str, Any]]:
        """验证用户凭据

        Args:
            username: 用户名
            password_hash: 密码哈希值

        Returns:
            Optional[Dict[str, Any]]: 用户信息字典，如果验证失败返回None
        """
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = ? AND password_hash = ? AND is_active = 1",
                (username, password_hash)
            )
            row = cursor.fetchone()
            return dict(row) if row else None


class ConversationCRUD:
    """会话CRUD操作"""

    @staticmethod
    def create_conversation(
        user_id: int,
        thread_id: str,
        title: str = "新对话"
    ) -> Optional[int]:
        """创建对话

        Args:
            user_id: 用户ID
            thread_id: 线程ID（唯一标识符）
            title: 对话标题

        Returns:
            Optional[int]: 对话ID，如果创建失败返回None
        """
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO conversations (user_id, thread_id, title)
                    VALUES (?, ?, ?)
                    """,
                    (user_id, thread_id, title)
                )
                return cursor.lastrowid
            except sqlite3.IntegrityError as e:
                # thread_id已存在
                print(f"创建对话失败：{e}")
                return None

    @staticmethod
    def get_conversation_by_thread_id(thread_id: str) -> Optional[Dict[str, Any]]:
        """根据线程ID获取对话

        Args:
            thread_id: 线程ID

        Returns:
            Optional[Dict[str, Any]]: 对话信息字典，如果不存在返回None
        """
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM conversations WHERE thread_id = ?", (thread_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_conversation_by_id(conversation_id: int) -> Optional[Dict[str, Any]]:
        """根据对话ID获取对话

        Args:
            conversation_id: 对话ID

        Returns:
            Optional[Dict[str, Any]]: 对话信息字典，如果不存在返回None
        """
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_user_conversations(user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """获取用户的所有对话

        Args:
            user_id: 用户ID
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[Dict[str, Any]]: 对话信息字典列表
        """
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM conversations
                WHERE user_id = ? AND is_active = 1
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, limit, offset)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def update_conversation_title(conversation_id: int, title: str) -> bool:
        """更新对话标题

        Args:
            conversation_id: 对话ID
            title: 新标题

        Returns:
            bool: 是否更新成功
        """
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE conversations
                SET title = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (title, conversation_id)
            )
            return cursor.rowcount > 0

    @staticmethod
    def delete_conversation(conversation_id: int) -> bool:
        """软删除对话（设置is_active=0）

        Args:
            conversation_id: 对话ID

        Returns:
            bool: 是否删除成功
        """
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE conversations SET is_active = 0 WHERE id = ?",
                (conversation_id,)
            )
            return cursor.rowcount > 0


class MessageCRUD:
    """消息CRUD操作"""

    @staticmethod
    def create_message(
        conversation_id: int,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """创建消息

        Args:
            conversation_id: 对话ID
            role: 角色（'user' 或 'assistant'）
            content: 消息内容
            metadata: 元数据（JSON格式）

        Returns:
            int: 消息ID
        """
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            metadata_str = json.dumps(metadata) if metadata else None
            cursor.execute(
                """
                INSERT INTO messages (conversation_id, role, content, metadata)
                VALUES (?, ?, ?, ?)
                """,
                (conversation_id, role, content, metadata_str)
            )
            return cursor.lastrowid

    @staticmethod
    def get_conversation_messages(
        conversation_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取对话的消息

        Args:
            conversation_id: 对话ID
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[Dict[str, Any]]: 消息字典列表
        """
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM messages
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
                LIMIT ? OFFSET ?
                """,
                (conversation_id, limit, offset)
            )
            rows = cursor.fetchall()
            messages = []
            for row in rows:
                message = dict(row)
                # 解析metadata字段
                if message.get("metadata"):
                    try:
                        message["metadata"] = json.loads(message["metadata"])
                    except json.JSONDecodeError:
                        message["metadata"] = None
                else:
                    message["metadata"] = None
                messages.append(message)
            return messages


class RepairOrderCRUD:
    """维修订单CRUD操作"""

    @staticmethod
    def get_user_repair_orders(user_id: str) -> List[Dict[str, Any]]:
        """获取用户的维修订单

        Args:
            user_id: 用户ID（格式如：user_1, user_2等）

        Returns:
            List[Dict[str, Any]]: 维修订单列表
        """
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM repair_orders WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_repair_order_by_id(order_id: str) -> Optional[Dict[str, Any]]:
        """根据订单ID获取维修订单

        Args:
            order_id: 订单ID

        Returns:
            Optional[Dict[str, Any]]: 维修订单信息，如果不存在返回None
        """
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM repair_orders WHERE order_id = ?", (order_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def batch_create_repair_orders(orders: List[Dict[str, Any]]) -> int:
        """批量创建维修订单

        Args:
            orders: 维修订单列表

        Returns:
            int: 成功创建的订单数量
        """
        db_manager = get_db_manager()
        success_count = 0
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            for order in orders:
                try:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO repair_orders
                        (user_id, order_id, device_model, status, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            order.get("user_id"),
                            order.get("order_id"),
                            order.get("device_model"),
                            order.get("status"),
                            order.get("created_at")
                        )
                    )
                    success_count += 1
                except Exception as e:
                    print(f"创建维修订单失败 {order.get('order_id')}: {e}")
        return success_count


class RepairProgressCRUD:
    """维修进度CRUD操作"""

    @staticmethod
    def get_repair_progress(order_id: str) -> Optional[Dict[str, Any]]:
        """获取维修进度

        Args:
            order_id: 订单ID

        Returns:
            Optional[Dict[str, Any]]: 维修进度信息，如果不存在返回None
        """
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM repair_progress WHERE order_id = ?", (order_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def batch_create_repair_progress(progresses: List[Dict[str, Any]]) -> int:
        """批量创建维修进度

        Args:
            progresses: 维修进度列表

        Returns:
            int: 成功创建的进度数量
        """
        db_manager = get_db_manager()
        success_count = 0
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            for progress in progresses:
                try:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO repair_progress
                        (order_id, device_model, status, latest_progress, expected_time, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            progress.get("order_id"),
                            progress.get("device_model"),
                            progress.get("status"),
                            progress.get("latest_progress"),
                            progress.get("expected_time"),
                            progress.get("updated_at")
                        )
                    )
                    success_count += 1
                except Exception as e:
                    print(f"创建维修进度失败 {progress.get('order_id')}: {e}")
        return success_count


class PriceProtectionCRUD:
    """价保信息CRUD操作"""

    @staticmethod
    def get_price_protection(order_id: str) -> Optional[Dict[str, Any]]:
        """获取价保信息

        Args:
            order_id: 订单ID

        Returns:
            Optional[Dict[str, Any]]: 价保信息，如果不存在返回None
        """
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM price_protection WHERE order_id = ?", (order_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def batch_create_price_protection(protections: List[Dict[str, Any]]) -> int:
        """批量创建价保信息

        Args:
            protections: 价保信息列表

        Returns:
            int: 成功创建的价保信息数量
        """
        db_manager = get_db_manager()
        success_count = 0
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            for protection in protections:
                try:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO price_protection
                        (order_id, user_id, product_name, original_price, current_price,
                         protect_amount, protect_deadline, is_protectable, status, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            protection.get("order_id"),
                            protection.get("user_id"),
                            protection.get("product"),
                            protection.get("original_price"),
                            protection.get("current_price"),
                            protection.get("protect_amount"),
                            protection.get("protect_deadline"),
                            protection.get("is_protectable"),
                            protection.get("status"),
                            protection.get("updated_at", datetime.now().isoformat())
                        )
                    )
                    success_count += 1
                except Exception as e:
                    print(f"创建价保信息失败 {protection.get('order_id')}: {e}")
        return success_count


class UserOrderCRUD:
    """用户订单CRUD操作"""

    @staticmethod
    def get_user_orders(user_id: str) -> List[Dict[str, Any]]:
        """获取用户订单

        Args:
            user_id: 用户ID（格式如：user_1, user_2等）

        Returns:
            List[Dict[str, Any]]: 用户订单列表
        """
        db_manager = get_db_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM user_orders WHERE user_id = ? ORDER BY order_time DESC",
                (user_id,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def batch_create_user_orders(orders: List[Dict[str, Any]]) -> int:
        """批量创建用户订单

        Args:
            orders: 用户订单列表

        Returns:
            int: 成功创建的订单数量
        """
        db_manager = get_db_manager()
        success_count = 0
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            for order in orders:
                try:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO user_orders
                        (user_id, order_id, product_name, order_time, price)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            order.get("user_id"),
                            order.get("order_id"),
                            order.get("product_name"),
                            order.get("order_time"),
                            order.get("price")
                        )
                    )
                    success_count += 1
                except Exception as e:
                    print(f"创建用户订单失败 {order.get('order_id')}: {e}")
        return success_count