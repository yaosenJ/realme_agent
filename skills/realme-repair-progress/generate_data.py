import asyncio
import json
import os
from datetime import datetime
from pydantic import BaseModel
from typing import List, Dict, Any

# ------------------------------
# 配置：本地数据文件
# ------------------------------
ORDER_DATA_FILE = "repair_orders_100.json"
PROGRESS_DATA_FILE = "repair_progress_100.json"

# ------------------------------
# 【一次性生成 100 条订单 + 100 条进度数据】
# ------------------------------
def generate_dummy_data():
    if not os.path.exists(ORDER_DATA_FILE):
        orders = []
        for i in range(1, 101):
            orders.append({
                "user_id": f"user_{i % 5 + 1}",  # 5个测试账号：user_1 ~ user_5
                "order_id": f"RMA20260413{i:03d}",
                "device_model": f"realme GT Neo{i % 10 + 1}",
                "status": ["待检测", "维修中", "待取件", "已完成"][i % 4]
            })
        with open(ORDER_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)

    if not os.path.exists(PROGRESS_DATA_FILE):
        progresses = []
        for i in range(1, 101):
            order_id = f"RMA20260413{i:03d}"
            progresses.append({
                "order_id": order_id,
                "device_model": f"realme GT Neo{i % 10 + 1}",
                "status": ["待检测", "维修中", "待取件", "已完成"][i % 4],
                "latest_progress": [
                    "等待工程师接单",
                    "硬件检测中",
                    "配件更换中",
                    "质检完成，待取件"
                ][i % 4],
                "expected_time": f"2026-04-{13 + (i % 3):02d} 18:00"
            })
        with open(PROGRESS_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(progresses, f, ensure_ascii=False, indent=2)

# 启动时自动生成数据
generate_dummy_data()