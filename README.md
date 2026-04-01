# NanoCoder

**The entire essence of an AI coding agent, in ~950 lines of Python.**

NanoCoder distills the core architecture of production AI coding agents (like Claude Code) into a minimal, hackable, and fully functional implementation. Think of it as **nanoGPT for coding agents** — small enough to read in one sitting, powerful enough to actually use.

> I analyzed 512,000 lines of leaked Claude Code source, extracted the key architectural patterns, and reimplemented them in under 1,000 lines of clean Python. This is the result.

[English](README.md) | [中文](README_CN.md)

## Why NanoCoder?

|  | Claude Code | Claw-Code | NanoCoder |
|---|---|---|---|
| Language | TypeScript (512K LoC) | Python + Rust | **Python (~950 LoC)** |
| LLM Support | Anthropic only | Multi-provider | **Any OpenAI-compatible API** |
| Can you read the full source? | No (proprietary) | Difficult (huge codebase) | **Yes, in one afternoon** |
| Designed for | End users | End users | **Developers who want to build their own** |
| Hackability | Closed source | Complex architecture | **Fork and build in minutes** |

NanoCoder is **not** trying to replace Claude Code. It's a **reference implementation** and **starting point** for developers who want to understand how AI coding agents work and build their own.

## Features

- **Agentic tool loop** — LLM calls tools, observes results, decides next step, repeats until done
- **6 built-in tools** — bash, read_file, write_file, edit_file, glob, grep
- **Search-and-replace editing** — the key innovation that makes LLM code edits reliable (exact match required, no ambiguity)
- **Streaming output** — tokens appear in real-time as the model generates
- **Context compression** — automatically summarizes old conversation when approaching token limit
- **Any LLM provider** — OpenAI, DeepSeek, Qwen, Kimi, GLM, Ollama, or any OpenAI-compatible endpoint
- **Interactive REPL** — command history, model switching, token tracking
- **One-shot mode** — pipe tasks via `nanocoder -p "fix the bug in main.py"`

## Quick Start

```bash
pip install nanocoder

# OpenAI
export OPENAI_API_KEY=sk-...
nanocoder

# DeepSeek
export OPENAI_API_KEY=sk-... OPENAI_BASE_URL=https://api.deepseek.com
nanocoder -m deepseek-chat

# Qwen (via DashScope)
export OPENAI_API_KEY=sk-... OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
nanocoder -m qwen-plus

# Ollama (local)
export OPENAI_API_KEY=ollama OPENAI_BASE_URL=http://localhost:11434/v1
nanocoder -m qwen2.5-coder
```

## Supported LLM Providers

NanoCoder works with **any OpenAI-compatible API**. Here are some popular ones:

| Provider | Base URL | Example Model |
|---|---|---|
| OpenAI | *(default)* | `gpt-4o`, `gpt-4o-mini` |
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat`, `deepseek-coder` |
| Qwen (Alibaba) | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus`, `qwen-max` |
| Kimi (Moonshot) | `https://api.moonshot.cn/v1` | `moonshot-v1-128k` |
| GLM (Zhipu) | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-plus` |
| Ollama | `http://localhost:11434/v1` | `qwen2.5-coder`, `llama3` |
| vLLM | `http://localhost:8000/v1` | *(your served model)* |
| OpenRouter | `https://openrouter.ai/api/v1` | `anthropic/claude-sonnet-4` |
| Together AI | `https://api.together.xyz/v1` | `meta-llama/Llama-3-70b` |

## Architecture

The entire codebase fits in your head:

```
nanocoder/
├── cli.py          # REPL interface & arg parsing         (~140 lines)
├── agent.py        # Core agent loop                      (~80 lines)
├── llm.py          # OpenAI-compatible streaming client    (~110 lines)
├── context.py      # Context window compression            (~85 lines)
├── prompt.py       # System prompt generation              (~35 lines)
├── config.py       # Environment-based configuration       (~30 lines)
└── tools/
    ├── base.py     # Tool base class                       (~20 lines)
    ├── bash.py     # Shell command execution               (~45 lines)
    ├── read.py     # File reading with line numbers        (~40 lines)
    ├── write.py    # File creation/overwrite               (~30 lines)
    ├── edit.py     # Search-and-replace editing            (~55 lines)
    ├── glob_tool.py # File pattern matching                (~35 lines)
    └── grep.py     # Regex content search                  (~60 lines)
```

### How the Agent Loop Works

```
User input
    │
    ▼
┌─────────────────────────────┐
│  Build messages              │
│  (system prompt + history)   │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Call LLM (streaming)        │◄──────────────┐
│  with tool definitions       │               │
└──────────┬──────────────────┘               │
           │                                   │
     ┌─────┴─────┐                            │
     │           │                             │
  text?     tool calls?                        │
     │           │                             │
     ▼           ▼                             │
  Return    Execute each tool                  │
  to user   Append results to history ─────────┘
```

This is the same fundamental loop used by Claude Code, ChatGPT, and every other agentic coding assistant. The difference is that here you can read and modify every piece of it.

### Key Design Decisions (from Claude Code)

1. **Search-and-replace editing** (`edit_file`): Instead of line-number patches or whole-file rewrites, the LLM specifies an exact substring to find and replace. The substring must be unique in the file, eliminating edit ambiguity. This is Claude Code's most important innovation for reliable code editing.

2. **Read-before-edit discipline**: The system prompt instructs the LLM to always read a file before modifying it, preventing blind edits.

3. **Context compression**: When conversation history approaches the model's context limit, older messages are automatically summarized to free up space, allowing indefinitely long coding sessions.

4. **Tool output truncation**: Very long command outputs are truncated to prevent context window waste on verbose logs.

## Extending NanoCoder

Adding a new tool takes ~20 lines:

```python
# nanocoder/tools/my_tool.py
from .base import Tool

class MyTool(Tool):
    name = "my_tool"
    description = "Does something useful."
    parameters = {
        "type": "object",
        "properties": {
            "arg1": {"type": "string", "description": "..."},
        },
        "required": ["arg1"],
    }

    def execute(self, arg1: str) -> str:
        # your logic here
        return "result"
```

Then register it in `tools/__init__.py`. That's it.

You can also use NanoCoder as a library:

```python
from nanocoder.agent import Agent
from nanocoder.llm import LLM

llm = LLM(model="deepseek-chat", api_key="sk-...", base_url="https://api.deepseek.com")
agent = Agent(llm=llm)
response = agent.chat("Read main.py and add error handling to the parse function")
print(response)
```

## Configuration

All config is via environment variables (no config files to manage):

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(required)* | API key for your LLM provider |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | API endpoint |
| `NANOCODER_MODEL` | `gpt-4o` | Model name |
| `NANOCODER_MAX_TOKENS` | `4096` | Max tokens per response |
| `NANOCODER_TEMPERATURE` | `0` | Sampling temperature |
| `NANOCODER_MAX_CONTEXT` | `128000` | Context window size |

## REPL Commands

| Command | Description |
|---|---|
| `/help` | Show available commands |
| `/reset` | Clear conversation history |
| `/model <name>` | Switch model mid-conversation |
| `/tokens` | Show token usage for this session |
| `quit` | Exit NanoCoder |

## Philosophy

NanoCoder follows the **nanoGPT philosophy**: minimize complexity, maximize understanding.

- Every file has a single responsibility
- No abstractions for the sake of abstractions
- Comments explain *why*, not *what*
- The whole thing is meant to be forked and modified

If Claude Code is a car, NanoCoder is the engine on a test bench. You can see every moving part, understand how it works, and swap components to build your own vehicle.

## Related

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — Anthropic's official coding agent (proprietary)
- [Claw-Code](https://github.com/instructkr/claw-code) — Full-featured clean-room reimplementation in Python/Rust
- [nanoGPT](https://github.com/karpata/nanoGPT) — The inspiration for this project's philosophy
- [Aider](https://github.com/paul-gauthier/aider) — Established Python AI pair programming tool

## License

MIT License. Fork it, ship it, build something great.

## Author

**Yufeng He** ([@he-yufeng](https://github.com/he-yufeng))

- Agentic AI Researcher @ Moonshot AI (Kimi)
- MS CS @ HKU | Former @ Baidu, Kuaishou
- [Zhihu article: Claude Code Source Analysis (170K+ reads)](https://zhuanlan.zhihu.com/p/1898797658343862272)
