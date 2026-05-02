#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Doubao 2.0 Hello World - 简化版
直接使用 OpenAI SDK 调用火山方舟
"""

import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL = os.getenv("LLM_MODEL")

if not all([API_KEY, BASE_URL, MODEL]):
    print("ERROR: 请配置 .env 文件: LLM_API_KEY, LLM_BASE_URL, LLM_MODEL")
    sys.exit(1)

print("Doubao 2.0 Hello World 测试\n")
print(f"BASE_URL: {BASE_URL}")
print(f"MODEL: {MODEL}\n")

try:
    from openai import OpenAI

    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL
    )
    print("客户端创建成功\n")

    # 简单对话
    print("发送测试消息...")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "你好，请用一句话证明你是AI助手"}
        ],
        temperature=0.7
    )

    print(f"收到响应:\n{response.choices[0].message.content}\n")

    # 测试工具调用
    print("测试工具调用...")
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_time",
                "description": "获取当前时间",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "现在几点了？"}
        ],
        tools=tools,
        tool_choice="auto"
    )

    print(f"工具调用测试完成")
    print(f"Finish reason: {response.choices[0].finish_reason}")
    if response.choices[0].message.tool_calls:
        print(f"Tool calls: {len(response.choices[0].message.tool_calls)}")
    print()

    print("=" * 50)
    print("Doubao 2.0 测试通过!")
    print("=" * 50)

except ImportError:
    print("ERROR: 请先安装依赖: pip install openai")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
