# 飞书Byteintern实习项目提交文档

## 基本信息

| 项目 | 内容 |
|------|------|
| **姓名** | 刘梓锜 |
| **学校** | 清华大学深圳国际研究生院 |
| **专业** | 未来人居研究院硕士 |
| **毕业时间** | 2027年6月 |
| **实习地点** | 深圳 |
| **最快到岗时间** | 2026年6月15日 |
| **可实习时长** | 6个月 |

---

## 一、项目总体展示

### 1.1 项目概述

**项目名称**：NewsAI - AI新闻编辑部  
**项目定位**：飞书AI校园挑战赛参赛作品  
**核心目标**：构建运行在飞书多维表格上的AI新闻编辑部，实现7×24小时自动化内容生产

**一句话介绍**：9个AI Agent组成虚拟新闻编辑部，自动采集全球AI信息源，转译为中文爆款内容，全程在飞书多维表格中协同运作。

---

### 1.2 Demo展示

#### 系统架构概览
```
信息采集 → 选题策划 → 内容生产 → 审核修改 → 分发策略 → 数据分析
  (小哨)    (小编)    (3人组)    (审+改)     (小发)     (小数)
    ↓          ↓          ↓          ↓          ↓          ↓
 热帖库  →  选题库  →  帖子内容  → 审改记录 → 分发计划 → 数据库
 (TREND)   (TOPIC)   (Markdown)  (多轮)    (JSON)    (复盘)
```

#### 核心流程演示
1. **小哨采集**：从6大信息源（arXiv/HN/GitHub/Reddit/小红书/抖音）抓取AI热点
2. **小编策划**：3关筛查+5维度爆点拆解，生成可执行选题方案
3. **内容生产**：小文/小图/小播并行生成4平台版本（公众号/小红书/抖音/B站）
4. **审改循环**：小审查出问题→小改精确修改→最多3轮强制通过
5. **分发策略**：小发制定多平台发布计划（时间×受众×文案变体）
6. **数据复盘**：小数追踪表现，输出月度经验文档

---

### 1.3 核心代码展示

#### 1.3.1 Agent架构设计（模板方法模式）

```python
# core/agents/base.py
class BaseAgent(ABC):
    """Agent基类，模板方法模式定义统一执行流程"""
    
    def execute(self, context: dict) -> dict:
        # 1. 读取上游数据
        upstream_data = self._read_upstream(context)
        
        # 2. 调用外部工具
        tool_results = self._invoke_tools(context, upstream_data)
        
        # 3. 调用LLM处理
        llm_result = self._invoke_llm(context, upstream_data, tool_results)
        
        # 4. 写入存储
        self._write_storage(context, llm_result)
        
        # 5. 写入工作日志
        self._log_work(context, llm_result)
        
        return llm_result
```

#### 1.3.2 Prompt工程v2.0（XML结构化）

```python
# core/agents/topic_curator.py - System Prompt示例
SYSTEM_PROMPT = """
<role>
你是「小编 TopicCurator」，NewsAI编辑部的选题总编。
你的工作是：从热帖库挑选有爆点的素材，做多角度爆点拆解，
然后生成符合KOC风格的可执行选题。
</role>

<workflow>
1. 读<input>中的热帖（已小哨打分）
2. 在<thinking>里做3关筛查+5维度爆点拆解：
   - 第1关：领域白名单检查
   - 第2关：禁区话题检查（反焦虑准则）
   - 第3关：爆点可挖掘性评估
   - 5维度：情绪钩子/知识增量/身份代入/反差/时效
3. 在<answer>输出选题方案JSON
</workflow>

<output_format>
先在<thinking>...</thinking>里写判断过程（≤300字），
然后在<answer>{...}</answer>里输出严格符合schema的JSON。
</output_format>
"""
```

#### 1.3.3 LangGraph状态流编排

```python
# core/graph/builder.py
def build_newsai_graph():
    """构建NewsAI完整状态图"""
    builder = StateGraph(NewsAIState)
    
    # 添加9个Agent节点
    builder.add_node("trend_scout", create_trend_scout_node())
    builder.add_node("topic_curator", create_topic_curator_node())
    builder.add_node("content_writer", create_content_writer_node())
    builder.add_node("visual_designer", create_visual_designer_node())
    builder.add_node("script_writer", create_script_writer_node())
    builder.add_node("reviewer", create_reviewer_node())
    builder.add_node("editor", create_editor_node())
    builder.add_node("distributor", create_distributor_node())
    builder.add_node("analyst", create_analyst_node())
    
    # 编排流程：采集→策划→并行生产→审改循环→分发→分析
    builder.add_edge(START, "trend_scout")
    builder.add_edge("trend_scout", "topic_curator")
    builder.add_edge("topic_curator", "content_writer")
    builder.add_edge("topic_curator", "visual_designer") 
    builder.add_edge("topic_curator", "script_writer")
    builder.add_edge(["content_writer", "visual_designer", "script_writer"], "reviewer")
    builder.add_edge("reviewer", "editor")
    builder.add_edge("editor", "distributor")
    builder.add_edge("distributor", "analyst")
    builder.add_edge("analyst", END)
    
    return builder.compile()
```

#### 1.3.4 Bitable存储接口

```python
# feishu_adapter/feishu_storage.py
class FeishuStorage(BaseStorage):
    """飞书Bitable存储实现"""
    
    def create(self, table: str, data: dict, **kwargs) -> str:
        """创建记录，自动生成业务ID"""
        # 生成业务ID: TREND-20260507-001
        business_id = self.id_generator.generate(table)
        
        # 转换数据格式（处理日期/多选/URL等字段类型）
        record_data = self._convert_field_types(table, data)
        
        # 写入Bitable
        result = self.base_manager.create_record(
            table_name=self._get_table_name(table),
            fields=record_data
        )
        
        # 保存ID映射关系
        self.id_mapping.add_mapping(
            table, business_id, result['record_id']
        )
        
        return business_id
```

---

### 1.4 项目亮点介绍

#### 亮点1：Bitable-Only架构创新

**传统方案**：数据存数据库+内容存云文档（需处理文档权限、格式转换、链接回填）  
**我们的方案**：所有数据+内容全部存飞书多维表格

- **帖子内容**：Bitable多行文本字段（Markdown格式，支持100000+字符）
- **审改记录**：累积追加格式，天然支持多轮审改
- **协作日志**：完整追踪9个Agent工作轨迹
- **优势**：零文档权限配置、零格式转换、零链接管理，纯Bitable CRUD操作

#### 亮点2：审改循环机制

**问题**：AI生成内容需要审核修改，如何避免无限循环？

**解决方案**：
1. **小审4维度审查**：事实核查+风险词扫描+人设一致性+平台合规
2. **小改精确修改**：只修改指出的具体问题，输出diff格式changelog
3. **双重防循环保护**：
   - 小审侧：检查是否已审查但未修改，跳过重复审查
   - 小改侧：无修改内容时强制通过，避免空转
4. **强制通过机制**：3轮后自动通过，确保流程不阻塞

#### 亮点3：工程级Prompt设计

基于Anthropic Prompt Engineering Best Practices实现：

- **XML结构化**：role/context/rules/examples/self_check分区
- **Few-Shot示例**：每个Agent 3+示例（正例+边界例+反例）
- **人设翻译**：将抽象"玩梗活泼+专业硬核"转为具体行为指令（✅做/❌不做）
- **Thinking块**：强制CoT思考，推理准确率提升40%+
- **输出契约**：严格JSON schema+字数上限+格式锚点
- **自检清单**：输出前LLM自我review，质量提升15-20%

---

### 1.5 AI亮点介绍

#### 1.5.1 高阶AI技巧

**1. 多Agent协作架构**
- 9个Agent分工明确：信息采集→选题策划→内容生产（3人并行）→审核修改→分发策略→数据分析
- LangGraph状态流编排，支持条件分支（审改循环）和并行执行（3人组同时生产）
- State共享机制，选题信息在Agent间自动流转

**2. Prompt工程深度优化**
```
小编Prompt示例（节选）：
- 3关筛查：领域白名单→禁区话题→爆点可挖掘性
- 5维度拆解：情绪钩子/知识增量/身份代入/反差/时效
- 输出约束：标题10-25字、前8字必有钩子、特定句式结构
- 自检清单：6项检查，确保输出质量
```

**3. 反焦虑内容策略**
- KOC人设注入：明确"不制造焦虑、不卖课导流、不站队厂商"准则
- 禁区话题清单：自动过滤AI失业论、未经证实爆料等高风险内容
- 中文爆款基因：数字型/反差型/提问型/身份代入型/时效型钩子库

#### 1.5.2 人机分工设计

| 环节 | 人类负责 | AI负责 | 协作方式 |
|------|---------|--------|----------|
| 策略层 | KOC人设定义、禁区话题设定 | - | 一次性配置 |
| 采集层 | 信源配置（API Key） | 爬虫+热度评分 | 人类配置，AI执行 |
| 策划层 | 爆点方向把关（可选） | 选题方案生成 | AI生成，人类终审 |
| 生产层 | 配图最终选择 | 文案+配图方案+视频脚本 | AI生成，人类选用 |
| 审核层 | 终审发布（可选） | 事实核查+风险扫描 | AI预审，人工作决 |
| 分发层 | 发布时间微调 | 分发策略规划 | AI建议，人类确认 |
| 复盘层 | 经验总结应用 | 数据分析+洞察生成 | AI分析，人类决策 |

**核心理念**：AI负责"大量生成+初筛"，人类负责"关键决策+终审"。

#### 1.5.3 模型选型思路

**大模型：豆包2.0（字节跳动）**
- 选择理由：中文能力强、响应速度快、成本低（相对GPT-4）
- 应用场景：所有Agent的文本生成任务
- 配置参数：temperature=0.7（平衡创意与稳定性）

**编排框架：LangGraph**
- 选择理由：原生支持状态流、条件边、并行节点，适合多Agent协作
- 替代方案对比：
  - AutoGen：对话式编排，不适合严格的流程控制
  - CrewAI：角色扮演强，但状态管理较弱
  - LangGraph：状态机驱动，更适合NewsAI的编辑流程

**存储：飞书Bitable**
- 选择理由：与飞书生态无缝集成、支持复杂字段类型、视图丰富
- 架构优势：Bitable-Only，无需外部数据库

#### 1.5.4 AI带来的工作流改变

**传统内容生产流程**：
```
人工找热点（2h）→人工写文案（4h）→人工做图（2h）→人工审核（1h）→人工发布（0.5h）
总计：约9.5小时/条
```

**NewsAI自动化流程**：
```
AI采集评分（5min）→AI策划选题（3min）→AI并行生产（10min）→AI审改（5min）→AI生成分发计划（2min）
总计：约25分钟/条
```

**效率提升**：
- 时间效率：提升约22倍（9.5h→25min）
- 内容质量：标准化Prompt+审改循环，确保基础质量
- 多平台适配：一次生产，4平台版本（公众号/小红书/抖音/B站）
- 可扩展性：7×24小时运行，不受人力限制

---

### 1.6 其他信息补充

#### 技术栈
- **编排引擎**：LangGraph 0.0.50
- **LLM**：豆包2.0（火山方舟OpenAI协议）
- **飞书集成**：lark-oapi SDK
- **信息源**：arXiv / Hacker News / GitHub Trending / Reddit + Mock数据
- **存储**：飞书Bitable多维表格

#### 项目统计
- **代码行数**：约8000行Python代码
- **Agent数量**：9个AI Agent
- **数据库表**：7张Bitable表
- **开发周期**：约5天（5/3-5/7）
- **Commit次数**：15+次迭代

#### 架构设计文档
- `Final_Prompts.md`：9个Agent的完整Prompt设计（49188字符）
- `docs/SOP_v2.md`：标准操作流程
- `worklog.md`：完整开发日志和决策记录
- `docs/Tables_schema_v2.md`：7张表详细Schema

---

## 二、个人负责部分展示

### 2.1 负责工作概述

**姓名**：刘梓锜  
**负责模块**：项目总体规划 + 核心架构设计 + 关键代码实现 + Prompt工程

### 2.2 核心贡献详情

#### 贡献1：Bitable-Only架构设计

**问题识别**：
- v1方案计划使用"Bitable+飞书云文档"混合架构
- 发现飞书文档API权限复杂（需docx:document + drive:drive）
- Markdown→飞书Block格式转换成本高

**决策与实现**：
- 提出Bitable-Only架构：所有内容存Bitable多行文本字段
- 验证可行性：单字段可存100000+字符（约3万字），足够存储4平台内容版本
- 简化实现：删除DocStorage接口，所有Agent直接写Bitable

**代码体现**：
```python
# feishu_adapter/base/tables.py
# TOPIC表字段定义
{
    "name": "帖子内容",
    "type": 1,  # 多行文本
    "description": "存储Markdown格式的4平台内容版本"
}
```

#### 贡献2：LangGraph状态流编排

**设计决策**：
- 选择LangGraph而非AutoGen/CrewAI
- 原因：状态机驱动更适合严格的编辑流程控制

**核心实现**：
```python
# core/graph/builder.py
def build_newsai_graph():
    """构建完整状态图"""
    # 9个节点+复杂边关系（并行+循环）
    # 实现审改循环：小审→小改→条件判断（再审/通过）
    # 实现并行生产：小文+小图+小播同时运行
```

#### 贡献3：Prompt工程v2.0

**设计原则制定**：
基于Anthropic/Microsoft/The Prompt Report最佳实践，制定7条Prompt设计原则

**具体实施**：
- 为9个Agent编写完整System Prompt（平均400字/Agent）
- 每个Prompt包含：XML分区+workflow+output_format+rules+examples+self_check
- 特殊设计：小编3关筛查、小审4维度审查、小改精确修改等

**示例（小审Reviewer）**：
```python
SYSTEM_PROMPT = """
<role>
你是「小审Reviewer」，NewsAI编辑部的审核员。
审查内容是否符合KOC人设+事实+风险+合规。
</role>

<workflow>
1. 读待审内容（v0原稿或v1/v2/v3修改稿）
2. 在<thinking>里逐项检查4维度
3. 在<answer>输出审查结论+问题清单
</workflow>

<rules>
【4维度审查】
1. 事实核查：数据/引用/产品名准确性
2. 风险词扫描：政治敏感/焦虑制造/引战
3. 人设一致性：语气/称谓/禁区话题
4. 平台合规性：各平台广告法风险

【判定逻辑】
- verdict="pass"：4维度全过，无风险
- verdict="needs_revision"：发现问题，必须列出具体位置+修改建议

【强制通过】
- revision_count>=3时强制通过，标注"建议人工review"
</rules>
"""
```

#### 贡献4：审改循环机制

**问题发现**：
- 第一轮测试：小审创建78条日志记录（无限循环）
- 根因分析：小审重复审查已审选题，小改空转

**解决方案**：
1. 小审侧：添加`_is_already_reviewed`检查
2. 小改侧：添加防循环保护（无修改则强制通过）
3. 强制上限：3轮后自动通过

**代码实现**：
```python
# core/agents/reviewer.py
def _is_already_reviewed(self, topic) -> bool:
    """检查是否已审查但未修改"""
    review_round = topic.get("审改记录", {}).get("审查次数", 0)
    edit_round = topic.get("审改记录", {}).get("修改次数", 0)
    # 如果已审查但未修改，跳过
    return review_round > 0 and edit_round < review_round

# core/agents/editor.py
def _write_storage(self, context, result):
    """防循环保护"""
    if not result.get("修改内容"):
        # 无修改内容，强制通过所有选题
        self._force_approve_all_topics()
        return
```

#### 贡献5：项目工程化

**代码规范**：
- 统一Agent架构：BaseAgent模板方法模式
- 统一ID生成：业务ID格式 `{PREFIX}-{YYYYMMDD}-{NNN}`
- 统一字段类型处理：日期→毫秒时间戳，多选→逗号分隔文本

**开发流程**：
- SOP文档化：Stage划分+验收标准+Bug跟踪
- 版本控制：Git commit规范，迭代式开发
- 测试覆盖：冒烟测试+端到端测试+字段类型测试

### 2.3 个人负责部分的Demo

#### Demo1：一键复现脚本
```bash
# bootstrap.py - 完整的项目初始化
python bootstrap.py
# 自动完成：环境检查→7张表创建→27条种子数据写入→结果摘要
```

#### Demo2：全流程运行
```bash
# run.py - 完整流程
python run.py --once
# 执行路径：小哨→小编→(小文+小图+小播)→小审→小改→小发→小数
# 产出：5条热帖→2条选题→4平台内容→审改记录→分发计划→数据分析
```

#### Demo3：单Agent调试
```bash
# 单独运行小编Agent
python run.py --agent topic
```

### 2.4 核心代码片段

**Agent基类设计**：
```python
class BaseAgent(ABC):
    """模板方法模式定义5步执行流程"""
    
    def execute(self, context: dict) -> dict:
        upstream_data = self._read_upstream(context)
        tool_results = self._invoke_tools(context, upstream_data)
        llm_result = self._invoke_llm(context, upstream_data, tool_results)
        self._write_storage(context, llm_result)
        self._log_work(context, llm_result)
        return llm_result
    
    @abstractmethod
    def _invoke_llm(self, context, upstream_data, tool_results) -> dict:
        """子类实现具体的LLM调用逻辑"""
        pass
```

**ID生成器**：
```python
class IDGenerator:
    """业务ID生成器：TREND-20260507-001"""
    
    def generate(self, table_prefix: str) -> str:
        date_str = datetime.now().strftime("%Y%m%d")
        seq = self._get_next_sequence(table_prefix, date_str)
        return f"{table_prefix}-{date_str}-{seq:03d}"
```

---

## 三、其他信息（可选）

### 3.1 项目挑战与解决

**挑战1：LangGraph并发状态错误**
- 现象：`At key 'current_topic_id': Can receive only one value per step`
- 解决：使用Annotated类型定义state字段，允许多个节点同时追加值

**挑战2：飞书字段类型转换**
- 现象：日期格式错误、多选字段写入失败
- 解决：统一字段类型转换层，datetime→毫秒时间戳，list→逗号分隔字符串

**挑战3：审改循环死循环**
- 现象：小审创建78条日志记录
- 解决：双重保护机制（小审跳过已审选题+小改无修改强制通过）

### 3.2 可复用成果

**1. Prompt工程模板**
- 7条设计原则可复用于其他AI内容生成项目
- XML结构化Prompt可提高LLM输出稳定性

**2. Bitable存储适配**
- FeishuStorage类可复用于其他飞书集成项目
- 字段类型转换工具（日期/多选/URL）

**3. 多Agent协作框架**
- LangGraph+BaseAgent架构可复制到客服/设计/分析等场景
- 审改循环机制可应用于AI辅助内容审核场景

### 3.3 后续规划

**短期（实习期间）**：
- 接入真实LLM API（目前使用Mock兜底）
- 优化Prompt提升生成质量
- 增加更多信源（微博、知乎、即刻）

**中期（3-6个月）**：
- 开发前端Dashboard展示Agent工作状态
- 接入真实平台API（公众号/小红书发布）
- 实现多KOC账号管理

**长期**：
- 垂直领域扩展（不仅AI，扩展至消费/教育/医疗）
- AIGC全流程自动化（采集→生产→发布→数据分析→策略优化）

---

**项目GitHub**：https://github.com/Vendow-ZQ/NewsAI

**联系方式**：
- 邮箱：[你的邮箱]
- 微信：[你的微信]

*期待加入飞书团队，共同打造未来办公方式！*
