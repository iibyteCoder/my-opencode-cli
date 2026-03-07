# OpenCode Python Client

Python 客户端库，用于与 OpenCode 服务器交互。

## 项目结构

```
src/opencode_client/
├── api/           # 低层 API（MessageAPI、SessionAPI 等）
├── client/        # 高层客户端（AsyncOpenCode、OpenCode）
├── core/          # 核心配置和错误
├── models/        # Pydantic 数据模型
├── transport/     # 传输层（HTTP、进程）
└── utils/         # 工具函数
```

## 开发规范

详见 [docs/coding-standards.md](docs/coding-standards.md)

关键点：

- Python 3.11+ / Pydantic v2 / 严格 mypy
- 异步优先，同步包装
- 非泛型基类用于类型注解
- 禁止 `# type: ignore` 取巧

## OpenCode 官方文档

API 端点和数据模型必须严格遵循 OpenCode 官方文档：

- [docs/opencode/](docs/opencode/) - OpenCode 服务器 API 文档

## 代码检查

```bash
# 类型检查（严格模式）
uv run mypy src/opencode_client --strict

# 代码风格检查
uv run ruff check src/opencode_client

# 运行测试
uv run pytest
```
