# -*- coding: utf-8 -*-
import re
from agentscope.message import TextBlock
from agentscope.tool._response import ToolResponse

MOCK_IMEI_DATABASE = {
    # 有效手机 + 有保卡 + 有保险
    "862178050123456": {
        "product_model": "realme GT Neo7",
        "activate_time": "2025-01-15 09:23:11",
        "warranty_end_time": "2026-01-15 23:59:59",
        "is_authentic": True
    },
    "862178050123457": {
        "product_model": "realme 13 Pro+",
        "activate_time": "2025-02-20 14:12:33",
        "warranty_end_time": "2026-02-20 23:59:59",
        "is_authentic": True
    },
    "862178050123458": {
        "product_model": "realme GT7 Pro",
        "activate_time": "2024-12-01 16:45:22",
        "warranty_end_time": "2025-12-01 23:59:59",
        "is_authentic": True
    },
    # 有效手机 + 有保卡 + 无保险
    "862178050123459": {
        "product_model": "realme V60s",
        "activate_time": "2025-03-10 11:10:15",
        "warranty_end_time": "2026-03-10 23:59:59",
        "is_authentic": True
    },
    "862178050123460": {
        "product_model": "realme C65",
        "activate_time": "2025-01-05 08:30:00",
        "warranty_end_time": "2026-01-05 23:59:59",
        "is_authentic": True
    },
    # 有效手机 + 无保卡（判定非正品）
    "862178050123461": {
        "product_model": None,
        "activate_time": None,
        "warranty_end_time": None,
        "is_authentic": False
    },
    "862178050123462": {
        "product_model": None,
        "activate_time": None,
        "warranty_end_time": None,
        "is_authentic": False
    },
}

MOCK_INSURANCE_DATABASE = {
    "862178050123456": [
        {
            "type": "碎屏保障险",
            "start_time": "2025-01-15",
            "end_time": "2026-01-15",
            "status": "有效",
            "insure_company": "realme官方保险"
        },
        {
            "type": "延长保修服务",
            "start_time": "2026-01-16",
            "end_time": "2027-01-16",
            "status": "未生效",
            "insure_company": "realme官方保险"
        }
    ],
    "862178050123457": [
        {
            "type": "全保险",
            "start_time": "2025-02-20",
            "end_time": "2026-02-20",
            "status": "有效",
            "insure_company": "realme官方保险"
        }
    ],
    "862178050123458": [
        {
            "type": "碎屏保障险",
            "start_time": "2024-12-01",
            "end_time": "2025-12-01",
            "status": "有效",
            "insure_company": "realme官方保险"
        }
    ],
}  

# ====================== 工具 1：校验 IMEI 有效性 ======================
async def check_imei_validity(
    imei: str,
) -> ToolResponse:
    """Verify the validity of the IMEI format (15 or 16 digits).

    Args:
        imei (`str`):
            The IMEI number provided by the user.

    Returns:
        `ToolResponse`:
            Validation result.
    """
    if not isinstance(imei, str) or not re.fullmatch(r"^\d{15,16}$", imei):
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Error: Invalid IMEI format. Please enter a 15-16 digit number.",
                ),
            ],
        )
    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text="Success: IMEI format is valid.",
            ),
        ],
    )

# ====================== 工具 2：查询电子保卡 & 产品真伪 ======================
async def query_e_warranty_card(
    imei: str,
) -> ToolResponse:
    """Query e-warranty and authenticity info by IMEI.

    Args:
        imei (`str`):
            Validated IMEI number.

    Returns:
        `ToolResponse`:
            Warranty and authenticity result.
    """
    if not re.fullmatch(r"^\d{15,16}$", imei):
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Error: IMEI format invalid, please check and try again.",
                ),
            ],
        )

    data = MOCK_IMEI_DATABASE.get(imei)
    if not data or not data["is_authentic"]:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Result: IMEI {imei} is NOT authentic. No e-warranty record found.",
                ),
            ],
        )

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=(
                    f"Success: E-warranty found for IMEI {imei}\n"
                    f"Model: {data['product_model']}\n"
                    f"Activated: {data['activate_time']}\n"
                    f"Warranty until: {data['warranty_end_time']}\n"
                    f"Authentic: YES"
                ),
            ),
        ],
    )

# ====================== 工具 3：查询已购保险 ======================
async def query_product_insurance(
    imei: str,
) -> ToolResponse:
    """Query all purchased insurance by IMEI.

    Args:
        imei (`str`):
            Validated IMEI number.

    Returns:
        `ToolResponse`:
            Insurance list or no insurance message.
    """
    insurance_list = MOCK_INSURANCE_DATABASE.get(imei, [])
    if not insurance_list:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Result: No insurance found for IMEI {imei}.",
                ),
            ],
        )

    insurance_text = "\n".join([
        f"- {item['type']} | {item['start_time']} ~ {item['end_time']} | {item['status']}"
        for item in insurance_list
    ])

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=f"Success: Found {len(insurance_list)} insurance(s):\n{insurance_text}",
            ),
        ],
    )

# ====================== 工具 4：判断是否为 IoT 产品 ======================
async def is_iot_product(
    product_name: str,
) -> ToolResponse:
    """Check if the product belongs to IoT category.

    Args:
        product_name (`str`):
            Product name input by user.

    Returns:
        `ToolResponse`:
            True/False judgment.
    """
    match = any(
        keyword in product_name.lower()
        for keyword in [
    "耳机", "蓝牙耳机", "真我耳机", "手表", "智能手表",
    "平板", "平板电脑", "笔记本", "笔记本电脑", "手环",
    "充电器", "移动电源", "数据线"
]
    )
    if match:
        return ToolResponse(
            content=[TextBlock(type="text", text="True")],
        )
    return ToolResponse(
        content=[TextBlock(type="text", text="False")],
    )

# ====================== 工具 5：获取 IoT 真伪说明 ======================
async def get_iot_authenticity_info(
    product_type: str,
) -> ToolResponse:
    """Get official authenticity description for IoT products.

    Args:
        product_type (`str`):
            IoT product type (earphone, watch, pad, etc.)

    Returns:
        `ToolResponse`:
            Official explanation text.
    """
    info = (
        f"Official realme {product_type} authenticity info:\n"
        "1. Purchased from official channels = authentic\n"
        "2. Enjoy official warranty service\n"
        "3. For doubt, please visit realme service center for detection."
    )
    return ToolResponse(
        content=[TextBlock(type="text", text=info)],
    )

# ====================== 工具 6：根据产品名获取标准型号 ======================
async def get_standard_product_model(
    product_name: str,
) -> ToolResponse:
    """Return standard model name for realme products.

    Args:
        product_name (`str`):
            User input product name.

    Returns:
        `ToolResponse`:
            Standard model string.
    """
    lower = product_name.lower()
    if "gt neo7" in lower:
        standard = "realme GT Neo7"
    elif "13 pro+" in lower:
        standard = "realme 13 Pro+"
    elif "gt7 pro" in lower:
        standard = "realme GT7 Pro"
    elif "v60s" in lower:
        standard = "realme V60s"
    elif "c65" in lower:
        standard = "realme C65"
    else:
        standard = "unknown realme device"

    return ToolResponse(
        content=[TextBlock(type="text", text=f"Standard model: {standard}")],
    )

