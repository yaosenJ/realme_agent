# 🤖 realme 智能客服系统

基于 AgentScope 框架的智能客服系统，支持 **单智能体+技能架构** 和 **多智能体架构** 两种模式，为 realme 用户提供全方位的售后服务支持。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![AgentScope](https://img.shields.io/badge/AgentScope-1.0.18-green.svg)](https://github.com/alibaba/AgentScope)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135.3-teal.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 目录

- [项目背景](#-项目背景)
- [架构设计](#-架构设计)
- [功能模块](#-功能模块)
- [技术亮点](#-技术亮点)
- [项目结构](#-项目结构)
- [快速开始](#-快速开始)
- [API接口](#-api接口)
- [技能开发](#-技能开发)
- [依赖说明](#-依赖说明)

## 🎯 项目背景

随着智能客服需求的增长，传统系统难以应对复杂的多领域问题。本项目提供两种架构模式：

| 模式 | 描述 | 适用场景 |
|------|------|----------|
| 🎯 **单智能体 + 技能架构** | 一个智能体通过动态加载技能模块处理不同业务场景 | 标准化、流程化的业务 |
| 🔄 **多智能体架构** | 调度智能体动态创建专业 Worker，适合复杂问题的自动拆解和并行处理 | 复杂多领域问题 |

## 🏗️ 架构设计

### 模式一：单智能体 + 技能架构 (Agent + Skills)

```
┌─────────────────────────────────────────────────────────────┐
│                      Single Agent (Friday)                  │
│  职责：识别意图 → 加载技能 → 执行技能流程 → 返回结果            │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │   view_text_file  │
                    │   读取技能文档     │
                    └─────────┬─────────┘
                              │
    ┌─────────────┬───────────┼───────────┬─────────────┐
    ▼             ▼           ▼           ▼             ▼
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│🔧维修进度│  │📍服务网点│  │⚡充电器  │  │💰订单价保│  │✅产品真伪│
│SKILL.md│  │SKILL.md│  │SKILL.md│  │SKILL.md│  │SKILL.md│
└────────┘  └────────┘  └────────┘  └────────┘  └────────┘
```

**✨ 特点：**
- 📝 技能与智能体解耦，通过 `SKILL.md` 定义业务流程
- 🔄 智能体运行时动态读取技能文档
- 📐 统一的技能定义格式，便于维护和扩展

### 模式二：多智能体架构 (Orchestrator-Workers)

```
        ┌─────────────────────────────────────────────────────────────┐
        │                    🎭 Orchestrator Agent                    │
        │  职责：分析用户问题 → 拆解任务 → 动态创建Worker → 汇总结果      │
        └─────────────────────────────────────────────────────────────┘
                                    │
                        ┌─────────┴─────────┐
                        │   🔧 Tool Calls   │
                        │  (动态创建Worker)  │
                        └─────────┬─────────┘
                                  │
┌────────┬────────┬────────┬──────┴──────┬────────┬────────┬────────┐
▼        ▼        ▼        ▼             ▼        ▼        ▼        ▼
┌──────┐┌──────┐┌──────┐┌──────┐  ┌──────┐┌──────┐┌──────┐┌──────┐
│🔧Repair││📍Service││⚡Charger││💰Price ││📦Order ││🏷️Discount││✅Authenticity│
│ Worker││ Worker││ Worker││Protect││Status ││ Worker││ Worker││
│(维修)  ││(网点)  ││(充电器)││(价保)  ││(物流)  ││(折扣)  ││(真伪)  │
└──────┘└──────┘└──────┘└──────┘  └──────┘└──────┘└──────┘└──────┘
```

**✨ 特点：**
- 🎭 Orchestrator 智能调度，Worker 专业处理
- 🔧 支持多 Worker 并行调用
- ⚡ 适合复杂多领域问题

### 📊 两种模式对比

| 特性 | 🎯 单智能体+技能 | 🔄 多智能体 |
|------|------------------|-------------|
| 入口文件 | `main_agent_skill.py` | `main.py` |
| 架构复杂度 | 简单 | 较高 |
| 技能定义 | SKILL.md 文件 | Worker 系统提示词 |
| 扩展方式 | 新增技能目录 | 新增 Worker 创建函数 |
| 适用场景 | 标准化流程业务 | 复杂多领域问题 |
| 并行处理 | ❌ 不支持 | ✅ 支持 |

## 🌟 功能模块

| 模块 | 图标 | 功能描述 |
|------|------|----------|
| 维修进度查询 | 🔧 | 查询维修订单状态、预计完成时间 |
| 服务网点查询 | 📍 | 查询服务网点地址、电话、营业时间 |
| 预约维修 | 📅 | 创建到店维修预约 |
| 充电器推荐 | ⚡ | 根据机型推荐适配充电器 |
| 订单价保 | 💰 | 查询订单价保信息、降价补差 |
| 订单物流 | 📦 | 查询订单状态、物流信息 |
| 价格折扣 | 🏷️ | 查询产品价格、优惠活动 |
| 产品真伪 | ✅ | IMEI 真伪验证、保修查询 |

## 💡 技术亮点

### 1. 🔄 双架构支持
- **单智能体+技能架构**：轻量级、易维护
- **多智能体架构**：复杂问题拆解、并行处理

### 2. 🧠 基于 AgentScope 框架
- 使用 ReActAgent 实现推理-行动循环
- 内置工具调用和记忆管理
- 流式输出支持

### 3. 📝 技能系统 (Skills)
- 🧩 可插拔的技能模块，通过 `SKILL.md` 定义业务流程和话术
- 🔄 智能体运行时动态读取技能文档
- 📐 标准化的技能定义格式（YAML Front Matter + Markdown）
- 💬 支持多轮对话流程控制

### 4. 🔌 MCP (Model Context Protocol) 集成
- 支持外部 MCP 服务扩展
- 实现服务网点查询的 MCP 服务端

### 5. 🧵 线程隔离记忆管理
- 每个会话线程拥有独立的记忆空间
- 自动清理过期记忆
- 支持 SQLite 持久化存储

### 6. 🌊 流式响应
- 支持 SSE (Server-Sent Events) 流式输出
- 增量文本推送，提升用户体验

## 📁 项目结构

```
realme_agent/
├── 📁 core/                          # 核心模块
│   ├── 📄 agent_setup.py             # 智能体初始化
│   ├── 📄 multi_agent_service.py     # 多智能体服务
│   ├── 📄 memory_manager.py          # 记忆管理
│   └── 📄 middleware.py              # 中间件
├── 📁 tools/                         # 工具函数
│   ├── 📄 repair.py                  # 维修相关工具
│   ├── 📄 price_protect.py           # 价保相关工具
│   ├── 📄 authenticity.py            # 真伪查询工具
│   ├── 📄 logistics.py               # 物流查询工具
│   └── 📄 discount.py                # 折扣查询工具
├── 📁 skills/                        # 技能模块
│   ├── 📁 realme-repair-progress/    # 维修进度查询技能
│   ├── 📁 find-service-center/       # 服务网点查询技能
│   ├── 📁 realme-charger-advisor/    # 充电器推荐技能
│   ├── 📁 realme-order-price-protection/  # 价保查询技能
│   ├── 📁 order-status-query/        # 物流查询技能
│   ├── 📁 realme-price-discount-query/    # 折扣查询技能
│   └── 📁 realme-product-authenticity-and-warranty-query/  # 真伪查询技能
├── 📁 database/                      # 数据库模块
│   ├── 📄 db.py                      # 数据库连接
│   ├── 📄 crud.py                    # CRUD 操作
│   └── 📄 migrations.py              # 数据库迁移
├── 📁 utils/                         # 工具模块
│   └── 📄 stream_utils.py            # 流式响应工具
├── 📁 test/                          # 测试文件
├── 📄 main.py                        # 多智能体模式入口
├── 📄 main_agent_skill.py            # 单智能体模式入口
├── 📄 gradio_app.py                  # Gradio 演示界面（多智能体）
├── 📄 gradio_app_stream.py           # Gradio 演示界面（流式）
├── 📄 config.py                      # 配置文件
├── 📄 .env                           # 环境变量
└── 📄 requirements.txt               # 依赖列表
```

## 🚀 快速开始

### 1. 📋 环境要求
- Python 3.10+
- pip

### 2. 📦 安装依赖

```bash
pip install -r requirements.txt
```

### 3. ⚙️ 配置环境变量

创建 `.env` 文件：

```env
# 模型配置
DOUBAO_API_KEY=your_api_key
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_MODEL_NAME=doubao-1-5-pro-32k-250115

# 可选：DashScope API Key
DASHSCOPE_API_KEY=your_dashscope_key
```

### 4. 🏃 启动服务

**🎯 单智能体+技能模式：**
```bash
python main_agent_skill.py
```

**🔄 多智能体模式：**
```bash
python main.py
```

**🖥️ Gradio 演示界面：**
```bash
python gradio_app.py          # 多智能体模式
python gradio_app_stream.py   # 流式响应模式
```

## 📡 API 接口

启动后访问 `http://localhost:8000`

| 接口 | 方法 | 描述 |
|------|------|------|
| `/register` | POST | 用户注册 |
| `/login` | POST | 用户登录 |
| `/chat` | POST | 对话接口 |
| `/chat/stream` | POST | 流式对话接口 |
| `/conversations` | GET | 获取会话列表 |

## 🛠️ 技能开发

### 技能目录结构
```
skill-name/
├── 📄 SKILL.md          # 技能定义文件（必需）
├── 📄 data.json         # 数据文件（可选）
└── 📄 mcp_server.py     # MCP 服务端（可选）
```

### SKILL.md 格式

技能文件采用 YAML Front Matter + Markdown 格式：

```markdown
---
name: skill-name
description: 技能描述，用于意图匹配
---

# 技能标题

## 技能概述
技能的整体功能说明

## 依赖工具
本技能需要调用的工具列表及说明

## 执行流程
### 1. 触发判断
触发条件和意图识别规则

### 2. 步骤一
具体执行步骤和话术

### 3. 步骤二
...

## 标准输出格式（必须严格使用）
结果输出模板

## 异常与兜底处理
各种异常情况的处理方式

## 执行约束
必须遵守的规则
```

### 技能加载流程

1. 🎯 智能体识别用户意图
2. 📄 通过 `view_text_file` 读取匹配的 `SKILL.md`
3. ⚙️ 按照技能定义的流程执行
4. 🔧 调用依赖工具获取数据
5. 📤 按标准格式输出结果

## 📚 依赖说明

| 依赖 | 用途 |
|------|------|
| 🤖 agentscope | 多智能体框架 |
| ⚡ fastapi | Web 框架 |
| 🔥 uvicorn | ASGI 服务器 |
| 🖥️ gradio | 演示界面 |
| 🗄️ sqlalchemy | ORM 框架 |
| 🔐 python-jose | JWT 认证 |
| 🔒 passlib | 密码加密 |
| 🌐 httpx | HTTP 客户端 |
| ⚙️ python-dotenv | 环境变量管理 |

## 📄 许可证

[MIT License](LICENSE)

---

<p align="center">
  Made with ❤️ for realme Customer Service
</p>
