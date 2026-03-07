# 文件操作

本文档介绍如何使用 OpenCode Python Client 进行文件操作。

## 概述

文件 API 提供以下功能：
- 列出目录内容
- 获取文件状态
- 搜索文件

## 列出文件

### list_all

列出目录中的文件和子目录：

```python
from my_opencode_cli import AsyncOpenCode

async with AsyncOpenCode(start_server=True) as client:
    # 列出当前目录
    files = await client.file.list_all(".")

    for f in files:
        print(f"- {f.name} ({f.type})")
```

### FileInfo 模型

```python
from my_opencode_cli.models import FileInfo

# FileInfo 属性
file.name      # 文件名
file.path      # 文件路径
file.type      # 类型（"file" 或 "directory"）
```

## 文件状态

### status

获取跟踪文件的状态：

```python
async with AsyncOpenCode(start_server=True) as client:
    status = await client.file.status()

    for file in status:
        print(f"- {file.path}: {file.status}")
```

## 完整示例

### 目录浏览

```python
import asyncio
from my_opencode_cli import AsyncOpenCode

async def browse_directory(path="."):
    async with AsyncOpenCode(start_server=True) as client:
        files = await client.file.list_all(path)

        print(f"\n目录: {path}")
        print("-" * 40)

        # 分类显示
        directories = [f for f in files if f.type == "directory"]
        files_only = [f for f in files if f.type == "file"]

        print("目录:")
        for d in directories:
            print(f"  📁 {d.name}/")

        print("\n文件:")
        for f in files_only:
            print(f"  📄 {f.name}")

asyncio.run(browse_directory("src"))
```

### 检查项目状态

```python
import asyncio
from my_opencode_cli import AsyncOpenCode

async def check_project_status():
    async with AsyncOpenCode(start_server=True) as client:
        # 获取文件状态
        status = await client.file.status()

        modified = [f for f in status if f.status == "modified"]
        added = [f for f in status if f.status == "added"]
        deleted = [f for f in status if f.status == "deleted"]

        if modified:
            print(f"修改的文件: {len(modified)}")
        if added:
            print(f"新增的文件: {len(added)}")
        if deleted:
            print(f"删除的文件: {len(deleted)}")

asyncio.run(check_project_status())
```

## 注意事项

- 文件操作基于 OpenCode 服务器的工作目录
- 路径使用相对于项目根目录的相对路径
- 文件状态需要 Git 仓库支持

## 下一步

- [会话管理](session.md) - 会话操作
- [消息发送](message.md) - 消息 API
- [项目信息](client.md) - 项目 API
