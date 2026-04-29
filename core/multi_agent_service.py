# -*- coding: utf-8 -*-
"""
多智能体服务 - Orchestrator-Workers 模式

架构说明：
        ┌─────────────────────────────────────────────────────────────┐
        │                      Orchestrator Agent                     │
        │  职责：分析用户问题 → 拆解任务 → 动态创建Worker → 汇总结果      │
        └─────────────────────────────────────────────────────────────┘
                                    │
                        ┌─────────┴─────────┐
                        │   Tool Calls      │
                        │  (动态创建Worker)  │
                        └─────────┬─────────┘
                            │
        ┌──────────┬──────────┬───┴───┬──────────┬──────────┬──────────┐
        ▼          ▼          ▼       ▼          ▼          ▼          ▼
    ┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
    │Repair  ││Service ││Charger ││Price   ││Order   ││Discount││Authent-│
    │Worker  ││Worker  ││Worker  ││Protect ││Status  ││Worker  ││icity   │
    │(维修)  ││(网点)  ││(充电器)││Worker  ││Worker  ││(折扣)  ││Worker  │
    │        ││        ││        ││(价保)  ││(物流)  ││        ││(真伪)  │
    └────────┘└────────┘└────────┘└────────┘└────────┘└────────┘└────────┘
        │          │          │          │          │          │          │
        └──────────┴──────────┴──────────┼──────────┴──────────┴──────────┘
                                ▼
                        ┌─────────────────┐
                        │   结果回传给     │
                        │  Orchestrator   │
                        └─────────────────┘
"""
import asyncio
import re
import os
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime
from typing import Dict, Optional
from agentscope.agent import ReActAgent
from agentscope.message import Msg
from agentscope.pipeline import stream_printing_messages
from agentscope.model import OpenAIChatModel
from agentscope.formatter import OpenAIChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit, view_text_file
from agentscope.tool._response import ToolResponse

# 环境变量
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
DOUBAO_API_KEY = os.environ.get("DOUBAO_API_KEY", "")
DOUBAO_BASE_URL = os.environ.get("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
DOUBAO_MODEL_NAME = os.environ.get("DOUBAO_MODEL_NAME", "doubao-1-5-pro-32k-250115")

# 智能体内存过期时间（分钟）
AGENT_MEMORY_EXPIRE_MINUTES = 30


# ==============================================================================
# Worker 创建工具函数
# ==============================================================================

async def create_repair_progress_worker(task_description: str) -> ToolResponse:
    """创建维修进度查询Worker智能体，处理维修订单进度相关问题。

    Args:
        task_description (str): 具体的任务描述，包含用户信息和需求。
    """
    toolkit = Toolkit()

    # 注册维修相关工具
    from tools.repair import check_login_status, get_user_repair_orders, get_repair_order_progress
    toolkit.register_tool_function(check_login_status)
    toolkit.register_tool_function(get_user_repair_orders)
    toolkit.register_tool_function(get_repair_order_progress)

    worker = ReActAgent(
        name="RepairProgressWorker",
        sys_prompt="""你是realme维修进度查询专家。

        ## 核心职责
        - 查询用户维修订单进度
        - 查询维修状态、预计完成时间

        ## 依赖工具（必须按顺序调用）
        1. `check_login_status`：校验用户是否登录
        2. `get_user_repair_orders`：获取当前账号下所有维修订单
        3. `get_repair_order_progress`：根据订单号查询详细维修进度

        ## 执行流程
        1. 触发后立即调用 `check_login_status` 校验登录状态。
        2. 未登录：直接回复“对不起，您未登录账号，无法为您查询，请登录后重试。”并结束流程。
        3. 已登录：询问“您好，请问是否使用当前登录账号查询维修进度？”
        4. 用户确认后调用 `get_user_repair_orders` 获取订单列表。
        5. 无订单：回复“您当前账号下暂无维修订单，可前往realme服务支持查看。”并结束流程。
        6. 有订单：展示订单号与状态，让用户指定要查询的订单号。
        7. 用户明确订单号后，调用 `get_repair_order_progress` 获取详细进度。
        8. 按标准格式返回结果。

        ## 标准输出格式（必须严格遵守）
        【维修进度查询结果】
        订单号：{order_id}
        设备型号：{device_model}
        当前状态：{status}
        最新进度：{latest_progress}
        预计完成时间：{expected_time}

        ## 异常与兜底处理
        1. 用户取消查询：
        回复“已取消本次维修进度查询，您可以随时重新发起。”并终止流程。

        2. 用户输入不明确：
        回复“请您确认要查询的维修订单号，或直接说‘查询维修进度’重新发起操作。”

        3. 无法识别意图：
        回复“很抱歉，我暂时无法理解您的需求，您可以直接说‘查询维修进度’再次尝试。”

        4. 工具调用异常：
        回复“当前查询服务暂时异常，请稍后重试或联系realme客服。”

        ## 执行约束
        1. 严格按照“登录校验 → 订单列表 → 进度查询”顺序执行。
        2. 未登录状态禁止调用任何订单相关工具。
        3. 必须在用户明确指定订单号后才可查询进度。
        4. 所有信息必须来自工具返回，严禁编造。
        5. 输出格式不可修改、不可省略关键字段。
        6. 保持客服友好语气，不暴露后台逻辑与技术细节。
        """,
        model=OpenAIChatModel(
            model_name=DOUBAO_MODEL_NAME,
            api_key=DOUBAO_API_KEY,
            stream=False,
            client_kwargs={"base_url": DOUBAO_BASE_URL},
        ),
        formatter=OpenAIChatFormatter(),
        memory=InMemoryMemory(),
        toolkit=toolkit,
    )

    print(f"🔧 [创建Worker] RepairProgressWorker")
    print(f"📝 [任务描述] {task_description}...")

    res = await worker(Msg("user", task_description, "user"))
    return ToolResponse(content=res.get_content_blocks("text"))


async def create_service_center_worker(task_description: str) -> ToolResponse:
    """创建服务网点查询Worker智能体，处理服务网点查询和预约相关问题。

    Args:
        task_description (str): 具体的任务描述，包含用户信息和需求。
    """
    toolkit = Toolkit()

    # 尝试注册MCP工具
    try:
        from agentscope.mcp._http_stateless_client import HttpStatelessClient
        mcp_client = HttpStatelessClient(
            name="ServiceCenter",
            transport="streamable_http",
            url="http://127.0.0.1:8002/mcp"
        )
        await toolkit.register_mcp_client(mcp_client)
    except Exception as e:
        print(f"⚠️ MCP服务未启动: {e}")

    worker = ReActAgent(
        name="ServiceCenterWorker",
        sys_prompt="""你是realme服务网点查询与预约专家。

            ## 可用工具
            你拥有两个MCP工具：
            1. `get_service_centers`：查询指定城市/区域的服务网点列表
            2. `create_instore_appointment`：创建到店维修预约

            ## 标准执行流程
            ### 流程1：用户查询服务网点
            1. 先判断用户是否提供了城市信息
            2. 未提供城市 → 直接使用固定话术引导用户
            3. 已提供城市 → 调用 `get_service_centers` 工具获取网点
            4. 按固定格式返回网点名称、地址、电话、营业时间

            ### 流程2：用户预约到店维修
            1. 先调用 `get_service_centers` 展示可预约网点列表
            2. 依次收集用户信息：姓名、手机号、预约时间、目标网点ID
            3. 信息收集完整后 → 调用 `create_instore_appointment` 工具
            4. 返回预约单号与成功提示信息

            ## 固定话术模板（必须严格使用）
            1. 未提供城市时：
            您好，请告诉我您所在的城市，我帮您查询就近服务网点~

            2. 网点查询结果：
            为您查询到附近服务网点：
            1. 【{name}】
            地址：{address}
            电话：{phone}
            营业时间：{business_hours}

            3. 预约成功后：
            已为您成功预约：
            预约单号：{appointment_id}
            请按时到店并携带购机凭证。

            ## 工作要求
            1. 回答必须简洁、专业、符合官方客服语气
            2. 严格按照流程执行，不擅自扩展功能
            3. 禁止处理职责范围外的问题
            4. 工具调用必须遵循规则，不滥用工具
""",
        model=OpenAIChatModel(
            model_name=DOUBAO_MODEL_NAME,
            api_key=DOUBAO_API_KEY,
            stream=False,
            client_kwargs={"base_url": DOUBAO_BASE_URL},
        ),
        formatter=OpenAIChatFormatter(),
        memory=InMemoryMemory(),
        toolkit=toolkit,
    )

    print(f"🔧 [创建Worker] ServiceCenterWorker")
    print(f"📝 [任务描述] {task_description}...")

    res = await worker(Msg("user", task_description, "user"))
    return ToolResponse(content=res.get_content_blocks("text"))


async def create_charger_advisor_worker(task_description: str) -> ToolResponse:
    """创建充电器推荐Worker智能体，处理充电器购买咨询相关问题。

    Args:
        task_description (str): 具体的任务描述，包含用户信息和需求。
    """
    toolkit = Toolkit()

    # 注册文件读取工具
    toolkit.register_tool_function(view_text_file)

    # 使用相对路径获取技能目录
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    _skills_dir = os.path.join(_current_dir, "..", "skills")
    toolkit.register_agent_skill(os.path.join(_skills_dir, "realme-charger-advisor"))

    worker = ReActAgent(
        name="ChargerAdvisorWorker",
        sys_prompt="""你是realme充电器购买咨询专家。

        # ⚠️ 首先检查输入信息（优先级最高）
        在执行任何步骤前，先检查用户输入中是否已包含：
        - 用户信息：姓名、手机号、邮箱
        - 用户机型
        - 用户已确认的事项

        如果用户输入中已包含这些信息，**直接使用，不要重复询问**！

        # 核心规则
        1. 【技能优先与执行原则】
        - 处理用户请求时，通过 view_text_file 读取技能文档后执行。
        - 但如果用户输入已包含所需信息，可以跳过信息收集步骤。

        2. 【语言一致性规则】
        - 严格使用用户输入的语言回复
        - 禁止多余解释、禁止无关说明

        3. 【信息真实性】
        - 所有输出必须完全来自已加载的技能
        """,
        model=OpenAIChatModel(
            model_name=DOUBAO_MODEL_NAME,
            api_key=DOUBAO_API_KEY,
            stream=False,
            client_kwargs={"base_url": DOUBAO_BASE_URL},
        ),
        formatter=OpenAIChatFormatter(),
        memory=InMemoryMemory(),
        toolkit=toolkit,
    )

    print(f"🔧 [创建Worker] ChargerAdvisorWorker")
    print(f"📝 [任务描述] {task_description}...")

    res = await worker(Msg("user", task_description, "user"))
    return ToolResponse(content=res.get_content_blocks("text"))


async def create_price_protection_worker(task_description: str) -> ToolResponse:
    """创建订单价保查询Worker智能体，处理订单价保相关问题。

    Args:
        task_description (str): 具体的任务描述，包含用户信息和需求。
    """
    toolkit = Toolkit()

    # 注册价保相关工具
    from tools.price_protect import check_realme_login_status, get_realme_user_orders, get_realme_order_price_protection
    toolkit.register_tool_function(check_realme_login_status)
    toolkit.register_tool_function(get_realme_user_orders)
    toolkit.register_tool_function(get_realme_order_price_protection)

    worker = ReActAgent(
        name="PriceProtectionWorker",
        sys_prompt="""你是realme订单价保查询专家。

        ## 核心职责
        - 查询订单价保信息
        - 处理降价补差、保价相关问题

        ## 执行流程（必须严格按顺序执行）
        1. 调用 `check_realme_login_status` 校验用户是否登录realme账号。
        2. 未登录：使用未登录标准话术，结束流程。
        3. 已登录：引导用户确认是否使用当前账号查询。
        4. 用户取消或未确认：使用取消话术，结束流程。
        5. 用户确认：调用 `get_realme_user_orders` 获取该账号下订单列表。
        6. 无订单：使用无订单话术，结束流程。
        7. 有订单：引导用户选择需要查询价保的订单。
        8. 用户选定订单后：调用 `get_realme_order_price_protection` 查询价保信息。
        9. 按统一价保卡片格式输出结果。

        ## 标准回复话术
        - 未登录：
        对不起，您未登录 realme 账号，无法为您查询订单价保信息，请先登录账号。
        - 确认账号引导：
        您好，您如果咨询的是当前 realme 账号订单价保，请点击确认~
        - 取消/未确认：
        您已取消订单价保信息查询，若有其他问题可随时咨询小真喔~
        - 无订单：
        很抱歉，暂未查询到您当前 realme 账号下的订单信息。
        - 选择订单引导：
        您好，请点击您想查询价保的 realme 订单。
        - 系统异常兜底：
        很抱歉，价保查询服务暂时繁忙，请您稍后再试。

        ## 工具调用规则
        仅按顺序使用以下3个工具，不可乱序、不可省略：
        1. `check_realme_login_status`：校验登录状态
        2. `get_realme_user_orders`：获取用户订单列表
        3. `get_realme_order_price_protection`：根据订单号查询价保信息

        ## 价保卡片输出格式（必须严格使用）
        价保查询结果
        订单号：{order_id}
        商品名称：{product_name}
        购买价格：{original_price}
        当前价格：{current_price}
        可价保金额：{protect_amount}
        价保截止时间：{protect_deadline}
        价保状态：{status}

        ## 异常与边界处理
        - 订单不属于当前用户：提示权限不足，结束流程。
        - 订单不支持价保：明确提示该订单无可申请价保。
        - 价保已过期：告知价保已失效并展示过期时间。
        - 接口查询失败：使用系统异常兜底话术。
        - 所有信息必须来自工具返回，不得编造。
        """,
        model=OpenAIChatModel(
            model_name=DOUBAO_MODEL_NAME,
            api_key=DOUBAO_API_KEY,
            stream=False,
            client_kwargs={"base_url": DOUBAO_BASE_URL},
        ),
        formatter=OpenAIChatFormatter(),
        memory=InMemoryMemory(),
        toolkit=toolkit,
    )

    print(f"🔧 [创建Worker] PriceProtectionWorker")
    print(f"📝 [任务描述] {task_description}...")

    res = await worker(Msg("user", task_description, "user"))
    return ToolResponse(content=res.get_content_blocks("text"))


async def create_order_status_worker(task_description: str) -> ToolResponse:
    """创建订单物流查询Worker智能体，处理订单状态和物流查询相关问题。

    Args:
        task_description (str): 具体的任务描述，包含用户信息和需求。
    """
    toolkit = Toolkit()

    # 注册物流相关工具
    from tools.logistics import order_check_login_status, query_order_info, query_logistics_info,cancel_order_query
    toolkit.register_tool_function(order_check_login_status)
    toolkit.register_tool_function(query_order_info)
    toolkit.register_tool_function(query_logistics_info)
    toolkit.register_tool_function(cancel_order_query)

    worker = ReActAgent(
        name="OrderStatusWorker",
        sys_prompt="""你是realme订单物流查询专家。

    ## 核心职责
    - 查询订单状态
    - 查询物流信息

    ## 首先检查输入信息（重要！）
    在执行任何步骤前，先检查用户输入中是否已包含以下信息：
    - 用户登录状态/账号信息
    - 用户已确认的事项（如”已确认使用当前账号查询”）
    - 用户已提供的信息

    如果用户输入中已包含这些信息，**直接跳过对应步骤**，不要重复询问！

    ### 示例
    - 若用户输入包含”用户登录了user_2账号” → 跳过登录检查，直接认为已登录
    - 若用户输入包含”确认使用当前账号查询” → 跳过确认步骤，直接查询订单

    ## 执行步骤（根据上下文灵活调整）
    1. **检查登录**：若输入未提及登录状态，调用 `order_check_login_status`；若已提及登录账号，直接使用该账号。
    2. **确认查询**：若输入未提及用户确认，询问是否查询当前账号订单；若用户已确认，跳过此步。
    3. **查询订单**：调用 `query_order_info` 获取订单列表。
    4. **展示结果**：展示订单列表，或告知无订单。
    5. **查询物流**：若用户指定订单，调用 `query_logistics_info` 查询物流。

    ## 订单状态
    包括：未发货、已发货、运输中、派送中、已签收、已取消。

    ## 注意事项
    - 优先使用用户输入中已有的信息，避免重复询问
    - 无物流的订单需明确提示，不可报错
    - 工具调用异常时统一回复：”系统繁忙，请稍后再试”
    - 语气友好通俗，避免专业术语
""",
        model=OpenAIChatModel(
            model_name=DOUBAO_MODEL_NAME,
            api_key=DOUBAO_API_KEY,
            stream=False,
            client_kwargs={"base_url": DOUBAO_BASE_URL},
        ),
        formatter=OpenAIChatFormatter(),
        memory=InMemoryMemory(),
        toolkit=toolkit,
    )

    print(f"🔧 [创建Worker] OrderStatusWorker")
    print(f"📝 [任务描述] {task_description}...")

    res = await worker(Msg("user", task_description, "user"))
    return ToolResponse(content=res.get_content_blocks("text"))


async def create_discount_query_worker(task_description: str) -> ToolResponse:
    """创建价格折扣查询Worker智能体，处理产品价格、折扣相关问题。

    Args:
        task_description (str): 具体的任务描述，包含用户信息和需求。
    """
    toolkit = Toolkit()

    # 注册折扣相关工具
    from tools.discount import query_product_discount, query_product_stock
    toolkit.register_tool_function(query_product_discount)
    toolkit.register_tool_function(query_product_stock)

    worker = ReActAgent(
        name="DiscountQueryWorker",
        sys_prompt="""你是realme价格折扣查询专家。

    ## 核心职责
    - 查询产品价格、折扣信息
    - 查询产品库存

    ## 执行流程（必须严格按顺序）
    1. 先判断用户是否已说明产品类型
    2. 未说明 → 引导：您好，请问您想要咨询优惠信息的产品是手机吗
    3. 已说明 → 进入产品分类判断

    ### 产品分类处理
    - 手机 → 继续询问型号：请问您想咨询哪款型号的优惠信息？
    - 平板/其他realme产品 → 使用平板优惠话术回复
    - 友商/非realme产品 → 使用友商引导话术回复

    ### 型号处理流程
    1. 收集用户提供的型号
    2. 若为友商型号 → 友商引导话术
    3. 若为realme型号且有库存 → 调用 `query_product_discount` 查询优惠信息
    4. 若型号下架/缺货/无结果 → 使用缺货话术回复

    ### 查询结果展示
    - 查询成功 → 按折扣卡片格式输出价格、折扣、赠品、活动
    - 查询失败 → 缺货话术兜底

    ### 结尾
    回复后可追加相关猜你想问引导，不暴露后台逻辑。

    ## 标准话术（必须严格使用）
    - 型号收集：请问您想咨询哪款型号的优惠信息？
    - 友商引导：您好，您可以咨询我真我产品的优惠信息
    - 缺货/下架：您好，您咨询型号似乎已下架或缺货，请点击通知我，库存恢复后我们会第一时间通知您
    - 平板优惠：您好，小真为您找到了以下信息：1、软件商店"最新活动"：您可以打开"软件商店"APP，在首页查看最新的优惠活动；2、线下门店活动：您可以前往就近的 realme 线下授权门店咨询专属优惠

    ## 折扣卡片输出格式
    【{model} 最新优惠】
    原价：¥{original_price}
    活动价：¥{discount_price}
    折扣：{discount_rate}
    赠品：{gift}
    活动说明：{activity}

    ## 工具使用规则
    1. `query_product_discount`：根据型号查询价格、折扣、赠品、活动，仅对有效realme型号调用
    2. `query_product_stock`：辅助判断库存，缺货则走缺货话术
    3. 工具调用失败统一使用缺货话术兜底

    ## 异常处理
    - 用户未提供型号：最多重复引导2次，仍不提供则引导咨询全系列优惠
    - 咨询友商产品：只回复友商引导话术，不提供任何信息
    - 非价格类需求：告知仅处理价格/折扣/赠品咨询，可引导转人工
    - 所有信息必须来自工具返回，不得编造
    - 回复语气友好简洁，全程中文，不暴露工具调用、流程判断等后台内容
""",
        model=OpenAIChatModel(
            model_name=DOUBAO_MODEL_NAME,
            api_key=DOUBAO_API_KEY,
            stream=False,
            client_kwargs={"base_url": DOUBAO_BASE_URL},
        ),
        formatter=OpenAIChatFormatter(),
        memory=InMemoryMemory(),
        toolkit=toolkit,
    )

    print(f"🔧 [创建Worker] DiscountQueryWorker")
    print(f"📝 [任务描述] {task_description}...")

    res = await worker(Msg("user", task_description, "user"))
    return ToolResponse(content=res.get_content_blocks("text"))


async def create_authenticity_query_worker(task_description: str) -> ToolResponse:
    """创建产品真伪查询Worker智能体，处理产品真伪、保修查询相关问题。

    Args:
        task_description (str): 具体的任务描述，包含用户信息和需求。
    """
    toolkit = Toolkit()

    # 注册真伪查询相关工具
    from tools.authenticity import check_imei_validity, query_e_warranty_card, query_product_insurance,is_iot_product,get_iot_authenticity_info,get_standard_product_model
    toolkit.register_tool_function(check_imei_validity)
    toolkit.register_tool_function(query_e_warranty_card)
    toolkit.register_tool_function(query_product_insurance)
    toolkit.register_tool_function(is_iot_product)
    toolkit.register_tool_function(get_iot_authenticity_info)
    toolkit.register_tool_function(get_standard_product_model)

    worker = ReActAgent(
        name="AuthenticityQueryWorker",
        sys_prompt="""你是realme产品真伪与保修查询专家。

    ## 业务流程（必须严格执行）
    1. 用户发起真伪/保修/保险相关查询
    2. 主动询问：请问您想查询哪款真我产品？
    3. 根据产品名称分流：
    - 手机类 → 进入IMEI收集流程
    - IoT及周边 → 直接返回通用真伪说明
    4. 收集IMEI并调用 `check_imei_validity` 校验格式：
    - 格式无效 → 提示重新输入
    - 格式有效 → 调用 `query_e_warranty_card` 查询电子保卡
    5. 根据保卡结果处理：
    - 无保卡记录 → 判定为非正品或未激活设备
    - 有保卡记录 → 展示设备信息请用户确认
    6. 用户确认设备后 → 调用 `query_product_insurance` 查询保险
    7. 综合输出：真伪状态、保修信息、保险信息
    8. 用户否认设备信息 → 重新收集IMEI并重试

    ## 支持产品范围
    - 手机类：realme全系列手机机型
    - IoT类：耳机、智能手表、平板、笔记本、手环、充电器、移动电源、数据线等

    ## 标准话术与输出格式
    ### 手机查询结果格式
    设备型号：{device_model}
    激活时间：{activate_time}
    保修截止：{warranty_expire}
    真伪状态：{authenticity_status}

    ### IoT产品真伪说明
    realme {product}真伪说明：
    1. 官方授权渠道购买均为正品；
    2. 可享受全国官方联保服务；
    3. 如有疑虑可前往realme官方服务中心检测。

    ### IMEI格式错误
    IMEI格式无效，请输入15‑16位数字。

    ### 无保险信息
    该设备暂无增值保障服务。

    ### 无保卡记录
    未查询到该设备的电子保卡信息，可能为非正品或未激活设备。

    ## 依赖工具（必须按流程调用）
    1. check_imei_validity：校验IMEI格式是否合法
    2. query_e_warranty_card：查询电子保卡与真伪信息
    3. query_product_insurance：查询碎屏险、延保等增值保险
    4. is_iot_product：判断是否为IoT产品
    5. get_iot_authenticity_info：获取IoT产品通用真伪说明
    6. get_standard_product_model：标准化产品型号

    ## 异常与容错策略
    - IMEI为空、过短、含非数字 → 提示格式错误并重试
    - 无保卡记录 → 提示非正品或未激活
    - 用户否认设备信息 → 重新收集IMEI
    - 产品名称模糊 → 引导明确具体型号
    - 无保险信息 → 友好提示暂无增值保障
    - 工具调用异常 → 提示服务繁忙请稍后重试

    ## 约束与注意事项
    1. 严格保护IMEI等隐私信息，不存储、不泄露、不滥用
    2. 语气专业友好，遵循realme官方服务规范
    3. IoT产品不使用IMEI，直接输出官方说明
    4. 支持多轮重试，不轻易中断流程
    5. 非官方渠道产品需明确提示保修风险
    6. 所有信息必须来自工具返回，不得编造
""",
        model=OpenAIChatModel(
            model_name=DOUBAO_MODEL_NAME,
            api_key=DOUBAO_API_KEY,
            stream=False,
            client_kwargs={"base_url": DOUBAO_BASE_URL},
        ),
        formatter=OpenAIChatFormatter(),
        memory=InMemoryMemory(),
        toolkit=toolkit,
    )

    print(f"🔧 [创建Worker] AuthenticityQueryWorker")
    print(f"📝 [任务描述] {task_description}...")

    res = await worker(Msg("user", task_description, "user"))
    return ToolResponse(content=res.get_content_blocks("text"))


# ==============================================================================
# Orchestrator-Workers 多智能体服务
# ==============================================================================

class MultiAgentService:
    """多智能体服务 - Orchestrator-Workers 模式

    架构特点：
    1. Orchestrator 负责任务拆解和分发
    2. 通过工具调用动态创建专业 Worker
    3. Worker 独立完成任务并返回结果（无状态）
    4. Orchestrator 汇总结果给用户
    """

    def __init__(self):
        self.orchestrator = None
        # Orchestrator 的线程隔离记忆
        self.orchestrator_memories: Dict[str, InMemoryMemory] = {}
        self.memory_last_active: Dict[str, datetime] = {}

    async def initialize(self):
        """初始化 Orchestrator 智能体"""
        # 创建工具包，注册所有 Worker 创建函数
        toolkit = Toolkit()
        toolkit.register_tool_function(create_repair_progress_worker)
        toolkit.register_tool_function(create_service_center_worker)
        toolkit.register_tool_function(create_charger_advisor_worker)
        toolkit.register_tool_function(create_price_protection_worker)
        toolkit.register_tool_function(create_order_status_worker)
        toolkit.register_tool_function(create_discount_query_worker)
        toolkit.register_tool_function(create_authenticity_query_worker)

        # 初始化 Orchestrator
        self.orchestrator = ReActAgent(
            name="Orchestrator",
            sys_prompt="""你是realme智能客服系统的总调度（Orchestrator）。

            ## 核心职责
            1. 分析用户问题，判断需要哪些专业支持
            2. 通过工具调用动态创建专业 Worker 来处理子任务
            3. 汇总各 Worker 的结果，给用户最终回复

            ## 可用的 Worker 工具

            | 工具名称 | 适用场景 |
            |---------|---------|
            | create_repair_progress_worker | 维修进度、维修状态、售后进度 |
            | create_service_center_worker | 服务网点、预约维修、门店地址 |
            | create_charger_advisor_worker | 充电器推荐、充电功率、充电器兼容性 |
            | create_price_protection_worker | 价保、降价补差、保价 |
            | create_order_status_worker | 订单状态、物流信息、快递查询 |
            | create_discount_query_worker | 价格、折扣、优惠、赠品、活动 |
            | create_authenticity_query_worker | 产品真伪、保修查询、保险查询 |

            ## 工作流程

            ## 工作流程

            ### 单一问题
            用户问题只涉及一个领域时：
            1. 识别问题类型
            2. 调用对应的 Worker 创建工具
            3. 将用户问题直接传入 task_description
            4. 返回 Worker 的结果

            ### 复杂问题（多领域）
            用户问题涉及多个领域时：
            1. 分析问题，拆解为多个子任务
            2. 并行调用多个 Worker 创建工具
            3. 汇总各 Worker 结果
            4. 整合后统一回复用户


            ## 输出规范
            - 等所有 Worker 返回结果后，再统一回复用户
            - 使用友好专业的客服语气
            - 不暴露内部架构和 Agent 名称

            ## 汇总规则
            1. **保留原意**：Worker 返回什么就转达什么
            2. **区分状态**：已完成的结果直接展示，待确认的问题保持提问形式
            3. **合并同类**：多个 Worker 询问信息时合并询问
            4. **禁止**：不要把"询问"改成"陈述"
            """,
            model=OpenAIChatModel(
                model_name=DOUBAO_MODEL_NAME,
                api_key=DOUBAO_API_KEY,
                stream=True,
                client_kwargs={"base_url": DOUBAO_BASE_URL},
                generate_kwargs={"parallel_tool_calls": True},
            ),
            formatter=OpenAIChatFormatter(),
            memory=InMemoryMemory(),
            toolkit=toolkit,
            parallel_tool_calls=True,
        )
        print("✅ MultiAgentService (Orchestrator-Workers模式) 初始化完成")

    async def process_request(self, user_input: str, thread_id: str = "default", memory: str = "") -> str:
        """
        处理用户请求

        Args:
            user_input: 用户输入
            thread_id: 线程ID
            memory: 检索回来的长期记忆

        Returns:
            响应文本
        """
        # 为 Orchestrator 设置线程隔离的 memory
        self.orchestrator.memory = self._get_orchestrator_memory(thread_id)

        print(f"\n{'='*60}")
        print(f"👤 [用户输入] {user_input}")
        print(f"{'='*60}")

        # 如果有长期记忆，先添加到短期记忆中（参考 agentscope 的处理方式）
        if memory:
            retrieved_msg = Msg(
                name="long_term_memory",
                content=f"<long_term_memory>以下是从长期记忆中检索到的内容，可能有帮助：\n{memory}</long_term_memory>",
                role="user",
            )
            await self.orchestrator.memory.add(retrieved_msg)

        # Orchestrator 直接处理用户问题
        response = await self.orchestrator(Msg("user", user_input, "user"))
        print("助手回复：", response)
        result = self._extract_text(response.content)

        return result

    async def stream_response(self, user_input: str, thread_id: str = "default_thread", memory: str = ""):
        """
        流式响应生成器

        Args:
            user_input: 用户输入
            thread_id: 线程ID
            memory: 检索回来的长期记忆

        Yields:
            响应文本块
        """
        # 为 Orchestrator 设置线程隔离的 memory
        self.orchestrator.memory = self._get_orchestrator_memory(thread_id)

        print(f"\n{'='*60}")
        print(f"👤 [用户输入] {user_input}")
        print(f"{'='*60}")

        # 如果有长期记忆，先添加到短期记忆中（参考 agentscope 的处理方式）
        if memory:
            retrieved_msg = Msg(
                name="long_term_memory",
                content=f"<long_term_memory>以下是从长期记忆中检索到的内容，可能有帮助：\n{memory}</long_term_memory>",
                role="user",
            )
            await self.orchestrator.memory.add(retrieved_msg)

        # 流式输出
        full_text = ""
        async for msg, last in stream_printing_messages(
            agents=[self.orchestrator],
            coroutine_task=self.orchestrator(Msg("user", user_input, "user")),
        ):
            now_text = self._extract_text(msg.content)

            # 只输出增量
            if now_text.startswith(full_text):
                delta = now_text[len(full_text):]
                if delta:
                    yield delta
            full_text = now_text

    # ==============================
    # 辅助方法
    # ==============================

    def _extract_text(self, content) -> str:
        """提取文本内容"""
        if isinstance(content, list):
            return "".join([c.get("text", "") for c in content if c.get("type") == "text"])
        return str(content)

    def _get_orchestrator_memory(self, thread_id: str) -> InMemoryMemory:
        """获取指定线程的 Orchestrator 记忆"""
        self.memory_last_active[thread_id] = datetime.now()

        if thread_id not in self.orchestrator_memories:
            self.orchestrator_memories[thread_id] = InMemoryMemory()

        return self.orchestrator_memories[thread_id]

    async def cleanup_expired_memories(self):
        """清理过期的记忆"""
        now = datetime.now()
        expired_threads = [
            thread_id for thread_id, last_active in self.memory_last_active.items()
            if (now - last_active).total_seconds() / 60 >= AGENT_MEMORY_EXPIRE_MINUTES
        ]

        for thread_id in expired_threads:
            if thread_id in self.orchestrator_memories:
                await self.orchestrator_memories[thread_id].clear()
                del self.orchestrator_memories[thread_id]
            self.memory_last_active.pop(thread_id, None)

        if expired_threads:
            print(f"🧹 清理过期记忆: {len(expired_threads)} 个线程")

    async def clear_thread_memory(self, thread_id: str):
        """清空指定线程的记忆"""
        if thread_id in self.orchestrator_memories:
            await self.orchestrator_memories[thread_id].clear()
            del self.orchestrator_memories[thread_id]
        self.memory_last_active.pop(thread_id, None)
        print(f"🧹 已清空线程 {thread_id} 的记忆")

    async def clear_all_memories(self):
        """清空所有线程的记忆"""
        print(f"🧹 清空所有记忆，共 {len(self.orchestrator_memories)} 个线程")

        for memory in self.orchestrator_memories.values():
            await memory.clear()
        self.orchestrator_memories.clear()
        self.memory_last_active.clear()
        print(f"   已清空所有记忆")


# ==============================================================================
# 演示入口
# ==============================================================================

async def demo_handoff():
    """演示 Orchestrator-Workers 模式"""
    service = MultiAgentService()
    await service.initialize()

    # 复杂用户问题（涉及多个领域）
    # customer_issue = "帮我我推荐手机充电器和查询附近网点。"

    # 记忆测试
    customer_issue = "你知道我是谁吗？"
    memory_content = "我叫张三"

    response = await service.process_request(user_input=customer_issue, memory=memory_content)
    print(f"\n💬 助手: {response}")


if __name__ == "__main__":
    asyncio.run(demo_handoff())





