import argparse
import sys
from openai import OpenAI

def parse_args():
    parser = argparse.ArgumentParser(description='Realme智能客服测试客户端')
    parser.add_argument('--port', type=int, default=8001, help='服务端口（默认：8001）')
    parser.add_argument('--service-type', choices=['single', 'multi'], default='multi',
                       help='服务类型：single-单智能体，multi-多智能体（默认）')
    parser.add_argument('--host', default='localhost', help='服务主机（默认：localhost）')
    parser.add_argument('--thread', default='123456', help='线程ID（默认：123456）')
    return parser.parse_args()

def chat_loop(args):
    # 构建base_url
    base_url = f"http://{args.host}:{args.port}/v1"
    thread_id = args.thread

    # 初始化客户端
    client = OpenAI(
        base_url=base_url,
        api_key="dummy-key"  # 随便填
    )

    print(f"✅ 交互式对话已启动（服务类型：{args.service_type}，端口：{args.port}，线程：{thread_id}）")
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
            import requests
            requests.post(f"http://{args.host}:{args.port}/clear?thread={thread_id}")
            messages = []
            print(f"🧹 线程 {thread_id} 对话已清空\n")
            continue

        # 加入用户消息
        messages.append({"role": "user", "content": user_input})

        # 发送流式请求 - 使用 extra_body 传递 thread 参数
        print("助手：", end="", flush=True)
        response = client.chat.completions.create(
            model="glm-5",
            messages=messages,
            stream=True,
            extra_body={"thread": thread_id}  # 关键修改：使用 extra_body
        )

        # 接收流式返回
        answer = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                answer += content
                print(content, end="", flush=True)

        # 把助手回答加入历史
        messages.append({"role": "assistant", "content": answer})
        print("\n")

if __name__ == "__main__":
    args = parse_args()
    chat_loop(args)