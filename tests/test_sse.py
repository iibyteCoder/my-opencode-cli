"""SSE 流处理工具测试。"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from my_opencode_cli.transport.sse import SSEParser, parse_sse_stream


def make_mock_response(lines: list[bytes]) -> MagicMock:
    """创建模拟的 aiohttp 响应对象。

    Args:
        lines: 原始字节行列表

    Returns:
        模拟的响应对象
    """
    response = MagicMock()
    # 创建异步迭代器
    async def async_iter() -> Any:
        for line in lines:
            yield line

    response.content = async_iter()
    return response


class TestSSEParserParseData:
    """测试 SSEParser._parse_data 方法。"""

    def test_parse_valid_json(self) -> None:
        """测试解析有效的 JSON 数据。"""
        parser = SSEParser()
        data_str = '{"key": "value", "number": 42}'
        result = parser._parse_data(data_str)

        assert result == {"key": "value", "number": 42}

    def test_parse_json_with_nested_object(self) -> None:
        """测试解析嵌套的 JSON 对象。"""
        parser = SSEParser()
        data_str = '{"outer": {"inner": "value"}, "list": [1, 2, 3]}'
        result = parser._parse_data(data_str)

        assert result == {"outer": {"inner": "value"}, "list": [1, 2, 3]}

    def test_parse_invalid_json_returns_raw(self) -> None:
        """测试解析无效 JSON 时返回原始字符串。"""
        parser = SSEParser()
        data_str = "not valid json"
        result = parser._parse_data(data_str)

        assert result == {"raw": "not valid json"}

    def test_parse_empty_string(self) -> None:
        """测试解析空字符串。"""
        parser = SSEParser()
        result = parser._parse_data("")

        # 空字符串不是有效 JSON
        assert result == {"raw": ""}

    def test_parse_json_array(self) -> None:
        """测试解析 JSON 数组。"""
        parser = SSEParser()
        data_str = '[{"id": 1}, {"id": 2}]'
        result = parser._parse_data(data_str)

        assert result == [{"id": 1}, {"id": 2}]


class TestSSEParserParse:
    """测试 SSEParser.parse 方法。"""

    @pytest.mark.asyncio
    async def test_parse_simple_data_only(self) -> None:
        """测试只有 data 字段的简单事件。"""
        parser = SSEParser()
        lines = [
            b'data: {"message": "hello"}\n',
            b'\n',
        ]
        response = make_mock_response(lines)

        events = []
        async for event in parser.parse(response):
            events.append(event)

        assert len(events) == 1
        assert events[0] == {"message": "hello"}

    @pytest.mark.asyncio
    async def test_parse_event_and_data(self) -> None:
        """测试带 event 和 data 字段的事件。"""
        parser = SSEParser()
        lines = [
            b'event: message\n',
            b'data: {"content": "test"}\n',
            b'\n',
        ]
        response = make_mock_response(lines)

        events = []
        async for event in parser.parse(response):
            events.append(event)

        assert len(events) == 1
        assert events[0] == {"event": "message", "content": "test"}

    @pytest.mark.asyncio
    async def test_parse_multiple_events(self) -> None:
        """测试解析多个连续事件。"""
        parser = SSEParser()
        lines = [
            b'event: start\n',
            b'data: {"status": "begin"}\n',
            b'\n',
            b'event: update\n',
            b'data: {"progress": 50}\n',
            b'\n',
            b'event: done\n',
            b'data: {"status": "complete"}\n',
            b'\n',
        ]
        response = make_mock_response(lines)

        events = []
        async for event in parser.parse(response):
            events.append(event)

        assert len(events) == 3
        assert events[0] == {"event": "start", "status": "begin"}
        assert events[1] == {"event": "update", "progress": 50}
        assert events[2] == {"event": "done", "status": "complete"}

    @pytest.mark.asyncio
    async def test_parse_multiline_data(self) -> None:
        """测试多行 data 字段（应合并为换行分隔）。"""
        parser = SSEParser()
        lines = [
            b'data: line one\n',
            b'data: line two\n',
            b'data: line three\n',
            b'\n',
        ]
        response = make_mock_response(lines)

        events = []
        async for event in parser.parse(response):
            events.append(event)

        assert len(events) == 1
        # 多行 data 会被合并，但不是有效 JSON
        assert events[0] == {"raw": "line one\nline two\nline three"}

    @pytest.mark.asyncio
    async def test_parse_comment_lines_ignored(self) -> None:
        """测试注释行（以 : 开头）被忽略。"""
        parser = SSEParser()
        lines = [
            b': this is a comment\n',
            b'event: test\n',
            b': another comment\n',
            b'data: {"value": 1}\n',
            b'\n',
        ]
        response = make_mock_response(lines)

        events = []
        async for event in parser.parse(response):
            events.append(event)

        assert len(events) == 1
        assert events[0] == {"event": "test", "value": 1}

    @pytest.mark.asyncio
    async def test_parse_empty_input(self) -> None:
        """测试空输入。"""
        parser = SSEParser()
        lines: list[bytes] = []
        response = make_mock_response(lines)

        events = []
        async for event in parser.parse(response):
            events.append(event)

        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_parse_no_terminating_newline(self) -> None:
        """测试没有终止空行的事件（不会被产出）。"""
        parser = SSEParser()
        lines = [
            b'event: incomplete\n',
            b'data: {"partial": true}',
            # 注意：没有结尾空行
        ]
        response = make_mock_response(lines)

        events = []
        async for event in parser.parse(response):
            events.append(event)

        # 没有空行终止，事件不会被产出
        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_parse_crlf_line_endings(self) -> None:
        """测试 CRLF 行尾。"""
        parser = SSEParser()
        lines = [
            b'event: test\r\n',
            b'data: {"key": "value"}\r\n',
            b'\r\n',
        ]
        response = make_mock_response(lines)

        events = []
        async for event in parser.parse(response):
            events.append(event)

        assert len(events) == 1
        assert events[0] == {"event": "test", "key": "value"}

    @pytest.mark.asyncio
    async def test_parse_field_with_spaces(self) -> None:
        """测试字段值中的空格处理。"""
        parser = SSEParser()
        lines = [
            b'event:  my event  \n',  # 值前有空格（会被 lstrip）
            b'data: {"text": "  spaced  "}\n',
            b'\n',
        ]
        response = make_mock_response(lines)

        events = []
        async for event in parser.parse(response):
            events.append(event)

        assert len(events) == 1
        # event 字段值只 lstrip（去掉左边空格），右边空格保留
        assert events[0]["event"] == "my event  "
        # JSON 内的空格保持不变
        assert events[0]["text"] == "  spaced  "

    @pytest.mark.asyncio
    async def test_parse_id_and_retry_fields_ignored(self) -> None:
        """测试 id 和 retry 字段被忽略但不影响解析。"""
        parser = SSEParser()
        lines = [
            b'event: message\n',
            b'id: 12345\n',
            b'retry: 3000\n',
            b'data: {"content": "test"}\n',
            b'\n',
        ]
        response = make_mock_response(lines)

        events = []
        async for event in parser.parse(response):
            events.append(event)

        assert len(events) == 1
        assert events[0] == {"event": "message", "content": "test"}

    @pytest.mark.asyncio
    async def test_parse_utf8_content(self) -> None:
        """测试 UTF-8 内容（包括中文）。"""
        parser = SSEParser()
        lines = [
            b'event: message\n',
           	b'data: {"text": "\xe4\xb8\xad\xe6\x96\x87\xe6\xb5\x8b\xe8\xaf\x95"}\n',  # 中文测试
            b'\n',
        ]
        response = make_mock_response(lines)

        events = []
        async for event in parser.parse(response):
            events.append(event)

        assert len(events) == 1
        assert events[0] == {"event": "message", "text": "中文测试"}

    @pytest.mark.asyncio
    async def test_parse_invalid_utf8_replaced(self) -> None:
        """测试无效 UTF-8 字符被替换为 U+FFFD。"""
        parser = SSEParser()
        lines = [
            b'data: {"text": "test\xff\xfe"}\n',  # 包含无效 UTF-8
            b'\n',
        ]
        response = make_mock_response(lines)

        events = []
        async for event in parser.parse(response):
            events.append(event)

        # 无效字节被替换为 U+FFFD (�)，JSON 仍然有效
        assert len(events) == 1
        assert events[0] == {"text": "test\ufffd\ufffd"}

    @pytest.mark.asyncio
    async def test_parse_unknown_field_ignored(self) -> None:
        """测试未知字段被忽略。"""
        parser = SSEParser()
        lines = [
            b'event: test\n',
            b'unknown_field: some_value\n',
            b'data: {"valid": true}\n',
            b'\n',
        ]
        response = make_mock_response(lines)

        events = []
        async for event in parser.parse(response):
            events.append(event)

        assert len(events) == 1
        assert events[0] == {"event": "test", "valid": True}


class TestParseSSEStream:
    """测试 parse_sse_stream 便捷函数。"""

    @pytest.mark.asyncio
    async def test_parse_sse_stream_basic(self) -> None:
        """测试基本功能。"""
        lines = [
            b'event: test\n',
            b'data: {"key": "value"}\n',
            b'\n',
        ]
        response = make_mock_response(lines)

        events = []
        async for event in parse_sse_stream(response):
            events.append(event)

        assert len(events) == 1
        assert events[0] == {"event": "test", "key": "value"}

    @pytest.mark.asyncio
    async def test_parse_sse_stream_yields_multiple(self) -> None:
        """测试产出多个事件。"""
        lines = [
            b'data: {"num": 1}\n',
            b'\n',
            b'data: {"num": 2}\n',
            b'\n',
            b'data: {"num": 3}\n',
            b'\n',
        ]
        response = make_mock_response(lines)

        events = []
        async for event in parse_sse_stream(response):
            events.append(event)

        assert len(events) == 3
        assert [e["num"] for e in events] == [1, 2, 3]


class TestSSEParserEdgeCases:
    """测试边界情况。"""

    @pytest.mark.asyncio
    async def test_empty_data_field(self) -> None:
        """测试空的 data 字段。"""
        parser = SSEParser()
        lines = [
            b'data: \n',  # 空 data
            b'\n',
        ]
        response = make_mock_response(lines)

        events = []
        async for event in parser.parse(response):
            events.append(event)

        assert len(events) == 1
        # 空字符串不是有效 JSON
        assert events[0] == {"raw": ""}

    @pytest.mark.asyncio
    async def test_empty_event_field(self) -> None:
        """测试空的 event 字段（不添加到结果）。"""
        parser = SSEParser()
        lines = [
            b'event: \n',  # 空 event
            b'data: {"key": "value"}\n',
            b'\n',
        ]
        response = make_mock_response(lines)

        events = []
        async for event in parser.parse(response):
            events.append(event)

        assert len(events) == 1
        # 空 event 不会添加到结果中
        assert "event" not in events[0]
        assert events[0] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_event_without_data(self) -> None:
        """测试只有 event 没有 data（产出空字典）。"""
        parser = SSEParser()
        lines = [
            b'event: ping\n',
            b'\n',
        ]
        response = make_mock_response(lines)

        events = []
        async for event in parser.parse(response):
            events.append(event)

        # 有 event 但没有 data，不会产出任何内容
        # 因为 data_buffer 为空
        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_colon_in_value(self) -> None:
        """测试值中包含冒号。"""
        parser = SSEParser()
        lines = [
            b'data: {"url": "http://example.com:8080"}\n',
            b'\n',
        ]
        response = make_mock_response(lines)

        events = []
        async for event in parser.parse(response):
            events.append(event)

        assert len(events) == 1
        assert events[0] == {"url": "http://example.com:8080"}

    @pytest.mark.asyncio
    async def test_multiple_colons_in_line(self) -> None:
        """测试行中有多个冒号。"""
        parser = SSEParser()
        lines = [
            b'event: type:subtype\n',  # 值中包含冒号
            b'data: {"key": "value"}\n',
            b'\n',
        ]
        response = make_mock_response(lines)

        events = []
        async for event in parser.parse(response):
            events.append(event)

        assert len(events) == 1
        assert events[0]["event"] == "type:subtype"
