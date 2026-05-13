"""LLM 输出解析器。

v3.0 关键设计：统一解析 <thinking> + <answer> 双标签，带重试机制。
"""

import json
import re
from typing import Tuple


class LLMOutputError(Exception):
    """LLM 输出格式错误，应当触发重试"""
    pass


def parse_thinking_answer(raw: str) -> Tuple[str, dict]:
    """
    解析 LLM 输出，提取 <thinking> 和 <answer> 内容。

    Returns:
        (thinking_text, answer_dict)

    Raises:
        LLMOutputError: 输出格式不符合预期，应触发重试
    """
    if not raw or not isinstance(raw, str):
        raise LLMOutputError(f"LLM 输出为空或非字符串：{type(raw)}")

    # 提取 <thinking>
    thinking_match = re.search(r'<thinking>(.*?)</thinking>', raw, re.DOTALL)
    thinking = thinking_match.group(1).strip() if thinking_match else ""

    # 提取 <answer>（必须存在）
    answer_match = re.search(r'<answer>(.*?)</answer>', raw, re.DOTALL)
    if not answer_match:
        raise LLMOutputError(
            f"LLM 输出缺少 <answer> 标签。"
            f"原文前 300 字符：{raw[:300]}"
        )

    answer_raw = answer_match.group(1).strip()

    # 容错：去掉可能的 markdown 代码块包裹
    answer_raw = re.sub(r'^```(?:json)?\s*', '', answer_raw)
    answer_raw = re.sub(r'\s*```$', '', answer_raw)

    # 解析 JSON
    try:
        answer_dict = json.loads(answer_raw)
    except json.JSONDecodeError as e:
        raise LLMOutputError(
            f"LLM 输出 JSON 解析失败：{e}\n"
            f"原 answer 内容：{answer_raw[:500]}"
        )

    return thinking, answer_dict


def invoke_with_retry(llm, messages, max_retries=3):
    """
    带重试的 LLM 调用。

    每次重试会在 user message 末尾追加错误反馈，让 LLM 修正。

    Args:
        llm: LLM 客户端实例（需有 invoke(messages) 方法）
        messages: message 列表
        max_retries: 最大重试次数

    Returns:
        (thinking_text, answer_dict, raw_response)
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            response = llm.invoke(messages)
            raw = response.content if hasattr(response, 'content') else str(response)
            thinking, answer = parse_thinking_answer(raw)
            return thinking, answer, raw
        except LLMOutputError as e:
            last_error = e
            if attempt < max_retries - 1:
                # 把错误反馈给 LLM
                messages = messages + [{
                    "role": "user",
                    "content": (
                        f"你上一次的回复格式有误：{e}\n"
                        f"请重新输出，严格遵守 <thinking>...</thinking>"
                        f"<answer>{{JSON}}</answer> 格式。"
                    )
                }]
            else:
                raise LLMOutputError(
                    f"LLM 调用重试 {max_retries} 次后仍失败：{last_error}"
                )
