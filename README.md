# Local Ollama Desktop Assistant

This project provides a terminal assistant that uses a local Ollama model to
choose and invoke registered Python automation tools. It does not use
LangChain, CrewAI, Playwright, or Selenium.

## Project structure

```text
ai/                    Ollama client and tool-calling conversation loop
config/                Environment-based settings
core/                  Tool registry, loader, validation, and execution
tools/metadata/        JSON Schema-compatible tool definitions
tools/whatsapp/        Adapter around the existing WhatsApp automation
tools/whatapp.py       Existing Brave/WhatsApp automation implementation
tests/                 Unit tests for registry and executor
main.py                One-shot and interactive terminal interface
requirements.txt       Python dependencies
```

## Setup

1. Install and start [Ollama](https://ollama.com/).
2. Download a tool-capable local model:

   ```bash
   ollama pull qwen3.6:35b-a3b
   ```

3. Create a virtual environment and install the SDK:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

4. For WhatsApp automation, Brave should be running and the terminal app must
   have macOS **Accessibility** permission under **System Settings → Privacy &
   Security → Accessibility**.

The defaults can be changed with environment variables:

```bash
export OLLAMA_HOST=http://127.0.0.1:11434
export OLLAMA_MODEL=qwen3.6:35b-a3b
export MAX_TOOL_ITERATIONS=5
export TOOL_EXECUTION_TIMEOUT=60
export LOG_LEVEL=INFO
```

## Usage

One-shot command:

```bash
python main.py "Send John a WhatsApp message saying I'll be late"
```

If you do not activate the virtual environment, run the command with its
interpreter explicitly:

```bash
.venv/bin/python main.py "Send John a WhatsApp message saying I'll be late"
```

Interactive mode:

```bash
python main.py
```

The assistant asks for confirmation before sending a WhatsApp message. The
model cannot bypass this confirmation or execute unregistered Python code.

The existing WhatsApp automation can still be run directly:

```bash
python tools/whatapp.py "John Doe" "Hello, I will call you soon."
```

## Adding a tool

1. Put the implementation in a Python module under `tools/`.
2. Add a JSON metadata file under `tools/metadata/` with the module, function,
   description, parameter schema, and confirmation requirement.
3. Restart `main.py`.

No changes to the Ollama client, assistant, registry, or executor are needed.

## Tests

```bash
python -m unittest discover -s tests -v
```
