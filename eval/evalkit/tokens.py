"""Token counting backends.

Two backends behind one interface:

* ``TiktokenCounter`` — **currently active**. Fast, offline, no credentials.
  It is an *approximation*: tiktoken is OpenAI's tokenizer, not Anthropic's, and
  it systematically **undercounts** Claude tokens — typically 15-20% on prose and
  worse on the heavy Markdown tables these instruction files are full of. Every
  number it produces is tagged ``approximate=True`` and the report labels it as
  such, so an approximate figure can never be mistaken for a real Claude count.
  Use it for *relative* signal — growth over time, which stage load-out is
  heaviest — not for absolute budget decisions.

* ``AnthropicCounter`` — **placeholder**, wired but not enabled. Uses
  ``client.messages.count_tokens``, the only source of truth for Claude token
  counts. Swapping backends is a single ``--token-backend anthropic`` flag once
  the body of ``_count_uncached`` is filled in; nothing else in the codebase
  changes, because every caller goes through ``TokenCounter``.

Counts are model-specific, so the model id is part of the cache key.
"""

from __future__ import annotations

import hashlib
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path

DEFAULT_MODEL = "claude-opus-5"
DEFAULT_TIKTOKEN_ENCODING = "cl100k_base"


class TokenCounter(ABC):
    """Counts tokens for a chunk of text."""

    #: Human-readable backend name, surfaced in the report.
    name: str = "abstract"
    #: True when counts are not real Claude tokens. Drives report labelling.
    approximate: bool = True
    #: One-line explanation printed alongside any approximate number.
    disclaimer: str = ""

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self.model = model

    @abstractmethod
    def _count_uncached(self, text: str) -> int: ...

    def count(self, text: str) -> int:
        return self._count_uncached(text)

    def count_composite(self, parts: list[str], separator: str = "\n\n") -> int:
        """Count a multi-file payload as ONE request.

        Deliberately not ``sum(count(p) for p in parts)``. Token counts are not
        additive: every message carries envelope overhead, and tokenization at a
        concatenation boundary differs from tokenizing each side alone. The
        composite is what a stage run actually sends, so it is what gets counted.
        """
        return self.count(separator.join(parts))


class TiktokenCounter(TokenCounter):
    name = "tiktoken"
    approximate = True
    disclaimer = (
        "tiktoken is OpenAI's tokenizer, not Anthropic's — counts undercount Claude "
        "(typically 15-20%, worse on tables). Treat as relative signal only."
    )

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        encoding: str = DEFAULT_TIKTOKEN_ENCODING,
    ) -> None:
        super().__init__(model)
        try:
            import tiktoken
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "tiktoken is not installed. Run `uv sync` in eval/."
            ) from exc
        self.encoding_name = encoding
        self._enc = tiktoken.get_encoding(encoding)
        self.name = f"tiktoken:{encoding}"

    def _count_uncached(self, text: str) -> int:
        return len(self._enc.encode(text, disallowed_special=()))


class AnthropicCounter(TokenCounter):
    """PLACEHOLDER — the real Claude token count. Not yet enabled.

    To activate, fill in ``_count_uncached`` with the call below, add
    ``anthropic`` to the base dependencies in pyproject.toml, and pass
    ``--token-backend anthropic``. No other code changes are needed.

        import anthropic
        client = anthropic.Anthropic()      # resolves ANTHROPIC_API_KEY, or an
                                            # `ant auth login` profile
        resp = client.messages.count_tokens(
            model=self.model,               # e.g. "claude-opus-5"
            messages=[{"role": "user", "content": text}],
        )
        return resp.input_tokens

    Two things to settle when enabling it:

    1. **Framing.** ``count_tokens`` counts a *request*, not a file. Everything
       here is framed as a single user message; that convention must be held
       constant or cross-commit deltas stop being comparable. If the real stage
       harness turns out to split system/user, re-baseline once and note it.
    2. **Rate limits.** A cold full run is ~15 calls (9 files + 6 composites),
       so this is cheap — but caching by content hash keeps repeat runs at zero.
    """

    name = "anthropic:count_tokens"
    approximate = False
    disclaimer = ""

    def _count_uncached(self, text: str) -> int:
        raise NotImplementedError(
            "AnthropicCounter is a placeholder — see the class docstring for the "
            "three-line body that activates it. Use --token-backend tiktoken for now."
        )


class CachingCounter(TokenCounter):
    """Wraps a backend with an on-disk cache keyed by content hash + backend + model.

    Keyed on content rather than mtime so a git checkout does not invalidate
    everything. Backend and model are in the key because counts differ per
    tokenizer — a cache written by tiktoken must never be served to the
    Anthropic backend.
    """

    def __init__(self, inner: TokenCounter, cache_dir: Path) -> None:
        super().__init__(inner.model)
        self.inner = inner
        self.name = inner.name
        self.approximate = inner.approximate
        self.disclaimer = inner.disclaimer
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._path = self.cache_dir / "tokens.json"
        self._data: dict[str, int] = {}
        self._dirty = False
        if self._path.exists():
            try:
                self._data = json.loads(self._path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._data = {}

    def _key(self, text: str) -> str:
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"{self.name}|{self.model}|{h}"

    def _count_uncached(self, text: str) -> int:
        return self.inner._count_uncached(text)

    def count(self, text: str) -> int:
        key = self._key(text)
        if key in self._data:
            return self._data[key]
        value = self.inner.count(text)
        self._data[key] = value
        self._dirty = True
        return value

    def flush(self) -> None:
        if not self._dirty:
            return
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data), encoding="utf-8")
        os.replace(tmp, self._path)
        self._dirty = False


def get_counter(
    backend: str = "tiktoken",
    model: str = DEFAULT_MODEL,
    cache_dir: Path | None = None,
) -> TokenCounter:
    if backend == "tiktoken":
        inner: TokenCounter = TiktokenCounter(model=model)
    elif backend == "anthropic":
        inner = AnthropicCounter(model=model)
    else:
        raise ValueError(f"unknown token backend: {backend!r} (tiktoken | anthropic)")
    return CachingCounter(inner, cache_dir) if cache_dir else inner
