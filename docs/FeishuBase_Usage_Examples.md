# FeishuBaseManager 使用示例

> 本文档展示如何在 Agent 开发中使用 FeishuBaseManager 类

---

## 一、基础用法

### 1.1 初始化

```python
from core.utils.feishu_base import FeishuBaseManager, get_base_manager

# 方式1: 自动从环境变量读取配置
base = get_base_manager()

# 方式2: 手动传入配置
base = FeishuBaseManager(
    app_id="cli_xxx",
    app_secret="xxx",
    base_token="RaFQxxx"
)
```

### 1.2 常用操作速查

```python
# 列出所有表
tables = base.list_tables()  # {表名: 表ID}

# 创建表
table_id = base.create_table("热帖池", [
    {"name": "标题", "type": "text"},
    {"name": "热度", "type": "number"},
])

# 获取或创建表（如果不存在则创建）
table_id = base.get_or_create_table("信息源配置", [...])

# 添加字段
base.add_field(table_id, "新字段", field_type="text")

# 创建记录
record_id = base.create_record(table_id, {"标题": "xxx", "热度": 100})

# 批量创建
base.batch_create_records(table_id, [
    {"fields": {"标题": "文章1"}},
    {"fields": {"标题": "文章2"}},
])

# 查询记录
record = base.get_record(table_id, record_id)

# 列出所有记录
records = base.list_records(table_id)

# 更新记录
base.update_record(table_id, record_id, {"热度": 200})

# 删除记录
base.delete_record(table_id, record_id)
```

---

## 二、Agent 开发示例

### 2.1 小哨 Agent - 抓取热帖并写入

```python
from core.utils.feishu_base import FeishuBaseManager

class TrendScoutAgent:
    """小哨 - 趋势侦察员"""
    
    def __init__(self):
        self.base = FeishuBaseManager()
        self.table_id = None
        
    def setup(self):
        """初始化表结构"""
        # 确保热帖池表存在
        self.table_id = self.base.get_or_create_table(
            "热帖池",
            fields=[
                {"name": "标题", "type": "text"},
                {"name": "来源", "type": "text"},
                {"name": "热度", "type": "number"},
                {"name": "链接", "type": "url"},
                {"name": "抓取时间", "type": "datetime"},
            ]
        )
        
    def save_trend(self, title: str, source: str, heat: int, url: str):
        """保存单条热帖"""
        from datetime import datetime
        
        record_id = self.base.create_record(
            self.table_id,
            fields={
                "标题": title,
                "来源": source,
                "热度": heat,
                "链接": url,
                "抓取时间": datetime.now().isoformat(),
            }
        )
        return record_id
    
    def batch_save_trends(self, trends: list):
        """批量保存热帖"""
        records = []
        for trend in trends:
            records.append({"fields": {
                "标题": trend["title"],
                "来源": trend["source"],
                "热度": trend["heat"],
                "链接": trend["url"],
            }})
        
        return self.base.batch_create_records(self.table_id, records)
```

### 2.2 小编 Agent - 读取待分析热帖

```python
class TopicCuratorAgent:
    """小编 - 选题策划"""
    
    def __init__(self):
        self.base = FeishuBaseManager()
        self.trend_table = None
        
    def get_pending_trends(self, min_heat: int = 100):
        """获取待分析的高热度热帖"""
        # 获取热帖池表ID
        tables = self.base.list_tables()
        if "热帖池" not in tables:
            return []
        
        self.trend_table = tables["热帖池"]
        
        # 读取所有记录
        records = self.base.list_records(self.trend_table)
        
        # 筛选高热度的
        hot_trends = []
        for record in records:
            fields = record["fields"]
            heat = fields.get("热度", 0)
            if isinstance(heat, (int, float)) and heat >= min_heat:
                hot_trends.append({
                    "record_id": record["record_id"],
                    "标题": fields.get("标题"),
                    "热度": heat,
                    "来源": fields.get("来源"),
                })
        
        return hot_trends
    
    def mark_as_analyzed(self, record_id: str):
        """标记为已分析"""
        self.base.update_record(
            self.trend_table,
            record_id,
            {"状态": "已分析"}
        )
```

### 2.3 小文 Agent - 创建内容稿件

```python
class ContentWriterAgent:
    """小文 - 内容创作者"""
    
    def __init__(self):
        self.base = FeishuBaseManager()
        self.draft_table = None
        
    def setup(self):
        """初始化稿件表"""
        self.draft_table = self.base.get_or_create_table(
            "内容稿件",
            fields=[
                {"name": "标题", "type": "text"},
                {"name": "正文", "type": "text"},
                {"name": "作者", "type": "text"},
                {"name": "状态", "type": "text"},  # 草稿/审核中/已发布
                {"name": "创建时间", "type": "datetime"},
            ]
        )
        
    def create_draft(self, title: str, content: str, author: str = "小文"):
        """创建新稿件"""
        from datetime import datetime
        
        record_id = self.base.create_record(
            self.draft_table,
            fields={
                "标题": title,
                "正文": content,
                "作者": author,
                "状态": "草稿",
                "创建时间": datetime.now().isoformat(),
            }
        )
        return record_id
    
    def submit_for_review(self, record_id: str):
        """提交审核"""
        self.base.update_record(
            self.draft_table,
            record_id,
            {"状态": "审核中"}
        )
```

---

## 三、完整工作流示例

```python
# 完整工作流：抓取 -> 分析 -> 创作 -> 审核

def main_workflow():
    # 初始化
    base = FeishuBaseManager()
    
    # 1. 小哨抓取
    scout = TrendScoutAgent()
    scout.setup()
    
    trends = [
        {"title": "MCP协议发布", "source": "arXiv", "heat": 847, "url": "https://..."},
        {"title": "AI新模型", "source": "Reddit", "heat": 532, "url": "https://..."},
    ]
    record_ids = scout.batch_save_trends(trends)
    print(f"抓取完成，写入 {len(record_ids)} 条热帖")
    
    # 2. 小编选题
    curator = TopicCuratorAgent()
    hot_trends = curator.get_pending_trends(min_heat=500)
    print(f"发现 {len(hot_trends)} 条高热帖")
    
    # 3. 小文创作
    writer = ContentWriterAgent()
    writer.setup()
    
    for trend in hot_trends[:3]:  # 取前3个
        draft_id = writer.create_draft(
            title=f"解读: {trend['标题']}",
            content=f"这是关于 {trend['标题']} 的深度分析...",
        )
        print(f"创建稿件: {draft_id}")
        
        # 标记热帖已分析
        curator.mark_as_analyzed(trend["record_id"])

if __name__ == "__main__":
    main_workflow()
```

---

## 四、错误处理最佳实践

```python
from core.utils.feishu_base import FeishuBaseManager

class RobustAgent:
    def __init__(self):
        self.base = FeishuBaseManager()
        
    def safe_create_record(self, table_id: str, fields: dict):
        """安全的记录创建（带重试）"""
        max_retries = 3
        for i in range(max_retries):
            try:
                return self.base.create_record(table_id, fields)
            except Exception as e:
                if "permission" in str(e).lower():
                    print(f"[ERROR] 权限不足，请检查应用协作者设置")
                    raise
                elif i < max_retries - 1:
                    print(f"[WARN] 创建失败，重试 {i+1}/{max_retries}")
                    import time
                    time.sleep(1)
                else:
                    print(f"[ERROR] 创建记录失败: {e}")
                    raise
    
    def safe_ensure_table(self, name: str, fields: list):
        """确保表存在（幂等操作）"""
        try:
            return self.base.get_or_create_table(name, fields)
        except Exception as e:
            print(f"[ERROR] 创建表失败: {e}")
            # 尝试获取已有表
            tables = self.base.list_tables()
            if name in tables:
                print(f"[INFO] 使用已有表: {name}")
                return tables[name]
            raise
```

---

## 五、性能优化建议

### 5.1 批量操作优先

```python
# ❌ 不推荐：逐条创建
for item in items:
    base.create_record(table_id, item)  # N次API调用

# ✅ 推荐：批量创建
records = [{"fields": item} for item in items]
base.batch_create_records(table_id, records)  # 1次API调用
```

### 5.2 使用缓存

```python
# 缓存表ID和字段ID，避免重复查询
class CachedAgent:
    def __init__(self):
        self.base = FeishuBaseManager()
        self._table_id = None
        self._field_map = None
    
    def get_table_id(self):
        if not self._table_id:
            tables = self.base.list_tables()
            self._table_id = tables.get("热帖池")
        return self._table_id
    
    def get_field_id(self, field_name):
        if not self._field_map:
            table_id = self.get_table_id()
            self._field_map = self.base.list_fields(table_id)
        return self._field_map.get(field_name)
```

---

*文档版本: v1.0 | 配套代码: `core/utils/feishu_base.py`*