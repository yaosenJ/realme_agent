import argparse
import requests
import json


def parse_args():
    parser = argparse.ArgumentParser(description='Realme智能客服HTTP非流式测试客户端')
    parser.add_argument('--port', type=int, default=8001, help='服务端口（默认：8001）')
    parser.add_argument('--service-type', choices=['single', 'multi'], default='multi',
                       help='服务类型：single-单智能体，multi-多智能体（默认）')
    parser.add_argument('--host', default='localhost', help='服务主机（默认：localhost）')
    parser.add_argument('--thread', default='test_thread', help='线程ID（默认：test_thread）')
    parser.add_argument('--memory', default='', help='长期记忆内容（可选）')
    return parser.parse_args()


def chat_loop(args):
    host = args.host
    port = args.port
    thread_id = args.thread
    memory = args.memory

    print(f"✅ 交互式对话已启动（非流式，服务类型：{args.service_type}，端口：{port}，线程：{thread_id}）")
    if memory:
        print(f"📝 长期记忆：{memory[:50]}..." if len(memory) > 50 else f"📝 长期记忆：{memory}")
    print("输入 'clear' 清空当前对话，输入 'exit' 退出\n")

    # 多轮对话历史
    messages = []

    while True:
        user_input = input("你：")

        # 退出
        if user_input.lower() == "exit":
            print("👋 再见！")
            break

        # 清空当前用户线程对话历史
        if user_input.lower() == "clear":
            requests.post(f"http://{host}:{port}/clear?thread={thread_id}")
            messages = []
            print(f"🧹 线程 {thread_id} 对话已清空\n")
            continue

        # 加入用户消息
        messages.append({"role": "user", "content": user_input})

        # 构建请求体
        request_body = {
            "model": "glm-5",
            "messages": messages,
            "stream": False,  # 非流式
            "thread": thread_id
        }
        if memory:
            request_body["memory"] = memory

        # 发送非流式请求
        print("助手：", end="", flush=True)
        response = requests.post(
            f"http://{host}:{port}/v1/chat/completions",
            json=request_body
        )

        # 解析响应
        try:
            result = response.json()
            if "choices" in result and result["choices"]:
                answer = result["choices"][0].get("message", {}).get("content", "")
                print(answer)

                # 把助手回答加入历史
                messages.append({"role": "assistant", "content": answer})
            else:
                print(f"❌ 响应格式错误: {result}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析错误: {e}")
            print(f"原始响应: {response.text}")

        print()


if __name__ == "__main__":
    args = parse_args()
    chat_loop(args)
