"""Validation, confirmation, timeout, and safe execution of registered tools."""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any, Callable, Mapping

from core.tool_registry import ToolDefinition, ToolRegistry


ConfirmationCallback = Callable[[ToolDefinition, dict[str, Any]], bool]


class ToolExecutor:
    """Execute only tools present in a registry and return structured results."""

    def __init__(
        self,
        registry: ToolRegistry,
        confirmation_callback: ConfirmationCallback | None = None,
        timeout_seconds: float = 60.0,
        logger: logging.Logger | None = None,
    ) -> None:
        self.registry = registry
        self.confirmation_callback = confirmation_callback
        self.timeout_seconds = timeout_seconds
        self.logger = logger or logging.getLogger(__name__)

    def execute(self, tool_name: str, arguments: Any) -> dict[str, Any]:
        """Validate and execute one model-requested tool call."""
        try:
            definition = self.registry.get(tool_name)
            parsed_arguments = self._parse_arguments(arguments)
            self._validate_arguments(definition.parameters, parsed_arguments)

            if definition.requires_confirmation:
                if self.confirmation_callback is None:
                    return self._failure(tool_name, "User confirmation is required.")
                if not self.confirmation_callback(definition, parsed_arguments):
                    return self._failure(tool_name, "User cancelled the tool execution.")

            handler = self.registry.handler(tool_name)
            result = self._run_with_timeout(handler, parsed_arguments)
            return {"success": True, "tool": tool_name, "result": result, "error": None}
        except (KeyError, TypeError, ValueError, TimeoutError) as error:
            return self._failure(tool_name, str(error))
        except Exception as error:  # Tool errors must be returned to the model.
            self.logger.exception("Tool execution failed: %s", tool_name)
            return self._failure(tool_name, str(error))

    def _run_with_timeout(self, handler: Callable[..., Any], arguments: dict[str, Any]) -> Any:
        pool = ThreadPoolExecutor(max_workers=1)
        future = pool.submit(handler, **arguments)
        try:
            return future.result(timeout=self.timeout_seconds)
        except FutureTimeoutError as error:
            future.cancel()
            raise TimeoutError(
                f"Tool execution exceeded {self.timeout_seconds} seconds."
            ) from error
        finally:
            pool.shutdown(wait=False, cancel_futures=True)

    @staticmethod
    def _parse_arguments(arguments: Any) -> dict[str, Any]:
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as error:
                raise ValueError(f"Tool arguments are not valid JSON: {error}") from error
        if not isinstance(arguments, dict):
            raise TypeError("Tool arguments must be a JSON object.")
        return arguments

    @classmethod
    def _validate_arguments(
        cls,
        schema: Mapping[str, Any],
        arguments: dict[str, Any],
    ) -> None:
        if schema.get("type") != "object":
            raise ValueError("Tool parameter schema must have type 'object'.")
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        if not isinstance(properties, dict) or not isinstance(required, list):
            raise ValueError("Tool parameter schema has invalid properties or required fields.")

        missing = [name for name in required if name not in arguments]
        if missing:
            raise ValueError(f"Missing required parameter(s): {', '.join(missing)}")
        unknown = [name for name in arguments if name not in properties]
        if unknown:
            raise ValueError(f"Unknown parameter(s): {', '.join(unknown)}")
        for name, value in arguments.items():
            expected = properties[name].get("type")
            if not cls._matches_type(value, expected):
                raise TypeError(
                    f"Parameter '{name}' must be of type '{expected}'."
                )

    @staticmethod
    def _matches_type(value: Any, expected: Any) -> bool:
        if expected == "string":
            return isinstance(value, str)
        if expected == "boolean":
            return isinstance(value, bool)
        if expected == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if expected == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        if expected == "object":
            return isinstance(value, dict)
        if expected == "array":
            return isinstance(value, list)
        if expected == "null":
            return value is None
        return False

    @staticmethod
    def _failure(tool_name: str, error: str) -> dict[str, Any]:
        return {"success": False, "tool": tool_name, "result": None, "error": error}
