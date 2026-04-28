# -*- coding: utf-8 -*-
"""
对话内存管理 - 为单智能体提供线程隔离记忆，定时清理过期记忆
"""
import asyncio
from datetime import datetime
from agentscope.memory import InMemoryMemory
import config


# 单智能体的线程记忆（保留用于 openai_stream_generator）
_thread_memories: dict = {}
_thread_last_active: dict = {}


async def get_or_create_thread_memory(thread_id: str) -> InMemoryMemory:
    """获取或创建线程的内存实例（用于单智能体）"""
    _thread_last_active[thread_id] = datetime.now()
    if thread_id not in _thread_memories:
        _thread_memories[thread_id] = InMemoryMemory()
    memory = _thread_memories[thread_id]
    # 确保 memory 有 metadata 属性
    if not hasattr(memory, 'metadata') or not isinstance(memory.metadata, dict):
        memory.metadata = {}
    memory.metadata["thread_id"] = thread_id
    return memory


async def clear_thread_memory(thread_id: str):
    """清空指定线程的记忆（用于单智能体）"""
    if thread_id in _thread_memories:
        await _thread_memories[thread_id].clear()
        del _thread_memories[thread_id]
    _thread_last_active.pop(thread_id, None)
    print(f"🧹 已清空线程 {thread_id} 的记忆")


async def cleanup_inactive_threads_task():
    """定时清理过期记忆的任务"""
    while True:
        await asyncio.sleep(config.CLEANUP_INTERVAL_MINUTES * 60)
        now = datetime.now()

        # 清理单智能体的过期记忆
        expired = [
            tid for tid, t in _thread_last_active.items()
            if (now - t).total_seconds() / 60 >= config.MEMORY_EXPIRE_MINUTES
        ]
        for tid in expired:
            memory = _thread_memories.get(tid)
            if memory:
                await memory.clear()
            _thread_memories.pop(tid, None)
            _thread_last_active.pop(tid, None)

        if expired:
            print(f"🧹 清理过期线程: {len(expired)}")
