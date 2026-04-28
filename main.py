# -*- coding: utf-8 -*-
"""
realme 智能客服系统 - 多智能体模式 (Orchestrator-Workers)
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import asyncio
import uuid
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

import jwt
from jose import JWTError
from passlib.context import CryptContext
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator

from core.agent_setup import init_agent_and_toolkit
from utils.stream_utils import multi_agent_stream_generator
from database.crud import UserCRUD, ConversationCRUD, MessageCRUD
import config



# =============================================================================
# 配置
# =============================================================================
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
security = HTTPBearer()


# =============================================================================
# Pydantic 模型
# =============================================================================
class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    real_name: Optional[str] = None

    @field_validator("email", "phone", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() == "":
            return None
        return v


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    real_name: Optional[str] = None
    created_at: str
    last_login: Optional[str] = None


class AuthResponse(BaseModel):
    success: bool
    user_id: Optional[int] = None
    username: Optional[str] = None
    token: Optional[str] = None
    error: Optional[str] = None


class ConversationCreateRequest(BaseModel):
    title: str = "新对话"


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    thread_id: str
    title: str
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    timestamp: str


class OpenAIChatMessage(BaseModel):
    role: str
    content: str


class OpenAIChatRequest(BaseModel):
    messages: List[OpenAIChatMessage]
    stream: bool = True
    model: str = "doubao-pro-1.5"
    thread: str = "default_thread"
    user_id: Optional[str] = None
    model_config = ConfigDict(extra="allow")


# =============================================================================
# 认证工具函数
# =============================================================================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
    except JWTError:
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证令牌")

    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌载荷")

    user = UserCRUD.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

    UserCRUD.update_user_last_login(user_id)
    return user


# =============================================================================
# 应用生命周期
# =============================================================================
async def cleanup_expired_agent_memories_task():
    """定时清理过期的多智能体记忆"""
    while True:
        await asyncio.sleep(config.CLEANUP_INTERVAL_MINUTES * 60)
        if config._multi_agent_service is not None:
            await config._multi_agent_service.cleanup_expired_memories()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_agent_and_toolkit()
    asyncio.create_task(cleanup_expired_agent_memories_task())
    yield
    print("[停止] 服务关闭")


app = FastAPI(lifespan=lifespan)


# =============================================================================
# 聊天 API
# =============================================================================
@app.post("/v1/chat/completions")
async def chat_completions(req: OpenAIChatRequest, thread: str = "default_thread"):
    """聊天接口 - 多智能体模式"""
    actual_thread = req.thread if req.thread != "default_thread" else thread
    print(f"[请求] thread={actual_thread}, messages={len(req.messages)}, stream={req.stream}")

    msg_dicts = [{"role": m.role, "content": m.content} for m in req.messages]
    last_content = msg_dicts[-1]["content"] if msg_dicts else ""

    if not req.stream:
        content = await config._multi_agent_service.process_request(last_content, actual_thread)
        return {"choices": [{"message": {"role": "assistant", "content": content}}]}

    return StreamingResponse(
            multi_agent_stream_generator(actual_thread, msg_dicts, req.user_id),
            media_type="text/event-stream"
        )


@app.post("/clear")
async def clear_history(thread: str = "default_thread"):
    """清空对话线程的记忆"""
    print(f"[清理] thread={thread}")
    if config._multi_agent_service is not None:
        await config._multi_agent_service.clear_thread_memory(thread)
    return {"status": "success", "msg": f"线程 {thread} 记忆已清空"}


# =============================================================================
# 用户认证 API
# =============================================================================
@app.post("/api/auth/register", response_model=AuthResponse)
async def register_user(user_data: UserRegisterRequest):
    """用户注册"""
    if UserCRUD.get_user_by_username(user_data.username):
        return AuthResponse(success=False, error=f"用户名 '{user_data.username}' 已存在")

    if user_data.email and UserCRUD.get_user_by_email(user_data.email):
        return AuthResponse(success=False, error=f"邮箱 '{user_data.email}' 已被注册")

    user_id = UserCRUD.create_user(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        email=user_data.email,
        phone=user_data.phone,
        real_name=user_data.real_name
    )

    if user_id is None:
        return AuthResponse(success=False, error="用户创建失败，请稍后重试")

    return AuthResponse(
        success=True,
        user_id=user_id,
        username=user_data.username,
        token=create_access_token(data={"user_id": user_id})
    )


@app.post("/api/auth/login", response_model=AuthResponse)
async def login_user(user_data: UserLoginRequest):
    """用户登录"""
    user = UserCRUD.get_user_by_username(user_data.username)
    if user is None or not verify_password(user_data.password, user["password_hash"]):
        return AuthResponse(success=False, error="用户名或密码错误")

    if not user.get("is_active", True):
        return AuthResponse(success=False, error="用户账户已被禁用")

    UserCRUD.update_user_last_login(user["id"])
    return AuthResponse(
        success=True,
        user_id=user["id"],
        username=user["username"],
        token=create_access_token(data={"user_id": user["id"]})
    )


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


# =============================================================================
# 会话管理 API
# =============================================================================
@app.get("/api/conversations", response_model=List[ConversationResponse])
async def get_user_conversations(current_user: Dict[str, Any] = Depends(get_current_user)):
    """获取用户的对话列表"""
    return ConversationCRUD.get_user_conversations(current_user["id"])


@app.post("/api/conversations", response_model=ConversationResponse)
async def create_conversation(
    conv_data: ConversationCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """创建新对话"""
    thread_id = f"thread_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    conv_id = ConversationCRUD.create_conversation(
        user_id=current_user["id"],
        thread_id=thread_id,
        title=conv_data.title
    )

    if conv_id is None:
        raise HTTPException(status_code=500, detail="创建对话失败")

    conversation = ConversationCRUD.get_conversation_by_thread_id(thread_id)
    if conversation is None:
        raise HTTPException(status_code=500, detail="获取对话信息失败")

    return conversation


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """删除对话"""
    conversation = ConversationCRUD.get_conversation_by_id(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="对话不存在")
    if conversation["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="无权删除此对话")

    if not ConversationCRUD.delete_conversation(conversation_id):
        raise HTTPException(status_code=500, detail="删除对话失败")

    return {"success": True, "message": "对话已删除"}


@app.get("/api/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """获取对话的消息列表"""
    conversation = ConversationCRUD.get_conversation_by_id(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="对话不存在")
    if conversation["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="无权访问此对话")

    return MessageCRUD.get_conversation_messages(conversation_id)


# =============================================================================
# 健康检查 API
# =============================================================================
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
