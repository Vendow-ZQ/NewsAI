# Feishu Docx 文档实现总结

## 概述
将原本存储在 Bitable 字段中的长文本内容，改为存储在飞书 Docx 文档（ldx 格式）中，通过文档链接关联。

## 4类文档实现

### 1. 帖子内容文档（小文 ContentWriter）
- **创建者**: 小文 Agent
- **文件名**: `core/agents/content_writer.py`
- **方法**: `_write_storage()`
- **文档标题**: `【帖子内容】{选题标题}`
- **包含内容**:
  - 公众号版本（标题、正文、配图说明）
  - 小红书版本（标题、正文、标签）
  - 抖音版本（文案、钩子、CTA）
  - B站版本（标题、简介、正文）
- **存储字段**:
  - `帖子内容文档ID` (ldx开头)
  - `帖子内容文档链接` (飞书文档URL)

### 2. 视频脚本文档（小播 ScriptWriter）
- **创建者**: 小播 Agent
- **文件名**: `core/agents/script_writer.py`
- **方法**: `_write_storage()`
- **文档标题**: `【视频脚本】{选题标题}`
- **包含内容**:
  - 抖音版脚本（钩子开场、核心内容、CTA、BGM建议）
  - B站版脚本（开场、分段内容、结尾、BGM建议）
- **存储字段**:
  - `视频脚本文档ID` (ldx开头)
  - `视频脚本文档链接` (飞书文档URL)

### 3. 审改记录文档（小审 Reviewer + 小改 Editor）
- **创建者**: 小审查时创建，小改修改时追加
- **文件名**: 
  - 小审: `core/agents/reviewer.py`
  - 小改: `core/agents/editor.py`
- **文档标题**: `【审改记录】{选题标题}`
- **小审 - 首次创建**:
  - 创建空白审改文档
  - 追加第1轮审查记录
  - 包含：审查结论、严重度、问题列表、审查指标
- **小改 - 修改追加**:
  - 读取现有审改文档ID
  - 追加修改记录
  - 包含：修改总结、具体修改项、修改原因
- **存储字段**:
  - `审改记录文档ID` (ldx开头)
  - `审改记录文档链接` (飞书文档URL)

### 4. 经验总结文档（小数 Analyst）
- **创建者**: 小数 Agent
- **文件名**: `core/agents/analyst.py`
- **方法**: `_write_storage()`
- **文档标题**: `【经验总结】{周期}AI内容复盘`
- **包含内容**:
  - 成败分析（LLM分析结果）
  - 选题建议列表
  - 各平台数据指标
- **存储字段**:
  - `经验总结文档ID` (ldx开头)
  - `经验总结文档链接` (飞书文档URL)

## 核心工具类

### FeishuDocStorage
- **文件**: `feishu_adapter/doc_storage.py`
- **关键方法**:
  - `create_document(title, content_blocks)` - 创建新文档
  - `create_post_document(...)` - 创建帖子文档
  - `create_script_document(...)` - 创建脚本文档
  - `create_audit_document(...)` - 创建审改记录文档（空白）
  - `create_experience_document(...)` - 创建经验总结文档
  - `append_to_document(doc_id, content_blocks)` - **追加内容到现有文档**
  - `get_document_url(doc_id)` - 获取文档分享链接

### Block类型映射
| Block类型 | 常量值 | 用途 |
|-----------|--------|------|
| TEXT | 2 | 普通文本 |
| HEADING1 | 3 | 一级标题 |
| HEADING2 | 4 | 二级标题 |
| HEADING3 | 5 | 三级标题 |
| BULLET | 12 | 无序列表 |
| NUMBERED | 13 | 有序列表 |
| CODE | 22 | 代码块 |

## 表结构更新

### TOPIC表（选题库）字段更新
```python
# 旧字段（已废弃）
make_field("帖子内容", FIELD_TYPE_TEXT),
make_field("视频脚本内容", FIELD_TYPE_TEXT),
make_field("审改记录", FIELD_TYPE_TEXT),

# 新字段（文档链接）
make_field("帖子内容文档ID", FIELD_TYPE_TEXT),      # ldx开头
make_field("帖子内容文档链接", FIELD_TYPE_URL),      # 飞书文档链接
make_field("视频脚本文档ID", FIELD_TYPE_TEXT),      # ldx开头
make_field("视频脚本文档链接", FIELD_TYPE_URL),      # 飞书文档链接
make_field("审改记录文档ID", FIELD_TYPE_TEXT),       # ldx开头
make_field("审改记录文档链接", FIELD_TYPE_URL),       # 飞书文档链接
```

### DATA表（数据库）字段更新
```python
# 旧字段（已废弃）
make_field("经验总结", FIELD_TYPE_TEXT),

# 新字段（文档链接）
make_field("经验总结文档ID", FIELD_TYPE_TEXT),      # ldx开头
make_field("经验总结文档链接", FIELD_TYPE_URL),      # 飞书文档链接
```

## 文档创建流程

### 帖子内容文档流程
```
小文.execute()
  └── _write_storage()
        ├── FeishuDocStorage()
        ├── create_post_document(topic_id, topic_title, platforms)
        │     └── create_document(title, blocks)
        ├── get_document_url(doc_id)
        └── storage.update("选题库", topic_id, {
              "帖子内容文档ID": doc_id,
              "帖子内容文档链接": doc_url,
              "状态": "生产中"
          })
```

### 审改记录文档流程
```
小审.execute() - 首次审查
  └── _write_storage()
        ├── FeishuDocStorage()
        ├── create_audit_document(topic_id, topic_title)  ← 创建空白文档
        ├── _format_review_blocks(review_data, round_num)
        ├── append_to_document(doc_id, review_blocks)     ← 追加审查记录
        └── storage.update("选题库", topic_id, {
              "审改记录文档ID": doc_id,
              "审改记录文档链接": doc_url,
              "审改轮次": current_round,
              "状态": "审改中"/"待发布"
          })

小改.execute() - 修改内容
  └── _write_storage()
        ├── FeishuDocStorage()
        ├── 读取现有 doc_id
        ├── _format_edit_blocks(edit_summary, edit_details)
        ├── append_to_document(doc_id, edit_blocks)       ← 追加修改记录
        └── （状态保持"审改中"，等待再审）
```

## 防循环保护机制

### 小审侧（跳过已审查选题）
- 方法: `_is_already_reviewed(topic)`
- 逻辑: 检查审改记录中审查次数是否 > 修改次数
- 效果: 如果已经审查过但小改尚未修改，跳过该选题

### 小改侧（无修改则强制通过）
- 位置: `_write_storage()` 开头
- 逻辑: 如果 `edit_results` 为空，将所有"审改中"选题强制改为"待发布"
- 效果: 防止无限循环

### 最大轮次限制
- 位置: `reviewer.py _invoke_llm()`
- 逻辑: 如果 `current_round > 3`，强制设置审查结论为"通过"
- 效果: 最多3轮审改，之后强制通过

## 状态流转

```
已选 → 生产中 → 审改中 → 待发布 → 已发布
        ↑_________|
          (审改循环，最多3轮)
```

## 测试验证清单

- [ ] 小文创建帖子文档成功
- [ ] 小播创建脚本文档成功
- [ ] 小审查时创建审改文档成功
- [ ] 小改追加修改记录成功
- [ ] 小数创建经验总结文档成功
- [ ] 文档链接正确回填到Bitable
- [ ] 审改循环最多3轮后强制通过
- [ ] 小改无修改时强制通过
- [ ] 小审不重复审查已审选题

## 注意事项

1. **飞书API权限**: 需要 `docx:document` 权限才能创建文档
2. **Block限制**: 每次API调用最多写入100个block
3. **文档链接格式**: `https://{domain}.feishu.cn/docx/{document_id}`
4. **文档ID格式**: 以 `ldx` 开头，例如 `ldx1234567890123456`
5. **错误处理**: 所有文档操作都有try-except保护，失败时打印错误但不中断流程

---

**实现完成时间**: 2026-05-05 02:30  
**实现者**: Claude Code
