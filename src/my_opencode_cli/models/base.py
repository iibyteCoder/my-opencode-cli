"""Pydantic 模型基类。"""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict


class OpenCodeModel(BaseModel):
    """所有 Pydantic 模型的基类。

    提供统一的配置和行为。
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",  # 禁止额外字段
        validate_assignment=True,  # 赋值时验证
        use_enum_values=True,  # 使用枚举值
        strict=True,  # 严格模式
    )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典。

        Returns:
            包含所有字段的字典
        """
        return self.model_dump()
