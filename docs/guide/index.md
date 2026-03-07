# OpenCode Python Client 使用指南

欢迎使用 OpenCode Python Client！本指南将帮助你快速上手并深入了解这个库的各种功能。

## 概述

OpenCode Python Client 是一个现代化的 Python 客户端库，用于与 [OpenCode](https://opencode.ai) 服务器交互。

### 核心特性

- **异步优先** - 完全基于 `asyncio` 构建，同时提供同步接口
- **类型安全** - 使用 Pydantic v2 和 mypy 严格模式
- **实时事件流** - 支持 Server-Sent Events (SSE) 实时流式输出
- **自动服务器管理** - 可选的本地服务器自动启动和清理

### 架构设计

```text
┌─────────────────────────────────────────────────────────────┐
│                    High-Level Client                         │
│           (AsyncOpenCode / OpenCode - 便捷 API)             │
├─────────────────────────────────────────────────────────────┤
│                      API Layer                               │
│     (SessionAPI, MessageAPI, FileAPI, ProjectAPI...)        │
├─────────────────────────────────────────────────────────────┤
│                    Transport Layer                           │
│           (HTTPTransport, SSE Parser, ServerProcess)        │
├─────────────────────────────────────────────────────────────┤
│                     Data Models                              │
│                (Pydantic v2 Models)                          │
└─────────────────────────────────────────────────────────────┘
```

## 文档目录

### 入门

| 文档 | 说明 |
| ---- | ---- |
| [安装指南](installation.md) | 安装要求和步骤 |
| [快速开始](quick-start.md) | 5 分钟上手教程 |

### 核心功能

| 文档 | 说明 |
| ---- | ---- |
| [客户端使用](client.md) | 异步/同步客户端详解 |
| [会话管理](session.md) | 创建、查询、删除会话 |
| [消息发送](message.md) | 发送消息和获取响应 |
| [事件处理](events.md) | SSE 事件流处理 |
| [文件操作](files.md) | 文件读取和搜索 |

### 配置与错误处理

| 文档 | 说明 |
| ---- | ---- |
| [配置选项](configuration.md) | 客户端配置详解 |
| [错误处理](error-handling.md) | 异常类型和处理方式 |

## 快速链接

```python
# 最简单的使用方式
from my_opencode_cli import AsyncOpenCode

async with AsyncOpenCode(start_server=True) as client:
    answer = await client.ask("什么是 Python 装饰器？")
    print(answer)
```

## 相关资源

- [OpenCode 官网](https://opencode.ai)
- [OpenCode API 文档](../opencode/)
- [开发规范](../coding-standards.md)
- [GitHub 仓库](https://github.com/example/my-opencode-cli)
