# 🤖 realme Intelligent Customer Service System

An intelligent customer service system based on the AgentScope framework, supporting **Single Agent + Skills** and **Multi-Agent** architectures, providing comprehensive after-sales service support for realme users.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![AgentScope](https://img.shields.io/badge/AgentScope-1.0.18-green.svg)](https://github.com/alibaba/AgentScope)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135.3-teal.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Table of Contents

- [Background](#-background)
- [Architecture Design](#-architecture-design)
- [Features](#-features)
- [Tech Highlights](#-tech-highlights)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [API Reference](#-api-reference)
- [Skill Development](#-skill-development)
- [Dependencies](#-dependencies)

## 🎯 Background

With the growing demand for intelligent customer service, traditional systems struggle to handle complex multi-domain problems. This project provides two architectural modes:

| Mode | Description | Use Case |
|------|-------------|----------|
| 🎯 **Single Agent + Skills** | One agent dynamically loads skill modules to handle different business scenarios | Standardized, process-oriented businesses |
| 🔄 **Multi-Agent (Orchestrator-Workers)** | Orchestrator agent dynamically creates specialized Workers | Complex multi-domain problems |

## 🏗️ Architecture Design

### Mode 1: Single Agent + Skills

```
┌─────────────────────────────────────────────────────────────┐
│                      Single Agent (Friday)                  │
│  Role: Intent Recognition → Load Skill → Execute → Result   │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │   view_text_file  │
                    │   Read Skill Docs │
                    └─────────┬─────────┘
                              │
    ┌─────────────┬───────────┼───────────┬─────────────┐
    ▼             ▼           ▼           ▼             ▼
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│Repair  │  │Service │  │Charger │  │Price   │  │Product │
│SKILL.md│  │SKILL.md│  │SKILL.md│  │SKILL.md│  │SKILL.md│
└────────┘  └────────┘  └────────┘  └────────┘  └────────┘
```

**✨ Features:**
- 📝 Skills decoupled from agent, defined via `SKILL.md`
- 🔄 Dynamic skill loading at runtime
- 📐 Standardized skill definition format

### Mode 2: Multi-Agent (Orchestrator-Workers)

```
        ┌─────────────────────────────────────────────────────────────┐
        │                    🎭 Orchestrator Agent                    │
        │  Role: Analyze → Decompose → Create Workers → Aggregate    │
        └─────────────────────────────────────────────────────────────┘
                                    │
                        ┌─────────┴─────────┐
                        │   🔧 Tool Calls   │
                        │ (Dynamic Workers) │
                        └─────────┬─────────┘
                                  │
┌────────┬────────┬────────┬──────┴──────┬────────┬────────┬────────┐
▼        ▼        ▼        ▼             ▼        ▼        ▼        ▼
┌──────┐┌──────┐┌──────┐┌──────┐  ┌──────┐┌──────┐┌──────┐┌──────┐
│🔧Repair││📍Service││⚡Charger││💰Price ││📦Order ││🏷️Discount││✅Authenticity│
│ Worker││ Worker││ Worker││Protect││Status ││ Worker││ Worker││
└──────┘└──────┘└──────┘└──────┘  └──────┘└──────┘└──────┘└──────┘
```

**✨ Features:**
- 🎭 Orchestrator for intelligent scheduling
- 🔧 Specialized Workers for domain-specific tasks
- ⚡ Parallel Worker invocation support

### 📊 Mode Comparison

| Feature | 🎯 Single Agent + Skills | 🔄 Multi-Agent |
|---------|-------------------------|----------------|
| Entry File | `main_agent_skill.py` | `main.py` |
| Complexity | Simple | Higher |
| Skill Definition | SKILL.md files | Worker system prompts |
| Extension Method | Add skill directory | Add Worker function |
| Use Case | Standardized processes | Complex multi-domain |
| Parallel Processing | ❌ | ✅ |

## 🌟 Features

| Module | Icon | Description |
|--------|------|-------------|
| Repair Progress | 🔧 | Query repair order status, estimated completion time |
| Service Centers | 📍 | Find service center locations, hours, contact info |
| Appointments | 📅 | Create in-store repair appointments |
| Charger Advisor | ⚡ | Recommend compatible chargers by device model |
| Price Protection | 💰 | Query price protection info, price difference refund |
| Order Tracking | 📦 | Query order status, logistics information |
| Discounts | 🏷️ | Query product prices, promotions, gifts |
| Authenticity | ✅ | IMEI verification, warranty status query |

## 💡 Tech Highlights

### 1. 🔄 Dual Architecture Support
- **Single Agent + Skills**: Lightweight, easy to maintain
- **Multi-Agent**: Complex problem decomposition, parallel processing

### 2. 🧠 Based on AgentScope Framework
- ReActAgent for reasoning-action loop
- Built-in tool calling and memory management
- Streaming output support

### 3. 📝 Skill System
- 🧩 Pluggable skill modules via `SKILL.md`
- 🔄 Runtime dynamic skill loading
- 📐 Standardized skill definition (YAML Front Matter + Markdown)
- 💬 Multi-turn conversation flow control

### 4. 🔌 MCP (Model Context Protocol) Integration
- External MCP service extension support
- MCP server implementation for service center queries

### 5. 🧵 Thread-Isolated Memory Management
- Independent memory space per conversation thread
- Automatic expired memory cleanup
- SQLite persistent storage support

### 6. 🌊 Streaming Response
- SSE (Server-Sent Events) streaming output
- Incremental text push for better UX

## 📁 Project Structure

```
realme_agent/
├── 📁 core/                          # Core modules
│   ├── 📄 agent_setup.py             # Agent initialization
│   ├── 📄 multi_agent_service.py     # Multi-agent service
│   ├── 📄 memory_manager.py          # Memory management
│   └── 📄 middleware.py              # Middleware
├── 📁 tools/                         # Tool functions
│   ├── 📄 repair.py                  # Repair tools
│   ├── 📄 price_protect.py           # Price protection tools
│   ├── 📄 authenticity.py            # Authenticity query tools
│   ├── 📄 logistics.py               # Logistics tools
│   └── 📄 discount.py                # Discount query tools
├── 📁 skills/                        # Skill modules
│   ├── 📁 realme-repair-progress/    # Repair progress skill
│   ├── 📁 find-service-center/       # Service center skill
│   ├── 📁 realme-charger-advisor/    # Charger advisor skill
│   ├── 📁 realme-order-price-protection/  # Price protection skill
│   ├── 📁 order-status-query/        # Order status skill
│   ├── 📁 realme-price-discount-query/    # Discount query skill
│   └── 📁 realme-product-authenticity-and-warranty-query/  # Authenticity skill
├── 📁 database/                      # Database modules
│   ├── 📄 db.py                      # Database connection
│   ├── 📄 crud.py                    # CRUD operations
│   └── 📄 migrations.py              # Migrations
├── 📁 utils/                         # Utilities
│   └── 📄 stream_utils.py            # Streaming utilities
├── 📁 test/                          # Test files
├── 📄 main.py                        # Multi-agent entry point
├── 📄 main_agent_skill.py            # Single agent entry point
├── 📄 gradio_app.py                  # Gradio demo (multi-agent)
├── 📄 gradio_app_stream.py           # Gradio demo (streaming)
├── 📄 config.py                      # Configuration
├── 📄 .env                           # Environment variables
└── 📄 requirements.txt               # Dependencies
```

## 🚀 Quick Start

### 1. 📋 Prerequisites
- Python 3.10+
- pip

### 2. 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. ⚙️ Configure Environment Variables

Create a `.env` file:

```env
# Model Configuration
DOUBAO_API_KEY=your_api_key
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_MODEL_NAME=doubao-1-5-pro-32k-250115

# Optional: DashScope API Key
DASHSCOPE_API_KEY=your_dashscope_key
```

### 4. 🏃 Start Service

**🎯 Single Agent + Skills Mode:**
```bash
python main_agent_skill.py
```

**🔄 Multi-Agent Mode:**
```bash
python main.py
```

**🖥️ Gradio Demo Interface:**
```bash
python gradio_app.py          # Multi-agent mode
python gradio_app_stream.py   # Streaming mode
```

## 📡 API Reference

After starting, access `http://localhost:8000`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/register` | POST | User registration |
| `/login` | POST | User login |
| `/chat` | POST | Chat interface |
| `/chat/stream` | POST | Streaming chat interface |
| `/conversations` | GET | Get conversation list |

## 🛠️ Skill Development

### Skill Directory Structure
```
skill-name/
├── 📄 SKILL.md          # Skill definition (required)
├── 📄 data.json         # Data file (optional)
└── 📄 mcp_server.py     # MCP server (optional)
```

### SKILL.md Format

Skill files use YAML Front Matter + Markdown format:

```markdown
---
name: skill-name
description: Skill description for intent matching
---

# Skill Title

## Overview
Overall functionality description

## Dependencies
Required tools and their descriptions

## Execution Flow
### 1. Trigger Detection
Trigger conditions and intent recognition rules

### 2. Step One
Specific execution steps and scripts

### 3. Step Two
...

## Standard Output Format (Must Follow Strictly)
Result output template

## Exception Handling
Handling of various exception scenarios

## Execution Constraints
Rules that must be followed
```

### Skill Loading Process

1. 🎯 Agent recognizes user intent
2. 📄 Read matching `SKILL.md` via `view_text_file`
3. ⚙️ Execute according to skill-defined flow
4. 🔧 Call dependency tools to fetch data
5. 📤 Output results in standard format

## 📚 Dependencies

| Dependency | Purpose |
|------------|---------|
| 🤖 agentscope | Multi-agent framework |
| ⚡ fastapi | Web framework |
| 🔥 uvicorn | ASGI server |
| 🖥️ gradio | Demo interface |
| 🗄️ sqlalchemy | ORM framework |
| 🔐 python-jose | JWT authentication |
| 🔒 passlib | Password encryption |
| 🌐 httpx | HTTP client |
| ⚙️ python-dotenv | Environment variable management |

## 📄 License

[MIT License](LICENSE)

---

<p align="center">
  Made with ❤️ for realme Customer Service
</p>
