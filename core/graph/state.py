"""LangGraph 共享 State 定义。"""

from typing import Annotated

from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    """单条新闻信息。"""
    source: str = ""
    title: str = ""
    url: str = ""
    summary: str = ""
    raw_content: str = ""
    hook_score: float = 0.0
    hook_reason: str = ""


class TopicPlan(BaseModel):
    """选题方案。"""
    title: str = ""
    angle: str = ""
    target_platform: str = ""
    news_items: list[str] = Field(default_factory=list)


class ContentDraft(BaseModel):
    """内容草稿。"""
    topic_title: str = ""
    platform: str = ""
    body: str = ""
    review_status: str = "pending"
    review_comments: str = ""


class GraphState(BaseModel):
    """LangGraph 全局状态。"""
    # 采集阶段
    raw_news: list[NewsItem] = Field(default_factory=list)

    # 分析阶段
    scored_news: list[NewsItem] = Field(default_factory=list)

    # 选题阶段
    topics: list[TopicPlan] = Field(default_factory=list)

    # 创作阶段
    drafts: list[ContentDraft] = Field(default_factory=list)

    # 视觉阶段
    image_urls: list[str] = Field(default_factory=list)

    # 审核阶段
    approved_drafts: list[ContentDraft] = Field(default_factory=list)

    # 分发阶段
    distribution_plan: dict = Field(default_factory=dict)

    # 元信息
    current_step: str = ""
    errors: list[str] = Field(default_factory=list)
