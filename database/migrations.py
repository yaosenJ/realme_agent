# -*- coding: utf-8 -*-
import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, Any, List
from .db import DatabaseManager, get_db_manager
from .crud import (
    RepairOrderCRUD,
    RepairProgressCRUD,
    PriceProtectionCRUD,
    UserOrderCRUD,
)
from config import BASE_DIR, ORDER_DATA_FILE, PROGRESS_DATA_FILE


class DataMigration:
    """数据迁移类，负责从JSON文件迁移数据到SQLite数据库"""

    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or get_db_manager()

    def migrate_all(self) -> Dict[str, int]:
        """执行所有数据迁移

        Returns:
            Dict[str, int]: 迁移结果统计
        """
        results = {
            "repair_orders": 0,
            "repair_progress": 0,
            "price_protection": 0,
            "user_orders": 0,
        }

        print("[开始] 开始数据迁移...")

        # 1. 迁移维修订单
        print("1. 迁移维修订单数据...")
        orders = self._load_repair_orders()
        if orders:
            results["repair_orders"] = RepairOrderCRUD.batch_create_repair_orders(orders)
            print(f"   [OK] 成功迁移 {results['repair_orders']} 条维修订单")

        # 2. 迁移维修进度
        print("2. 迁移维修进度数据...")
        progresses = self._load_repair_progress()
        if progresses:
            results["repair_progress"] = RepairProgressCRUD.batch_create_repair_progress(progresses)
            print(f"   [OK] 成功迁移 {results['repair_progress']} 条维修进度")

        # 3. 迁移价保信息（从硬编码数据）
        print("3. 迁移价保信息数据...")
        price_protections = self._extract_price_protection_data()
        if price_protections:
            results["price_protection"] = PriceProtectionCRUD.batch_create_price_protection(price_protections)
            print(f"   [OK] 成功迁移 {results['price_protection']} 条价保信息")

        # 4. 迁移用户订单（从硬编码数据）
        print("4. 迁移用户订单数据...")
        user_orders = self._extract_user_orders_data()
        if user_orders:
            results["user_orders"] = UserOrderCRUD.batch_create_user_orders(user_orders)
            print(f"   [OK] 成功迁移 {results['user_orders']} 条用户订单")

        print(f"[完成] 数据迁移完成！总计迁移：")
        for key, count in results.items():
            print(f"   {key}: {count} 条")

        return results

    def _load_repair_orders(self) -> List[Dict[str, Any]]:
        """加载维修订单数据

        Returns:
            List[Dict[str, Any]]: 维修订单列表
        """
        try:
            if not os.path.exists(ORDER_DATA_FILE):
                print(f"   警告：维修订单文件不存在：{ORDER_DATA_FILE}")
                return []

            with open(ORDER_DATA_FILE, "r", encoding="utf-8") as f:
                orders = json.load(f)

            print(f"   从 {ORDER_DATA_FILE} 加载了 {len(orders)} 条维修订单")
            return orders

        except Exception as e:
            print(f"   加载维修订单失败：{e}")
            return []

    def _load_repair_progress(self) -> List[Dict[str, Any]]:
        """加载维修进度数据

        Returns:
            List[Dict[str, Any]]: 维修进度列表
        """
        try:
            if not os.path.exists(PROGRESS_DATA_FILE):
                print(f"   警告：维修进度文件不存在：{PROGRESS_DATA_FILE}")
                return []

            with open(PROGRESS_DATA_FILE, "r", encoding="utf-8") as f:
                progresses = json.load(f)

            print(f"   从 {PROGRESS_DATA_FILE} 加载了 {len(progresses)} 条维修进度")
            return progresses

        except Exception as e:
            print(f"   加载维修进度失败：{e}")
            return []

    def _extract_price_protection_data(self) -> List[Dict[str, Any]]:
        """从工具文件中提取价保信息数据

        Returns:
            List[Dict[str, Any]]: 价保信息列表
        """
        try:
            # 这里需要从tools/price_protect.py中提取数据
            # 由于该文件包含硬编码数据，我们直接在这里定义转换逻辑
            # 这是price_protect.py中数据的简化版本

            price_protection_data = [
                # user_2
                {
                    "order_id": "RM20250401001",
                    "user_id": "user_2",
                    "product": "realme GT Neo6 SE",
                    "original_price": 1999.00,
                    "current_price": 1899.00,
                    "protect_amount": 100.00,
                    "protect_deadline": "2025-05-01",
                    "is_protectable": True,
                    "status": "可申请价保"
                },
                {
                    "order_id": "RM20250410002",
                    "user_id": "user_2",
                    "product": "realme Buds Air 6",
                    "original_price": 399.00,
                    "current_price": 399.00,
                    "protect_amount": 0.00,
                    "protect_deadline": "2025-05-10",
                    "is_protectable": False,
                    "status": "不支持价保"
                },
                # user_1
                {
                    "order_id": "RM20250315003",
                    "user_id": "user_1",
                    "product": "realme 12 Pro+",
                    "original_price": 2799.00,
                    "current_price": 2599.00,
                    "protect_amount": 200.00,
                    "protect_deadline": "2025-04-15",
                    "is_protectable": True,
                    "status": "可申请价保"
                },
                # user_3
                {
                    "order_id": "RM20250201004",
                    "user_id": "user_3",
                    "product": "realme Pad 2",
                    "original_price": 1499.00,
                    "current_price": 1399.00,
                    "protect_amount": 100.00,
                    "protect_deadline": "2025-03-01",
                    "is_protectable": True,
                    "status": "可申请价保"
                },
                {
                    "order_id": "RM20250210005",
                    "user_id": "user_3",
                    "product": "realme Watch 3",
                    "original_price": 349.00,
                    "current_price": 349.00,
                    "protect_amount": 0.00,
                    "protect_deadline": "2025-03-10",
                    "is_protectable": False,
                    "status": "不支持价保"
                },
                {
                    "order_id": "RM20250305006",
                    "user_id": "user_3",
                    "product": "realme GT Neo6 SE",
                    "original_price": 1999.00,
                    "current_price": 1999.00,
                    "protect_amount": 0.00,
                    "protect_deadline": "2025-04-05",
                    "is_protectable": False,
                    "status": "价保已过期"
                },
                # 其他用户的数据可以类似添加
            ]

            print(f"   提取了 {len(price_protection_data)} 条价保信息")
            return price_protection_data

        except Exception as e:
            print(f"   提取价保信息失败：{e}")
            return []

    def _extract_user_orders_data(self) -> List[Dict[str, Any]]:
        """从工具文件中提取用户订单数据

        Returns:
            List[Dict[str, Any]]: 用户订单列表
        """
        try:
            # 这是从tools/price_protect.py中提取的用户订单数据简化版本

            user_orders_data = [
                # user_2
                {
                    "user_id": "user_2",
                    "order_id": "RM20250401001",
                    "product_name": "realme GT Neo6 SE",
                    "order_time": "2025-04-01 15:30:00",
                    "price": 1999.00
                },
                {
                    "user_id": "user_2",
                    "order_id": "RM20250410002",
                    "product_name": "realme Buds Air 6",
                    "order_time": "2025-04-10 11:20:00",
                    "price": 399.00
                },
                # user_1
                {
                    "user_id": "user_1",
                    "order_id": "RM20250315003",
                    "product_name": "realme 12 Pro+",
                    "order_time": "2025-03-15 09:45:00",
                    "price": 2799.00
                },
                # user_3
                {
                    "user_id": "user_3",
                    "order_id": "RM20250201004",
                    "product_name": "realme Pad 2",
                    "order_time": "2025-02-01 16:10:00",
                    "price": 1499.00
                },
                {
                    "user_id": "user_3",
                    "order_id": "RM20250210005",
                    "product_name": "realme Watch 3",
                    "order_time": "2025-02-10 10:00:00",
                    "price": 349.00
                },
                {
                    "user_id": "user_3",
                    "order_id": "RM20250305006",
                    "product_name": "realme GT Neo6 SE",
                    "order_time": "2025-03-05 18:30:00",
                    "price": 1999.00
                },
                # 可以根据需要添加更多数据
            ]

            print(f"   提取了 {len(user_orders_data)} 条用户订单")
            return user_orders_data

        except Exception as e:
            print(f"   提取用户订单失败：{e}")
            return []

    def verify_migration(self) -> Dict[str, Any]:
        """验证迁移结果

        Returns:
            Dict[str, Any]: 验证结果
        """
        verification = {
            "tables_exist": False,
            "table_counts": {},
            "data_consistency": {},
            "total_records": 0
        }

        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # 检查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row["name"] for row in cursor.fetchall()]
            expected_tables = [
                "users", "conversations", "messages",
                "repair_orders", "repair_progress",
                "price_protection", "user_orders"
            ]

            verification["tables_exist"] = all(table in tables for table in expected_tables)
            verification["existing_tables"] = tables
            verification["missing_tables"] = [t for t in expected_tables if t not in tables]

            # 统计每个表的记录数
            for table in expected_tables:
                if table in tables:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cursor.fetchone()["count"]
                    verification["table_counts"][table] = count
                    verification["total_records"] += count
                else:
                    verification["table_counts"][table] = 0

            # 检查数据一致性（维修订单和进度表的订单ID对应关系）
            if "repair_orders" in tables and "repair_progress" in tables:
                cursor.execute("""
                    SELECT
                        COUNT(DISTINCT ro.order_id) as total_orders,
                        COUNT(DISTINCT rp.order_id) as orders_with_progress,
                        COUNT(DISTINCT ro.order_id) - COUNT(DISTINCT rp.order_id) as missing_progress
                    FROM repair_orders ro
                    LEFT JOIN repair_progress rp ON ro.order_id = rp.order_id
                """)
                consistency = cursor.fetchone()
                verification["data_consistency"]["repair"] = {
                    "total_orders": consistency["total_orders"],
                    "orders_with_progress": consistency["orders_with_progress"],
                    "missing_progress": consistency["missing_progress"]
                }

        return verification

    def create_backup(self) -> str:
        """创建数据库备份

        Returns:
            str: 备份文件路径
        """
        if not self.db_manager.check_database_exists():
            print("   数据库不存在，无需备份")
            return ""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BASE_DIR, f"realme_customer_service_backup_{timestamp}.db")

        try:
            with open(self.db_manager.db_path, "rb") as source, open(backup_path, "wb") as target:
                target.write(source.read())
            print(f"   数据库已备份到：{backup_path}")
            return backup_path
        except Exception as e:
            print(f"   数据库备份失败：{e}")
            return ""


def run_migration() -> Dict[str, Any]:
    """运行完整的数据迁移流程

    Returns:
        Dict[str, Any]: 迁移结果
    """
    print("=" * 60)
    print("[数据迁移] Realme客户服务系统 - 数据迁移工具")
    print("=" * 60)

    db_manager = get_db_manager()
    migration = DataMigration(db_manager)

    # 1. 创建备份
    print("\n[备份] 创建数据库备份...")
    backup_file = migration.create_backup()
    if backup_file:
        print(f"   备份文件：{backup_file}")

    # 2. 初始化数据库（如果不存在）
    print("\n[初始化] 初始化数据库...")
    if not db_manager.check_database_exists():
        db_manager.initialize_database()
        print("   数据库已初始化")
    else:
        print("   数据库已存在，跳过初始化")

    # 3. 执行数据迁移
    print("\n[迁移] 执行数据迁移...")
    migration_results = migration.migrate_all()

    # 4. 验证迁移结果
    print("\n[验证] 验证迁移结果...")
    verification = migration.verify_migration()

    # 打印验证结果
    print("\n[报告] 迁移验证报告：")
    print(f"   表结构完整性: {'[OK]' if verification['tables_exist'] else '[FAIL]'}")
    if not verification['tables_exist']:
        print(f"   缺少的表: {verification['missing_tables']}")

    print(f"\n   表记录统计：")
    for table, count in verification["table_counts"].items():
        print(f"     {table}: {count} 条")

    print(f"\n   总计记录数: {verification['total_records']}")

    if "repair" in verification["data_consistency"]:
        repair_consistency = verification["data_consistency"]["repair"]
        print(f"\n   维修数据一致性：")
        print(f"     总订单数: {repair_consistency['total_orders']}")
        print(f"     有进度的订单: {repair_consistency['orders_with_progress']}")
        print(f"     缺少进度的订单: {repair_consistency['missing_progress']}")

    print("\n" + "=" * 60)
    print("[完成] 数据迁移流程完成！")
    print("=" * 60)

    return {
        "migration_results": migration_results,
        "verification": verification,
        "backup_file": backup_file
    }


if __name__ == "__main__":
    # 命令行入口点
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        print("[警告] 强制运行迁移（不创建备份）")
        # 这里可以跳过备份步骤
        pass

    results = run_migration()

    # 如果有缺失的表，提供修复建议
    if results["verification"].get("missing_tables"):
        print("\n[建议] 建议修复：")
        print("   1. 删除现有数据库文件重新运行迁移")
        print("   2. 或手动运行 database/db.py 中的 initialize_database() 函数")