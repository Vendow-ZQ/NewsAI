# NewsAI Architecture

## Overview

NewsAI adopts a layered architecture separating business logic from platform integration:

```
+-------------------+
|     run.py        |   Entry point
+-------------------+
|   core/graph/     |   LangGraph orchestration
+-------------------+
|   core/agents/    |   9 AI agents (platform-agnostic)
+-------------------+
|   core/sources/   |   Information source collectors
|   core/visual/    |   Image generation pipeline
|   core/llm/       |   LLM client (Doubao 1.6)
+-------------------+
| feishu_adapter/   |   Feishu Base CRUD + LangChain Tools
+-------------------+
```

## Data Flow

1. **Collect**: TrendScout gathers news from 4+ sources
2. **Analyze**: HookAnalyst scores viral potential
3. **Curate**: TopicCurator selects top stories
4. **Create**: ContentWriter + VisualDesigner + ScriptWriter produce content
5. **Review**: Reviewer performs fact-check and compliance
6. **Distribute**: Distributor plans multi-platform release
7. **Analyze**: Analyst reviews performance metrics

## Key Design Decisions

- Agents receive tools via dependency injection (adapter layer provides implementation)
- `core/` has zero knowledge of Feishu -- fully portable
- LangGraph StateGraph enables fan-out for parallel content creation
