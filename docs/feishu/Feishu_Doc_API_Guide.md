# 飞书云文档（Docx）API 操作手册

> 版本：v1.0  
> 适用：NewsAI v2 飞书文档产物形态  
> 基础：基于 lark-oapi SDK  
> 关键结论：**不支持 markdown 直接写入，必须通过 block 结构构造内容**

---

## 一、核心结论

### 1.1 不支持 markdown 直接写入

飞书文档 API **没有** "直接写入 markdown 字符串" 的接口。所有内容必须通过 **Block（块）** 结构逐块构造。

这意味着：
- 如果 Agent 输出的是 markdown，需要一个 `markdown_to_lark_blocks()` 转换器
- 转换器需要把 `# 标题` → `block_type=3` 的 heading1 block
- 转换器需要把 `- 列表项` → `block_type=12` 的 bullet block
- 转换器需要把 ` ```python\ncode\n``` ` → `block_type=22` 的 code block

### 1.2 Block 是唯一的写入单元

飞书文档的内容由 Block 组成，每个 Block 有：
- `block_type`：块类型（见下表）
- `block_id`：块的唯一标识
- 内容属性：如 `heading1`、`text`、`bullet`、`code` 等

---

## 二、Block 类型映射表

| Block 类型 | block_type 值 | SDK 方法 | 说明 |
|---|---|---|---|
| 页面 | 1 | `.page(...)` | 文档根节点，一般不手动创建 |
| 正文 | 2 | `.text(Text)` | 普通段落 |
| 一级标题 | 3 | `.heading1(Text)` | H1 |
| 二级标题 | 4 | `.heading2(Text)` | H2 |
| 三级标题 | 5 | `.heading3(Text)` | H3 |
| 四级标题 | 6 | `.heading4(Text)` | H4 |
| 五级标题 | 7 | `.heading5(Text)` | H5 |
| 六级标题 | 8 | `.heading6(Text)` | H6 |
| 无序列表 | 12 | `.bullet(Text)` | 圆点列表 |
| 有序列表 | 13 | `.ordered(Text)` | 数字列表 |
| 引用块 | 19 | `.quote(Text)` | 引用 |
| 代码块 | 22 | `.code(Text)` | 代码 |
| 分割线 | 14 | `.divider(...)` | 水平线 |
| 图片 | 27 | `.image(...)` | 图片 |

---

## 三、Text 结构（块的内容）

所有文本类型的 Block（heading、text、bullet、code 等），其内容都通过 `Text` 对象描述。

### 3.1 Text 的嵌套结构

```
Block
  └─ heading1 / heading2 / text / bullet / code (Text 类型)
       └─ elements: List[TextElement]
            └─ text_run (TextRun 类型)
                 └─ content: str  ← 实际文本内容
                 └─ text_element_style: 样式
```

### 3.2 构造一个文本块

```python
from lark_oapi.api.docx.v1 import (
    BlockBuilder, TextBuilder, TextElementBuilder, TextRunBuilder,
)

# 1. 构造 TextRun（实际文本）
text_run = TextRunBuilder().content("这是文本内容").build()

# 2. 构造 TextElement（包装 TextRun）
element = TextElementBuilder().text_run(text_run).build()

# 3. 构造 Text（元素列表）
text = TextBuilder().elements([element]).build()

# 4. 构造 Block（设置类型和内容）
block = BlockBuilder() \
    .block_type(3) \  # 3 = heading1
    .heading1(text) \
    .build()
```

### 3.3 封装函数

```python
def make_text_block(content: str, block_type: int) -> Block:
    """构造一个文本类型的 Block。

    block_type: 2=text, 3=heading1, 4=heading2, 12=bullet, 22=code_block
    """
    text_run = TextRunBuilder().content(content).build()
    element = TextElementBuilder().text_run(text_run).build()
    text = TextBuilder().elements([element]).build()

    builder = BlockBuilder().block_type(block_type)

    if block_type == 2:
        builder = builder.text(text)
    elif block_type == 3:
        builder = builder.heading1(text)
    elif block_type == 4:
        builder = builder.heading2(text)
    elif block_type == 12:
        builder = builder.bullet(text)
    elif block_type == 22:
        builder = builder.code(text)
    else:
        builder = builder.text(text)

    return builder.build()
```

---

## 四、完整流程：创建文档 → 写入内容 → 设置权限

### 4.1 创建文档

```python
from lark_oapi import Client
from lark_oapi.api.docx.v1 import (
    CreateDocumentRequest,
    CreateDocumentRequestBodyBuilder,
)

client = Client.builder().app_id(APP_ID).app_secret(APP_SECRET).build()

resp = client.docx.v1.document.create(
    CreateDocumentRequest.builder()
        .request_body(
            CreateDocumentRequestBodyBuilder()
                .title("文档标题")
                .build()
        )
        .build()
)

document_id = resp.data.document.document_id
```

**需要的权限**：`docx:document` + `docx:document:create`

### 4.2 写入 Block 内容

```python
from lark_oapi.api.docx.v1 import (
    CreateDocumentBlockChildrenRequest,
    CreateDocumentBlockChildrenRequestBodyBuilder,
)

blocks = [
    make_text_block("一级标题", 3),
    make_text_block("二级标题", 4),
    make_text_block("正文段落", 2),
    make_text_block("列表项", 12),
    make_text_block("代码内容", 22),
]

resp = client.docx.v1.document_block_children.create(
    CreateDocumentBlockChildrenRequest.builder()
        .document_id(document_id)
        .request_body(
            CreateDocumentBlockChildrenRequestBodyBuilder()
                .children(blocks)
                .build()
        )
        .build()
)
```

**需要的权限**：`docx:document:readonly`（读取已有 block）+ `docx:document`（写入）

### 4.3 设置文档权限

飞书文档权限通过 **drive API** 设置：

```python
import requests

# 获取 tenant token
token_resp = client.auth.v3.tenant_access_token.internal(...)
tenant_token = json.loads(token_resp.raw.content)['tenant_access_token']

# 设置权限
url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{document_id}/public"
headers = {"Authorization": f"Bearer {tenant_token}", "Content-Type": "application/json"}
data = {
    "security_entity": "anyone_can_view",
    "comment_entity": "anyone_can_view",
    "share_entity": "tenant_can_view",
    "link_share_entity": "tenant_readable",
}

resp = requests.patch(url, headers=headers, json=data)
```

**需要的权限**：`drive:drive` + `drive:drive:readonly`

### 4.4 分享链接格式

```
https://{tenant}.feishu.cn/docx/{document_id}
```

其中 `{tenant}` 是租户域名（如 `f5tgebopkn`），可在飞书后台查看。

---

## 五、与多维表格（Bitable）API 的对比

| 能力 | Bitable API | Docx API |
|---|---|---|
| 创建 | `app_table.create` | `document.create` |
| 写入 | `app_table_record.create`（字段键值对） | `document_block_children.create`（Block 列表） |
| 读取 | `app_table_record.list` | `document_block_children.list` |
| 更新 | `app_table_record.update`（单字段） | `batch_update_document_block`（批量） |
| 删除 | `app_table_record.delete` | `batch_delete_document_block_children` |
| 内容格式 | 纯文本/数字/日期等 | 富文本（Block 结构） |
| Markdown | 不支持 | 不支持（需转换器） |

---

## 六、待实现：markdown_to_lark_blocks 转换器

v2 中 Agent 输出 markdown 字符串，需要转换为飞书 Block 列表。转换器需要处理：

```markdown
# 标题        → heading1
## 副标题     → heading2
正文段落      → text
- 列表项      → bullet
1. 有序项     → ordered
`代码`        → text（inline code）
```python
代码块
```          → code_block
> 引用        → quote
---           → divider
```

**实现建议**：用 `markdown-it-py` 或正则表达式解析 markdown AST，然后遍历节点生成对应 Block。

---

## 七、错误码速查

| 错误码 | 含义 | 解决方案 |
|---|---|---|
| 99991672 | 缺少 docx 权限 | 在开放平台添加 `docx:document` 等权限 |
| 1254302 | RolePermNotAllow | 应用未添加到文档协作者 |
| 1770034 | 文档不存在 | 检查 document_id 是否正确 |

---

*文档版本: v1.0 | 最后更新: 2026-05-04 | 编写: Claude*  
*配套代码: `tests/test_lark_doc_hello.py`*
