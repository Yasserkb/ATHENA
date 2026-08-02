from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from athena.config import AppConfig
from athena.orchestrator import AthenaRuntime
from athena.tokenization import (
    GenericTokenCounter,
    ProviderEstimateTokenCounter,
    create_token_counter,
    estimate_tokens,
)


def _write_large_project(root: Path) -> None:
    source = root / "LargeService.py"
    source.write_text(
        "class LargeService:\n"
        + "\n".join(
            f"    def operation_{index}(self): return 'payload-{index}'" for index in range(180)
        )
        + "\n",
        encoding="utf-8",
    )


def test_generic_and_claude_counters_are_honest_estimates() -> None:
    generic = create_token_counter("generic")
    claude = create_token_counter("claude", "claude-test-model")

    assert isinstance(generic, GenericTokenCounter)
    assert generic.count("Athena").value == estimate_tokens("Athena")
    assert generic.exact is False
    assert isinstance(claude, ProviderEstimateTokenCounter)
    assert claude.exact is False
    assert claude.target_model == "claude-test-model"
    assert "remote-counting-disabled" in claude.tokenizer


def test_openai_counter_matches_tiktoken_encoding() -> None:
    tiktoken = pytest.importorskip("tiktoken")
    counter = create_token_counter("openai", openai_encoding="o200k_base")
    if not counter.exact:
        pytest.skip("tiktoken vocabulary is not available in this offline environment")
    text = '{"task":"Update CaféService","evidence":[]}'

    assert counter.exact is True
    assert counter.count(text).value == len(tiktoken.get_encoding("o200k_base").encode(text))
    assert counter.tokenizer == "tiktoken:o200k_base"


def test_context_accounts_for_final_canonical_json_payload(tmp_path: Path) -> None:
    _write_large_project(tmp_path)
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        bundle = runtime.context(
            "Update LargeService operation_50",
            "developer",
            tokenizer_provider="generic",
        )

        payload = bundle.to_json()
        decoded = json.loads(payload)
        assert bundle.estimated_tokens == estimate_tokens(payload)
        assert bundle.exact_tokens is None
        assert bundle.provider_tokens is None
        assert bundle.token_count_source == "heuristic-estimate"
        assert bundle.serialized_bytes == len(payload.encode("utf-8"))
        assert bundle.remaining_budget == bundle.hard_budget - bundle.estimated_tokens
        assert bundle.estimated_tokens <= bundle.hard_budget
        assert decoded["task"] == bundle.task
        assert decoded["persona_card"] == bundle.persona.prompt_card()
        assert decoded["architecture"] == list(bundle.architecture)
        assert decoded["warnings"] == list(bundle.warnings)
        assert decoded["evidence"][0]["start_line"] >= 1
        assert decoded["payload_format"] == "athena-mcp-json-v1"


def test_openai_exact_count_and_cache_are_model_aware(tmp_path: Path) -> None:
    tiktoken = pytest.importorskip("tiktoken")
    _write_large_project(tmp_path)
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        generic = runtime.context(
            "Update LargeService operation_80",
            "developer",
            tokenizer_provider="generic",
        )
        exact = runtime.context(
            "Update LargeService operation_80",
            "developer",
            tokenizer_provider="openai",
            target_model="unknown-test-model",
        )
        if exact.exact_tokens is None:
            pytest.skip("tiktoken vocabulary is not available in this offline environment")

        assert exact is not generic
        assert exact.exact_tokens == len(
            tiktoken.get_encoding("o200k_base").encode(exact.to_json())
        )
        assert exact.provider_tokens == exact.exact_tokens
        assert exact.token_count_source == "local-exact"
        assert exact.target_model == "unknown-test-model"
        assert exact.remaining_budget == exact.hard_budget - exact.exact_tokens
        assert exact.exact_tokens <= exact.hard_budget


def test_hard_payload_budget_drops_evidence_and_reports_it(tmp_path: Path) -> None:
    _write_large_project(tmp_path)
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        persona = runtime.personas.get("developer")
        constrained = replace(
            persona,
            policy=replace(persona.policy, max_context_tokens=700),
        )
        bundle = runtime.retrieval.build_bundle(
            "Update every operation in LargeService and retain all implementation details",
            constrained,
            tmp_path.name,
            1.0,
            tokenizer_provider="generic",
        )

        assert bundle.estimated_tokens <= 700
        assert bundle.remaining_budget >= 0
        assert bundle.dropped_evidence > 0 or any(
            "truncated" in warning.casefold() for warning in bundle.warnings
        )
        assert bundle.estimated_tokens == estimate_tokens(bundle.to_json())


def test_tokenization_configuration_is_strict() -> None:
    config = AppConfig.model_validate(
        {
            "tokenization": {
                "provider": "openai",
                "target_model": "configured-model",
                "openai_encoding": "o200k_base",
                "claude_remote_counting": False,
                "anthropic_api_key_env": "ATHENA_TEST_ANTHROPIC_KEY",
                "copilot_model_provider": "auto",
                "copilot_input_usd_per_million": 3.0,
                "copilot_monthly_ai_credits": 6000,
            }
        }
    )

    assert config.tokenization.provider == "openai"
    assert config.tokenization.target_model == "configured-model"
    assert config.tokenization.copilot_input_usd_per_million == 3.0
    with pytest.raises(ValueError):
        AppConfig.model_validate({"tokenization": {"provider": "invented"}})


def test_claude_remote_provider_count_is_used_without_claiming_exactness(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, object]] = []

    class FakeMessages:
        def count_tokens(self, **kwargs: object) -> SimpleNamespace:
            calls.append(kwargs)
            messages = kwargs["messages"]
            assert isinstance(messages, list)
            content = str(messages[0]["content"])
            return SimpleNamespace(input_tokens=estimate_tokens(content) + 17)

    fake_client = SimpleNamespace(messages=FakeMessages())
    fake_module = SimpleNamespace(Anthropic=lambda api_key: fake_client)
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)
    monkeypatch.setenv("ATHENA_TEST_ANTHROPIC_KEY", "secret-test-key")
    _write_large_project(tmp_path)

    with AthenaRuntime(tmp_path) as runtime:
        runtime.config.tokenization.anthropic_api_key_env = "ATHENA_TEST_ANTHROPIC_KEY"
        runtime.scan()
        bundle = runtime.context(
            "Update LargeService operation_40",
            "developer",
            tokenizer_provider="claude",
            target_model="claude-test-model",
            allow_remote_token_counting=True,
        )

        assert calls
        assert calls[-1]["model"] == "claude-test-model"
        assert bundle.provider_tokens == estimate_tokens(bundle.to_json()) + 17
        assert bundle.exact_tokens is None
        assert bundle.token_count_source == "provider-estimate"
        assert bundle.tokenizer == "anthropic:messages.count_tokens"
        assert bundle.remaining_budget == bundle.hard_budget - bundle.provider_tokens
        assert "secret-test-key" not in bundle.to_json()


def test_claude_remote_failure_degrades_to_visible_local_estimate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingMessages:
        def count_tokens(self, **_: object) -> None:
            raise RuntimeError("synthetic provider failure")

    fake_client = SimpleNamespace(messages=FailingMessages())
    fake_module = SimpleNamespace(Anthropic=lambda api_key: fake_client)
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)
    monkeypatch.setenv("ATHENA_TEST_ANTHROPIC_KEY", "secret-test-key")
    counter = create_token_counter(
        "claude",
        "claude-test-model",
        allow_remote_counting=True,
        anthropic_api_key_env="ATHENA_TEST_ANTHROPIC_KEY",
    )
    count = counter.count('{"task":"test"}')

    assert count.use_for_budget is False
    assert count.exact is False
    assert "remote-count-failed" in count.tokenizer


def test_copilot_counter_delegates_without_claiming_a_github_tokenizer() -> None:
    claude = create_token_counter("copilot", "claude-sonnet-test")
    unknown = create_token_counter("copilot", "vendor-model")

    claude_count = claude.count("Athena context")
    assert claude.provider == "copilot"
    assert claude_count.exact is False
    assert claude_count.use_for_budget is False
    assert claude_count.tokenizer.startswith("copilot:claude-compatible-estimate:")
    assert unknown.tokenizer.startswith("copilot:estimated:")


def test_copilot_economy_reports_input_only_ai_credit_estimate(tmp_path: Path) -> None:
    _write_large_project(tmp_path)
    with AthenaRuntime(tmp_path) as runtime:
        runtime.config.tokenization.copilot_input_usd_per_million = 3.0
        runtime.config.tokenization.copilot_monthly_ai_credits = 6_000
        runtime.scan()
        bundle = runtime.context(
            "Update LargeService operation_20",
            "developer",
            tokenizer_provider="copilot",
            target_model="claude-sonnet-test",
        )

        assert bundle.profile == "copilot-economy"
        assert bundle.hard_budget == 1200
        assert bundle.estimated_tokens <= 1200
        assert bundle.estimated_input_ai_credits == round(bundle.estimated_tokens * 3.0 / 10_000, 6)
        assert bundle.monthly_ai_credit_budget == 6_000
        assert bundle.estimated_monthly_athena_payloads == int(
            6_000 / bundle.estimated_input_ai_credits
        )
        assert bundle.ai_credit_scope == "athena-input-only-uncached"
