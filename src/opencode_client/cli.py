"""OpenCode Client 命令行工具。

提供简单的命令行接口来测试和使用 OpenCode 客户端。
"""

from __future__ import annotations

import asyncio
import sys


async def main():
    """命令行入口。"""
    if len(sys.argv) < 2:
        print("用法: opencode-client <message>")
        print("示例: opencode-client '查询当前时间'")
        sys.exit(1)

    message = " ".join(sys.argv[1:])

    from opencode_client import OpenCodeClient, ServerConfig

    print("启动 OpenCode 服务器...")

    async with OpenCodeClient(ServerConfig(port=4096)) as client:
        print(f"服务器已启动: {client.config.base_url}")

        print(f"发送消息: {message}")

        session_id = await client.create_session("CLI Test")
        response = await client.send_message(session_id, message)
        print(f"响应: {response}")

        await client.delete_session(session_id)
        print("会话已清理")


if __name__ == "__main__":
    asyncio.run(main())
