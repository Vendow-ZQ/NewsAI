# 飞书多维表格 API 操作手册

> 版本：v1.0  
> 适用：NewsAI Agent Tool Calling 开发  
> 基础：基于 lark-oapi SDK 和 HTTP API

---

## 一、核心概念

### 1.1 术语对照

| 飞书概念 | 对应API字段 | 说明 |
|---------|------------|------|
| Base (多维表格) | `app_token` | 整个表格文档的ID |
| 数据表 | `table_id` | 单张表的ID |
| 字段 | `field_id` / `field_name` | 列的唯一标识或名称 |
| 记录 | `record_id` | 行的唯一标识 |

### 1.2 ID 格式

```
Base Token:    RaFQbhb74aqFigsjqBEcQ0ZInHd  (22位随机字符串)
Table ID:      tblXClVXc16jyPSy            (tbl前缀+16位随机)
Field ID:      fldzdLr28b                   (fld前缀+10位随机)
Record ID:     recvizIY8BuwbE               (rec前缀+随机)
```

---

## 二、操作流程总览

```
1. 创建表 (Table) → 2. 添加字段 (Field) → 3. 写入记录 (Record)
                     ↓
              4. 更新/删除/查询记录
```

---

## 三、详细操作指南

### 3.1 创建数据表

**使用场景**：Agent需要新建一张业务表（如"信息源配置"、"热帖池"）

**API**：`POST /open-apis/bitable/v1/apps/{app_token}/tables`

**必需参数**：
- `name`: 表名（如"信息源配置"）
- `fields`: 至少一个字段（不能为空数组）

**SDK代码**：
```python
from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.bitable.v1.model.req_table import ReqTable
from lark_oapi.api.bitable.v1.model.app_table_create_header import AppTableCreateHeader

resp = client.bitable.v1.app_table.create(
    CreateAppTableRequest.builder()
        .app_token(BASE_TOKEN)
        .request_body(CreateAppTableRequestBody.builder()
            .table(
                ReqTable.builder()
                    .name("信息源配置")  # 表名
                    .fields([
                        AppTableCreateHeader.builder()
                            .field_name("源名称")
                            .type(1)  # 1=文本类型
                            .build(),
                    ])
                    .build()
            )
            .build()
        )
        .build()
)

if resp.success():
    table_id = resp.data.table_id  # 保存此ID后续使用
```

**常见错误**：
- `RolePermNotAllow`：应用未添加到Base协作者
- `field validation failed`: 未提供fields或fields为空数组

---

### 3.2 重命名数据表

**使用场景**：修改已有表的名称

**API**：`PATCH /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}`

**SDK代码**：
```python
from lark_oapi.api.bitable.v1.model.patch_app_table_request import PatchAppTableRequest, PatchAppTableRequestBody

resp = client.bitable.v1.app_table.patch(
    PatchAppTableRequest.builder()
        .app_token(BASE_TOKEN)
        .table_id(table_id)
        .request_body(PatchAppTableRequestBody.builder()
            .name("新表名")
            .build())
        .build()
)
```

---

### 3.3 添加字段

**使用场景**：为已有表新增列（如添加"优先级"、"标签"字段）

**API**：`POST /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields`

**HTTP代码**（SDK不支持，需用HTTP）：
```python
import requests

def add_field(table_id, field_name, field_type=1):
    """
    添加字段
    field_type: 1=文本, 2=数字, 3=单选, 4=多选, 5=日期时间, etc.
    """
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_TOKEN}/tables/{table_id}/fields"
    headers = {
        "Authorization": f"Bearer {get_tenant_token()}",
        "Content-Type": "application/json"
    }
    data = {
        "field_name": field_name,
        "type": field_type
    }
    resp = requests.post(url, headers=headers, json=data)
    return resp.json()

# 使用示例
result = add_field("tblXClVXc16jyPSy", "优先级", field_type=1)
if result.get("code") == 0:
    field_id = result["data"]["field"]["field_id"]
```

**字段类型对照**：
| 类型 | 数值 | 说明 |
|-----|------|------|
| 文本 | 1 | 单行/多行文本 |
| 数字 | 2 | 整数/小数 |
| 单选 | 3 | 下拉单选 |
| 多选 | 4 | 下拉多选 |
| 日期时间 | 5 | 日期+时间 |
| 复选框 | 7 | Checkbox |
| 人员 | 11 | @用户 |
| 电话 | 13 | 电话号码 |
| 超链接 | 15 | URL链接 |

---

### 3.4 列出所有字段

**使用场景**：获取表的字段结构，用于确认字段是否存在

**SDK代码**：
```python
resp = client.bitable.v1.app_table_field.list(
    ListAppTableFieldRequest.builder()
        .app_token(BASE_TOKEN)
        .table_id(table_id)
        .build()
)

if resp.success():
    fields = {}
    for f in resp.data.items:
        fields[f.field_name] = f.field_id
    # fields: {"标题": "fldzdLr28b", "内容": "fldpoYbFnb", ...}
```

---

### 3.5 创建记录（写入数据）

**使用场景**：Agent写入业务数据（如小哨写入抓取的热帖）

**API**：`POST /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records`

**SDK代码**：
```python
resp = client.bitable.v1.app_table_record.create(
    CreateAppTableRecordRequest.builder()
        .app_token(BASE_TOKEN)
        .table_id(table_id)
        .request_body({
            "fields": {
                "标题": "MCP Protocol: A Universal Interface",
                "内容": "本文提出模型上下文协议(MCP)...",
                "平台": "arXiv",
                "热度值": 847
            }
        })
        .build()
)

if resp.success():
    record_id = resp.data.record.record_id  # 保存记录ID
```

**注意**：
- 字段名必须与表中实际名称完全匹配（区分大小写）
- 如果字段不存在会报 `FieldNameNotFound`

---

### 3.6 批量创建记录

**使用场景**：一次性写入多条数据（如批量导入热帖）

**SDK代码**：
```python
records = [
    {"fields": {"标题": "文章1", "内容": "摘要1"}},
    {"fields": {"标题": "文章2", "内容": "摘要2"}},
    {"fields": {"标题": "文章3", "内容": "摘要3"}},
]

resp = client.bitable.v1.app_table_record.batch_create(
    BatchCreateAppTableRecordRequest.builder()
        .app_token(BASE_TOKEN)
        .table_id(table_id)
        .request_body(BatchCreateAppTableRecordRequestBody.builder().records(records).build())
        .build()
)
```

---

### 3.7 更新记录

**使用场景**：修改已有数据（如更新"状态"从"待分析"改为"已分析"）

**API**：`PUT /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}`

**SDK代码**：
```python
resp = client.bitable.v1.app_table_record.update(
    UpdateAppTableRecordRequest.builder()
        .app_token(BASE_TOKEN)
        .table_id(table_id)
        .record_id(record_id)  # 要更新的记录ID
        .request_body({
            "fields": {
                "状态": "已分析",  # 只更新指定字段，其他字段不变
                "分析时间": "2026-05-04T12:00:00"
            }
        })
        .build()
)
```

---

### 3.8 查询记录

**使用场景**：读取单条记录详情

**SDK代码**：
```python
resp = client.bitable.v1.app_table_record.get(
    GetAppTableRecordRequest.builder()
        .app_token(BASE_TOKEN)
        .table_id(table_id)
        .record_id(record_id)
        .build()
)

if resp.success():
    record = resp.data.record
    print(record.fields)  # 字段值字典
```

---

### 3.9 列出所有记录

**使用场景**：批量查询数据（如小读取所有"待分析"的热帖）

**SDK代码**：
```python
resp = client.bitable.v1.app_table_record.list(
    ListAppTableRecordRequest.builder()
        .app_token(BASE_TOKEN)
        .table_id(table_id)
        .build()
)

if resp.success():
    total = resp.data.total  # 总记录数
    items = resp.data.items  # 记录列表
    for record in items:
        print(f"ID: {record.record_id}")
        print(f"Fields: {record.fields}")
```

**分页查询**（数据量大时）：
```python
page_token = None
all_records = []

while True:
    builder = ListAppTableRecordRequest.builder()
        .app_token(BASE_TOKEN)
        .table_id(table_id)
        .page_size(100)  # 每页100条
    
    if page_token:
        builder.page_token(page_token)
    
    resp = client.bitable.v1.app_table_record.list(builder.build())
    
    if resp.success():
        all_records.extend(resp.data.items)
        if not resp.data.has_more:
            break
        page_token = resp.data.page_token
    else:
        break
```

---

### 3.10 删除记录

**使用场景**：删除不需要的数据

**SDK代码**：
```python
resp = client.bitable.v1.app_table_record.delete(
    DeleteAppTableRecordRequest.builder()
        .app_token(BASE_TOKEN)
        .table_id(table_id)
        .record_id(record_id)
        .build()
)
```

---

## 四、通用工具函数

### 4.1 获取 Tenant Access Token

所有HTTP API调用都需要此token：

```python
import json
from lark_oapi.api.auth.v3 import InternalTenantAccessTokenRequest, InternalTenantAccessTokenRequestBody

def get_tenant_token(client, app_id, app_secret):
    """获取 tenant_access_token"""
    resp = client.auth.v3.tenant_access_token.internal(
        InternalTenantAccessTokenRequest.builder()
            .request_body(InternalTenantAccessTokenRequestBody.builder()
                .app_id(app_id)
                .app_secret(app_secret)
                .build())
            .build()
    )
    if resp.success():
        data = json.loads(resp.raw.content)
        return data.get('tenant_access_token')
    return None
```

---

## 五、完整流程示例

### 场景：创建"信息源配置"表并写入mock数据

```python
from feishu_base_manager import FeishuBaseManager  # 假设的封装类

# 初始化
base = FeishuBaseManager(app_id, app_secret, base_token)

# 1. 创建表
table_id = base.create_table("信息源配置", [
    {"name": "源名称", "type": 1},
    {"name": "源类型", "type": 3},  # 单选
    {"name": "平台", "type": 3},
    {"name": "权重", "type": 2},    # 数字
])

# 2. 写入数据
record_id = base.create_record(table_id, {
    "源名称": "arXiv AI 论文",
    "源类型": "API",
    "平台": "arXiv",
    "权重": 0.95
})

# 3. 查询并更新
record = base.get_record(table_id, record_id)
base.update_record(table_id, record_id, {"权重": 0.98})
```

---

## 六、错误码速查

| 错误码 | 含义 | 解决方案 |
|-------|------|---------|
| 91403 | 应用未授权访问Base | 将应用添加为Base协作者 |
| 1254302 | RolePermNotAllow | 应用缺少权限，检查权限配置和协作者状态 |
| 1254045 | FieldNameNotFound | 字段名不存在，检查字段名拼写 |
| 1254043 | RecordIdNotFound | 记录ID不存在或已被删除 |
| 1254002 | FieldNameDuplicated | 字段名已存在 |
| 99992402 | field validation failed | 请求参数校验失败，检查必填字段 |

---

## 七、Agent开发建议

### 7.1 Tool Calling 设计

每个Agent应该封装自己的数据操作工具：

```python
class TrendScoutAgent:
    """小哨Agent - 抓取热帖并写入"""
    
    def __init__(self, base_manager):
        self.base = base_manager
        self.table_id = None
    
    def ensure_table(self):
        """确保热帖池表存在"""
        if not self.table_id:
            # 尝试查找已有表
            tables = self.base.list_tables()
            if "热帖池" in tables:
                self.table_id = tables["热帖池"]
            else:
                # 创建新表
                self.table_id = self.base.create_table("热帖池", [...])
        return self.table_id
    
    def save_trend(self, trend_data):
        """保存热帖记录"""
        table_id = self.ensure_table()
        return self.base.create_record(table_id, trend_data)
```

### 7.2 字段缓存策略

避免每次操作都查询字段列表：

```python
class TableCache:
    """缓存表结构信息"""
    
    def __init__(self):
        self._tables = {}  # {table_name: table_id}
        self._fields = {}  # {table_id: {field_name: field_id}}
    
    def get_field_id(self, base_manager, table_id, field_name):
        """获取字段ID（带缓存）"""
        if table_id not in self._fields:
            # 从API加载
            fields = base_manager.list_fields(table_id)
            self._fields[table_id] = fields
        return self._fields[table_id].get(field_name)
```

---

*文档版本: v1.0 | 最后更新: 2026-05-04 | 编写: Claude*