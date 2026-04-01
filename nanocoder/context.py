"""Context window management.

When the conversation grows past a threshold, we compress older messages
into a summary to stay within the model's context limit.  This is a
simplified version of Claude Code's multi-layer compaction strategy.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .llm import LLM


def _approx_tokens(text: str) -> int:
    """Rough token count (~3.5 chars/token for mixed en/zh)."""
    return len(text) // 3


def estimate_tokens(messages: list[dict]) -> int:
    total = 0
    for m in messages:
        if m.get("content"):
            total += _approx_tokens(m["content"])
        if m.get("tool_calls"):
            total += _approx_tokens(str(m["tool_calls"]))
    return total


class ContextManager:
    def __init__(self, max_tokens: int = 128_000, ratio: float = 0.7):
        self.max_tokens = max_tokens
        self.threshold = int(max_tokens * ratio)

    def maybe_compress(self, messages: list[dict], llm: LLM | None = None) -> bool:
        """Compress old messages if we're past threshold. Returns True if compressed."""
        if estimate_tokens(messages) < self.threshold:
            return False
        if len(messages) <= 6:
            return False

        # keep the last few messages intact, summarize the rest
        keep = 6
        old = messages[:-keep]
        tail = messages[-keep:]

        summary = self._summarize(old, llm)

        messages.clear()
        messages.append({
            "role": "user",
            "content": f"[Conversation history compressed]\n{summary}",
        })
        messages.append({
            "role": "assistant",
            "content": "Understood, I have the context. Let's continue.",
        })
        messages.extend(tail)
        return True

    def _summarize(self, messages: list[dict], llm: LLM | None) -> str:
        """Try LLM summary, fall back to naive truncation."""
        flat = self._flatten(messages)

        if llm:
            try:
                resp = llm.chat(
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Summarize this conversation concisely. "
                                "Keep: file paths, key decisions, code changes, errors encountered. "
                                "Drop: verbose tool outputs, redundant details."
                            ),
                        },
                        {"role": "user", "content": flat[:12000]},
                    ],
                )
                return resp.content
            except Exception:
                pass

        # fallback: just keep the last N chars
        return flat[-4000:] if len(flat) > 4000 else flat

    @staticmethod
    def _flatten(messages: list[dict]) -> str:
        parts = []
        for m in messages:
            role = m.get("role", "?")
            text = m.get("content", "") or ""
            if text:
                parts.append(f"[{role}] {text[:300]}")
        return "\n".join(parts)
