"""Terminal entry point for the local Ollama automation assistant."""

from __future__ import annotations

import argparse
import json
import logging
from typing import Any

from ai.assistant import Assistant
from ai.ollama_client import OllamaClient
from config.settings import Settings
from core.tool_executor import ToolExecutor
from core.tool_loader import load_tools
from core.tool_registry import ToolDefinition, ToolRegistry


def confirm_tool(definition: ToolDefinition, arguments: dict[str, Any]) -> bool:
    """Ask the human to approve a side-effecting tool call."""
    print(f"\nThe assistant wants to run: {definition.name}")
    print(json.dumps(arguments, indent=2, ensure_ascii=False))
    answer = input("Confirm? (y/n): ").strip().lower()
    return answer in {"y", "yes"}


def build_assistant(settings: Settings) -> Assistant:
    registry = ToolRegistry()
    loaded = load_tools(registry)
    logging.getLogger(__name__).info("Loaded %d tool(s)", loaded)
    executor = ToolExecutor(
        registry,
        confirmation_callback=confirm_tool,
        timeout_seconds=settings.tool_execution_timeout,
    )
    client = OllamaClient(settings.ollama_host, settings.ollama_model)
    return Assistant(client, registry, executor, settings.max_tool_iterations)


def run_interactive(assistant: Assistant) -> None:
    print("AI Assistant is ready. Type 'exit' or 'quit' to stop.")
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if user_input.lower() in {"exit", "quit"}:
            return
        if not user_input:
            continue
        try:
            print(f"Assistant: {assistant.run(user_input)}")
        except Exception as error:
            print(f"Assistant error: {error}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local Ollama AI assistant.")
    parser.add_argument("command", nargs="*", help="natural-language command")
    args = parser.parse_args()

    settings = Settings.from_environment()
    settings.configure_logging()
    try:
        assistant = build_assistant(settings)
        if args.command:
            print(assistant.run(" ".join(args.command)))
        else:
            run_interactive(assistant)
    except Exception as error:
        logging.getLogger(__name__).error("Assistant startup failed: %s", error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
