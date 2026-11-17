"""Environment-based settings for the local assistant."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3.6:35b-a3b"
    max_tool_iterations: int = 5
    tool_execution_timeout: float = 60.0
    log_level: str = "INFO"

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            ollama_host=os.getenv("OLLAMA_HOST", cls.ollama_host),
            ollama_model=os.getenv("OLLAMA_MODEL", cls.ollama_model),
            max_tool_iterations=_positive_int(
                os.getenv("MAX_TOOL_ITERATIONS"), cls.max_tool_iterations
            ),
            tool_execution_timeout=_positive_float(
                os.getenv("TOOL_EXECUTION_TIMEOUT"), cls.tool_execution_timeout
            ),
            log_level=os.getenv("LOG_LEVEL", cls.log_level).upper(),
        )

    def configure_logging(self) -> None:
        logging.basicConfig(
            level=getattr(logging, self.log_level, logging.INFO),
            format="%(levelname)s %(name)s: %(message)s",
        )


def _positive_int(value: str | None, default: int) -> int:
    try:
        parsed = int(value) if value is not None else default
        return parsed if parsed > 0 else default
    except ValueError:
        return default


def _positive_float(value: str | None, default: float) -> float:
    try:
        parsed = float(value) if value is not None else default
        return parsed if parsed > 0 else default
    except ValueError:
        return default
