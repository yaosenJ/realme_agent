import argparse
import requests
from openai import OpenAI


def parse_args():
    parser = argparse.ArgumentParser(description='Realme智能客服OpenAI非流式测试客户端')
    parser.add_argument('--port', type=int, default=8001, help='服务端口（默认：8001）')
    parser.add_argument('--service-type', choices=['single', 'multi'], default='multi',
                       help='服务类型：single-单智能体，multi-多智能体（默认）')
    parser.add_argument('--host', default='localhost', help='服务主机（默认：localhost）')
    parser.add_argument('--thread', default='test_thread', help='线程ID（默认：test_thread）')
    parser.add_argument('--memory', default='', help='长期记忆内容（可选）')
    return parser.parse_args()


def chat_loop(args):
    # 构建base_url
    base_url = f"http://{args.host}:{args.port}/v1"
    thread_id = args.thread
    memory = args.memory

    # 初始化客户端
    client = OpenAI(
        base_url=base_url,
        api_key="dummy-key"
    )

    print(f"✅ 交互式对话已启动（非流式，服务类型：{args.service_type}，端口：{args.port}，线程：{thread_id}）")
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
            requests.post(f"http://{args.host}:{args.port}/clear?thread={thread_id}")
            messages = []
            print(f"🧹 线程 {thread_id} 对话已清空\n")
            continue

        # 加入用户消息
        messages.append({"role": "user", "content": user_input})

        # 构建 extra_body
        extra_body = {"thread": thread_id}
        if memory:
            extra_body["memory"] = memory

        # 发送非流式请求
        print("助手：", end="", flush=True)
        response = client.chat.completions.create(
            model="glm-5",
            messages=messages,
            stream=False,  # 非流式
            extra_body=extra_body
        )

        # 获取回答
        answer = response.choices[0].message.content
        print(answer)

        # 把助手回答加入历史
        messages.append({"role": "assistant", "content": answer})
        print()


if __name__ == "__main__":
    args = parse_args()
    chat_loop(args)
