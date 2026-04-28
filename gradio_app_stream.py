# -*- coding: utf-8 -*-
"""
Realme智能客服 - Gradio前端应用（流式输出版本）
支持历史对话加载和清理功能
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import gradio as gr
import requests
import json
import time
import uuid
from typing import Dict, List, Generator
from datetime import datetime

# 后端API配置
API_BASE_URL = "http://localhost:8001"

def create_thread_id() -> str:
    return f"thread_{int(time.time())}_{uuid.uuid4().hex[:8]}"

# ==============================
# API调用函数
# ==============================

def api_login(username: str, password: str) -> Dict:
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )
        return response.json() if response.status_code == 200 else {"success": False, "error": "登录失败"}
    except Exception as e:
        return {"success": False, "error": f"请求失败: {str(e)}"}

def api_register(username: str, password: str, email: str = "", phone: str = "") -> Dict:
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/auth/register",
            json={"username": username, "password": password, "email": email, "phone": phone},
            timeout=10
        )
        return response.json() if response.status_code == 200 else {"success": False, "error": "注册失败"}
    except Exception as e:
        return {"success": False, "error": f"请求失败: {str(e)}"}

def api_get_conversations(token: str) -> List[Dict]:
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.get(f"{API_BASE_URL}/api/conversations", headers=headers, timeout=10)
        return response.json() if response.status_code == 200 else []
    except:
        return []

def api_get_messages(token: str, conversation_id: int) -> List[Dict]:
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.get(
            f"{API_BASE_URL}/api/conversations/{conversation_id}/messages",
            headers=headers,
            timeout=10
        )
        return response.json() if response.status_code == 200 else []
    except:
        return []

def api_delete_conversation(token: str, conversation_id: int) -> bool:
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.delete(
            f"{API_BASE_URL}/api/conversations/{conversation_id}",
            headers=headers,
            timeout=10
        )
        return response.status_code == 200
    except:
        return False

def api_create_conversation(token: str, title: str = "新对话") -> Dict:
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.post(
            f"{API_BASE_URL}/api/conversations",
            headers=headers,
            json={"title": title},
            timeout=10
        )
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

def api_send_message_stream(message: str, thread_id: str, user_id: str = None) -> Generator[str, None, None]:
    """流式发送消息"""
    try:
        payload = {
            "messages": [{"role": "user", "content": message}],
            "stream": True,
            "thread": thread_id
        }
        # 如果有 user_id，添加到请求中
        if user_id:
            payload["user_id"] = user_id

        response = requests.post(
            f"{API_BASE_URL}/v1/chat/completions",
            json=payload,
            stream=True,
            timeout=60
        )

        if response.status_code != 200:
            yield f"请求失败: {response.status_code}"
            return

        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith('data: '):
                    data = decoded[6:]
                    if data == '[DONE]':
                        break
                    try:
                        json_data = json.loads(data)
                        content = json_data['choices'][0]['delta'].get('content', '')
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        yield f"请求失败: {str(e)}"

def api_clear_thread(thread_id: str) -> bool:
    try:
        response = requests.post(f"{API_BASE_URL}/clear", params={"thread": thread_id}, timeout=10)
        return response.status_code == 200
    except:
        return False

# ==============================
# 样式定义
# ==============================

css = """
footer {display: none !important;}
.gradio-container {max-width: 1400px !important; margin: auto !important;}

.sidebar-panel {
    background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    padding: 20px;
}

.sidebar-panel h1 {
    color: white;
    font-size: 1.5rem;
    margin-bottom: 20px;
    text-align: center;
}

.sidebar-panel .user-info {
    background: rgba(255,255,255,0.15);
    padding: 12px;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 15px;
}

.sidebar-panel input, .sidebar-panel textarea {
    background: rgba(255,255,255,0.9) !important;
    border-radius: 8px !important;
}

.sidebar-panel button.primary-btn {
    background: white !important;
    color: #667eea !important;
    font-weight: bold;
    border-radius: 8px;
    width: 100%;
    padding: 10px;
    margin-top: 10px;
}

.sidebar-panel button.secondary-btn {
    background: rgba(255,255,255,0.2) !important;
    color: white !important;
    border-radius: 8px;
    width: 100%;
    padding: 10px;
}

.chat-panel {
    background: #f8fafc;
    min-height: 100vh;
    padding: 20px;
}

.chatbot-box {
    background: white;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border: 1px solid #e2e8f0;
}

.input-area {
    background: white;
    border-radius: 12px;
    padding: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.input-area input {
    border: 2px solid #e2e8f0 !important;
    border-radius: 10px !important;
    font-size: 15px;
}

.input-area input:focus {
    border-color: #667eea !important;
}

.send-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border-radius: 10px !important;
    padding: 12px 24px !important;
    font-weight: bold;
}

.status-text {
    color: #64748b;
    font-size: 13px;
    padding: 5px 10px;
}

@media (max-width: 768px) {
    .sidebar-panel {min-height: auto; padding: 15px;}
    .chat-panel {min-height: auto;}
}
"""

# ==============================
# 创建应用
# ==============================

def create_app():
    with gr.Blocks(title="Realme智能客服 - 流式版") as app:
        # 状态管理
        user_token = gr.State(value="")
        username_state = gr.State(value="")
        user_id_state = gr.State(value="")  # 新增：存储用户ID
        thread_state = gr.State(value=create_thread_id())
        current_conv_id = gr.State(value=None)

        # 主布局
        with gr.Row(equal_height=True):
            # ===== 左侧边栏 =====
            with gr.Column(scale=1, min_width=280, elem_classes="sidebar-panel"):
                gr.Markdown("# 🤖 Realme智能客服")

                user_display = gr.Markdown("欢迎访问", elem_classes="user-info")

                with gr.Group(visible=True) as login_form:
                    with gr.Tabs():
                        with gr.TabItem("登录"):
                            login_user = gr.Textbox(label="用户名", placeholder="请输入用户名")
                            login_pass = gr.Textbox(label="密码", type="password", placeholder="请输入密码")
                            login_btn = gr.Button("登 录", variant="primary", elem_classes="primary-btn")
                            login_msg = gr.Markdown("")

                        with gr.TabItem("注册"):
                            reg_user = gr.Textbox(label="用户名", placeholder="3-50字符")
                            reg_pass = gr.Textbox(label="密码", type="password", placeholder="至少6位")
                            reg_email = gr.Textbox(label="邮箱", placeholder="可选")
                            reg_btn = gr.Button("注 册", variant="primary", elem_classes="primary-btn")
                            reg_msg = gr.Markdown("")

                    gr.Markdown("")
                    guest_btn = gr.Button("👤 访客模式", elem_classes="secondary-btn")

                with gr.Group(visible=False) as session_form:
                    new_chat_btn = gr.Button("✨ 新对话", variant="primary", elem_classes="primary-btn")
                    logout_btn = gr.Button("退出登录", elem_classes="secondary-btn")

                    gr.Markdown("### 📜 历史对话")
                    history_radio = gr.Radio(
                        choices=[],
                        label="点击选择历史对话",
                        show_label=False,
                        interactive=True
                    )

                    with gr.Row():
                        refresh_btn = gr.Button("🔄 刷新", size="sm", scale=1)
                        delete_btn = gr.Button("🗑️ 删除选中", size="sm", scale=1, variant="stop")

            # ===== 右侧聊天区域 =====
            with gr.Column(scale=4, elem_classes="chat-panel"):
                gr.Markdown("### 💬 对话窗口（流式输出）")

                chatbot = gr.Chatbot(
                    label="",
                    height=500,
                    show_label=False,
                    elem_classes="chatbot-box"
                )

                with gr.Row(elem_classes="input-area"):
                    msg_input = gr.Textbox(
                        placeholder="请输入您的问题... (Enter发送)",
                        show_label=False,
                        scale=9,
                        container=False
                    )
                    send_btn = gr.Button("发送 ➤", variant="primary", scale=1, elem_classes="send-btn")

                with gr.Row():
                    clear_btn = gr.Button("🧹 清空当前对话", size="sm")
                    status_msg = gr.Markdown("", elem_classes="status-text")

        # ==============================
        # 事件处理
        # ==============================

        def do_login(user, pwd, token, name, user_id):
            result = api_login(user, pwd)
            if result.get("success"):
                new_token = result.get("token", "")
                new_user_id = result.get("user_id", "")  # 获取用户ID
                conversations = api_get_conversations(new_token)
                choices = [f"{c['id']}: {c['title']}" for c in conversations]
                return (
                    new_token, user, new_user_id, create_thread_id(), None,
                    f"👤 **{user}**",
                    gr.update(visible=False), gr.update(visible=True),
                    [], "✅ 登录成功！",
                    gr.update(choices=choices, value=None)
                )
            return (
                token, name, user_id, create_thread_id(), None,
                "欢迎访问",
                gr.update(), gr.update(),
                [], f"❌ {result.get('error', '登录失败')}",
                gr.update(choices=[], value=None)
            )

        def do_register(user, pwd, email):
            if len(user) < 3:
                return "❌ 用户名至少3个字符"
            if len(pwd) < 6:
                return "❌ 密码至少6位"
            result = api_register(user, pwd, email)
            if result.get("success"):
                return "✅ 注册成功！请登录"
            return f"❌ {result.get('error', '注册失败')}"

        def do_guest(token, name, user_id):
            return (
                token, "访客", "", create_thread_id(), None,  # user_id为空表示访客
                "👤 **访客模式**",
                gr.update(visible=False), gr.update(visible=True),
                [], "✅ 已进入访客模式",
                gr.update(choices=[], value=None)
            )

        def do_logout():
            return (
                "", "", "", create_thread_id(), None,  # 清空user_id
                "欢迎访问",
                gr.update(visible=True), gr.update(visible=False),
                [], "已退出登录",
                gr.update(choices=[], value=None)
            )

        def do_new_chat(token):
            if token:
                conv = api_create_conversation(token, "新对话")
                if conv:
                    conversations = api_get_conversations(token)
                    choices = [f"{c['id']}: {c['title']}" for c in conversations]
                    return [], create_thread_id(), conv.get('id'), "✅ 新对话已创建", gr.update(choices=choices, value=None)
            return [], create_thread_id(), None, "✅ 新对话已创建", gr.update()

        def do_load_conversation(selected, token):
            if not selected or not token:
                return [], None, "请选择一个对话"
            try:
                conv_id = int(selected.split(":")[0])
            except:
                return [], None, "无效的对话ID"

            messages = api_get_messages(token, conv_id)
            if not messages:
                return [], conv_id, "该对话暂无消息"

            history = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    history.append({"role": "user", "content": content})
                elif role == "assistant":
                    history.append({"role": "assistant", "content": content})

            return history, conv_id, f"✅ 已加载对话 {conv_id}"

        def do_delete_conversation(selected, token):
            if not selected or not token:
                return gr.update(), "请选择要删除的对话"
            try:
                conv_id = int(selected.split(":")[0])
            except:
                return gr.update(), "无效的对话ID"

            if api_delete_conversation(token, conv_id):
                conversations = api_get_conversations(token)
                choices = [f"{c['id']}: {c['title']}" for c in conversations]
                return gr.update(choices=choices, value=None), f"✅ 对话 {conv_id} 已删除"
            return gr.update(), f"❌ 删除失败"

        def do_refresh_history(token):
            if not token:
                return gr.update(choices=[], value=None)
            conversations = api_get_conversations(token)
            choices = [f"{c['id']}: {c['title']}" for c in conversations]
            return gr.update(choices=choices, value=None)

        def do_send_stream(message, history, thread, token, conv_id, user_id):
            """流式发送消息"""
            if not message.strip():
                yield history, thread, conv_id, "⚠️ 请输入消息"
                return

            history = history + [{"role": "user", "content": message}]
            history = history + [{"role": "assistant", "content": ""}]

            yield history, thread, conv_id, "🤖 思考中..."

            full_response = ""
            # 传递user_id到API
            for chunk in api_send_message_stream(message, thread, user_id):
                full_response += chunk
                history[-1] = {"role": "assistant", "content": full_response}
                yield history, thread, conv_id, ""

            yield history, thread, conv_id, "✅ 完成"

        def do_clear_chat(thread):
            if api_clear_thread(thread):
                return [], "✅ 对话已清空"
            return [], "❌ 清空失败"

        # 绑定事件
        login_btn.click(
            fn=do_login,
            inputs=[login_user, login_pass, user_token, username_state, user_id_state],
            outputs=[user_token, username_state, user_id_state, thread_state, current_conv_id, user_display,
                     login_form, session_form, chatbot, status_msg, history_radio]
        )

        reg_btn.click(fn=do_register, inputs=[reg_user, reg_pass, reg_email], outputs=reg_msg)

        guest_btn.click(
            fn=do_guest,
            inputs=[user_token, username_state, user_id_state],
            outputs=[user_token, username_state, user_id_state, thread_state, current_conv_id, user_display,
                     login_form, session_form, chatbot, status_msg, history_radio]
        )

        logout_btn.click(
            fn=do_logout,
            outputs=[user_token, username_state, user_id_state, thread_state, current_conv_id, user_display,
                     login_form, session_form, chatbot, status_msg, history_radio]
        )

        new_chat_btn.click(
            fn=do_new_chat,
            inputs=[user_token],
            outputs=[chatbot, thread_state, current_conv_id, status_msg, history_radio]
        )

        history_radio.select(
            fn=do_load_conversation,
            inputs=[history_radio, user_token],
            outputs=[chatbot, current_conv_id, status_msg]
        )

        delete_btn.click(
            fn=do_delete_conversation,
            inputs=[history_radio, user_token],
            outputs=[history_radio, status_msg]
        )

        refresh_btn.click(
            fn=do_refresh_history,
            inputs=[user_token],
            outputs=history_radio
        )

        send_btn.click(
            fn=do_send_stream,
            inputs=[msg_input, chatbot, thread_state, user_token, current_conv_id, user_id_state],
            outputs=[chatbot, thread_state, current_conv_id, status_msg]
        ).then(lambda: "", outputs=msg_input)

        msg_input.submit(
            fn=do_send_stream,
            inputs=[msg_input, chatbot, thread_state, user_token, current_conv_id, user_id_state],
            outputs=[chatbot, thread_state, current_conv_id, status_msg]
        ).then(lambda: "", outputs=msg_input)

        clear_btn.click(
            fn=do_clear_chat,
            inputs=[thread_state],
            outputs=[chatbot, status_msg]
        )

    return app

if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False,
        show_error=True,
        theme=gr.themes.Soft(),
        css=css
    )
