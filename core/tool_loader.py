"""Discover JSON tool metadata and load its Python callable dynamically."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from core.tool_registry import ToolDefinition, ToolRegistry


def default_metadata_directory() -> Path:
    return Path(__file__).resolve().parents[1] / "tools" / "metadata"


def load_tools(
    registry: ToolRegistry,
    metadata_directory: Path | None = None,
) -> int:
    """Load every JSON tool definition and return the number registered."""
    directory = metadata_directory or default_metadata_directory()
    if not directory.exists():
        raise FileNotFoundError(f"Tool metadata directory does not exist: {directory}")

    loaded = 0
    for metadata_path in sorted(directory.glob("*.json")):
        metadata = _read_metadata(metadata_path)
        module_name = _required_string(metadata, "module", metadata_path)
        function_name = _required_string(metadata, "function", metadata_path)
        module = importlib.import_module(module_name)
        handler = getattr(module, function_name, None)
        if handler is None or not callable(handler):
            raise TypeError(
                f"Configured tool function is not callable: {module_name}.{function_name}"
            )

        definition = ToolDefinition(
            name=_required_string(metadata, "name", metadata_path),
            description=_required_string(metadata, "description", metadata_path),
            module=module_name,
            function=function_name,
            parameters=_required_object(metadata, "parameters", metadata_path),
            requires_confirmation=bool(metadata.get("requires_confirmation", False)),
        )
        registry.register(definition, handler)
        loaded += 1
    return loaded


def _read_metadata(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as file:
            value = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in tool metadata {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"Tool metadata must be a JSON object: {path}")
    return value


def _required_string(metadata: dict[str, Any], key: str, path: Path) -> str:
    value = metadata.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Tool metadata field '{key}' must be a non-empty string: {path}")
    return value


def _required_object(metadata: dict[str, Any], key: str, path: Path) -> dict[str, Any]:
    value = metadata.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Tool metadata field '{key}' must be an object: {path}")
    return value
