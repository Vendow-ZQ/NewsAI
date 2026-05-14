#!/usr/bin/env python3
"""小数复盘流程 — 一键启动数据收集与后评估。

用法:
    python scripts/run_analyst.py

流程:
    1. 运行 mock_data_demo.py 收集/生成模拟数据到【数据库】表
    2. 运行 小数 (AnalystAgent) 对已有数据做深度复盘分析
"""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def run_mock_data():
    """Step 1: 运行 mock_data_demo.py 生成模拟数据。"""
    print("=" * 60)
    print("Step 1: Mock Data Demo — 生成模拟分发数据")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, "scripts/mock_data_demo.py"],
        cwd=Path(__file__).parent.parent,
        capture_output=False,
    )
    if result.returncode != 0:
        print("[错误] Mock Data Demo 运行失败，退出。")
        sys.exit(1)
    print("Mock Data Demo 完成。\n")


def run_analyst_agent():
    """Step 2: 运行 小数 (AnalystAgent) 做数据复盘。"""
    print("=" * 60)
    print("Step 2: Analyst — 数据复盘分析")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, "run.py", "--agent", "analyze"],
        cwd=Path(__file__).parent.parent,
        capture_output=False,
    )
    if result.returncode != 0:
        print("[错误] 小数 Agent 运行失败，退出。")
        sys.exit(1)
    print("小数复盘完成。\n")


def main():
    print("\n" + "=" * 60)
    print("NewsAI 小数复盘流程")
    print("=" * 60 + "\n")

    run_mock_data()
    run_analyst_agent()

    print("=" * 60)
    print("小数复盘全流程完成。")
    print("=" * 60)


if __name__ == "__main__":
    main()
