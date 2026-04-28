# -*- coding: utf-8 -*-
import json
from agentscope.message import TextBlock
from agentscope.tool._response import ToolResponse
from config import USE_DATABASE

# 尝试导入数据库模块
try:
    from database.crud import PriceProtectionCRUD, UserOrderCRUD
    HAS_DATABASE = True
except ImportError:
    HAS_DATABASE = False
    print("⚠️ 数据库模块导入失败，将使用硬编码数据模式")

# ==============================
# 工具1：realme用户登录状态校验
# ==============================
async def check_realme_login_status(user_id: str = None) -> ToolResponse:
    """Check whether the user is logged into realme account for price protection query.

    Args:
        user_id: 用户ID，如果为None则使用默认测试用户

    Returns:
        ToolResponse: Login status and user info.
    """
    try:
        # 如果未提供user_id，使用默认的测试用户（向后兼容）
        if user_id is None:
            user_id = "user_2"

        session = {
            "is_logged_in": True,
            "user_id": user_id,
        }

        if not session["is_logged_in"]:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"""Login check result:
{{
    "is_logged_in": false,
    "user_id": null
}}"""
                    )
                ]
            )

        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"""Login check result:
{{
    "is_logged_in": true,
    "user_id": "{session['user_id']}"
}}"""
                )
            ]
        )

    except Exception as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error checking login status: {str(e)}"
                )
            ]
        )

# ==============================
# 工具2：查询用户realme订单列表
# ==============================
async def get_realme_user_orders(
    user_id: str,
) -> ToolResponse:
    """Query all realme orders under current user account.

    Args:
        user_id (str): realme user ID

    Returns:
        ToolResponse: Order list and whether has orders.
    """
    if not user_id:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Error: user_id cannot be empty."
                )
            ]
        )

    try:
        # 检查是否使用数据库
        if USE_DATABASE and HAS_DATABASE:
            try:
                # 从数据库查询用户订单
                orders = UserOrderCRUD.get_user_orders(user_id)
                if orders is None:
                    orders = []

                has_order = len(orders) > 0
                source = "database"

            except Exception as db_error:
                print(f"数据库查询失败，回退到硬编码数据：{db_error}")
                # 回退到硬编码数据
                orders = _get_user_orders_from_hardcoded(user_id)
                has_order = len(orders) > 0
                source = "hardcoded (fallback)"
        else:
            # 使用硬编码数据
            orders = _get_user_orders_from_hardcoded(user_id)
            has_order = len(orders) > 0
            source = "hardcoded"

        if not has_order:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"""Order query result ({source}):
{{
    "user_id": "{user_id}",
    "has_order": false,
    "order_list": []
}}"""
                    )
                ]
            )

        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"""Order query result ({source}):
{{
    "user_id": "{user_id}",
    "has_order": true,
    "order_list": {orders}
}}"""
                )
            ]
        )

    except Exception as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error querying realme orders: {str(e)}"
                )
            ]
        )

# ==============================
# 工具3：查询realme订单价保信息
# ==============================
async def get_realme_order_price_protection(
    order_id: str,
) -> ToolResponse:
    """Query realme order price protection info.

    Args:
        order_id (str): realme order ID

    Returns:
        ToolResponse: Price protection card data.
    """
    if not order_id:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Error: order_id cannot be empty."
                )
            ]
        )

    try:
        # 检查是否使用数据库
        if USE_DATABASE and HAS_DATABASE:
            try:
                # 从数据库查询价保信息
                protection = PriceProtectionCRUD.get_price_protection(order_id)
                if protection:
                    source = "database"
                    # 准备返回数据
                    data = {
                        "order_id": protection["order_id"],
                        "product": protection["product_name"],
                        "original_price": protection["original_price"],
                        "current_price": protection["current_price"],
                        "protect_amount": protection["protect_amount"],
                        "protect_deadline": protection["protect_deadline"],
                        "is_protectable": protection["is_protectable"],
                        "status": protection["status"]
                    }
                else:
                    # 数据库中没有找到，回退到硬编码数据
                    data = _get_price_protection_from_hardcoded(order_id)
                    source = "hardcoded (fallback)"
            except Exception as db_error:
                print(f"数据库查询失败，回退到硬编码数据：{db_error}")
                # 回退到硬编码数据
                data = _get_price_protection_from_hardcoded(order_id)
                source = "hardcoded (fallback)"
        else:
            # 使用硬编码数据
            data = _get_price_protection_from_hardcoded(order_id)
            source = "hardcoded"

        if not data:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"""Price protection result ({source}):
{{
    "order_id": "{order_id}",
    "is_protectable": false,
    "msg": "No price protection info found"
}}"""
                    )
                ]
            )

        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"""Price protection card ({source}):
{{
    "order_id": "{data['order_id']}",
    "product": "{data['product']}",
    "original_price": {data['original_price']},
    "current_price": {data['current_price']},
    "protect_amount": {data['protect_amount']},
    "protect_deadline": "{data['protect_deadline']}",
    "is_protectable": {data['is_protectable']},
    "status": "{data['status']}"
}}"""
                )
            ]
        )

    except Exception as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error querying price protection: {str(e)}"
                )
            ])


def _get_user_orders_from_hardcoded(user_id: str) -> list:
    """从硬编码数据获取用户订单（辅助函数）

    Args:
        user_id: 用户ID

    Returns:
        list: 用户订单列表
    """
    # 从mock_protection字典中提取该用户的所有订单
    mock_protection = {
        # user_2
        "RM20250401001": {
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
        "RM20250410002": {
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
        "RM20250315003": {
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
        "RM20250201004": {
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
        "RM20250210005": {
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
        "RM20250305006": {
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
        # user_4
        "RM20250415001": {
            "order_id": "RM20250415001",
            "user_id": "user_4",
            "product": "realme 12 Pro",
            "original_price": 2199.00,
            "current_price": 2099.00,
            "protect_amount": 100.00,
            "protect_deadline": "2025-05-15",
            "is_protectable": True,
            "status": "可申请价保"
        },
        # user_5
        "RM20250412001": {
            "order_id": "RM20250412001",
            "user_id": "user_5",
            "product": "realme GT Neo7",
            "original_price": 2599.00,
            "current_price": 2499.00,
            "protect_amount": 100.00,
            "protect_deadline": "2025-05-12",
            "is_protectable": True,
            "status": "可申请价保"
        },
        "RM20250413001": {
            "order_id": "RM20250413001",
            "user_id": "user_5",
            "product": "realme Buds Air 5",
            "original_price": 299.00,
            "current_price": 299.00,
            "protect_amount": 0.00,
            "protect_deadline": "2025-05-13",
            "is_protectable": False,
            "status": "不支持价保"
        },
        # user_6
        "RM20250408001": {
            "order_id": "RM20250408001",
            "user_id": "user_6",
            "product": "realme C65",
            "original_price": 1299.00,
            "current_price": 1199.00,
            "protect_amount": 100.00,
            "protect_deadline": "2025-05-08",
            "is_protectable": True,
            "status": "可申请价保"
        },
        "RM20250409001": {
            "order_id": "RM20250409001",
            "user_id": "user_6",
            "product": "realme Pad Go",
            "original_price": 1599.00,
            "current_price": 1599.00,
            "protect_amount": 0.00,
            "protect_deadline": "2025-05-09",
            "is_protectable": False,
            "status": "不支持价保"
        },
        "RM20250410001": {
            "order_id": "RM20250410001",
            "user_id": "user_6",
            "product": "realme Watch 4",
            "original_price": 499.00,
            "current_price": 449.00,
            "protect_amount": 50.00,
            "protect_deadline": "2025-05-10",
            "is_protectable": True,
            "status": "可申请价保"
        },
        # user_7
        "RM20250411001": {
            "order_id": "RM20250411001",
            "user_id": "user_7",
            "product": "realme GT 7 Pro",
            "original_price": 3599.00,
            "current_price": 3599.00,
            "protect_amount": 0.00,
            "protect_deadline": "2025-05-11",
            "is_protectable": False,
            "status": "价保已过期"
        },
        # user_8
        "RM20250414001": {
            "order_id": "RM20250414001",
            "user_id": "user_8",
            "product": "realme 12x",
            "original_price": 1499.00,
            "current_price": 1399.00,
            "protect_amount": 100.00,
            "protect_deadline": "2025-05-14",
            "is_protectable": True,
            "status": "可申请价保"
        },
        "RM20250415002": {
            "order_id": "RM20250415002",
            "user_id": "user_8",
            "product": "realme Power Bank 10000mAh",
            "original_price": 199.00,
            "current_price": 199.00,
            "protect_amount": 0.00,
            "protect_deadline": "2025-05-15",
            "is_protectable": False,
            "status": "不支持价保"
        },
        # user_10
        "RM20250413002": {
            "order_id": "RM20250413002",
            "user_id": "user_10",
            "product": "realme GT Neo6",
            "original_price": 2299.00,
            "current_price": 2199.00,
            "protect_amount": 100.00,
            "protect_deadline": "2025-05-13",
            "is_protectable": True,
            "status": "可申请价保"
        },
        "RM20250414002": {
            "order_id": "RM20250414002",
            "user_id": "user_10",
            "product": "realme Buds T300",
            "original_price": 349.00,
            "current_price": 329.00,
            "protect_amount": 20.00,
            "protect_deadline": "2025-05-14",
            "is_protectable": True,
            "status": "可申请价保"
        },
        "RM20250415003": {
            "order_id": "RM20250415003",
            "user_id": "user_10",
            "product": "realme 11 Pro+",
            "original_price": 2699.00,
            "current_price": 2699.00,
            "protect_amount": 0.00,
            "protect_deadline": "2025-05-15",
            "is_protectable": False,
            "status": "不支持价保"
        }
    }

    # 过滤出该用户的订单，并转换为用户订单格式
    user_orders = []
    for order_id, data in mock_protection.items():
        if data["user_id"] == user_id:
            # 转换为用户订单格式（简化，只包含必要字段）
            order = {
                "order_id": data["order_id"],
                "product_name": data["product"],
                "order_time": f"2025-{data['protect_deadline'][5:7]}-{data['protect_deadline'][8:10]} 12:00:00",
                "price": data["original_price"]
            }
            user_orders.append(order)

    return user_orders


def _get_price_protection_from_hardcoded(order_id: str) -> dict:
    """从硬编码数据获取价保信息（辅助函数）

    Args:
        order_id: 订单ID

    Returns:
        dict: 价保信息字典，如果不存在返回None
    """
    mock_protection = {
        # user_2
        "RM20250401001": {
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
        "RM20250410002": {
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
        "RM20250315003": {
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
        "RM20250201004": {
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
        "RM20250210005": {
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
        "RM20250305006": {
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
        # user_4
        "RM20250415001": {
            "order_id": "RM20250415001",
            "user_id": "user_4",
            "product": "realme 12 Pro",
            "original_price": 2199.00,
            "current_price": 2099.00,
            "protect_amount": 100.00,
            "protect_deadline": "2025-05-15",
            "is_protectable": True,
            "status": "可申请价保"
        },
        # user_5
        "RM20250412001": {
            "order_id": "RM20250412001",
            "user_id": "user_5",
            "product": "realme GT Neo7",
            "original_price": 2599.00,
            "current_price": 2499.00,
            "protect_amount": 100.00,
            "protect_deadline": "2025-05-12",
            "is_protectable": True,
            "status": "可申请价保"
        },
        "RM20250413001": {
            "order_id": "RM20250413001",
            "user_id": "user_5",
            "product": "realme Buds Air 5",
            "original_price": 299.00,
            "current_price": 299.00,
            "protect_amount": 0.00,
            "protect_deadline": "2025-05-13",
            "is_protectable": False,
            "status": "不支持价保"
        },
        # user_6
        "RM20250408001": {
            "order_id": "RM20250408001",
            "user_id": "user_6",
            "product": "realme C65",
            "original_price": 1299.00,
            "current_price": 1199.00,
            "protect_amount": 100.00,
            "protect_deadline": "2025-05-08",
            "is_protectable": True,
            "status": "可申请价保"
        },
        "RM20250409001": {
            "order_id": "RM20250409001",
            "user_id": "user_6",
            "product": "realme Pad Go",
            "original_price": 1599.00,
            "current_price": 1599.00,
            "protect_amount": 0.00,
            "protect_deadline": "2025-05-09",
            "is_protectable": False,
            "status": "不支持价保"
        },
        "RM20250410001": {
            "order_id": "RM20250410001",
            "user_id": "user_6",
            "product": "realme Watch 4",
            "original_price": 499.00,
            "current_price": 449.00,
            "protect_amount": 50.00,
            "protect_deadline": "2025-05-10",
            "is_protectable": True,
            "status": "可申请价保"
        },
        # user_7
        "RM20250411001": {
            "order_id": "RM20250411001",
            "user_id": "user_7",
            "product": "realme GT 7 Pro",
            "original_price": 3599.00,
            "current_price": 3599.00,
            "protect_amount": 0.00,
            "protect_deadline": "2025-05-11",
            "is_protectable": False,
            "status": "价保已过期"
        },
        # user_8
        "RM20250414001": {
            "order_id": "RM20250414001",
            "user_id": "user_8",
            "product": "realme 12x",
            "original_price": 1499.00,
            "current_price": 1399.00,
            "protect_amount": 100.00,
            "protect_deadline": "2025-05-14",
            "is_protectable": True,
            "status": "可申请价保"
        },
        "RM20250415002": {
            "order_id": "RM20250415002",
            "user_id": "user_8",
            "product": "realme Power Bank 10000mAh",
            "original_price": 199.00,
            "current_price": 199.00,
            "protect_amount": 0.00,
            "protect_deadline": "2025-05-15",
            "is_protectable": False,
            "status": "不支持价保"
        },
        # user_10
        "RM20250413002": {
            "order_id": "RM20250413002",
            "user_id": "user_10",
            "product": "realme GT Neo6",
            "original_price": 2299.00,
            "current_price": 2199.00,
            "protect_amount": 100.00,
            "protect_deadline": "2025-05-13",
            "is_protectable": True,
            "status": "可申请价保"
        },
        "RM20250414002": {
            "order_id": "RM20250414002",
            "user_id": "user_10",
            "product": "realme Buds T300",
            "original_price": 349.00,
            "current_price": 329.00,
            "protect_amount": 20.00,
            "protect_deadline": "2025-05-14",
            "is_protectable": True,
            "status": "可申请价保"
        },
        "RM20250415003": {
            "order_id": "RM20250415003",
            "user_id": "user_10",
            "product": "realme 11 Pro+",
            "original_price": 2699.00,
            "current_price": 2699.00,
            "protect_amount": 0.00,
            "protect_deadline": "2025-05-15",
            "is_protectable": False,
            "status": "不支持价保"
        }
    }

    return mock_protection.get(order_id)

