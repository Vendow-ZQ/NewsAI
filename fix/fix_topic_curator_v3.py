import re

with open('core/agents/topic_curator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if already batch version
if 'for trend in trends_to_analyze:' in content and 'trends_to_analyze = trends[:8]' not in content:
    print("Replacing _invoke_llm with batch version...")

    # Find the _invoke_llm method and replace it
    pattern = r'    def _invoke_llm\(self, context: dict, upstream_data: dict, tool_results: dict\) -> dict:.*?return \{"topics": topics, "count": len\(topics\)\}'

    new_invoke = '''    def _invoke_llm(self, context: dict, upstream_data: dict, tool_results: dict) -> dict:
        """LLM批量分析选题潜力——一次性分析多条，只选最佳1条。"""
        trends = upstream_data.get("trends", [])
        koc = context.get("koc", {})
        koc = parse_koc_data(koc)
        trends_to_analyze = trends[:8] if len(trends) > 8 else trends
        print(f"[小编] 从{len(trends)}条热帖中批量分析前{len(trends_to_analyze)}条，选出最佳1条...")
        if not trends_to_analyze:
            return {"topics": [], "count": 0}
        prompt = self._build_batch_analysis_prompt(trends_to_analyze, koc)
        try:
            response = self.llm.invoke(prompt)
            analysis = self._parse_llm_response(response)
            selected = analysis.get("最佳选题", {})
            if not selected or not selected.get("是否适合", False):
                print("[小编] 未找到合适的选题")
                return {"topics": [], "count": 0}
            idx = selected.get("热帖序号", 0)
            matched = trends_to_analyze[idx] if 0 <= idx < len(trends_to_analyze) else trends_to_analyze[0]
            topic = {
                "热帖ID": matched.get("id", ""),
                "热帖标题": matched.get("标题", ""),
                "选题标题": selected.get("选题标题", ""),
                "选题角度": selected.get("选题角度", ""),
                "预估爆点": selected.get("预估爆点", ""),
                "预估受众": selected.get("预估受众", ""),
                "推荐优先级": selected.get("推荐优先级", 5),
            }
            print(f"[小编] 最佳选题: {topic['选题标题'][:40]}... (优先级:{topic['推荐优先级']})")
            return {"topics": [topic], "count": 1}
        except Exception as e:
            print(f"[小编] LLM批量分析失败: {e}")
            return {"topics": [], "count": 0}

    def _build_batch_analysis_prompt(self, trends: list, koc: dict) -> str:
        """构建批量选题分析提示词——让LLM从多条热帖中只选最佳1条。"""
        trend_lines = []
        for i, t in enumerate(trends):
            trend_lines.append(f"[{i}] {t.get('信源平台','')} | {t.get('标题','')} | score:{t.get('热度评分',0.5)}\n    摘要:{t.get('原文摘要','')[:80]}")
        trends_text = "\n".join(trend_lines)
        return f"""你是【小编 TopicCurator】，为KOC【{koc.get('账号名','学AI的刘同学')}】选题。
KOC定位：{koc.get('一句话定位','给非科班大众看的AI资讯速递')}
目标受众：{koc.get('目标受众','22-35岁非技术背景知识工作者')}
禁区：{koc.get('禁区话题','政治敏感/引战/卖课/制造焦虑')}

候选热帖（{len(trends)}条）：
{trends_text}

请**只选最适合的1条**，返回JSON：
{{"最佳选题": {{
  "是否适合": true/false,
  "热帖序号": 0,
  "选题标题": "一句话选题（20字内）",
  "选题角度": "切入角度（80字）",
  "预估爆点": "为什么爆（80字）",
  "预估受众": "目标受众（40字）",
  "推荐优先级": 1-10
}}}}
注意：推荐优先级8分以上才值得选。"""'''

    content = re.sub(pattern, new_invoke, content, flags=re.DOTALL)

    with open('core/agents/topic_curator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Done: Replaced _invoke_llm with batch version")
else:
    print("Already batch version or pattern not found")

# Verify syntax
import subprocess
r = subprocess.run(['python', '-m', 'py_compile', 'core/agents/topic_curator.py'], capture_output=True)
print('Syntax OK' if r.returncode == 0 else f'Error: {r.stderr.decode()[:200]}')
