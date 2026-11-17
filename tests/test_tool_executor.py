import unittest

from core.tool_executor import ToolExecutor
from core.tool_registry import ToolDefinition, ToolRegistry


def add(first: int, second: int) -> int:
    return first + second


class ToolExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = ToolRegistry()
        self.registry.register(
            ToolDefinition(
                name="add",
                description="Add numbers",
                module=__name__,
                function="add",
                parameters={
                    "type": "object",
                    "properties": {
                        "first": {"type": "integer"},
                        "second": {"type": "integer"},
                    },
                    "required": ["first", "second"],
                },
            ),
            add,
        )

    def test_successful_execution(self) -> None:
        result = ToolExecutor(self.registry).execute("add", {"first": 2, "second": 3})
        self.assertEqual(result, {"success": True, "tool": "add", "result": 5, "error": None})

    def test_unknown_tool_is_rejected(self) -> None:
        result = ToolExecutor(self.registry).execute("missing", {})
        self.assertFalse(result["success"])
        self.assertIn("Unknown tool", result["error"])

    def test_missing_and_invalid_arguments_are_rejected(self) -> None:
        missing = ToolExecutor(self.registry).execute("add", {"first": 2})
        invalid = ToolExecutor(self.registry).execute(
            "add", {"first": "two", "second": 3}
        )
        self.assertIn("Missing required", missing["error"])
        self.assertIn("must be of type", invalid["error"])

    def test_confirmation_can_cancel_execution(self) -> None:
        definition = self.registry.get("add")
        self.registry = ToolRegistry()
        self.registry.register(
            ToolDefinition(
                name=definition.name,
                description=definition.description,
                module=definition.module,
                function=definition.function,
                parameters=definition.parameters,
                requires_confirmation=True,
            ),
            add,
        )
        result = ToolExecutor(self.registry, confirmation_callback=lambda *_: False).execute(
            "add", {"first": 1, "second": 2}
        )
        self.assertFalse(result["success"])
        self.assertIn("cancelled", result["error"])
