"""事件解析器。

从 OpenCode 响应中提取结构化数据。
支持多种输出格式：
1. json_result 代码块（推荐）：```json_result ... ```
2. RESULT 标记格式（旧）：{RESULT}...{RESULT}
3. 普通 json 代码块（后备）：```json ... ```
"""

from __future__ import annotations

import json
import re
from typing import Any

# 结构化结果标记（旧格式，保持兼容）
RESULT_MARKER = "{RESULT}"


class EventParser:
    """OpenCode 事件解析器。

    从原始事件列表或响应数据中提取结构化结果。

    这个类只负责解析，不负责执行，方便单独测试和适配。
    """

    def parse_events(self, events: list[dict[str, Any]]) -> ParsedResult:
        """解析事件列表，提取结构化数据。

        Args:
            events: OpenCode 返回的原始事件列表

        Returns:
            解析后的结果对象
        """
        sql = self._extract_sql(events)
        text_result = self._extract_text_result(events)
        structured = self._parse_structured_result(text_result)

        # 优先级：结构化数据 > 工具调用 > 文本提取（后备）
        final_sql = structured.sql or sql or self._extract_sql_from_text(text_result)

        return ParsedResult(
            sql=final_sql,
            row_count=structured.row_count,
            columns=structured.columns,
            data=structured.data,
            raw_text=text_result,
        )

    def parse_response(self, response: dict[str, Any]) -> ParsedResult:
        """解析 HTTP API 响应。

        将 HTTP API 返回的 parts 格式转换为解析结果。

        Args:
            response: HTTP API 返回的响应数据

        Returns:
            解析后的结果对象
        """
        parts = response.get("parts", [])
        # 转换格式：HTTP API parts → CLI events
        events: list[dict[str, Any]] = []
        for part in parts:
            part_type = part.get("type", "") or part.get("event", "")
            event: dict[str, Any] = {
                "type": part_type,
                "part": part,
            }
            events.append(event)

        return self.parse_events(events)

    def _extract_sql_from_text(self, text: str | None) -> str | None:
        """从文本中提取 SQL 语句（后备方案）。

        当智能体没有调用工具时，尝试从文本中提取 SQL。

        Args:
            text: Agent 返回的文本

        Returns:
            SQL 语句或 None
        """
        if not text:
            return None

        # 匹配 ```sql ... ``` 代码块
        sql_block_match = re.search(r"```sql\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if sql_block_match:
            return sql_block_match.group(1).strip()

        return None

    def _extract_sql(self, events: list[dict[str, Any]]) -> str | None:
        """从事件列表提取 SQL 语句。

        Args:
            events: 原始事件列表

        Returns:
            SQL 语句或 None
        """
        for event in events:
            if event.get("type") not in ("tool_use", "tool"):
                continue

            part = event.get("part", {})
            tool = part.get("tool", "")

            # 匹配 execute_query 或类似工具
            if "execute" in tool.lower() and "query" in tool.lower():
                state = part.get("state", {})
                return state.get("input", {}).get("query")

        return None

    def _extract_text_result(self, events: list[dict[str, Any]]) -> str | None:
        """从事件列表提取文本结果。

        Args:
            events: 原始事件列表

        Returns:
            文本结果或 None
        """
        result = None
        for event in events:
            if event.get("type") == "text":
                text = event.get("part", {}).get("text")
                if text:
                    result = text
        return result

    def _parse_structured_result(self, text: str | None) -> StructuredData:
        """从文本中解析结构化 JSON 结果。

        支持多种格式（按优先级）：
        1. ```json_result ... ``` 代码块（推荐格式）
        2. {RESULT}...{RESULT} 标记（旧格式，保持兼容）
        3. ```json ... ``` 代码块（后备）

        Args:
            text: Agent 返回的文本

        Returns:
            结构化数据对象
        """
        if not text:
            return StructuredData()

        # 方式1: 尝试解析 json_result 代码块（推荐格式）
        json_str = self._extract_json_result_block(text)
        if json_str:
            parsed = self._safe_parse_json(json_str)
            if parsed:
                return self._build_structured_data(parsed)

        # 方式2: 尝试解析 {RESULT}...{RESULT} 标记（旧格式）
        json_str = self._extract_result_marker(text)
        if json_str:
            parsed = self._safe_parse_json(json_str)
            if parsed:
                return self._build_structured_data(parsed)

        # 方式3: 尝试解析普通 json 代码块（后备）
        json_str = self._extract_json_block(text)
        if json_str:
            parsed = self._safe_parse_json(json_str)
            if parsed:
                return self._build_structured_data(parsed)

        return StructuredData()

    def _build_structured_data(self, parsed: dict[str, Any]) -> StructuredData:
        """从解析的 JSON 构建结构化数据。

        Args:
            parsed: 解析后的 JSON 字典

        Returns:
            结构化数据对象
        """
        return StructuredData(
            row_count=parsed.get("row_count", 0),
            columns=parsed.get("columns", []),
            data=parsed.get("data", []) or parsed.get("data_preview", []),
            sql=parsed.get("sql"),
        )

    def _extract_json_result_block(self, text: str) -> str | None:
        """提取 json_result 代码块内容。

        Args:
            text: 原始文本

        Returns:
            JSON 字符串或 None
        """
        # 匹配 ```json_result ... ``` 代码块
        match = re.search(r"```json_result\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _extract_result_marker(self, text: str) -> str | None:
        """提取 {RESULT}...{RESULT} 标记之间的内容。

        Args:
            text: 原始文本

        Returns:
            JSON 字符串或 None
        """
        marker_count = text.count(RESULT_MARKER)
        if marker_count < 2:
            return None

        start_idx = text.find(RESULT_MARKER)
        if start_idx == -1:
            return None
        start_idx += len(RESULT_MARKER)

        end_idx = text.find(RESULT_MARKER, start_idx)
        if end_idx == -1:
            return None

        json_str = text[start_idx:end_idx].strip()

        # 可能被 ```json 包裹
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", json_str)
        if json_match:
            return json_match.group(1).strip()

        return json_str

    def _extract_json_block(self, text: str) -> str | None:
        """提取普通 json 代码块内容（后备方案）。

        只提取包含 sql 或 row_count 字段的 JSON 块。

        Args:
            text: 原始文本

        Returns:
            JSON 字符串或 None
        """
        # 匹配所有 ```json ... ``` 代码块
        for match in re.finditer(r"```json\s*([\s\S]*?)\s*```", text, re.IGNORECASE):
            content = match.group(1).strip()
            # 检查是否包含必要字段
            if "sql" in content or "row_count" in content:
                return content
        return None

    def _safe_parse_json(self, json_str: str) -> dict[str, Any] | None:
        """安全解析 JSON 字符串。

        尝试多种方式解析 JSON，增加容错性。

        Args:
            json_str: JSON 字符串

        Returns:
            解析后的字典或 None
        """
        if not json_str:
            return None

        # 尝试1: 直接解析
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # 尝试2: 移除可能的注释（JSON5 风格）
        try:
            # 移除单行注释
            cleaned = re.sub(r"//[^\n]*", "", json_str)
            # 移除尾随逗号
            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # 尝试3: 提取第一个完整的 JSON 对象
        try:
            # 找到第一个 { 和最后一个 }
            start = json_str.find("{")
            end = json_str.rfind("}")
            if start != -1 and end != -1 and end > start:
                extracted = json_str[start : end + 1]
                return json.loads(extracted)
        except json.JSONDecodeError:
            pass

        return None


class StructuredData:
    """结构化数据容器。

    存储从响应中解析出的结构化数据。

    Attributes:
        row_count: 数据行数
        columns: 列名列表
        data: 数据二维数组
        sql: SQL 语句
    """

    def __init__(
        self,
        row_count: int = 0,
        columns: list[str] | None = None,
        data: list[list[Any]] | None = None,
        sql: str | None = None,
    ) -> None:
        """初始化结构化数据。

        Args:
            row_count: 数据行数
            columns: 列名列表
            data: 数据二维数组
            sql: SQL 语句
        """
        self.row_count: int = row_count
        self.columns: list[str] = columns or []
        self.data: list[list[Any]] = data or []
        self.sql: str | None = sql


class ParsedResult:
    """解析后的完整结果。

    包含 SQL 语句、结构化数据和原始文本。

    Attributes:
        sql: 最终的 SQL 语句
        row_count: 数据行数
        columns: 列名列表
        data: 数据二维数组
        raw_text: 原始文本结果
    """

    def __init__(
        self,
        sql: str | None = None,
        row_count: int = 0,
        columns: list[str] | None = None,
        data: list[list[Any]] | None = None,
        raw_text: str | None = None,
    ) -> None:
        """初始化解析结果。

        Args:
            sql: SQL 语句
            row_count: 数据行数
            columns: 列名列表
            data: 数据二维数组
            raw_text: 原始文本结果
        """
        self.sql: str | None = sql
        self.row_count: int = row_count
        self.columns: list[str] = columns or []
        self.data: list[list[Any]] = data or []
        self.raw_text: str | None = raw_text

    @property
    def success(self) -> bool:
        """判断是否成功获取结果。

        Returns:
            有 SQL 或有数据则返回 True
        """
        return bool(self.sql) or self.row_count > 0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式。

        Returns:
            包含所有属性的字典
        """
        return {
            "sql": self.sql,
            "row_count": self.row_count,
            "columns": self.columns,
            "data": self.data,
            "raw_text": self.raw_text,
            "success": self.success,
        }
