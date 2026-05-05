#!/usr/bin/env python3
"""查找Base所在的folder_token - 方法2"""

import os
import requests
import json

# 加载 .env
env_path = '.env'
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

app_id = os.getenv("LARK_APP_ID")
app_secret = os.getenv("LARK_APP_SECRET")
base_token = os.getenv("LARK_BASE_APP_TOKEN")

print("=" * 60)
print("查找Base所在的文件夹 - 方法2")
print("=" * 60)

# 1. 获取tenant_access_token
token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
token_resp = requests.post(token_url, json={
    "app_id": app_id,
    "app_secret": app_secret
})
token_data = token_resp.json()
access_token = token_data.get("tenant_access_token")

print(f"\n[1] 获取Access Token: {access_token[:20]}...")

# 2. 使用 drive/explorer API 获取根文件夹内容
print(f"\n[2] 遍历云文档查找Base...")

def find_bitable_in_folder(folder_token, depth=0):
    """递归查找Base"""
    indent = "  " * depth

    url = f"https://open.feishu.cn/open-apis/drive/v1/files"
    params = {"folder_token": folder_token}

    resp = requests.get(url, headers={
        "Authorization": f"Bearer {access_token}"
    }, params=params)

    data = resp.json()

    if data.get("code") != 0:
        print(f"{indent}错误: {data.get('msg')}")
        return None

    files = data.get("data", {}).get("files", [])

    for f in files:
        name = f.get("name", "")
        ftoken = f.get("token", "")
        ftype = f.get("type", "")

        if ftype == "bitable" and base_token in ftoken:
            print(f"{indent}✅ 找到Base: {name}")
            print(f"{indent}   folder_token: {folder_token}")
            return folder_token

        if ftype == "folder":
            result = find_bitable_in_folder(ftoken, depth + 1)
            if result:
                return result

    return None

# 从根目录开始查找
root_token = ""  # 空字符串表示根目录
found_folder = find_bitable_in_folder(root_token)

if found_folder:
    print(f"\n[OK] Base所在的folder_token: {found_folder}")
    with open('.folder_token', 'w') as f:
        f.write(found_folder)
else:
    print(f"\n未找到Base，可能需要权限或Base在共享空间中")

print("\n" + "=" * 60)
