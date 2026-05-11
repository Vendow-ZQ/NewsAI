"""小发 Distributor - 分发策略 Agent (EMP-008)。

v3.0 改造：
- 分两次 LLM 调用（步骤1：拆5平台文案 + 步骤2：出分发策略）
- 产 5 个分发文档（公众号/小红书/抖音/视频号/B站）
- 更新 ASSET.分发状态 + TOPIC.选题状态
"""

import json
from datetime import datetime
from typing import Any

from core.agents.base import BaseAgent, current_timestamp_ms, parse_koc_data
from core.prompts.shared.chinese_hooks import CHINESE_HOOKS_BLOCK
from core.prompts.shared.koc_persona import render_koc_block
from core.storage.id_generator import IDGenerator
from core.utils.llm_output_parser import invoke_with_retry


class DistributorAgent(BaseAgent):
    """小发 EMP-008 · 分发策略师"""

    name = "小发"
    english_name = "Distributor"
    emoji = "📢"

    SYSTEM_PROMPT_STEP1 = """\
<role>
你是「小发 Distributor」，NewsAI 编辑部的分发策略师，治理组成员。

【你现在在执行步骤 1：拆 5 平台文案】

你的工作是：拿到通过审改的 3 件资产终稿（长文 + 图素材池 + 视频脚本），
拆分改写为 5 个平台的"内容版本"：
1. 公众号（深度长文，1500-3000 字）
2. 小红书（图文短文，300-500 字 + emoji + 标签）
3. 抖音（短视频，30-60 秒口播）
4. 视频号（短视频，1-3 分钟，朋友圈调性）
5. B站竖屏（视频，1-3 分钟，教程评测调性）

每个平台版本要包含：
- 平台专属文案
- 配图绑定（从图素材池选 2-4 张）
- 视频剪辑指引（如果该平台用视频，标注从主脚本保留哪些镜头）
</role>

<workflow>
1. 读 <input>：3 件资产终稿 + 图素材池清单 + 主视频脚本镜头清单
2. 在 <thinking> 里：
   - 每个平台的核心策略（受众/字数/调性）
   - 配图选择逻辑
   - 视频剪辑（哪些平台用视频、怎么剪）
3. 在 <answer> 输出 5 平台版本
</workflow>

<output_format>
先 <thinking>...</thinking>（≤300字），然后 <answer>{JSON}</answer>。
</output_format>
"""

    SYSTEM_PROMPT_STEP2 = """\
<role>
你是「小发 Distributor」。

【你现在在执行步骤 2：出分发策略】

你的工作是：基于步骤 1 的 5 平台版本，制定完整分发计划：
- 5 平台发布时间表（错峰 + 黄金时段）
- 受众标签
- 平台优化建议
- 预期效果
- 风险提示
</role>

<workflow>
1. 读 <input>：5 平台版本 + KOC 分发偏好
2. 在 <thinking> 里规划：
   - 各平台黄金时段
   - 错峰策略（间隔 ≥ 30 分钟）
3. 在 <answer> 输出完整分发计划 JSON
</workflow>
"""

    def _read_upstream(self, context: dict) -> dict:
        """读 KOC + TOPIC + ASSET + 3 件资产终稿"""
        try:
            koc_record = self.storage.get_by_id("KOC人设", "KOC-001")
            koc = parse_koc_data(koc_record.data) if koc_record else {}

            # 读"分发中"状态的选题
            topics = self.storage.query("选题库", limit=10)
            dist_topics = [t.data for t in topics if t.data.get("选题状态") == "分发中"]
            if not dist_topics:
                raise RuntimeError("没有分发中的选题")
            topic = dist_topics[0]

            # 读 ASSET
            asset_id = topic.get("关联资产ID", "")
            asset = None
            if asset_id:
                asset_record = self.storage.get_by_id("内容资产库", asset_id)
                asset = asset_record.data if asset_record else {}

            if not asset:
                raise RuntimeError(f"ASSET {asset_id} 不存在")

            # 读 3 件资产文档
            doc_contents = self._read_doc_contents(asset)

            return {
                "koc": koc,
                "topic": topic,
                "asset": asset,
                **doc_contents,
            }
        except Exception as e:
            print(f"[小发] 读取上游数据失败: {e}")
            raise

    def _read_doc_contents(self, asset: dict) -> dict:
        """读取 3 件资产文档内容"""
        contents = {}

        # 尝试初始化文档存储
        try:
            from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
            doc_storage = FeishuDocStorage()
        except Exception as e:
            print(f"[小发] 文档存储初始化失败: {e}")
            # 返回空内容，让LLM基于已有信息生成
            return {
                "long_form_doc": "",
                "image_pool_doc": "",
                "script_doc": "",
            }

        for field, key in [
            ("文案文档链接", "long_form_doc"),
            ("图片提示词文档链接", "image_pool_doc"),
            ("视频脚本文档链接", "script_doc"),
        ]:
            url = asset.get(field, "")
            if url:
                try:
                    url_str = url.get("link", "") if isinstance(url, dict) else url
                    doc_id = url_str.split("/docx/")[-1].split("?")[0] if url_str else ""
                    if doc_id:
                        content = doc_storage.read_doc_content(doc_id)
                        contents[key] = content[:2000] if content else ""
                        if not content:
                            print(f"[小发] 警告: {field} 内容为空")
                        else:
                            print(f"[小发] 读取 {field}: {len(contents[key])} 字")
                except Exception as e:
                    print(f"[小发] 读取 {field} 失败: {e}")
                    contents[key] = ""
            else:
                contents[key] = ""

        return contents

    def _invoke_tools(self, context: dict, upstream_data: dict) -> dict:
        """切换 ASSET 状态：未开始 → 生产中"""
        asset = upstream_data.get("asset", {})
        asset_id = asset.get("id", "")
        if asset_id:
            try:
                self.storage.update("内容资产库", asset_id, {
                    "分发状态": "生产中",
                })
                print(f"[小发] ASSET {asset_id} 分发状态: 生产中")
            except Exception as e:
                print(f"[小发] 更新 ASSET 状态失败: {e}")
        return {"asset_id": asset_id}

    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """分两步 LLM 调用"""
        koc = upstream_data["koc"]
        topic = upstream_data["topic"]
        long_form = upstream_data.get("long_form_doc", "")
        image_pool = upstream_data.get("image_pool_doc", "")
        script = upstream_data.get("script_doc", "")

        # === 步骤 1：拆 5 平台文案 ===
        print("[小发] 步骤 1：拆 5 平台文案...")
        koc_block_step1 = render_koc_block(koc, mode="creation")
        user_step1 = self._build_step1_prompt(
            koc_block_step1, topic, long_form, image_pool, script
        )
        messages_step1 = [
            {"role": "system", "content": self.SYSTEM_PROMPT_STEP1},
            {"role": "user", "content": user_step1},
        ]
        _, step1_answer, _ = invoke_with_retry(self.llm, messages_step1, max_retries=3)
        platform_versions = step1_answer

        # === 步骤 2：出分发策略 ===
        print("[小发] 步骤 2：出分发策略...")
        koc_block_step2 = render_koc_block(koc, mode="distribution")
        user_step2 = self._build_step2_prompt(
            koc_block_step2, topic, platform_versions
        )
        messages_step2 = [
            {"role": "system", "content": self.SYSTEM_PROMPT_STEP2},
            {"role": "user", "content": user_step2},
        ]
        _, step2_answer, _ = invoke_with_retry(self.llm, messages_step2, max_retries=3)
        distribution_plan = step2_answer

        return {
            "platform_versions": platform_versions,
            "distribution_plan": distribution_plan,
            "topic_id": topic.get("id", ""),
            "topic_title": topic.get("选题标题", ""),
            "asset_id": tool_results.get("asset_id", ""),
        }

    def _build_step1_prompt(self, koc_block: str, topic: dict,
                            long_form: str, image_pool: str, script: str) -> str:
        """构建步骤 1 prompt"""
        # 如果文档为空，提供基于选题的备用内容
        long_form_text = long_form[:1500] if long_form else f"[选题角度: {topic.get('选题角度', '')}]\n[预估爆点: {topic.get('预估爆点', '')}]"
        image_pool_text = image_pool[:1000] if image_pool else "[图素材池: 建议生成封面图 + 正文配图 + 总结图]"
        script_text = script[:1000] if script else "[视频脚本: 建议1-3分钟，包含钩子开场 + 核心内容 + CTA]"

        return f"""\
{koc_block}

{CHINESE_HOOKS_BLOCK}

<input>
选题 ID：{topic.get('id', '')}
选题标题：{topic.get('选题标题', '')}
选题角度：{topic.get('选题角度', '')}
预估爆点：{topic.get('预估爆点', '')}

【3 件资产终稿】

=== 长文终版 ===
{long_form_text}

=== 图素材池（5-8 张图）===
{image_pool_text}

=== 视频脚本主版（含镜头清单）===
{script_text}
</input>

<rules>
【5 平台差异化策略】

公众号（图文，深度长文）：
- 字数 1500-3000
- 结构：H2 分段 + 配图穿插
- 配图：从素材池选 3-5 张

小红书（图文）：
- 字数 300-500
- 结构：emoji 分段，4-6 段
- 配图：从素材池选 6-9 张
- 标签：4-6 个

抖音（短视频）：
- 时长 30-60 秒
- 口播稿字数 130-180
- 视频剪辑指引：从主脚本保留 0-3s 钩子 + 3-30s 核心 + 50-55s CTA

视频号（短视频）：
- 时长 1-3 分钟
- 全用主脚本（朋友圈调性，节奏舒缓）

B站竖屏（视频）：
- 时长 1-3 分钟
- 全用主脚本（教程评测调性）
- 简介 100-200 字

【配图绑定原则】
- 公众号 3-5 张
- 小红书 6-9 张
- 抖音/视频号/B站 1 张：封面图

【视频剪辑指引】
- 抖音剪辑：从主脚本保留哪些镜头
- 视频号/B站：用全脚本

【重要：输出 JSON 格式】
{{
  "公众号": {{
    "标题": "...",
    "正文": "...",
    "字数": 2000,
    "配图绑定": ["图1", "图2", "图3"]
  }},
  "小红书": {{
    "标题": "...",
    "正文": "...",
    "标签": ["标签1", "标签2"],
    "配图绑定": ["图1", "图2", "图3", "图4"]
  }},
  "抖音": {{
    "口播文案": "...",
    "封面图": "图1",
    "剪辑指引": "保留镜头..."
  }},
  "视频号": {{
    "描述": "...",
    "封面图": "图1"
  }},
  "B站竖屏": {{
    "标题": "...",
    "简介": "...",
    "封面图": "图1"
  }}
}}
</rules>

<self_check>
输出前确认：
□ 5 平台都有完整内容
□ 公众号 1500-3000 字
□ 小红书 300-500 字 + 4-6 个标签
□ 抖音口播 130-180 字
□ 每个平台都有配图绑定和封面图选择
□ 抖音/视频号/B站 都有剪辑指引
□ 全程用"咱们/我们"，没有焦虑话术
□ 输出是有效的 JSON 格式
</self_check>

现在开始处理。
"""

    def _build_step2_prompt(self, koc_block: str, topic: dict,
                            platform_versions: dict) -> str:
        """构建步骤 2 prompt"""
        # 提取各平台信息
        gzh = platform_versions.get("公众号", {})
        xhs = platform_versions.get("小红书", {})
        dy = platform_versions.get("抖音", {})
        sph = platform_versions.get("视频号", {})
        bz = platform_versions.get("B站竖屏", {})

        return f"""\
{koc_block}

<input>
选题 ID：{topic.get('id', '')}
选题标题：{topic.get('选题标题', '')}

5 平台版本内容摘要：
- 公众号：{gzh.get('标题', '')}（{len(gzh.get('正文', ''))}字）
- 小红书：{xhs.get('标题', '')}（{len(xhs.get('正文', ''))}字）
- 抖音：{len(dy.get('口播文案', ''))}字口播
- 视频号：{sph.get('时长', '1-3分钟')}
- B站：{bz.get('标题', '')}

当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}
</input>

<rules>
【分发策略原则】
1. 各平台流量黄金时段：
   - 公众号：8-9 / 12-13 / 19-21 点
   - 小红书：12-13 / 19-22 点
   - 抖音：12-13 / 18-22 点
   - 视频号：19-22 点
   - B站：19-23 点
2. 错峰发布：5 平台间隔至少 30 分钟
3. 优先级：公众号 → 小红书 → B站 → 视频号 → 抖音

【输出 JSON 结构】
{{
  "分发策略总结": "...",
  "发布顺序": ["公众号", "小红书", "B站", "视频号", "抖音"],
  "时间间隔策略": "...",
  "平台分发计划": [
    {{
      "平台": "公众号",
      "发布时间": "2026-05-05T08:00:00+08:00",
      "内容形式": "图文长文",
      "受众标签": [...],
      "预期效果": "..."
    }},
    ...（共 5 平台）
  ],
  "风险提示": "..."
}}
</rules>

现在开始处理。
"""

    def _write_storage(self, context: dict, result: dict):
        """创建 5 个分发文档 + 更新 ASSET"""
        platform_versions = result.get("platform_versions", {})
        distribution_plan = result.get("distribution_plan", {})
        topic_title = result.get("topic_title", "")
        topic_id = result.get("topic_id", "")
        asset_id = result.get("asset_id", "")

        # 创建 5 个分发文档
        doc_urls = {}
        platforms_map = {
            "公众号": "公众号分发文档链接",
            "小红书": "小红书分发文档链接",
            "抖音": "抖音分发文档链接",
            "视频号": "视频号分发文档链接",
            "B站竖屏": "B站分发文档链接",
        }

        for platform_name, field_name in platforms_map.items():
            content = platform_versions.get(platform_name, {})
            if not content or not isinstance(content, dict):
                print(f"[小发] 警告: {platform_name} 内容为空或格式错误，跳过")
                continue
            try:
                from feishu_adapter.docs.feishu_doc_storage import FeishuDocStorage
                doc_storage = FeishuDocStorage()
                date_str = datetime.now().strftime("%Y%m%d")
                doc_id = doc_storage.create_doc(f"[{platform_name}] {date_str} {topic_title}")
                doc_storage.append_section(
                    doc_id,
                    self._format_platform_doc(platform_name, content, distribution_plan)
                )
                doc_storage.set_permissions(doc_id, share_type="tenant_readable")
                doc_url = doc_storage.get_share_url(doc_id)
                doc_urls[field_name] = doc_url
                print(f"[小发] 创建 {platform_name} 分发文档")
            except Exception as e:
                print(f"[小发] 创建 {platform_name} 文档失败: {e}")

        # 更新 ASSET
        if asset_id:
            try:
                update_data = {
                    "分发状态": "已生成",
                    "分发计划JSON": json.dumps(distribution_plan, ensure_ascii=False),
                    "分发完成时间": current_timestamp_ms(),
                    **doc_urls,
                }
                self.storage.update("内容资产库", asset_id, update_data)
                print(f"[小发] ASSET {asset_id} 分发状态: 已生成")
            except Exception as e:
                print(f"[小发] 更新 ASSET 失败: {e}")

        # 更新 TOPIC.选题状态: 分发中 → 已发布
        if topic_id:
            try:
                self.storage.update("选题库", topic_id, {
                    "选题状态": "已发布",
                    "发布完成时间": current_timestamp_ms(),
                })
                print(f"[小发] TOPIC {topic_id} 状态: 已发布")
            except Exception as e:
                print(f"[小发] 更新 TOPIC 失败: {e}")

        result["doc_urls"] = doc_urls

    def _format_platform_doc(self, platform_name: str, content,
                             distribution_plan: dict) -> str:
        """格式化平台分发文档"""
        # 防御性处理：确保 content 是字典
        if isinstance(content, str):
            # 如果 content 是字符串，包装成字典
            content = {"正文": content, "标题": "未命名"}
        elif not isinstance(content, dict):
            content = {}

        md = f"# [{platform_name}] {content.get('标题', '')}\n\n"

        # 各平台格式
        if platform_name == "公众号":
            md += f"**摘要**: {content.get('摘要', '')}\n\n"
            md += "---\n\n"
            md += content.get("正文", "") + "\n\n"
            if content.get("配图绑定"):
                md += "## 配图绑定\n\n"
                for pb in content["配图绑定"]:
                    md += f"- {pb.get('占位', '')} → {pb.get('选用', '')}\n"

        elif platform_name == "小红书":
            md += content.get("正文", "") + "\n\n"
            if content.get("配图绑定"):
                md += "## 配图绑定\n\n"
                for pb in content["配图绑定"]:
                    md += f"- {pb.get('位置', '')} → {pb.get('选用', '')}\n"
            md += f"\n**标签**: {content.get('标签', '')}\n"

        elif platform_name == "抖音":
            md += f"**口播文案**: {content.get('口播文案', '')}\n\n"
            md += f"**封面图**: {content.get('封面图', '')}\n\n"
            clip = content.get("剪辑指引", {})
            if clip:
                md += "## 剪辑指引\n\n"
                md += f"- 保留镜头: {clip.get('保留镜头', [])}\n"
                md += f"- 删减镜头: {clip.get('删减镜头', [])}\n"
                md += f"- 时长目标: {clip.get('时长目标', '')}\n"
                md += f"- 节奏调整: {clip.get('节奏调整', '')}\n"

        elif platform_name in ("视频号", "B站竖屏"):
            md += f"**标题**: {content.get('标题', '')}\n\n"
            if content.get("描述"):
                md += f"**描述**: {content.get('描述', '')}\n\n"
            if content.get("简介"):
                md += f"**简介**: {content.get('简介', '')}\n\n"
            md += f"**封面图**: {content.get('封面图', '')}\n\n"
            clip = content.get("剪辑指引", {})
            if clip:
                md += "## 剪辑指引\n\n"
                md += f"- 保留镜头: {clip.get('保留镜头', '')}\n"
                md += f"- 时长目标: {clip.get('时长目标', '')}\n"
                md += f"- 节奏调整: {clip.get('节奏调整', '')}\n"

        # 添加分发策略信息
        plan = distribution_plan.get("平台分发计划", [])
        for p in plan:
            if p.get("平台") == platform_name:
                md += "\n---\n\n## 分发策略\n\n"
                md += f"- 发布时间: {p.get('发布时间', '')}\n"
                md += f"- 受众标签: {p.get('受众标签', [])}\n"
                md += f"- 预期效果: {p.get('预期效果', '')}\n"
                break

        return md


Distributor = DistributorAgent
