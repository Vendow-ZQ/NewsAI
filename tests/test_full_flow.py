"""全流程测试脚本 - 验证小哨到小发（含小数）"""
import os
import sys
from datetime import datetime

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

print("="*60)
print("NewsAI 全流程测试")
print("="*60)

# 1. 检查环境
print("\n[1] 检查环境变量...")
required_vars = ['LARK_APP_ID', 'LARK_APP_SECRET', 'LARK_BASE_APP_TOKEN', 'DOUBAO_API_KEY']
for var in required_vars:
    if os.getenv(var):
        print(f"  OK {var}")
    else:
        print(f"  FAIL {var} 缺失")
        sys.exit(1)

# 2. 导入模块
print("\n[2] 导入模块...")
try:
    from core.graph.builder import build_newsai_graph
    from feishu_adapter.feishu_storage import FeishuStorage
    from core.llm.client import LLMClient
    print("  OK 所有模块导入成功")
except Exception as e:
    print(f"  FAIL 导入失败: {e}")
    sys.exit(1)

# 3. 初始化组件
print("\n[3] 初始化组件...")
try:
    storage = FeishuStorage(
        app_id=os.getenv('LARK_APP_ID'),
        app_secret=os.getenv('LARK_APP_SECRET'),
        base_token=os.getenv('LARK_BASE_APP_TOKEN')
    )
    print("  OK Storage 初始化成功")

    llm = LLMClient(api_key=os.getenv('DOUBAO_API_KEY'))
    print("  OK LLM Client 初始化成功")

    graph = build_newsai_graph(storage, llm)
    print("  OK LangGraph 构建成功")
except Exception as e:
    print(f"  FAIL 初始化失败: {e}")
    sys.exit(1)

print("\n准备就绪！可以运行全流程测试")
print("运行命令: python run.py --once")
