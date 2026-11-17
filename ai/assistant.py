"""Conversation and native tool-calling loop for the local assistant."""

from __future__ import annotations

import json
from typing import Any

from ai.ollama_client import OllamaClient
from core.tool_executor import ToolExecutor
from core.tool_registry import ToolRegistry


class AssistantError(RuntimeError):
    """Raised when the assistant cannot complete a conversation."""


class Assistant:
    """Maintain conversation messages and execute Ollama-requested tools."""

    def __init__(
        self,
        client: OllamaClient,
        registry: ToolRegistry,
        executor: ToolExecutor,
        max_iterations: int,
    ) -> None:
        self.client = client
        self.registry = registry
        self.executor = executor
        self.max_iterations = max_iterations
        self.messages: list[dict[str, Any]] = []

    def run(self, user_input: str) -> str:
        """Process one user request, including any sequential tool calls."""
        self.messages.append({"role": "user", "content": user_input})

        for _ in range(self.max_iterations):
            response = self.client.chat(self.messages, self.registry.ollama_tools())
            message = response.get("message")
            if not isinstance(message, dict):
                raise AssistantError("Ollama returned a response without a message.")

            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                content = message.get("content", "")
                if not isinstance(content, str):
                    content = str(content)
                self.messages.append({"role": "assistant", "content": content})
                return content

            assistant_message = {
                "role": "assistant",
                "content": message.get("content", "") or "",
                "tool_calls": tool_calls,
            }
            self.messages.append(assistant_message)

            for tool_call in tool_calls:
                name, arguments = self._parse_tool_call(tool_call)
                result = self.executor.execute(name, arguments)
                self.messages.append(
                    {
                        "role": "tool",
                        "content": json.dumps(result, default=str),
                    }
                )

        raise AssistantError(
            f"The assistant reached its maximum of {self.max_iterations} tool-call iterations."
        )

    @staticmethod
    def _parse_tool_call(tool_call: Any) -> tuple[str, Any]:
        if not isinstance(tool_call, dict):
            raise AssistantError("Ollama returned an invalid tool call.")
        function = tool_call.get("function", {})
        if not isinstance(function, dict):
            raise AssistantError("Ollama returned an invalid tool function.")
        name = function.get("name")
        if not isinstance(name, str) or not name:
            raise AssistantError("Ollama returned a tool call without a name.")
        return name, function.get("arguments", {})
