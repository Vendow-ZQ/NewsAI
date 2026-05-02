#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Doubao 2.0 Hello World
验证火山方舟 API 连通性
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
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage

    # 创建客户端
    llm = ChatOpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        model=MODEL,
        temperature=0.7,
    )
    print("客户端创建成功\n")

    # 简单调用
    print("发送测试消息...")
    messages = [HumanMessage(content="你好，请用一句话证明你是AI助手")]

    response = llm.invoke(messages)

    print(f"收到响应:\n{response.content}\n")

    print("=" * 50)
    print("Doubao 2.0 测试通过!")
    print("=" * 50)

except ImportError as e:
    print(f"ERROR: 导入失败 - {e}")
    print("请运行: pip install langchain-openai langchain")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
