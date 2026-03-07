"""模型单元测试。"""

from __future__ import annotations

import pytest

from my_opencode_cli.models.session import Session, SessionCreate, SessionUpdate
from my_opencode_cli.models.message import TextPart, MessageContent
from my_opencode_cli.models.event import TextEvent, DoneEvent, SSEEventBase


class TestSessionModels:
    """测试会话模型。"""

    def test_session_create_defaults(self):
        """测试 SessionCreate 默认值。"""
        request = SessionCreate()
        assert request.title is None
        assert request.parent_id is None

    def test_session_create_with_values(self):
        """测试 SessionCreate 带值。"""
        request = SessionCreate(title="Test Session", parent_id="parent-123")
        assert request.title == "Test Session"
        assert request.parent_id == "parent-123"

    def test_session_create_model_dump(self):
        """测试 SessionCreate 序列化。"""
        request = SessionCreate(title="Test")
        data = request.model_dump(exclude_none=True)
        assert data == {"title": "Test"}

        request2 = SessionCreate()
        data2 = request2.model_dump(exclude_none=True)
        assert data2 == {}

    def test_session_update(self):
        """测试 SessionUpdate。"""
        update = SessionUpdate(title="New Title")
        assert update.title == "New Title"


class TestMessageModels:
    """测试消息模型。"""

    def test_text_part(self):
        """测试 TextPart。"""
        part = TextPart(text="Hello")
        assert part.type == "text"
        assert part.text == "Hello"

    def test_message_content_from_text(self):
        """测试 MessageContent.from_text。"""
        content = MessageContent.from_text("Hello World")
        assert len(content.parts) == 1
        assert isinstance(content.parts[0], TextPart)
        assert content.parts[0].text == "Hello World"


class TestEventModels:
    """测试事件模型。"""

    def test_text_event(self):
        """测试 TextEvent。"""
        event = TextEvent(text="Hello")
        assert event.type == "text"
        assert event.text == "Hello"

    def test_done_event(self):
        """测试 DoneEvent。"""
        event = DoneEvent()
        assert event.type == "done"

    def test_sse_event(self):
        """测试 SSEEventBase (OpenCodeEvent) 基类。"""
        event = SSEEventBase(type="custom", properties={"key": "value"})
        assert event.type == "custom"
        assert event.properties == {"key": "value"}
