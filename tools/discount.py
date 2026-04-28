
# -*- coding: utf-8 -*-
import json
from agentscope.message import TextBlock
from agentscope.tool._response import ToolResponse

# 模拟产品数据库
PRODUCT_DB = {
    "GT7": {
        "product_type": "phone",
        "original_price": 3799,
        "discount_price": 3499,
        "discount_rate": "92%",
        "gift": ["手机壳", "钢化膜", "碎屏险1个月"],
        "activity": "新品首销直降300元",
        "stock_status": "in_stock"
    },
    "GT8 Pro": {
        "product_type": "phone",
        "original_price": 4299,
        "discount_price": 3999,
        "discount_rate": "93%",
        "gift": ["67W充电器", "手机壳", "碎屏险1个月"],
        "activity": "618大促直降300元",
        "stock_status": "in_stock"
    },
    "realme Pad 2": {
        "product_type": "tablet",
        "original_price": 1999,
        "discount_price": 1799,
        "discount_rate": "90%",
        "gift": ["平板保护套", "触控笔"],
        "activity": "教育优惠直降200元",
        "stock_status": "in_stock"
    },
    "GT Neo 5": {
        "product_type": "phone",
        "original_price": 2599,
        "discount_price": 2299,
        "discount_rate": "88%",
        "gift": ["充电器", "手机壳"],
        "activity": "清仓特惠",
        "stock_status": "out_of_stock"
    }
}

async def query_product_discount(model: str, product_type: str = "phone") -> ToolResponse:
    """
    查询产品折扣信息工具
    :param model: 产品型号
    :param product_type: 产品类型，默认phone
    :return: 工具响应
    """

    # 校验型号是否存在
    if model not in PRODUCT_DB:
        return ToolResponse(
            content=[
                TextBlock(type="text", text=f"model: {model}"),
                TextBlock(type="text", text=f"status: model_not_found"),
                TextBlock(type="text", text=f"stock_status: out_of_stock")
            ]
        )

    product_info = PRODUCT_DB[model]

    return ToolResponse(
        content=[
            TextBlock(type="text", text=json.dumps({
                "model": model,
                "product_type": product_info["product_type"],
                "original_price": product_info["original_price"],
                "discount_price": product_info["discount_price"],
                "discount_rate": product_info["discount_rate"],
                "gift": product_info["gift"],
                "activity": product_info["activity"],
                "stock_status": product_info["stock_status"]
            }, ensure_ascii=False, indent=2))
        ]
    )

async def query_product_stock(model: str) -> ToolResponse:
    """
    查询产品库存状态工具
    :param model: 产品型号
    :return: 工具响应
    """
    if model not in PRODUCT_DB:
        stock_status = "out_of_stock"
        stock_count = 0
    else:
        stock_status = PRODUCT_DB[model]["stock_status"]
        stock_count = 120 if stock_status == "in_stock" else 0

    return ToolResponse(
        content=[
            TextBlock(type="text", text=f"model: {model}"),
            TextBlock(type="text", text=f"stock_status: {stock_status}"),
            TextBlock(type="text", text=f"stock_count: {stock_count}")
        ]
    )
