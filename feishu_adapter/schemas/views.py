"""飞书多维表格视图配置。"""

VIEWS = {
    "信息源配置": [
        {"view_name": "全部信息源", "view_type": "grid"},
    ],
    "原始信息": [
        {"view_name": "按来源分组", "view_type": "grid"},
        {"view_name": "时间线", "view_type": "grid"},
    ],
    "爆点分析": [
        {"view_name": "按分数排序", "view_type": "grid"},
    ],
    "选题库": [
        {"view_name": "看板视图", "view_type": "kanban"},
        {"view_name": "按优先级", "view_type": "grid"},
    ],
    "内容草稿": [
        {"view_name": "审核看板", "view_type": "kanban"},
    ],
    "分发计划": [
        {"view_name": "日历视图", "view_type": "grid"},
    ],
    "数据看板": [
        {"view_name": "数据总览", "view_type": "grid"},
    ],
}
