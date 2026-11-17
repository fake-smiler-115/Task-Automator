import unittest

from core.tool_registry import ToolDefinition, ToolRegistry


class ToolRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = ToolRegistry()
        self.definition = ToolDefinition(
            name="echo",
            description="Return text",
            module="tests",
            function="echo",
            parameters={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        )

    def test_register_and_export_for_ollama(self) -> None:
        self.registry.register(self.definition, lambda text: text)
        self.assertEqual(self.registry.get("echo"), self.definition)
        self.assertEqual(self.registry.ollama_tools()[0]["function"]["name"], "echo")

    def test_duplicate_registration_is_rejected(self) -> None:
        self.registry.register(self.definition, lambda text: text)
        with self.assertRaises(ValueError):
            self.registry.register(self.definition, lambda text: text)
