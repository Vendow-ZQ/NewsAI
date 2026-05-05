#!/usr/bin/env python3
"""查找Base所在的folder_token"""

import os

# 加载 .env
env_path = '.env'
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

from lark_oapi import Client

app_id = os.getenv("LARK_APP_ID")
app_secret = os.getenv("LARK_APP_SECRET")
base_token = os.getenv("LARK_BASE_APP_TOKEN")

print("=" * 60)
print("查找Base所在的文件夹")
print("=" * 60)
print(f"Base Token: {base_token}")

client = Client.builder() \
    .app_id(app_id) \
    .app_secret(app_secret) \
    .build()

# 方法1: 直接尝试创建文档并指定Base token作为folder_token
# 如果不行，就使用一个已知的folder_token

# 让我先用最简单的方法：询问用户
print("\n" + "=" * 60)
print("\n请从浏览器地址栏获取folder_token：")
print("1. 打开飞书云文档")
print("2. 进入包含这个Base的文件夹")
print("3. 复制URL中 folder/ 后面的部分")
print("\n示例:")
print("https://jneyh7qlo8i.feishu.cn/drive/folder/AbCdEfGh123")
print("                                    folder_token: AbCdEfGh123")
print("=" * 60)
