"""常量定义。"""

from __future__ import annotations

from typing import Final

# 默认服务器配置
DEFAULT_SERVER_HOST: Final[str] = "127.0.0.1"
DEFAULT_SERVER_PORT: Final[int] = 4096
DEFAULT_STARTUP_TIMEOUT: Final[float] = 30.0

# 默认请求配置
DEFAULT_REQUEST_TIMEOUT: Final[int] = 600  # 10 分钟

# SSE 事件类型
EVENT_TYPE_TEXT: Final[str] = "text"
EVENT_TYPE_TOOL_USE: Final[str] = "tool_use"
EVENT_TYPE_TOOL_RESULT: Final[str] = "tool_result"
EVENT_TYPE_ERROR: Final[str] = "error"
EVENT_TYPE_DONE: Final[str] = "done"

# API 路径
API_PATH_SESSION = "/session"
API_PATH_MESSAGE = "/message"
API_PATH_FILE = "/file"
API_PATH_FIND = "/find"
API_PATH_GLOB = "/glob"
API_PATH_GREP = "/grep"
API_PATH_EVENTS = "/events"
API_PATH_AGENT = "/agent"
API_PATH_PROJECT = "/project"
API_PATH_HEALTH = "/global/health"

# HTTP 头
HEADER_ACCEPT = "Accept"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_ACCEPT_SSE = "text/event-stream"
HEADER_CONTENT_TYPE_JSON = "application/json"

# 用户代理
USER_AGENT: Final[str] = "OpenCode-Python-Client/0.2.0"
