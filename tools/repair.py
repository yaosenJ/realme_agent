# -*- coding: utf-8 -*-
import json
import os
from agentscope.message import TextBlock
from agentscope.tool._response import ToolResponse
from config import ORDER_DATA_FILE, PROGRESS_DATA_FILE, USE_DATABASE

# 尝试导入数据库模块
try:
    from database.crud import RepairOrderCRUD, RepairProgressCRUD
    HAS_DATABASE = True
except ImportError:
    HAS_DATABASE = False
    print("⚠️ 数据库模块导入失败，将使用JSON文件模式")

# ------------------------------
# 工具1：登录状态校验
# ------------------------------
async def check_login_status(user_id: str = None) -> ToolResponse:
    """检查用户登录状态

    Args:
        user_id: 用户ID，如果为None则使用默认测试用户
    """
    # 如果未提供user_id，使用默认的测试用户（向后兼容）
    if user_id is None:
        user_id = "user_2"

    login_info = {
        "is_logged_in": True,
        "user_id": user_id
    }
    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=f"is_logged_in: {login_info['is_logged_in']}"
            ),
            TextBlock(
                type="text",
                text=f"user_id: {login_info['user_id']}"
            )
        ]
    )

# ------------------------------
# 工具2：根据账号查询订单
# ------------------------------
async def get_user_repair_orders(user_id: str) -> ToolResponse:
    """获取用户的维修订单

    优先从数据库查询，如果数据库不可用则从JSON文件查询
    """

    # 检查是否使用数据库
    if USE_DATABASE and HAS_DATABASE:
        try:
            # 从数据库查询
            orders = RepairOrderCRUD.get_user_repair_orders(user_id)
            if orders is None:
                orders = []

            response_text = f"订单列表（数据库查询）：{orders}"

        except Exception as e:
            print(f"数据库查询失败，回退到JSON文件：{e}")
            # 回退到JSON文件
            orders = _get_orders_from_json(user_id)
            response_text = f"订单列表（JSON文件查询）：{orders}"
    else:
        # 使用JSON文件
        orders = _get_orders_from_json(user_id)
        response_text = f"订单列表（JSON文件查询）：{orders}"

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=response_text
            )
        ]
    )

def _get_orders_from_json(user_id: str):
    """从JSON文件获取用户订单（辅助函数）"""
    try:
        with open(ORDER_DATA_FILE, "r", encoding="utf-8") as f:
            all_orders = json.load(f)
        user_orders = [o for o in all_orders if o["user_id"] == user_id]
        return user_orders
    except Exception as e:
        print(f"从JSON文件读取订单失败：{e}")
        return []

# ------------------------------
# 工具3：查询维修订单进度
# ------------------------------
async def get_repair_order_progress(order_id: str) -> ToolResponse:
    """查询维修订单进度

    优先从数据库查询，如果数据库不可用则从JSON文件查询
    """

    # 检查是否使用数据库
    if USE_DATABASE and HAS_DATABASE:
        try:
            # 从数据库查询
            progress = RepairProgressCRUD.get_repair_progress(order_id)

            if not progress:
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=f"查询失败 | 订单 {order_id} 不存在（数据库查询）"
                        )
                    ]
                )

            response_text = (
                f"【维修进度查询结果 - 数据库】\n"
                f"订单号：{progress['order_id']}\n"
                f"设备型号：{progress.get('device_model', '未知')}\n"
                f"当前状态：{progress['status']}\n"
                f"最新进度：{progress.get('latest_progress', '无')}\n"
                f"预计完成时间：{progress.get('expected_time', '未知')}"
            )

        except Exception as e:
            print(f"数据库查询失败，回退到JSON文件：{e}")
            # 回退到JSON文件
            progress = _get_progress_from_json(order_id)
            if not progress:
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=f"查询失败 | 订单 {order_id} 不存在（JSON文件查询）"
                        )
                    ]
                )

            response_text = (
                f"【维修进度查询结果 - JSON文件】\n"
                f"订单号：{progress['order_id']}\n"
                f"设备型号：{progress['device_model']}\n"
                f"当前状态：{progress['status']}\n"
                f"最新进度：{progress['latest_progress']}\n"
                f"预计完成时间：{progress['expected_time']}"
            )
    else:
        # 使用JSON文件
        progress = _get_progress_from_json(order_id)
        if not progress:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"查询失败 | 订单 {order_id} 不存在（JSON文件查询）"
                    )
                ]
            )

        response_text = (
            f"【维修进度查询结果 - JSON文件】\n"
            f"订单号：{progress['order_id']}\n"
            f"设备型号：{progress['device_model']}\n"
            f"当前状态：{progress['status']}\n"
            f"最新进度：{progress['latest_progress']}\n"
            f"预计完成时间：{progress['expected_time']}"
        )

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=response_text
            )
        ]
    )

def _get_progress_from_json(order_id: str):
    """从JSON文件获取维修进度（辅助函数）"""
    try:
        with open(PROGRESS_DATA_FILE, "r", encoding="utf-8") as f:
            all_progress = json.load(f)
        progress = next((p for p in all_progress if p["order_id"] == order_id), None)
        return progress
    except Exception as e:
        print(f"从JSON文件读取进度失败：{e}")
        return None

