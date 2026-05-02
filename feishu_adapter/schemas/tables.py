"""10 张业务表的 Schema 定义。

每张表定义为字典，key 为字段名，value 为飞书多维表格字段类型。
bootstrap 脚本读取这些 schema 自动建表。
"""

# 字段类型常量
TEXT = 1        # 多行文本
NUMBER = 2     # 数字
SELECT = 3     # 单选
MULTI_SELECT = 4  # 多选
DATE = 5       # 日期
CHECKBOX = 7   # 复选框
URL = 15       # 超链接
ATTACHMENT = 17  # 附件

TABLES = {
    "信息源配置": {
        "fields": [
            {"field_name": "源名称", "type": TEXT},
            {"field_name": "类型", "type": SELECT},
            {"field_name": "URL", "type": URL},
            {"field_name": "启用", "type": CHECKBOX},
            {"field_name": "抓取频率", "type": SELECT},
        ],
    },
    "原始信息": {
        "fields": [
            {"field_name": "标题", "type": TEXT},
            {"field_name": "来源", "type": SELECT},
            {"field_name": "链接", "type": URL},
            {"field_name": "摘要", "type": TEXT},
            {"field_name": "采集时间", "type": DATE},
        ],
    },
    "爆点分析": {
        "fields": [
            {"field_name": "标题", "type": TEXT},
            {"field_name": "爆点分数", "type": NUMBER},
            {"field_name": "爆点理由", "type": TEXT},
            {"field_name": "推荐平台", "type": MULTI_SELECT},
        ],
    },
    "选题库": {
        "fields": [
            {"field_name": "选题标题", "type": TEXT},
            {"field_name": "切入角度", "type": TEXT},
            {"field_name": "目标平台", "type": SELECT},
            {"field_name": "状态", "type": SELECT},
            {"field_name": "优先级", "type": NUMBER},
        ],
    },
    "内容草稿": {
        "fields": [
            {"field_name": "选题", "type": TEXT},
            {"field_name": "平台", "type": SELECT},
            {"field_name": "正文", "type": TEXT},
            {"field_name": "审核状态", "type": SELECT},
            {"field_name": "审核意见", "type": TEXT},
        ],
    },
    "视觉素材": {
        "fields": [
            {"field_name": "关联内容", "type": TEXT},
            {"field_name": "类型", "type": SELECT},
            {"field_name": "图片", "type": ATTACHMENT},
            {"field_name": "Prompt", "type": TEXT},
        ],
    },
    "短视频脚本": {
        "fields": [
            {"field_name": "选题", "type": TEXT},
            {"field_name": "脚本正文", "type": TEXT},
            {"field_name": "时长", "type": TEXT},
            {"field_name": "分镜描述", "type": TEXT},
        ],
    },
    "分发计划": {
        "fields": [
            {"field_name": "内容标题", "type": TEXT},
            {"field_name": "平台", "type": SELECT},
            {"field_name": "发布时间", "type": DATE},
            {"field_name": "状态", "type": SELECT},
        ],
    },
    "数据看板": {
        "fields": [
            {"field_name": "内容标题", "type": TEXT},
            {"field_name": "平台", "type": SELECT},
            {"field_name": "阅读量", "type": NUMBER},
            {"field_name": "互动量", "type": NUMBER},
            {"field_name": "转化率", "type": NUMBER},
        ],
    },
    "KOC人设": {
        "fields": [
            {"field_name": "人设名称", "type": TEXT},
            {"field_name": "人设描述", "type": TEXT},
            {"field_name": "适用平台", "type": MULTI_SELECT},
            {"field_name": "语气风格", "type": TEXT},
        ],
    },
}
