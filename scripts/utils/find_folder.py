#!/usr/bin/env python3
"""使用HTTP请求查找Base所在的folder"""

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
print("使用HTTP API查找Base所在的文件夹")
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

# 2. 获取Base的元数据（包含parent_token）
print(f"\n[2] 获取Base的元数据...")

# 正确的API端点和参数
meta_url = "https://open.feishu.cn/open-apis/drive/v1/metas/batch_get"
params = {
    "request_file_list": json.dumps([{"token": base_token, "type": "bitable"}])
}

meta_resp = requests.get(meta_url, headers={
    "Authorization": f"Bearer {access_token}"
}, params=params)

print(f"   状态码: {meta_resp.status_code}")
print(f"   响应: {meta_resp.text[:500]}")

try:
    meta_data = meta_resp.json()

    if meta_data.get("code") == 0:
        metas = meta_data.get("data", {}).get("metas", [])
        for meta in metas:
            print(f"\n   Base名称: {meta.get('name')}")
            print(f"   类型: {meta.get('type')}")
            print(f"   Parent Token (folder_token): {meta.get('parent_token')}")

            # 保存folder_token到文件
            folder_token = meta.get('parent_token')
            if folder_token:
                print(f"\n[OK] 找到folder_token: {folder_token}")
                with open('.folder_token', 'w') as f:
                    f.write(folder_token)
                print("   已保存到 .folder_token 文件")
    else:
        print(f"   错误码: {meta_data.get('code')}")
        print(f"   错误信息: {meta_data.get('msg')}")
except Exception as e:
    print(f"   解析响应失败: {e}")

print("\n" + "=" * 60)
