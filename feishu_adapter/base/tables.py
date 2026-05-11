"""
飞书Bitable表Schema定义

基于 Tables_schema_v2.md 定义的7张表结构
字段类型映射：
- 文本 → 单行文本 (1)
- 多行文本 → 多行文本 (文本类型，但UI显示为多行)
- URL → 超链接 (15)
- 单选 → 单选 (3)
- 多选 → 多选 (4)
- 数字 → 数字 (2)
- 日期时间 → 日期 (5)
- 复选框 → 复选框 (7)

注：飞书Base没有JSON字段，所有JSON配置用多行文本存储
"""

from typing import Dict, List, Tuple, Any


# 字段类型常量
FIELD_TYPE_TEXT = 1          # 单行文本
FIELD_TYPE_NUMBER = 2        # 数字
FIELD_TYPE_SINGLE_SELECT = 3 # 单选
FIELD_TYPE_MULTI_SELECT = 4  # 多选
FIELD_TYPE_DATETIME = 5      # 日期时间
FIELD_TYPE_CHECKBOX = 7      # 复选框
FIELD_TYPE_URL = 15          # 超链接
FIELD_TYPE_DOCUMENT = 22     # 文档（富文本）


def make_field(name: str, field_type: int, required: bool = False) -> Dict[str, Any]:
    """创建字段定义"""
    return {
        "name": name,
        "type": field_type,
        "required": required
    }


# =============================================================================
# 表1: 信源配置 (SRC)
# =============================================================================

SOURCE_CONFIG_FIELDS: List[Dict[str, Any]] = [
    make_field("id", FIELD_TYPE_TEXT, required=True),              # 业务ID: SRC-YYYYMMDD-NNN
    make_field("信源名称", FIELD_TYPE_TEXT, required=True),         # 例: "arXiv cs.AI"
    make_field("平台", FIELD_TYPE_SINGLE_SELECT, required=True),    # arXiv/HackerNews/GitHub/Reddit/小红书/抖音/X
    make_field("类型", FIELD_TYPE_SINGLE_SELECT, required=True),    # 真实爬虫/Mock数据
    make_field("配置JSON", FIELD_TYPE_TEXT, required=True),         # 平台特定配置，JSON字符串
    make_field("每次抓取上限", FIELD_TYPE_NUMBER, required=True),   # 单次最多抓多少条
    make_field("是否启用", FIELD_TYPE_CHECKBOX, required=True),     # 复选框
    make_field("优先级", FIELD_TYPE_NUMBER, required=True),         # 1-10
    make_field("创建时间", FIELD_TYPE_DATETIME, required=True),     # 日期时间
]

SOURCE_CONFIG_SEED_DATA = [
    {
        "id": "SRC-20260504-001",
        "信源名称": "arXiv cs.AI",
        "平台": "arXiv",
        "类型": "真实爬虫",
        "配置JSON": '{"category": "cs.AI", "sort_by": "submittedDate"}',
        "每次抓取上限": 5,
        "是否启用": True,
        "优先级": 9,
        "创建时间": "2026-05-01T00:00:00",
    },
    {
        "id": "SRC-20260504-002",
        "信源名称": "HackerNews AI板块",
        "平台": "HackerNews",
        "类型": "真实爬虫",
        "配置JSON": '{"keywords": ["AI", "LLM", "GPT"]}',
        "每次抓取上限": 5,
        "是否启用": True,
        "优先级": 8,
        "创建时间": "2026-05-01T00:00:00",
    },
    {
        "id": "SRC-20260504-003",
        "信源名称": "GitHub Trending",
        "平台": "GitHub",
        "类型": "真实爬虫",
        "配置JSON": '{"language": "python", "since": "daily", "topics": ["llm", "agent"]}',
        "每次抓取上限": 5,
        "是否启用": True,
        "优先级": 7,
        "创建时间": "2026-05-01T00:00:00",
    },
    {
        "id": "SRC-20260504-004",
        "信源名称": "Reddit r/LocalLLaMA",
        "平台": "Reddit",
        "类型": "真实爬虫",
        "配置JSON": '{"subreddit": "LocalLLaMA", "sort": "hot"}',
        "每次抓取上限": 5,
        "是否启用": False,
        "优先级": 6,
        "创建时间": "2026-05-01T00:00:00",
    },
    {
        "id": "SRC-20260504-005",
        "信源名称": "小红书AI爆款",
        "平台": "小红书",
        "类型": "Mock数据",
        "配置JSON": '{"file": "mock_data/xiaohongshu_hot.json"}',
        "每次抓取上限": 10,
        "是否启用": True,
        "优先级": 5,
        "创建时间": "2026-05-01T00:00:00",
    },
    {
        "id": "SRC-20260504-006",
        "信源名称": "抖音AI爆款",
        "平台": "抖音",
        "类型": "Mock数据",
        "配置JSON": '{"file": "mock_data/douyin_hot.json"}',
        "每次抓取上限": 10,
        "是否启用": True,
        "优先级": 5,
        "创建时间": "2026-05-01T00:00:00",
    },
    {
        "id": "SRC-20260504-007",
        "信源名称": "X AI圈",
        "平台": "X",
        "类型": "Mock数据",
        "配置JSON": '{"file": "mock_data/x_hot.json"}',
        "每次抓取上限": 10,
        "是否启用": True,
        "优先级": 4,
        "创建时间": "2026-05-01T00:00:00",
    },
]


# =============================================================================
# 表2: 热帖库 (TREND)
# =============================================================================

TREND_FIELDS: List[Dict[str, Any]] = [
    make_field("id", FIELD_TYPE_TEXT, required=True),               # 业务ID: TREND-YYYYMMDD-NNN
    make_field("信源ID", FIELD_TYPE_TEXT, required=True),           # 引用 SRC.id
    make_field("信源平台", FIELD_TYPE_SINGLE_SELECT, required=True), # 冗余字段，方便筛选
    make_field("标题", FIELD_TYPE_TEXT, required=True),             # 帖子原标题
    make_field("原文链接", FIELD_TYPE_URL, required=True),          # 原帖URL
    make_field("原文摘要", FIELD_TYPE_TEXT, required=True),         # 完整原文/摘要（限500字）
    make_field("原文语言", FIELD_TYPE_SINGLE_SELECT, required=True), # 中文/英文
    make_field("主题标签", FIELD_TYPE_MULTI_SELECT, required=True),  # LLM自动打标签
    make_field("阅览量", FIELD_TYPE_NUMBER),                        # 原平台数据
    make_field("互动量", FIELD_TYPE_NUMBER),                        # 点赞+评论+转发
    make_field("发布时间", FIELD_TYPE_DATETIME, required=True),     # 原帖发布时间
    make_field("抓取时间", FIELD_TYPE_DATETIME, required=True),     # 自动
    make_field("热度评分", FIELD_TYPE_NUMBER, required=True),       # 0-1，小哨用LLM打分
    make_field("内容质量", FIELD_TYPE_SINGLE_SELECT, required=True), # 高/中/低
    make_field("状态", FIELD_TYPE_SINGLE_SELECT, required=True),    # 待选/已选/已弃
]


# =============================================================================
# 表3: 选题库 (TOPIC) - 核心枢纽
# =============================================================================

TOPIC_FIELDS: List[Dict[str, Any]] = [
    make_field("id", FIELD_TYPE_TEXT, required=True),               # 业务ID: TOPIC-YYYYMMDD-NNN
    make_field("选题标题", FIELD_TYPE_TEXT, required=True),         # 一句话选题
    make_field("选题角度", FIELD_TYPE_TEXT, required=True),         # 200字内说明切入角度
    make_field("预估爆点", FIELD_TYPE_TEXT, required=True),         # LLM分析：为什么这个选题会爆
    make_field("预估受众", FIELD_TYPE_TEXT, required=True),         # 目标受众分析
    make_field("关联热帖IDs", FIELD_TYPE_TEXT, required=True),      # JSON数组，例 ["TREND-20260504-003"]
    make_field("KOC人设ID", FIELD_TYPE_TEXT, required=True),        # 引用 KOC.id，默认 KOC-001
    make_field("推荐优先级", FIELD_TYPE_NUMBER, required=True),     # 1-10，小编按这个排序
    make_field("状态", FIELD_TYPE_TEXT, required=True),    # 待选/已选/生产中/审改中/待发布/已发布/已弃
    make_field("生产开始时间", FIELD_TYPE_DATETIME),                # 状态变"生产中"时填
    make_field("生产完成时间", FIELD_TYPE_DATETIME),                # 状态变"审改中"时填
    make_field("发布完成时间", FIELD_TYPE_DATETIME),                # 状态变"已发布"时填
    make_field("帖子文档链接", FIELD_TYPE_URL),                    # 飞书Docx链接 - 小文创建
    make_field("配图方案文档链接", FIELD_TYPE_URL),                # 飞书Docx链接 - 小图创建
    make_field("视频脚本文档链接", FIELD_TYPE_URL),                # 飞书Docx链接 - 小播创建
    make_field("审改文档链接", FIELD_TYPE_URL),                    # 飞书Docx链接 - 小审/小改维护
    make_field("审改轮次", FIELD_TYPE_NUMBER, required=True),       # 默认0，每轮+1，max 3
    make_field("审改最终状态", FIELD_TYPE_SINGLE_SELECT),           # 通过/卡死/待人工
    make_field("分发计划JSON", FIELD_TYPE_TEXT),                    # 小发产出，存平台×时间×版本
    make_field("数据回流ID", FIELD_TYPE_TEXT),                      # 引用 DATA.id，发布后小数填
    make_field("创建时间", FIELD_TYPE_DATETIME, required=True),     # 自动
    make_field("创建者Agent", FIELD_TYPE_TEXT, required=True), # 默认"小编 TopicCurator"
]


# =============================================================================
# 表4: 数据库 (DATA)
# =============================================================================

DATA_FIELDS: List[Dict[str, Any]] = [
    make_field("id", FIELD_TYPE_TEXT, required=True),               # 业务ID: DATA-YYYYMMDD-NNN
    make_field("选题ID", FIELD_TYPE_TEXT, required=True),           # 引用 TOPIC.id
    make_field("选题标题", FIELD_TYPE_TEXT, required=True),         # 冗余字段
    # 公众号指标
    make_field("公众号_阅读量", FIELD_TYPE_NUMBER),
    make_field("公众号_点赞数", FIELD_TYPE_NUMBER),
    make_field("公众号_在看数", FIELD_TYPE_NUMBER),
    # 小红书指标
    make_field("小红书_阅读量", FIELD_TYPE_NUMBER),
    make_field("小红书_点赞数", FIELD_TYPE_NUMBER),
    make_field("小红书_收藏数", FIELD_TYPE_NUMBER),
    make_field("小红书_评论数", FIELD_TYPE_NUMBER),
    # 抖音指标
    make_field("抖音_播放量", FIELD_TYPE_NUMBER),
    make_field("抖音_点赞数", FIELD_TYPE_NUMBER),
    make_field("抖音_评论数", FIELD_TYPE_NUMBER),
    # B站指标
    make_field("B站_播放量", FIELD_TYPE_NUMBER),
    make_field("B站_点赞数", FIELD_TYPE_NUMBER),
    make_field("B站_投币数", FIELD_TYPE_NUMBER),
    # 综合分析
    make_field("综合评分", FIELD_TYPE_NUMBER, required=True),       # 0-1，小数计算
    make_field("爆点验证", FIELD_TYPE_SINGLE_SELECT, required=True), # 验证成功/部分验证/未爆
    make_field("经验文档链接", FIELD_TYPE_URL),                    # 飞书Docx链接 - 小数创建
    make_field("数据分析文档链接", FIELD_TYPE_URL),                # 飞书Docx链接 - 小数创建
    make_field("数据采集时间", FIELD_TYPE_DATETIME, required=True), # 自动
    make_field("数据状态", FIELD_TYPE_SINGLE_SELECT, required=True), # 初次采集/已迭代分析/已沉淀经验
]


# =============================================================================
# 表5: KOC人设 (KOC)
# =============================================================================

KOC_FIELDS: List[Dict[str, Any]] = [
    make_field("id", FIELD_TYPE_TEXT, required=True),               # 业务ID: KOC-NNN（不带日期）
    make_field("人设名称", FIELD_TYPE_TEXT, required=True),         # 例: "学AI的刘同学"
    make_field("人设简介", FIELD_TYPE_TEXT, required=True),         # 一句话简介
    make_field("基础设定JSON", FIELD_TYPE_TEXT, required=True),     # 身份/职业/年龄/城市等
    make_field("语言风格JSON", FIELD_TYPE_TEXT, required=True),     # 语气/口头禅/emoji使用等
    make_field("内容偏好JSON", FIELD_TYPE_TEXT, required=True),     # 偏爱内容结构/中文爆款偏好等
    make_field("平台策略JSON", FIELD_TYPE_TEXT, required=True),     # 平台差异化策略
    make_field("是否默认", FIELD_TYPE_CHECKBOX, required=True),     # 是否默认人设
    make_field("创建时间", FIELD_TYPE_DATETIME, required=True),     # 自动
]

KOC_SEED_DATA = [
    {
        "id": "KOC-001",
        "人设名称": "学AI的刘同学",
        "人设简介": "一个正在学习AI的产品经理，喜欢分享实用的AI工具和技巧",
        "基础设定JSON": '{"身份": "产品经理", "年龄": "28岁", "城市": "北京"}',
        "语言风格JSON": '{"语气": "亲切友好", "口头禅": "说实话", "emoji": "适度使用"}',
        "内容偏好JSON": '{"结构": "问题-方案-案例", "偏好": "实用工具/效率提升"}',
        "平台策略JSON": '{"公众号": "深度长文", "小红书": "图文笔记", "抖音": "短视频", "B站": "教程视频"}',
        "是否默认": True,
        "创建时间": "2026-05-01T00:00:00",
    }
]


# =============================================================================
# 表6: Agent花名册 (EMP)
# =============================================================================

EMP_FIELDS: List[Dict[str, Any]] = [
    make_field("id", FIELD_TYPE_TEXT, required=True),               # 业务ID: EMP-NNN（不带日期）
    make_field("花名", FIELD_TYPE_TEXT, required=True),             # 例: "小哨"
    make_field("英文代号", FIELD_TYPE_TEXT, required=True),         # 例: "TrendScout"
    make_field("部门", FIELD_TYPE_SINGLE_SELECT, required=True),    # 信息组/决策组/生产组/治理组/复盘
    make_field("职责描述", FIELD_TYPE_TEXT, required=True),         # 主要职责
    make_field("输入", FIELD_TYPE_TEXT, required=True),             # 接收什么输入
    make_field("输出", FIELD_TYPE_TEXT, required=True),             # 产出什么输出
    make_field("调用模型", FIELD_TYPE_TEXT),                        # 使用的LLM模型
    make_field("系统提示词", FIELD_TYPE_TEXT),                      # 系统prompt摘要
    make_field("是否启用", FIELD_TYPE_CHECKBOX, required=True),     # 是否启用
    make_field("创建时间", FIELD_TYPE_DATETIME, required=True),     # 自动
]

EMP_SEED_DATA = [
    {"id": "EMP-001", "花名": "小哨", "英文代号": "TrendScout", "部门": "信息组", "职责描述": "监控各平台AI相关热帖，抓取并结构化存储", "输入": "信源配置", "输出": "热帖库记录", "调用模型": "Doubao-pro-32k", "系统提示词": "", "是否启用": True, "创建时间": "2026-05-01T00:00:00"},
    {"id": "EMP-002", "花名": "小编", "英文代号": "TopicCurator", "部门": "决策组", "职责描述": "从热帖库筛选选题，评估爆点潜力", "输入": "热帖库", "输出": "选题库记录", "调用模型": "Doubao-pro-32k", "系统提示词": "", "是否启用": True, "创建时间": "2026-05-01T00:00:00"},
    {"id": "EMP-003", "花名": "小文", "英文代号": "ContentWriter", "部门": "生产组", "职责描述": "撰写图文内容（公众号/小红书）", "输入": "选题库记录", "输出": "帖子内容", "调用模型": "Doubao-pro-128k", "系统提示词": "", "是否启用": True, "创建时间": "2026-05-01T00:00:00"},
    {"id": "EMP-004", "花名": "小图", "英文代号": "VisualDesigner", "部门": "生产组", "职责描述": "生成配图和信息图", "输入": "选题库记录", "输出": "配图链接", "调用模型": "Doubao-lite-32k", "系统提示词": "", "是否启用": True, "创建时间": "2026-05-01T00:00:00"},
    {"id": "EMP-005", "花名": "小播", "英文代号": "ScriptWriter", "部门": "生产组", "职责描述": "撰写视频脚本（抖音/B站）", "输入": "选题库记录", "输出": "视频脚本内容", "调用模型": "Doubao-pro-32k", "系统提示词": "", "是否启用": True, "创建时间": "2026-05-01T00:00:00"},
    {"id": "EMP-006", "花名": "小审", "英文代号": "Reviewer", "部门": "治理组", "职责描述": "审查内容质量，提出修改意见", "输入": "帖子内容/视频脚本", "输出": "审改意见", "调用模型": "Doubao-pro-32k", "系统提示词": "", "是否启用": True, "创建时间": "2026-05-01T00:00:00"},
    {"id": "EMP-007", "花名": "小改", "英文代号": "Editor", "部门": "治理组", "职责描述": "根据审改意见修改内容", "输入": "审改意见", "输出": "修改后内容", "调用模型": "Doubao-pro-32k", "系统提示词": "", "是否启用": True, "创建时间": "2026-05-01T00:00:00"},
    {"id": "EMP-008", "花名": "小发", "英文代号": "Distributor", "部门": "治理组", "职责描述": "制定分发计划，mock发布", "输入": "已通过审查的内容", "输出": "分发计划JSON", "调用模型": "Doubao-lite-32k", "系统提示词": "", "是否启用": True, "创建时间": "2026-05-01T00:00:00"},
    {"id": "EMP-009", "花名": "小数", "英文代号": "Analyst", "部门": "复盘", "职责描述": "追踪内容表现，沉淀经验", "输入": "已发布内容", "输出": "数据分析/经验总结", "调用模型": "Doubao-pro-128k", "系统提示词": "", "是否启用": True, "创建时间": "2026-05-01T00:00:00"},
]


# =============================================================================
# 表7: Agent协作日志 (LOG)
# =============================================================================

LOG_FIELDS: List[Dict[str, Any]] = [
    make_field("id", FIELD_TYPE_TEXT, required=True),               # 业务ID: LOG-YYYYMMDD-NNN
    make_field("AgentID", FIELD_TYPE_TEXT, required=True),          # 引用 EMP.id
    make_field("Agent花名", FIELD_TYPE_TEXT, required=True),        # 冗余字段，方便查看
    make_field("任务类型", FIELD_TYPE_SINGLE_SELECT, required=True), # 信源抓取/选题筛选/内容撰写/配图生成/脚本撰写/内容审查/内容修改/分发计划/数据分析
    make_field("关联业务ID", FIELD_TYPE_TEXT),                      # 关联的TOPIC/TREND等ID
    make_field("输入摘要", FIELD_TYPE_TEXT, required=True),         # 输入内容摘要
    make_field("输出摘要", FIELD_TYPE_TEXT, required=True),         # 输出内容摘要
    make_field("执行状态", FIELD_TYPE_SINGLE_SELECT, required=True), # 成功/失败/重试中
    make_field("耗时秒数", FIELD_TYPE_NUMBER),                      # 任务执行耗时
    make_field("Token消耗", FIELD_TYPE_NUMBER),                     # LLM调用token数
    make_field("错误信息", FIELD_TYPE_TEXT),                        # 失败时的错误信息
    make_field("执行时间", FIELD_TYPE_DATETIME, required=True),     # 自动
]


# =============================================================================
# 表配置汇总
# =============================================================================

TABLES: Dict[str, Dict[str, Any]] = {
    "信源配置": {
        "prefix": "SRC",
        "fields": SOURCE_CONFIG_FIELDS,
        "seed_data": SOURCE_CONFIG_SEED_DATA,
    },
    "热帖库": {
        "prefix": "TREND",
        "fields": TREND_FIELDS,
    },
    "选题库": {
        "prefix": "TOPIC",
        "fields": TOPIC_FIELDS,
    },
    "数据库": {
        "prefix": "DATA",
        "fields": DATA_FIELDS,
    },
    "KOC人设": {
        "prefix": "KOC",
        "fields": KOC_FIELDS,
        "seed_data": KOC_SEED_DATA,
    },
    "Agent花名册": {
        "prefix": "EMP",
        "fields": EMP_FIELDS,
        "seed_data": EMP_SEED_DATA,
    },
    "Agent协作日志": {
        "prefix": "LOG",
        "fields": LOG_FIELDS,
    },
}


def get_table_fields(table_name: str) -> List[Dict[str, Any]]:
    """
    获取指定表的字段定义

    Args:
        table_name: 中文表名

    Returns:
        字段定义列表
    """
    table_config = TABLES.get(table_name)
    if not table_config:
        raise ValueError(f"未知的表名: {table_name}")
    return table_config["fields"]


def get_table_prefix(table_name: str) -> str:
    """
    获取指定表的ID前缀

    Args:
        table_name: 中文表名

    Returns:
        ID前缀，如 "SRC", "TREND" 等
    """
    table_config = TABLES.get(table_name)
    if not table_config:
        raise ValueError(f"未知的表名: {table_name}")
    return table_config["prefix"]


def get_seed_data(table_name: str) -> List[Dict[str, Any]]:
    """
    获取指定表的种子数据

    Args:
        table_name: 中文表名

    Returns:
        种子数据列表，如果没有则返回空列表
    """
    table_config = TABLES.get(table_name)
    if not table_config:
        raise ValueError(f"未知的表名: {table_name}")
    return table_config.get("seed_data", [])
