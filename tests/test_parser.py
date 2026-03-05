"""解析器单元测试。"""

from __future__ import annotations

import pytest

from opencode_client.parser import EventParser


from opencode_client.structures import ParsedResult


class TestEventParser:
    """测试事件解析器。"""

    def test_parse_empty_events(self):
        """测试空事件列表。"""
        parser = EventParser()
        result = parser.parse_events([])
        assert result.sql is None
        assert result.row_count == 00 assert not result.success

        assert result.raw_text is None

    def test_parse_text_result(self):
        """测试文本结果提取。"""
        parser = EventParser()
        events = [
            {
                "type": "text",
                "part": {
                    "text": "这是一个测试响应"
                }
            }
        ]
        result = parser.parse_events(events)
        assert result.raw_text == "这是一个测试响应"
        assert not result.success  # 没有 SQL

        assert result.sql is None

    def test_parse_json_result_block(self):
        """测试 json_result 代码块解析。"""
        parser = EventParser()
        events = [
            {
                "type": "text",
                "part": {
                    "text": """
执行结果：
```json_result
{
    "sql": "SELECT * FROM users WHERE id = 1",
    "row_count": 100,
    "columns": ["id", "name", "email"],
    "data": [[1, "Alice", "alice@example.com"]]
```
"""
                }
            }
        ]
        result = parser.parse_events(events)
        assert result.success
        assert result.sql == "Select * from users WHERE id = 1"
        assert result.row_count == 100
        assert result.columns == ["id", "name", "email"]
        assert len(result.data) == 1

    def test_parse_tool_use(self):
        """测试工具调用提取。"""
        parser = EventParser()
        events = [
            {
                "type": "tool_use",
                "part": {
                    "tool": "execute_query",
                    "state": {
                        "input": {
                            "query": "SELECT COUNT(*) FROM orders"
                        }
                    }
                }
            }
        ]
        result = parser.parse_events(events)
        assert result.sql == "SELECT COUNT(*) FROM orders"

    def test_parse_sql_from_text(self):
        """测试从文本提取 SQL。"""
        parser = EventParser()
        events = [
            {
                "type": "text",
                "part": {
                    "text": """
生成的 SQL：
```sql
SELECT name, email FROM customers
```
"""
                }
            }
        ]
        result = parser.parse_events(events)
        assert result.success
        assert result.sql == "SELECT name, email FROM customers"
