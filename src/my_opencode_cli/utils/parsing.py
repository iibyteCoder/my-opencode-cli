"""响应解析工具。"""

from __future__ import annotations

import json
import re
from typing import Any


def parse_json_result(text: str) -> dict[str, Any] | None:
    """解析 json_result 代码块。

    从文本中提取 ```json_result ... ``` 代码块中的 JSON。

    Args:
        text: 原始文本

    Returns:
        解析后的字典，如果没有找到则返回 None
    """
    pattern = r"```json_result\s*([\s\S]*?)\s*```"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        json_str = match.group(1).strip()
        return _safe_parse_json(json_str)
    return None


def parse_structured_output(text: str) -> dict[str, Any]:
    """解析结构化输出。

    按优先级尝试多种格式：
    1. ```json_result ... ``` 代码块
    2. {RESULT}...{RESULT} 标记
    3. ```json ... ``` 代码块

    Args:
        text: 原始文本

    Returns:
        解析后的字典，如果没有找到则返回空字典
    """
    if not text:
        return {}

    # 方式1: json_result 代码块
    result = parse_json_result(text)
    if result is not None:
        return result

    # 方式2: {RESULT}...{RESULT} 标记
    result = _parse_result_marker(text)
    if result is not None:
        return result

    # 方式3: 普通 json 代码块
    result = _parse_json_block(text)
    if result is not None:
        return result

    return {}


def extract_json(text: str) -> dict[str, Any] | None:
    """从文本中提取第一个有效的 JSON 对象。

    Args:
        text: 原始文本

    Returns:
        解析后的字典，如果没有找到则返回 None
    """
    if not text:
        return None

    # 找到第一个 { 和最后一个 }
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        return None

    json_str = text[start : end + 1]
    return _safe_parse_json(json_str)


def _parse_result_marker(text: str) -> dict[str, Any] | None:
    """解析 {RESULT}...{RESULT} 标记格式。"""
    marker = "{RESULT}"
    marker_count = text.count(marker)

    if marker_count < 2:
        return None

    start_idx = text.find(marker)
    if start_idx == -1:
        return None
    start_idx += len(marker)

    end_idx = text.find(marker, start_idx)
    if end_idx == -1:
        return None

    json_str = text[start_idx:end_idx].strip()

    # 可能被 ```json 包裹
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", json_str)
    if json_match:
        json_str = json_match.group(1).strip()

    return _safe_parse_json(json_str)


def _parse_json_block(text: str) -> dict[str, Any] | None:
    """解析普通 json 代码块。"""
    pattern = r"```json\s*([\s\S]*?)\s*```"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        json_str = match.group(1).strip()
        return _safe_parse_json(json_str)
    return None


def _safe_parse_json(json_str: str) -> dict[str, Any] | None:
    """安全解析 JSON 字符串。

    尝试多种方式解析 JSON，增加容错性。

    Args:
        json_str: JSON 字符串

    Returns:
        解析后的字典，失败返回 None
    """
    if not json_str:
        return None

    # 尝试1: 直接解析
    try:
        result = json.loads(json_str)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # 尝试2: 移除可能的注释（JSON5 风格）
    try:
        # 移除单行注释
        cleaned = re.sub(r"//[^\n]*", "", json_str)
        # 移除尾随逗号
        cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
        result = json.loads(cleaned)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # 尝试3: 提取第一个完整的 JSON 对象
    return extract_json(json_str)
