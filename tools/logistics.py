# -*- coding: utf-8 -*-
from agentscope.message import TextBlock
from agentscope.tool._response import ToolResponse

ORDER_DATA = {
    "user_2": [
        {
            "order_id": "ORD20260414001",
            "create_time": "2026-04-14 10:30:00",
            "status": "已发货",
            "logistics": {
                "company": "顺丰速运",
                "tracking_no": "SF1234567890123",
                "status": "运输中",
                "update_time": "2026-04-14 14:00:00",
                "trace": [
                    "2026-04-14 10:00:00 【深圳】已揽收",
                    "2026-04-14 14:00:00 【深圳】已发往【合肥】"
                ]
            }
        },
        {
            "order_id": "ORD20260410001",
            "create_time": "2026-04-10 09:15:00",
            "status": "已签收",
            "logistics": {
                "company": "中通快递",
                "tracking_no": "ZT9876543210987",
                "status": "已签收",
                "update_time": "2026-04-12 18:30:00",
                "trace": [
                    "2026-04-10 09:00:00 【杭州】已揽收",
                    "2026-04-12 18:30:00 【合肥】已签收"
                ]
            }
        }
    ],
    "user_002": [],  # 无订单
    "user_003": [
        {
            "order_id": "ORD20260413001",
            "create_time": "2026-04-13 16:20:00",
            "status": "未发货",
            "logistics": None
        },
        {
            "order_id": "ORD20260412002",
            "create_time": "2026-04-12 11:40:00",
            "status": "已签收",
            "logistics": {
                "company": "圆通速递",
                "tracking_no": "YT5678901234567",
                "status": "已签收",
                "update_time": "2026-04-13 09:15:00",
                "trace": [
                    "2026-04-12 11:30:00 【上海】已揽收",
                    "2026-04-12 18:00:00 【上海】已发往【南京】",
                    "2026-04-13 08:30:00 【南京】派送中",
                    "2026-04-13 09:15:00 【南京】已签收"
                ]
            }
        }
    ],
    "user_004": [
        {
            "order_id": "ORD20260414002",
            "create_time": "2026-04-14 09:10:00",
            "status": "已发货",
            "logistics": {
                "company": "京东物流",
                "tracking_no": "JD1122334455667",
                "status": "派送中",
                "update_time": "2026-04-14 13:30:00",
                "trace": [
                    "2026-04-14 08:00:00 【北京】已揽收",
                    "2026-04-14 10:00:00 【北京】已发往【天津】",
                    "2026-04-14 13:30:00 【天津】派送员正在派送"
                ]
            }
        }
    ],
    "user_005": [
        {
            "order_id": "ORD20260411001",
            "create_time": "2026-04-11 15:25:00",
            "status": "已取消",
            "logistics": None
        },
        {
            "order_id": "ORD20260409001",
            "create_time": "2026-04-09 10:00:00",
            "status": "已签收",
            "logistics": {
                "company": "申通快递",
                "tracking_no": "ST7766554433221",
                "status": "已签收",
                "update_time": "2026-04-10 17:40:00",
                "trace": [
                    "2026-04-09 09:30:00 【广州】已揽收",
                    "2026-04-10 17:40:00 【成都】已签收"
                ]
            }
        }
    ],
    "user_006": [
        {
            "order_id": "ORD20260414003",
            "create_time": "2026-04-14 11:20:00",
            "status": "已发货",
            "logistics": {
                "company": "极兔快递",
                "tracking_no": "JT9988776655443",
                "status": "运输中",
                "update_time": "2026-04-14 15:10:00",
                "trace": [
                    "2026-04-14 11:00:00 【武汉】已揽收",
                    "2026-04-14 15:10:00 【武汉】已发往【长沙】"
                ]
            }
        }
    ],
    "user_007": [],
    "user_008": [
        {
            "order_id": "ORD20260413002",
            "create_time": "2026-04-13 14:30:00",
            "status": "未发货",
            "logistics": None
        },
        {
            "order_id": "ORD20260411002",
            "create_time": "2026-04-11 16:10:00",
            "status": "已签收",
            "logistics": {
                "company": "中国邮政",
                "tracking_no": "YZ123123123123",
                "status": "已签收",
                "update_time": "2026-04-13 10:20:00",
                "trace": [
                    "2026-04-11 15:45:00 【西安】已揽收",
                    "2026-04-13 10:20:00 【郑州】已签收"
                ]
            }
        }
    ],
    "user_009": [
        {
            "order_id": "ORD20260414004",
            "create_time": "2026-04-14 13:00:00",
            "status": "已发货",
            "logistics": {
                "company": "顺丰速运",
                "tracking_no": "SF5566778899001",
                "status": "运输中",
                "update_time": "2026-04-14 16:00:00",
                "trace": [
                    "2026-04-14 12:30:00 【重庆】已揽收",
                    "2026-04-14 16:00:00 【重庆】已发往【贵阳】"
                ]
            }
        }
    ],
    "user_010": [
        {
            "order_id": "ORD20260412001",
            "create_time": "2026-04-12 10:00:00",
            "status": "已签收",
            "logistics": {
                "company": "中通快递",
                "tracking_no": "ZT2233445566778",
                "status": "已签收",
                "update_time": "2026-04-13 11:50:00",
                "trace": [
                    "2026-04-12 09:40:00 【苏州】已揽收",
                    "2026-04-13 11:50:00 【无锡】已签收"
                ]
            }
        }
    ]
}

# 注：这个工具，只是模拟用户是否登录
async def order_check_login_status(
    user_id: str,
) -> ToolResponse:
    """
    校验用户登录状态
    
    Args:
        user_id (`str`): 用户唯一标识ID
    
    Returns:
        `ToolResponse`: 登录状态结果
    """
    if not user_id:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="错误：用户ID不能为空",
                ),
            ],
        )
    
    login_status = "已登录" if user_id in ORDER_DATA else "未登录"
    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=f"登录状态校验结果：{login_status}",
            ),
        ],
        metadata={"login_status": login_status}
    )

async def query_order_info(
    user_id: str,
    include_history: bool = True,
) -> ToolResponse:
    """
    查询用户订单信息（支持历史订单）

    Args:
        user_id (`str`): 用户唯一标识ID
        include_history (`bool`): 是否包含历史订单，默认True

    Returns:
        `ToolResponse`: 订单列表结果
    """
    if not user_id:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="错误：用户ID不能为空",
                ),
            ],
        )

    if user_id not in ORDER_DATA:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"错误：用户 {user_id} 不存在",
                ),
            ],
        )

    orders = ORDER_DATA[user_id]
    if not orders:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="未查询到该用户的任何订单信息",
                ),
            ],
            metadata={"has_order": False, "orders": []}
        )

    if not include_history:
        orders = [o for o in orders if o["status"] != "已签收"]

    # 构建包含订单详情的返回文本
    order_list = []
    for order in orders:
        order_list.append(
            f"订单号：{order['order_id']}，"
            f"下单时间：{order['create_time']}，"
            f"状态：{order['status']}"
        )

    result_text = f"为用户 {user_id} 找到 {len(orders)} 个订单：\n" + "\n".join(order_list)

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=result_text,
            ),
        ],
        metadata={"has_order": True, "orders": orders}
    )

async def query_logistics_info(
    order_id: str,
    user_id: str,
) -> ToolResponse:
    """
    查询指定订单的物流信息
    
    Args:
        order_id (`str`): 订单ID
        user_id (`str`): 用户唯一标识ID
    
    Returns:
        `ToolResponse`: 物流轨迹结果
    """
    if not order_id or not user_id:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="错误：订单ID和用户ID均不能为空",
                ),
            ],
        )
    
    if user_id not in ORDER_DATA:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"错误：用户 {user_id} 不存在",
                ),
            ],
        )
    
    target_order = None
    for order in ORDER_DATA[user_id]:
        if order["order_id"] == order_id:
            target_order = order
            break
    
    if not target_order:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"错误：未找到用户 {user_id} 的订单 {order_id}",
                ),
            ],
        )
    
    if not target_order["logistics"]:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"订单 {order_id} 状态：{target_order['status']}，暂无物流信息",
                ),
            ],
        )
    
    logistics = target_order["logistics"]
    trace_str = "\n".join(logistics["trace"])
    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=f"""
订单 {order_id} 物流信息：
快递公司：{logistics['company']}
运单编号：{logistics['tracking_no']}
物流状态：{logistics['status']}
最新更新：{logistics['update_time']}

物流轨迹：
{trace_str}""",
            ),
        ],
        metadata={"logistics": logistics}
    )

async def cancel_order_query(
    user_id: str,
) -> ToolResponse:
    """
    处理用户取消订单查询请求
    
    Args:
        user_id (`str`): 用户唯一标识ID
    
    Returns:
        `ToolResponse`: 取消操作结果
    """
    if not user_id:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="错误：用户ID不能为空",
                ),
            ],
        )
    
    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=f"用户 {user_id} 已成功取消订单查询",
            ),
        ],
        metadata={"status": "cancelled"}
    )

