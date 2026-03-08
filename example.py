"""
my-opencode-cli 使用示例

运行前请确保已安装 OpenCode CLI 并启动服务：
    opencode

或者使用 uv 运行：
    uv run python example.py
"""

from __future__ import annotations

import asyncio
import time

from my_opencode_cli import AsyncOpenCode


async def basic_ask():
    """简单问答"""
    print("\n=== 1. 简单问答 ===")
    async with AsyncOpenCode(start_server=True) as client:
        answer = await client.ask("用一句话解释什么是 Python")
        print(f"回答: {answer}")


async def stream_response():
    """流式输出"""
    print("\n=== 2. 流式输出 ===")
    async with AsyncOpenCode(start_server=True) as client:
        print("回答: ", end="", flush=True)
        async for event in client.ask_stream("写一个 Python 冒泡排序"):
            # 处理增量事件（流式文本）
            if event.type == "message.part.delta":
                delta = event.properties.delta
                if isinstance(delta, str) and delta:
                    print(delta, end="", flush=True)
            # 处理完整更新事件
            elif event.type == "message.part.updated":
                text = event.properties.part.text
                if text:
                    # 只在最终更新时打印（避免重复）
                    pass
        print()


async def stream_realtime_test():
    """流式输出实时测试 - 带时间戳和统计"""
    print("\n=== 流式输出实时测试 ===")
    async with AsyncOpenCode(start_server=True) as client:
        prompt = "请写一篇 500 字左右的短文，介绍 Python 异步编程的优势和应用场景，包括 asyncio、协程、并发等概念"
        print(f"问题: {prompt}")
        print("-" * 40)

        start_time = time.perf_counter()
        first_chunk_time = None
        event_count = 0
        total_chars = 0

        print("实时输出:\n")
        async for event in client.ask_stream(prompt):
            event_count += 1

            if event.type == "message.part.delta":
                delta = event.properties.delta
                if isinstance(delta, str) and delta:
                    if first_chunk_time is None:
                        first_chunk_time = time.perf_counter()
                    total_chars += len(delta)
                    # 每收到一个 chunk 立即打印
                    print(delta, end="", flush=True)

        end_time = time.perf_counter()
        print("\n")
        print("-" * 40)
        print("统计信息:")
        print(f"  - 总事件数: {event_count}")
        print(f"  - 总字符数: {total_chars}")
        print(f"  - 首字节延迟: {(first_chunk_time or start_time) - start_time:.3f}s" if first_chunk_time else "  - 首字节延迟: N/A")
        print(f"  - 总耗时: {end_time - start_time:.3f}s")
        print(f"  - 平均速度: {total_chars / (end_time - start_time):.1f} 字符/秒" if end_time > start_time else "")


async def session_management():
    """会话管理"""
    print("\n=== 3. 会话管理 ===")
    async with AsyncOpenCode(start_server=True) as client:
        # 创建会话
        session = await client.create_session(title="测试会话")
        print(f"创建会话: {session.id}")

        # 多轮对话
        answer1 = await client.ask("记住数字 42", session_id=session.id)
        print(f"第一轮: {answer1[:50]}...")

        answer2 = await client.ask("我让你记住的数字是多少？", session_id=session.id)
        print(f"第二轮: {answer2[:50]}...")

        # 删除会话
        await client.session.delete(session.id)
        print("会话已删除")


async def list_files():
    """文件列表"""
    print("\n=== 4. 文件列表 ===")
    async with AsyncOpenCode(start_server=True) as client:
        files = await client.file.list_all(".")
        print(f"文件数量: {len(files)}")
        for f in files[:5]:  # 只显示前5个
            print(f"  - {f.name} ({f.type})")
        if len(files) > 5:
            print(f"  ... 还有 {len(files) - 5} 个")


async def main():
    """运行所有示例"""
    print("=" * 50)
    print("my-opencode-cli 功能演示")
    print("=" * 50)

    try:
        await basic_ask()
        await stream_response()
        await stream_realtime_test()  # 流式输出实时测试
        await session_management()
        await list_files()

        print("\n" + "=" * 50)
        print("所有示例运行完成！")
        print("=" * 50)

    except Exception as e:
        print(f"\n错误: {e}")
        print("请确保 OpenCode 服务正在运行 (执行 'opencode' 命令)")


if __name__ == "__main__":
    asyncio.run(main())
