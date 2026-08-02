from __future__ import annotations

import importlib
import math
import os
from dataclasses import dataclass
from typing import Any, Literal, Protocol

TokenizerProvider = Literal["generic", "openai", "claude", "copilot"]
CopilotModelProvider = Literal["auto", "generic", "openai", "claude"]


def estimate_tokens(text: str) -> int:
    """Estimate tokens without assuming a provider vocabulary."""
    if not text:
        return 0
    return max(1, math.ceil(len(text.encode("utf-8")) / 3.6))


class TokenCounter(Protocol):
    @property
    def provider(self) -> TokenizerProvider: ...

    @property
    def target_model(self) -> str | None: ...

    @property
    def tokenizer(self) -> str: ...

    @property
    def exact(self) -> bool: ...

    def count(self, text: str) -> TokenCount: ...


@dataclass(frozen=True, slots=True)
class TokenCount:
    value: int
    exact: bool
    use_for_budget: bool
    tokenizer: str


@dataclass(frozen=True, slots=True)
class GenericTokenCounter:
    provider: TokenizerProvider = "generic"
    target_model: str | None = None
    tokenizer: str = "estimated:utf8-bytes-v1"
    exact: bool = False

    def count(self, text: str) -> TokenCount:
        return TokenCount(estimate_tokens(text), False, False, self.tokenizer)


@dataclass(frozen=True, slots=True)
class OpenAITokenCounter:
    encoding: Any
    target_model: str | None
    encoding_name: str
    provider: TokenizerProvider = "openai"
    exact: bool = True

    @property
    def tokenizer(self) -> str:
        return f"tiktoken:{self.encoding_name}"

    def count(self, text: str) -> TokenCount:
        return TokenCount(len(self.encoding.encode(text)), True, True, self.tokenizer)


@dataclass(frozen=True, slots=True)
class ProviderEstimateTokenCounter:
    provider: TokenizerProvider
    target_model: str | None
    reason: str
    exact: bool = False

    @property
    def tokenizer(self) -> str:
        return f"{self.provider}-compatible-estimate:utf8-bytes-v1:{self.reason}"

    def count(self, text: str) -> TokenCount:
        return TokenCount(estimate_tokens(text), False, False, self.tokenizer)


@dataclass(frozen=True, slots=True)
class AnthropicTokenCounter:
    client: Any
    target_model: str
    provider: TokenizerProvider = "claude"
    tokenizer: str = "anthropic:messages.count_tokens"
    exact: bool = False

    def count(self, text: str) -> TokenCount:
        try:
            response = self.client.messages.count_tokens(
                model=self.target_model,
                messages=[{"role": "user", "content": text}],
            )
            return TokenCount(int(response.input_tokens), False, True, self.tokenizer)
        except Exception:
            fallback = "claude-compatible-estimate:utf8-bytes-v1:remote-count-failed"
            return TokenCount(estimate_tokens(text), False, False, fallback)


@dataclass(frozen=True, slots=True)
class CopilotTokenCounter:
    delegate: TokenCounter
    target_model: str | None
    provider: TokenizerProvider = "copilot"

    @property
    def tokenizer(self) -> str:
        return f"copilot:{self.delegate.tokenizer}"

    @property
    def exact(self) -> bool:
        return self.delegate.exact

    def count(self, text: str) -> TokenCount:
        result = self.delegate.count(text)
        return TokenCount(
            result.value,
            result.exact,
            result.use_for_budget,
            f"copilot:{result.tokenizer}",
        )


def create_token_counter(
    provider: TokenizerProvider,
    target_model: str | None = None,
    openai_encoding: str = "o200k_base",
    allow_remote_counting: bool = False,
    anthropic_api_key_env: str = "ANTHROPIC_API_KEY",
    copilot_model_provider: CopilotModelProvider = "auto",
) -> TokenCounter:
    """Resolve a local counter without transmitting repository content."""
    if provider == "generic":
        return GenericTokenCounter(target_model=target_model)
    if provider == "copilot":
        delegated_provider = _copilot_model_provider(target_model, copilot_model_provider)
        delegate = create_token_counter(
            delegated_provider,
            target_model,
            openai_encoding,
            False,
            anthropic_api_key_env,
        )
        return CopilotTokenCounter(delegate, target_model)
    if provider == "claude":
        api_key = os.getenv(anthropic_api_key_env)
        if allow_remote_counting and target_model and api_key:
            try:
                anthropic = importlib.import_module("anthropic")
                return AnthropicTokenCounter(
                    client=anthropic.Anthropic(api_key=api_key),
                    target_model=target_model,
                )
            except (ImportError, AttributeError):
                reason = "anthropic-sdk-unavailable"
        elif allow_remote_counting and not target_model:
            reason = "target-model-required"
        elif allow_remote_counting and not api_key:
            reason = f"missing-api-key:{anthropic_api_key_env}"
        else:
            reason = "remote-counting-disabled"
        return ProviderEstimateTokenCounter(
            provider="claude",
            target_model=target_model,
            reason=reason,
        )
    try:
        tiktoken = importlib.import_module("tiktoken")
    except ImportError:
        return ProviderEstimateTokenCounter(
            provider="openai",
            target_model=target_model,
            reason="tiktoken-not-installed",
        )
    try:
        if target_model:
            encoding = tiktoken.encoding_for_model(target_model)
            return OpenAITokenCounter(encoding, target_model, encoding.name)
    except KeyError:
        pass
    except Exception:
        return ProviderEstimateTokenCounter(
            provider="openai",
            target_model=target_model,
            reason="encoding-unavailable",
        )
    try:
        encoding = tiktoken.get_encoding(openai_encoding)
    except Exception:
        return ProviderEstimateTokenCounter(
            provider="openai",
            target_model=target_model,
            reason="encoding-unavailable",
        )
    return OpenAITokenCounter(encoding, target_model, encoding.name)


def _copilot_model_provider(
    target_model: str | None, configured: CopilotModelProvider
) -> Literal["generic", "openai", "claude"]:
    if configured != "auto":
        return configured
    normalized = (target_model or "").casefold()
    if normalized.startswith("claude"):
        return "claude"
    if normalized.startswith(("gpt-", "o1", "o3", "o4")):
        return "openai"
    return "generic"
