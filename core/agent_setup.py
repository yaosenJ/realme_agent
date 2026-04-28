# -*- coding: utf-8 -*-
import os
import sys
import asyncio
from dotenv import load_dotenv
load_dotenv()
from agentscope.agent import ReActAgent
from agentscope.model import OpenAIChatModel
from agentscope.formatter import OpenAIChatFormatter
from agentscope.tool import Toolkit
from agentscope.mcp import HttpStatelessClient
from tools import *
from core.middleware import create_auto_activate_middleware
import config
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit, view_text_file
from core.multi_agent_service import MultiAgentService

async def init_agent_and_toolkit():
    """初始化工具包和智能体系统，根据启动的脚本自动选择初始化单智能体或多智能体系统"""
    # 获取当前启动的脚本名称
    script_name = os.path.basename(sys.argv[0])
    print(f"[检测] 检测到启动脚本: {script_name}")

    # 判断启动的服务类型
    if script_name == "main_agent_skill.py":
        service_type = "single"  # 单智能体服务
    elif script_name == "main.py":
        service_type = "multi"   # 多智能体服务
    else:
        # 默认启动单智能体服务（向后兼容）
        service_type = "single"
        print(f"[警告] 未知脚本 {script_name}，默认启动单智能体服务")

    print(f"[启动] 启动 {service_type} 智能体系统")

    # ====================== 工具包初始化（两个系统都需要） ======================
    config.toolkit = Toolkit()

    # 注册技能目录
    skill_list = [
        "realme-repair-progress", "find-service-center",
        "realme-charger-advisor", "realme-order-price-protection",
        "realme-product-authenticity-and-warranty-query",
        "realme-price-discount-query", "order-status-query"
    ]
    for name in skill_list:
        path = os.path.join(config.SKILLS_DIR, name)
        if os.path.exists(path):
            config.toolkit.register_agent_skill(path)

    # 创建工具组
    groups = [
        ("realme-repair-progress", "realme维修进度查询工具组"),
        ("find-service-center", "realme服务中心查询工具组"),
        ("realme-order-price-protection", "realme订单价保查询工具组"),
        ("realme-price-discount-query", "realme价格折扣查询工具组"),
        ("order-status-query", "订单物流状态查询工具组"),
        ("realme-product-authenticity-and-warranty-query", "realme产品真伪保障查询工具组"),
    ]
    for n, d in groups:
        config.toolkit.create_tool_group(n, d, active=False)

    # 注册所有工具
    config.toolkit.register_tool_function(check_login_status, group_name="realme-repair-progress")
    config.toolkit.register_tool_function(get_user_repair_orders, group_name="realme-repair-progress")
    config.toolkit.register_tool_function(get_repair_order_progress, group_name="realme-repair-progress")

    config.toolkit.register_tool_function(check_realme_login_status, group_name="realme-order-price-protection")
    config.toolkit.register_tool_function(get_realme_user_orders, group_name="realme-order-price-protection")
    config.toolkit.register_tool_function(get_realme_order_price_protection, group_name="realme-order-price-protection")

    config.toolkit.register_tool_function(query_product_discount, group_name="realme-price-discount-query")
    config.toolkit.register_tool_function(query_product_stock, group_name="realme-price-discount-query")

    config.toolkit.register_tool_function(order_check_login_status, group_name="order-status-query")
    config.toolkit.register_tool_function(query_order_info, group_name="order-status-query")
    config.toolkit.register_tool_function(query_logistics_info, group_name="order-status-query")
    config.toolkit.register_tool_function(cancel_order_query, group_name="order-status-query")

    config.toolkit.register_tool_function(check_imei_validity, group_name="realme-product-authenticity-and-warranty-query")
    config.toolkit.register_tool_function(query_e_warranty_card, group_name="realme-product-authenticity-and-warranty-query")
    config.toolkit.register_tool_function(query_product_insurance, group_name="realme-product-authenticity-and-warranty-query")
    config.toolkit.register_tool_function(is_iot_product, group_name="realme-product-authenticity-and-warranty-query")
    config.toolkit.register_tool_function(get_iot_authenticity_info, group_name="realme-product-authenticity-and-warranty-query")
    config.toolkit.register_tool_function(get_standard_product_model, group_name="realme-product-authenticity-and-warranty-query")

    config.toolkit.register_tool_function(view_text_file)

    # MCP客户端
    try:
        config.mcp_client = HttpStatelessClient(name="ServiceCenter", transport="streamable_http", url="http://127.0.0.1:8002/mcp")
        await config.toolkit.register_mcp_client(config.mcp_client, group_name="find-service-center")
    except Exception as e:
        print("MCP 跳过:", e)

    # 中间件
    config.toolkit.register_middleware(create_auto_activate_middleware(config.toolkit))

    # ====================== 智能体系统初始化（根据服务类型选择） ======================

    if service_type == "single":
        # 初始化单智能体系统
        config._global_agent = ReActAgent(
            name="Friday",
            sys_prompt = """
            你是名为 Friday 的智能助手。

            # 核心规则（强制执行，优先级最高）
            1. 【技能优先与执行原则】
            - 处理用户请求时，必须**首先匹配并加载对应的已装备技能（skill）**，通过 view_text_file 读取技能文档后，严格按照技能流程、话术、触发条件执行。
            - 必须完整遵循技能步骤，不得擅自修改流程、跳过节点、变更话术或自行新增逻辑。

            2. 【基础工具直接调用权限】
            - 以下一个基础工具**不受技能流程限制，可随时直接调用**：
                1. view_text_file
            - 适用场景：读取技能文件、查看文本内容。

            3. 【语言一致性规则】
            - 严格使用用户输入的语言回复：
                - 用户中文 → 中文回复
                - 用户英文 → 英文回复
            - 禁止多余解释、禁止无关说明、禁止自问自答。

            4. 【信息真实性与安全规则】
            - 所有输出、行为、判断必须完全来自已加载的技能，禁止编造信息、禁止主观假设、禁止 extrapolate。
            - 技能明确禁止触发的场景，必须拒绝执行相关操作。
            """,
            model=OpenAIChatModel(
                model_name=os.environ.get("DOUBAO_MODEL_NAME", "doubao-1-5-pro-32k-250115"),
                api_key=os.environ.get("DOUBAO_API_KEY", ""),
                stream=True,
                client_kwargs={"base_url": os.environ.get("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")},
            ),
            formatter=OpenAIChatFormatter(),
            memory=InMemoryMemory(),
            toolkit=config.toolkit,
            enable_meta_tool=True
        )
        print("[完成] 单智能体系统初始化完成")

        # 确保多智能体服务为 None，避免意外使用
        config._multi_agent_service = None

    elif service_type == "multi":
        # 初始化多智能体系统
        config._multi_agent_service = MultiAgentService()
        await config._multi_agent_service.initialize()
        print("[完成] 多智能体系统初始化完成")

        # 确保单智能体全局变量为 None，避免意外使用
        config._global_agent = None

    print(f"[完成] {service_type} 智能体系统启动完成")