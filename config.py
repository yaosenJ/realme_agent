# -*- coding: utf-8 -*-
import os
from datetime import datetime

# ====================== 全局路径配置 ======================
BASE_DIR = r"D:\code\realme_agent"
SKILLS_DIR = os.path.join(BASE_DIR, "skills")


ORDER_DATA_FILE = os.path.join(SKILLS_DIR, "realme-repair-progress", "repair_orders_100.json")
PROGRESS_DATA_FILE = os.path.join(SKILLS_DIR, "realme-repair-progress", "repair_progress_100.json")
CHAT_LOG_FILE = os.path.join(BASE_DIR, "chat_history03.jsonl")


# ====================== 数据库配置 ======================
DATABASE_URL = os.path.join(BASE_DIR, "realme_customer_service.db")


USE_DATABASE = True  # 是否使用SQLite数据库，False时使用JSON文件和内存数据
USE_SQLALCHEMY = False  # 是否使用SQLAlchemy ORM，False时使用原生sqlite3

# ====================== 认证和会话配置 ======================
SECRET_KEY = "realme_customer_service_secret_key_change_in_production"  # JWT密钥，生产环境需要更改
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ====================== 多线程记忆配置 ======================
MEMORY_EXPIRE_MINUTES = 30
CLEANUP_INTERVAL_MINUTES = 5

# ====================== 用户数据配置 ======================
TEST_USER_COUNT = 10  # 测试用户数量，扩展至10个用户
USE_REAL_DATABASE = False  # 是否使用真实数据库，False时使用模拟数据（向后兼容）

# ====================== 全局对象占位 ======================
_global_agent = None
_multi_agent_service = None  # 多智能体服务实例
toolkit = None
mcp_client = None