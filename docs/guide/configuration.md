# 配置选项

本文档介绍 OpenCode Python Client 的配置选项。

## ClientConfig

```python
from opencode_client import ClientConfig

config = ClientConfig(
    # 服务器配置
    server_hostname="127.0.0.1",
    server_port=4096,
    startup_timeout=30.0,

    # 请求配置
    request_timeout=600,

    # 会话配置
    cleanup_sessions=True,
)
```

## 配置项详解

### 服务器配置

| 选项 | 类型 | 默认值 | 说明 |
| ---- | ---- | ------ | ---- |
| `server_hostname` | `str` | `"127.0.0.1"` | 服务器主机名 |
| `server_port` | `int` | `4096` | 服务器端口 |
| `startup_timeout` | `float` | `30.0` | 服务器启动超时（秒） |

### 请求配置

| 选项 | 类型 | 默认值 | 说明 |
| ---- | ---- | ------ | ---- |
| `request_timeout` | `int` | `600` | HTTP 请求超时（秒） |

### 会话配置

| 选项 | 类型 | 默认值 | 说明 |
| ---- | ---- | ------ | ---- |
| `cleanup_sessions` | `bool` | `False` | 自动清理 `ask` 创建的临时会话 |

## 使用配置

### 传递给客户端

```python
from opencode_client import AsyncOpenCode, ClientConfig

# 方式 1: 构造函数
config = ClientConfig(server_port=4097, cleanup_sessions=True)
client = AsyncOpenCode(start_server=True, config=config)

# 方式 2: 上下文管理器
async with AsyncOpenCode(start_server=True, config=config) as client:
    pass
```

### 配置示例

#### 长时间任务

对于需要长时间处理的任务，增加超时：

```python
config = ClientConfig(
    startup_timeout=60.0,   # 服务器启动超时
    request_timeout=1200,   # 请求超时 20 分钟
)
```

#### 自动清理

避免会话堆积：

```python
config = ClientConfig(cleanup_sessions=True)

async with AsyncOpenCode(start_server=True, config=config) as client:
    # ask 创建的会话会在退出上下文时自动删除
    answer = await client.ask("Hello")
```

#### 多实例运行

使用不同端口运行多个实例：

```python
config1 = ClientConfig(server_port=4097)
config2 = ClientConfig(server_port=4098)

client1 = AsyncOpenCode(start_server=True, config=config1)
client2 = AsyncOpenCode(start_server=True, config=config2)
```

## 环境变量

客户端支持以下环境变量：

| 变量 | 说明 | 默认值 |
| ---- | ---- | ------ |
| `OPENCODE_URL` | 默认服务器 URL | `http://127.0.0.1:4096` |
| `OPENCODE_TIMEOUT` | 默认请求超时（秒） | `600` |

使用示例：

```bash
export OPENCODE_URL=http://remote-server:4096
export OPENCODE_TIMEOUT=1200

python your_script.py
```

## 完整配置示例

```python
from opencode_client import AsyncOpenCode, ClientConfig

async def main():
    config = ClientConfig(
        # 服务器配置
        server_hostname="127.0.0.1",
        server_port=4096,
        startup_timeout=60.0,

        # 请求配置
        request_timeout=1200,  # 20 分钟

        # 会话配置
        cleanup_sessions=True,
    )

    async with AsyncOpenCode(start_server=True, config=config) as client:
        answer = await client.ask("Hello")
        print(answer)

asyncio.run(main())
```

## 下一步

- [错误处理](error-handling.md) - 异常类型和处理
- [客户端使用](client.md) - 客户端详解
