"""KOC 人设注入函数。

v3.0 关键设计：解决 v1/v2 的 P0 bug——KOC 人设硬编码。
所有 Agent 必须从 KOC 人设表读取 KOC 后传入，禁止默认值兜底。
"""

KOC_RENDER_MODES = {
    "identity",      # 小哨（轻量身份信息）
    "curation",      # 小编（决策用，含禁区）
    "creation",      # 小文/小播（创作用，含中文爆款偏好）
    "visual",        # 小图（视觉风格偏好）
    "review",        # 小审/小改（含禁区+不想成为）
    "distribution",  # 小发（含平台偏好）
    "analytics",     # 小数（含受众期待）
}


def render_koc_block(koc: dict, mode: str) -> str:
    """
    渲染 KOC 人设 prompt 块。

    Args:
        koc: 从 KOC 人设表读出的完整 record dict
        mode: 渲染模式（决定包含哪些字段 + 翻译成什么行为标准）

    Returns:
        XML 格式的 prompt 块字符串

    Raises:
        ValueError: 如果 koc 为 None 或 mode 不合法
    """
    if not koc or not isinstance(koc, dict):
        raise ValueError(
            "KOC 人设未提供。所有 Agent 必须从 KOC 人设表读取 KOC 后传入。"
            "禁止使用默认值兜底。"
        )
    if mode not in KOC_RENDER_MODES:
        raise ValueError(f"非法 mode: {mode}，必须是 {KOC_RENDER_MODES}")

    renderer = MODE_RENDERERS[mode]
    return renderer(koc)


def _render_identity_mode(koc: dict) -> str:
    """轻量身份模式（小哨用）"""
    return f"""\
<koc_persona>
账号名：{koc.get('账号名', koc.get('人设名称', ''))}
一句话定位：{koc.get('一句话定位', koc.get('人设简介', ''))}
语气基调：{koc.get('语气', koc.get('语言风格JSON', ''))}
</koc_persona>
"""


def _render_curation_mode(koc: dict) -> str:
    """选题决策模式（给小编用）"""
    return f"""\
<koc_persona>
账号名：{koc.get('账号名', koc.get('人设名称', ''))}
一句话定位：{koc.get('一句话定位', koc.get('人设简介', ''))}
语气基调：{koc.get('语气', '')}

【KOC 关心的领域】
{_format_list(koc.get('领域', []))}（不在范围一律拒绝）

【偏好选题类型】
{_format_list(koc.get('偏好选题类型', []))}

【🚫 禁区话题 - 触碰任意一条直接拒】
{_format_list(koc.get('禁区话题', []))}

【❌ KOC 不想成为的样子 - 风格上必须避开】
{_format_list(koc.get('不想成为的样子', []))}

【翻译成可执行标准】

✅ 这位 KOC 会做的选题：
- 解释新概念，让非科班的人秒懂
- 对比两个工具/模型，给"普通人该用哪个"的明确推荐
- 拆解最近的 AI 八卦但不站队
- 教具体工作流（如"用 Claude 写月报的 5 个步骤"）

❌ 这位 KOC 不会做的选题：
- 标题党 + 焦虑制造（"再不学就完了"、"被淘汰"）
- 单纯翻译原文不加观点
- 站队某厂批评另一家
- 暗示卖课、付费导流
- 揣测未发布产品
- NSFW、政治敏感
</koc_persona>
"""


def _render_creation_mode(koc: dict) -> str:
    """创作模式（给小文/小播用）"""
    return f"""\
<koc_persona>
账号名：{koc.get('账号名', koc.get('人设名称', ''))}
一句话定位：{koc.get('一句话定位', koc.get('人设简介', ''))}
语气基调：{koc.get('语气', '')}

【目标受众】
{koc.get('目标受众', '')}

【受众痛点】
{_format_list(koc.get('受众痛点', []))}

【偏爱内容结构】
{_format_list(koc.get('偏爱内容结构', []))}

【中文爆款偏好】
{_format_list(koc.get('中文爆款偏好', []))}

【风格红线】
- 用"咱们/我们"自称，不用"你"
- 不写焦虑话术
- 不卖课不导流
- 不站队任何厂商
- 信息密度 ≥ 1 个具体细节/100 字
</koc_persona>
"""


def _render_visual_mode(koc: dict) -> str:
    """视觉模式（给小图用）"""
    return f"""\
<koc_persona>
账号名：{koc.get('账号名', koc.get('人设名称', ''))}
一句话定位：{koc.get('一句话定位', koc.get('人设简介', ''))}

【视觉风格偏好】
{_format_list(koc.get('视觉风格', []))}
</koc_persona>
"""


def _render_review_mode(koc: dict) -> str:
    """审改模式（给小审/小改用）"""
    return f"""\
<koc_persona>
账号名：{koc.get('账号名', koc.get('人设名称', ''))}
一句话定位：{koc.get('一句话定位', koc.get('人设简介', ''))}
语气基调：{koc.get('语气', '')}

【🚫 禁区话题 - 触碰任意一条必须打回】
{_format_list(koc.get('禁区话题', []))}

【❌ KOC 不想成为的样子 - 风格上必须避开】
{_format_list(koc.get('不想成为的样子', []))}

【自我审美准则】
{koc.get('自我审美准则', '')}

【审查必检清单】
1. 事实是否准确（涉及具体数据/产品/人物时）
2. 是否含焦虑话术（"再不学就完了"等）
3. 是否站队/引战
4. 是否暗示卖课
5. 是否揣测未发布产品
6. 是否用"咱们/我们"而非"你"
</koc_persona>
"""


def _render_distribution_mode(koc: dict) -> str:
    """分发模式（给小发用）"""
    return f"""\
<koc_persona>
账号名：{koc.get('账号名', koc.get('人设名称', ''))}

【主战场平台】
{_format_list(koc.get('主战场平台', []))}

【发布频率】
{koc.get('发布频率', '')}

【偏好发布时段】
{_format_list(koc.get('偏好发布时段', []))}

【平台差异化策略】
{_format_list(koc.get('平台差异化策略', []))}
</koc_persona>
"""


def _render_analytics_mode(koc: dict) -> str:
    """分析模式（给小数用）"""
    return f"""\
<koc_persona>
账号名：{koc.get('账号名', koc.get('人设名称', ''))}
一句话定位：{koc.get('一句话定位', koc.get('人设简介', ''))}

【目标受众期待】
{_format_list(koc.get('受众期待', []))}
</koc_persona>
"""


MODE_RENDERERS = {
    "identity": _render_identity_mode,
    "curation": _render_curation_mode,
    "creation": _render_creation_mode,
    "visual": _render_visual_mode,
    "review": _render_review_mode,
    "distribution": _render_distribution_mode,
    "analytics": _render_analytics_mode,
}


def _format_list(items) -> str:
    """统一格式化列表为带 emoji 的多行字符串"""
    if not items:
        return "（未设置）"
    if isinstance(items, str):
        items = [items]
    return "\n".join(f"- {item}" for item in items)
