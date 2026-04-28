from mcp.server import FastMCP
from typing import List, Dict

mcp = FastMCP("ServiceCenter", port=8002)

# ==============================
# 工具1：查询服务网点
# ==============================
@mcp.tool()
def get_service_centers(city: str, area: str = "") -> List[Dict]:
    """
    查询指定城市/区域的官方服务网点
    :param city: 城市，如 合肥市
    :param area: 区域，如 蜀山区，可为空
    """
    return [
        {
            "center_id": "HF001",
            "name": f"{city}官方服务中心({area or '主城'}店)",
            "address": f"{city}{area or '经开区'}智慧产业园1楼",
            "phone": "400-123-8888",
            "business_hours": "9:00-18:00 全年无休",
            "distance": "1.2km"
        }
    ]

# ==============================
# 工具2：预约到店维修
# ==============================
@mcp.tool()
def create_instore_appointment(
    user_name: str,
    user_phone: str,
    city: str,
    center_id: str,
    appointment_time: str
) -> Dict:
    """
    创建到店维修预约
    :param user_name: 用户姓名
    :param user_phone: 用户手机号
    :param city: 所在城市
    :param center_id: 服务网点ID
    :param appointment_time: 预约时间，格式 YYYY-MM-DD HH:mm
    """
    return {
        "status": "success",
        "appointment_id": f"APT_{center_id}_{user_phone[-4:]}",
        "message": "预约成功，请按时到店并携带购机凭证。"
    }

if __name__ == "__main__":
    mcp.run(transport="streamable-http")