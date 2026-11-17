"""Registry of safe, explicitly registered tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


ToolCallable = Callable[..., Any]


@dataclass(frozen=True)
class ToolDefinition:
    """Metadata needed by Ollama and the execution engine."""

    name: str
    description: str
    module: str
    function: str
    parameters: dict[str, Any]
    requires_confirmation: bool = False

    def ollama_definition(self) -> dict[str, Any]:
        """Return this tool in Ollama's native function-tool format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    """Map metadata names to callable implementations without duplicates."""

    def __init__(self) -> None:
        self._definitions: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, ToolCallable] = {}

    def register(self, definition: ToolDefinition, handler: ToolCallable) -> None:
        if definition.name in self._definitions:
            raise ValueError(f"Tool already registered: {definition.name}")
        if not callable(handler):
            raise TypeError(f"Handler for {definition.name} is not callable")
        self._definitions[definition.name] = definition
        self._handlers[definition.name] = handler

    def get(self, name: str) -> ToolDefinition:
        try:
            return self._definitions[name]
        except KeyError as error:
            raise KeyError(f"Unknown tool: {name}") from error

    def handler(self, name: str) -> ToolCallable:
        try:
            return self._handlers[name]
        except KeyError as error:
            raise KeyError(f"Unknown tool: {name}") from error

    def definitions(self) -> tuple[ToolDefinition, ...]:
        return tuple(self._definitions.values())

    def ollama_tools(self) -> list[dict[str, Any]]:
        return [definition.ollama_definition() for definition in self.definitions()]
