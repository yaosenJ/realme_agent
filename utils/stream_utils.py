# -*- coding: utf-8 -*-
import json
from datetime import datetime
from agentscope.message import Msg
from agentscope.pipeline import stream_printing_messages
from core.memory_manager import get_or_create_thread_memory
import config


async def openai_stream_generator(thread_id: str, messages: list):
    """单智能体流式响应生成器"""
    thread_memory = await get_or_create_thread_memory(thread_id)
    config._global_agent.memory = thread_memory

    # 最后一条消息作为当前输入
    last_content = messages[-1]["content"] if messages else ""
    last_role = messages[-1]["role"] if messages else "user"
    user_msg = Msg(name=last_role, role=last_role, content=last_content)
    full_text = ""

    async for msg, is_last in stream_printing_messages(
        agents=[config._global_agent],
        coroutine_task=config._global_agent(user_msg)
    ):
        if not isinstance(msg.content, list):
            continue
        current_text = ""
        for block in msg.content:
            if block.get("type") == "text":
                current_text += block.get("text", "")
        if len(current_text) > len(full_text):
            new_text = current_text[len(full_text):]
            full_text = current_text
            chunk = json.dumps({
                "id": "chatcmpl-realme",
                "object": "chat.completion.chunk",
                "created": int(datetime.now().timestamp()),
                "model": "doubao-pro-1.5",
                "choices": [{"delta": {"content": new_text}, "index": 0, "finish_reason": None}]
            }, ensure_ascii=False)
            yield f"data: {chunk}\n\n"
    yield "data: [DONE]\n\n"


async def multi_agent_stream_generator(thread_id: str, messages: list, user_id: str = None):
    """多智能体流式响应生成器"""

    # 最后一条消息作为当前输入
    last_content = messages[-1]["content"] if messages else ""

    # 使用多智能体服务流式响应
    async for chunk in config._multi_agent_service.stream_response(last_content, thread_id):
        if chunk:
            chunk_data = json.dumps({
                "id": "chatcmpl-realme-multi",
                "object": "chat.completion.chunk",
                "created": int(datetime.now().timestamp()),
                "model": "doubao-pro-1.5",
                "choices": [{"delta": {"content": chunk}, "index": 0, "finish_reason": None}]
            }, ensure_ascii=False)
            yield f"data: {chunk_data}\n\n"

    yield "data: [DONE]\n\n"