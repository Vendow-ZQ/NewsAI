#!/usr/bin/env python3
"""更新表结构，添加文档链接字段"""

with open('feishu_adapter/base/tables.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换旧字段为新字段（文档ID和链接）
old_text = '''    make_field("帖子内容", FIELD_TYPE_TEXT),                        # 小文产出后回填，4平台版本完整内容
    make_field("视频脚本内容", FIELD_TYPE_TEXT),                    # 小播产出后回填，抖音+B站脚本
    make_field("审改记录", FIELD_TYPE_TEXT),                        # 小审/小改累积追加，每轮审查+修改内容'''

new_text = '''    make_field("帖子内容文档ID", FIELD_TYPE_TEXT),                 # 飞书文档ID (ldx开头) - 小文创建
    make_field("帖子内容文档链接", FIELD_TYPE_URL),                 # 飞书文档分享链接
    make_field("视频脚本文档ID", FIELD_TYPE_TEXT),                 # 飞书文档ID (ldx开头) - 小播创建
    make_field("视频脚本文档链接", FIELD_TYPE_URL),                 # 飞书文档分享链接
    make_field("审改记录文档ID", FIELD_TYPE_TEXT),                 # 飞书文档ID (ldx开头) - 小审创建
    make_field("审改记录文档链接", FIELD_TYPE_URL),                 # 飞书文档分享链接'''

if old_text in content:
    content = content.replace(old_text, new_text)
    with open('feishu_adapter/base/tables.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✅ TOPIC表字段已更新为文档链接字段')
else:
    print('❌ 未找到旧字段')
    # 打印相关字段
    import re
    matches = re.findall(r'make_field\("([^"]+)"', content)
    print('相关字段:', [m for m in matches if '帖子' in m or '视频' in m or '审改' in m])
