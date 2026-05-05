#!/usr/bin/env python3
"""更新DATA表结构，添加经验总结文档字段"""

with open('feishu_adapter/base/tables.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找DATA表的"经验总结"字段并替换
old_text = '    make_field("经验总结", FIELD_TYPE_TEXT),                        # 小数月度沉淀的经验总结'

new_text = '''    make_field("经验总结文档ID", FIELD_TYPE_TEXT),                 # 飞书文档ID (ldx开头) - 小数创建
    make_field("经验总结文档链接", FIELD_TYPE_URL),                 # 飞书文档分享链接'''

if old_text in content:
    content = content.replace(old_text, new_text)
    with open('feishu_adapter/base/tables.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('DATA表字段已更新')
else:
    print('未找到经验总结字段')
