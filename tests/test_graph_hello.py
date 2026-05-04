#!/usr/bin/env python3
"""
Stage 1.3: LangGraph Hello World
2个节点：A节点调LLM生成文字 → B节点打印文字
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# 检查环境变量（使用 LLM_API_KEY）
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
LLM_MODEL = os.getenv("LLM_MODEL", "doubao-2.0-32k")
if not LLM_API_KEY:
    print("[ERROR] 请配置 .env：LLM_API_KEY")
    sys.exit(1)

print("[TEST] LangGraph Hello World\n")

# 测试1: 基础Graph能跑通
print("[STEP 1] 测试基础StateGraph...")
try:
    from langgraph.graph import StateGraph, END
    from typing import TypedDict

    class State(TypedDict):
        message: str
        output: str

    def node_a(state: State) -> State:
        """A节点：生成文字"""
        return {"output": f"A节点收到: {state['message']}"}

    def node_b(state: State) -> State:
        """B节点：打印并追加"""
        result = f"B节点处理: {state['output']} -> 完成!"
        print(f"   {result}")
        return {"output": result}

    # 构建图
    builder = StateGraph(State)
    builder.add_node("node_a", node_a)
    builder.add_node("node_b", node_b)
    builder.set_entry_point("node_a")
    builder.add_edge("node_a", "node_b")
    builder.add_edge("node_b", END)

    graph = builder.compile()

    # 运行
    result = graph.invoke({"message": "Hello LangGraph!"})
    assert result["output"] == "B节点处理: A节点收到: Hello LangGraph! -> 完成!"
    print("   [OK] 基础Graph运行成功\n")

except Exception as e:
    print(f"   [ERROR] {e}")
    sys.exit(1)

# 测试2: Graph + LLM调用
print("[STEP 2] 测试Graph + LLM调用...")
try:
    from langchain_openai import ChatOpenAI

    # 初始化 Doubao
    llm = ChatOpenAI(
        model=LLM_MODEL,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        temperature=0.7,
    )

    def llm_node(state: State) -> State:
        """调用LLM生成回复"""
        response = llm.invoke(f"请用一句话回复: {state['message']}")
        return {"output": response.content}

    def print_node(state: State) -> State:
        """打印输出"""
        # 过滤掉emoji避免Windows控制台编码错误
        output = state['output'].encode('ascii', 'ignore').decode('ascii')
        print(f"   LLM回复: {output[:100]}...")  # 只打印前100字符
        return state

    # 构建LLM Graph
    builder2 = StateGraph(State)
    builder2.add_node("llm_node", llm_node)
    builder2.add_node("print_node", print_node)
    builder2.set_entry_point("llm_node")
    builder2.add_edge("llm_node", "print_node")
    builder2.add_edge("print_node", END)

    llm_graph = builder2.compile()

    # 运行
    result = llm_graph.invoke({"message": "Hello LangGraph!"})
    assert result["output"] and len(result["output"]) > 0
    print("   [OK] LLM调用成功\n")

except Exception as e:
    print(f"   [ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 50)
print("[DONE] LangGraph Hello World 完成!")
print("[INFO] Stage 1.3 通过: graph.invoke() 运行正常")
