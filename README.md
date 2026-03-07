# OpenCode Python Client

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-green.svg)](https://docs.pydantic.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Python 客户端库，用于与 [OpenCode](https://opencode.ai) 服务器交互。

## 安装

```bash
uv add my-opencode-cli
# 或
pip install my-opencode-cli
```

## 快速开始

```python
import asyncio
from my_opencode_cli import AsyncOpenCode

async def main():
    async with AsyncOpenCode(start_server=True) as client:
        # 快速提问
        answer = await client.ask("什么是 Python 装饰器？")
        print(answer)

        # 流式输出
        async for event in client.ask_stream("写一个快速排序"):
            if event.type == "message.part.updated":
                text = event.properties.part.text
                if text:
                    print(text, end="")

asyncio.run(main())
```

同步客户端：

```python
from my_opencode_cli import OpenCode

with OpenCode(start_server=True) as client:
    print(client.ask("什么是闭包？"))
```

## 文档

详细文档请参阅 [docs/guide/](docs/guide/)。

## 开发

```bash
git clone https://github.com/iibyteCoder/my-opencode-cli.git
cd my-opencode-cli
uv sync --all-extras

# 测试
uv run pytest

# 类型检查
uv run mypy src/opencode_client --strict
```

## 许可证

[MIT License](LICENSE)
