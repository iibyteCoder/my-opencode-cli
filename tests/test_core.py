"""核心模块测试。"""

from __future__ import annotations

import pytest

from opencode_client.core.config import ClientConfig
from opencode_client.core.errors import (
    APIError,
    ConnectionError,
    MessageError,
    OpenCodeError,
    ParseError,
    ServerStartError,
    SessionError,
    TimeoutError,
    ValidationError,
)


class TestClientConfig:
    """测试 ClientConfig 配置类。"""

    def test_default_values(self) -> None:
        """测试默认配置值。"""
        config = ClientConfig()
        assert config.server_hostname == "127.0.0.1"
        assert config.server_port == 4096
        assert config.startup_timeout == 30.0
        assert config.request_timeout == 600
        assert config.cleanup_sessions is True
        assert config.retry_count == 0
        assert config.retry_delay == 1.0
        assert config.log_level == "INFO"

    def test_custom_values(self) -> None:
        """测试自定义配置值。"""
        config = ClientConfig(
            server_hostname="localhost",
            server_port=8080,
            startup_timeout=60.0,
            request_timeout=1200,
            cleanup_sessions=False,
            retry_count=3,
            retry_delay=2.0,
            log_level="DEBUG",
        )
        assert config.server_hostname == "localhost"
        assert config.server_port == 8080
        assert config.startup_timeout == 60.0
        assert config.request_timeout == 1200
        assert config.cleanup_sessions is False
        assert config.retry_count == 3
        assert config.retry_delay == 2.0
        assert config.log_level == "DEBUG"

    def test_base_url_property(self) -> None:
        """测试 base_url 属性。"""
        config = ClientConfig(server_hostname="192.168.1.1", server_port=9000)
        assert config.base_url == "http://192.168.1.1:9000"

    def test_port_validation_min(self) -> None:
        """测试端口最小值验证。"""
        with pytest.raises(ValueError):
            ClientConfig(server_port=0)

    def test_port_validation_max(self) -> None:
        """测试端口最大值验证。"""
        with pytest.raises(ValueError):
            ClientConfig(server_port=65536)

    def test_port_validation_valid(self) -> None:
        """测试有效端口值。"""
        config = ClientConfig(server_port=1)
        assert config.server_port == 1
        config = ClientConfig(server_port=65535)
        assert config.server_port == 65535

    def test_startup_timeout_validation(self) -> None:
        """测试启动超时验证。"""
        with pytest.raises(ValueError):
            ClientConfig(startup_timeout=0.5)
        with pytest.raises(ValueError):
            ClientConfig(startup_timeout=121.0)

    def test_request_timeout_validation(self) -> None:
        """测试请求超时验证。"""
        with pytest.raises(ValueError):
            ClientConfig(request_timeout=5)
        with pytest.raises(ValueError):
            ClientConfig(request_timeout=3601)

    def test_retry_count_validation(self) -> None:
        """测试重试次数验证。"""
        with pytest.raises(ValueError):
            ClientConfig(retry_count=-1)
        with pytest.raises(ValueError):
            ClientConfig(retry_count=6)

    def test_retry_delay_validation(self) -> None:
        """测试重试延迟验证。"""
        with pytest.raises(ValueError):
            ClientConfig(retry_delay=-0.1)
        with pytest.raises(ValueError):
            ClientConfig(retry_delay=11.0)

    def test_log_level_validation(self) -> None:
        """测试日志级别验证。"""
        with pytest.raises(ValueError):
            ClientConfig(log_level="TRACE")  # type: ignore[arg-type]

    def test_extra_fields_forbidden(self) -> None:
        """测试禁止额外字段。"""
        with pytest.raises(ValueError):
            ClientConfig(unknown_field="value")  # type: ignore[arg-type]

    def test_validate_assignment(self) -> None:
        """测试赋值时验证。"""
        config = ClientConfig()
        with pytest.raises(ValueError):
            config.server_port = 70000  # type: ignore[misc]


class TestOpenCodeErrors:
    """测试异常类。"""

    def test_base_error(self) -> None:
        """测试基础异常。"""
        error = OpenCodeError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"

    def test_connection_error(self) -> None:
        """测试连接错误。"""
        error = ConnectionError("Failed to connect")
        assert isinstance(error, OpenCodeError)
        assert error.message == "Failed to connect"

    def test_server_start_error(self) -> None:
        """测试服务器启动错误。"""
        error = ServerStartError("Failed to start server")
        assert isinstance(error, OpenCodeError)

    def test_session_error(self) -> None:
        """测试会话错误。"""
        error = SessionError("Session not found")
        assert isinstance(error, OpenCodeError)

    def test_message_error(self) -> None:
        """测试消息错误。"""
        error = MessageError("Failed to send message")
        assert isinstance(error, OpenCodeError)

    def test_api_error_basic(self) -> None:
        """测试 API 错误基本功能。"""
        error = APIError("API call failed")
        assert isinstance(error, OpenCodeError)
        assert error.status_code is None
        assert error.response is None

    def test_api_error_with_details(self) -> None:
        """测试带详情的 API 错误。"""
        error = APIError(
            "Not found",
            status_code=404,
            response={"error": "session not found"},
        )
        assert error.status_code == 404
        assert error.response == {"error": "session not found"}

    def test_parse_error(self) -> None:
        """测试解析错误。"""
        error = ParseError("Failed to parse JSON")
        assert isinstance(error, OpenCodeError)

    def test_timeout_error_basic(self) -> None:
        """测试超时错误基本功能。"""
        error = TimeoutError()
        assert isinstance(error, OpenCodeError)
        assert error.timeout is None

    def test_timeout_error_with_timeout(self) -> None:
        """测试带超时值的错误。"""
        error = TimeoutError("Request timed out", timeout=30.0)
        assert error.timeout == 30.0

    def test_validation_error_basic(self) -> None:
        """测试验证错误基本功能。"""
        error = ValidationError("Invalid value")
        assert error.field is None
        assert error.value is None

    def test_validation_error_with_details(self) -> None:
        """测试带详情的验证错误。"""
        error = ValidationError(
            "Invalid port number",
            field="port",
            value=70000,
        )
        assert error.field == "port"
        assert error.value == 70000

    def test_error_inheritance_chain(self) -> None:
        """测试异常继承链。"""
        errors = [
            ConnectionError(""),
            ServerStartError(""),
            SessionError(""),
            MessageError(""),
            APIError(""),
            ParseError(""),
            TimeoutError(),
            ValidationError(""),
        ]
        for error in errors:
            assert isinstance(error, OpenCodeError)
            assert isinstance(error, Exception)
