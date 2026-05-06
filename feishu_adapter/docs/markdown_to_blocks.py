"""Markdown → 飞书 Docx Block 转换器。

支持核心语法：
- H1/H2/H3
- 段落（含粗体、斜体、行内代码）
- 无序列表 / 有序列表
- 代码块
- 引用块
- 分隔线
"""

import re
from typing import List, Dict, Any, Optional

from lark_oapi.api.docx.v1 import (
    Block, BlockBuilder,
    Text, TextBuilder,
    TextElement, TextElementBuilder,
    TextRun, TextRunBuilder,
    TextStyle, TextStyleBuilder,
    TextElementStyle, TextElementStyleBuilder,
)


# Block 类型常量（飞书 docx）
BLOCK_PAGE = 1           # 页面（根）
BLOCK_TEXT = 2           # 普通文本
BLOCK_HEADING1 = 3       # 标题1
BLOCK_HEADING2 = 4       # 标题2
BLOCK_HEADING3 = 5       # 标题3
BLOCK_BULLET = 12        # 无序列表
BLOCK_ORDERED = 13       # 有序列表
BLOCK_CODE = 22          # 代码块
BLOCK_QUOTE = 15         # 引用
BLOCK_DIVIDER = 16       # 分隔线


def _parse_inline_style(text: str) -> List[Dict[str, Any]]:
    """解析行内样式：粗体 **text**、斜体 *text*、行内代码 `text`。

    返回元素列表，每个元素含 text 和 style 标志。
    """
    # 按模式分割：粗体、斜体、行内代码
    pattern = r'(\*\*.*?\*\*|\*.*?\*|`.*?`)'
    parts = re.split(pattern, text)
    elements = []
    for part in parts:
        if not part:
            continue
        if part.startswith('**') and part.endswith('**'):
            elements.append({"text": part[2:-2], "bold": True})
        elif part.startswith('*') and part.endswith('*') and not part.startswith('**'):
            elements.append({"text": part[1:-1], "italic": True})
        elif part.startswith('`') and part.endswith('`'):
            elements.append({"text": part[1:-1], "code": True})
        else:
            elements.append({"text": part})
    return elements


def _make_text_block(block_type: int, text: str) -> Block:
    """根据文本和 block 类型构造 Block。"""
    # 解析行内样式
    elements_data = _parse_inline_style(text)

    text_elements = []
    for elem in elements_data:
        style = TextElementStyleBuilder().build()
        if elem.get("bold"):
            style = TextElementStyleBuilder().bold(True).build()
        elif elem.get("italic"):
            style = TextElementStyleBuilder().italic(True).build()
        elif elem.get("code"):
            # 行内代码用等宽 + 灰色背景效果，飞书用 code_inline 样式
            style = TextElementStyleBuilder().build()

        run = TextRunBuilder().content(elem["text"]).text_element_style(style).build()
        text_elements.append(TextElementBuilder().text_run(run).build())

    text_obj = TextBuilder().elements(text_elements).build()

    builder = BlockBuilder().block_type(block_type)
    if block_type == BLOCK_TEXT:
        builder = builder.text(text_obj)
    elif block_type == BLOCK_HEADING1:
        builder = builder.heading1(text_obj)
    elif block_type == BLOCK_HEADING2:
        builder = builder.heading2(text_obj)
    elif block_type == BLOCK_HEADING3:
        builder = builder.heading3(text_obj)
    elif block_type == BLOCK_BULLET:
        builder = builder.bullet(text_obj)
    elif block_type == BLOCK_ORDERED:
        builder = builder.ordered(text_obj)
    elif block_type == BLOCK_CODE:
        builder = builder.code(text_obj)
    elif block_type == BLOCK_QUOTE:
        builder = builder.quote(text_obj)
    else:
        builder = builder.text(text_obj)

    return builder.build()


def _make_divider_block() -> Optional[Block]:
    """分隔线：飞书 divider type=16 API 报 99992402，直接跳过（不生成 block）。"""
    return None


def markdown_to_blocks(markdown_content: str) -> List[Block]:
    """将 Markdown 文本转换为飞书 Docx Block 列表。

    Args:
        markdown_content: Markdown 格式字符串

    Returns:
        Block 列表，可直接通过 create_document_block_children API 写入
    """
    lines = markdown_content.split('\n')
    blocks: List[Block] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # H1
        if stripped.startswith('# ') and not stripped.startswith('## '):
            blocks.append(_make_text_block(BLOCK_HEADING1, stripped[2:].strip()))
            i += 1
            continue

        # H2
        if stripped.startswith('## ') and not stripped.startswith('### '):
            blocks.append(_make_text_block(BLOCK_HEADING2, stripped[3:].strip()))
            i += 1
            continue

        # H3
        if stripped.startswith('### '):
            blocks.append(_make_text_block(BLOCK_HEADING3, stripped[4:].strip()))
            i += 1
            continue

        # 分隔线（跳过，不生成 block）
        if stripped in ('---', '***', '___'):
            i += 1
            continue

        # 代码块（type=22 API 报 1770001，改用 text block 模拟）
        if stripped.startswith('```'):
            lang = stripped[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            # 用普通文本块模拟代码块，跳过空行
            if lang:
                blocks.append(_make_text_block(BLOCK_TEXT, f"[{lang}]"))
            for cl in code_lines:
                if cl.strip():  # 跳过空行，避免生成空 text block
                    blocks.append(_make_text_block(BLOCK_TEXT, f"    {cl}"))
            i += 1  # 跳过 ```
            continue

        # 无序列表
        if stripped.startswith('- ') or stripped.startswith('* '):
            item_text = stripped[2:].strip()
            blocks.append(_make_text_block(BLOCK_BULLET, item_text))
            i += 1
            continue

        # 有序列表
        ordered_match = re.match(r'^(\d+)\.\s+(.*)', stripped)
        if ordered_match:
            item_text = ordered_match.group(2)
            blocks.append(_make_text_block(BLOCK_ORDERED, item_text))
            i += 1
            continue

        # 引用块
        if stripped.startswith('>'):
            quote_text = stripped[1:].strip()
            blocks.append(_make_text_block(BLOCK_QUOTE, quote_text))
            i += 1
            continue

        # 普通段落（合并连续行）
        para_lines = [stripped]
        i += 1
        while i < len(lines):
            next_line = lines[i].strip()
            if not next_line:
                i += 1
                break
            # 如果下一行是特殊块，停止合并
            if next_line.startswith(('# ', '## ', '### ', '- ', '* ', '>', '```', '---')):
                break
            if re.match(r'^\d+\.\s', next_line):
                break
            para_lines.append(next_line)
            i += 1

        para_text = ' '.join(para_lines)
        blocks.append(_make_text_block(BLOCK_TEXT, para_text))

    return blocks
