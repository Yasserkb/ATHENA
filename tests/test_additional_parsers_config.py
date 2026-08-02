from __future__ import annotations

from pathlib import Path

import pytest

from athena.config import load_config
from athena.errors import ConfigurationError
from athena.indexing.chunker import build_chunks
from athena.indexing.common import content_hash, exact_search_terms, search_terms
from athena.indexing.parsers.config import ConfigurationParser
from athena.indexing.parsers.generic import GenericParser
from athena.indexing.parsers.sql import SqlParser


def test_configuration_and_sql_parsers() -> None:
    yaml_text = "service:\n  endpoint: ${SERVICE_URL:http://localhost}\n"
    config = ConfigurationParser().analyze("application.yml", yaml_text, content_hash(yaml_text))
    assert any(node.qualified_name == "service.endpoint" for node in config.nodes)
    assert any(edge.relation == "BINDS_ENV" for edge in config.edges)

    properties = "client.timeout=2000\n"
    result = ConfigurationParser().analyze(
        "application.properties", properties, content_hash(properties)
    )
    assert any(node.qualified_name == "client.timeout" for node in result.nodes)

    sql = "CREATE TABLE axa.payment(id BIGINT); ALTER TABLE axa.payment ADD amount BIGINT;"
    sql_result = SqlParser().analyze("V1__payment.sql", sql, content_hash(sql))
    assert any(node.qualified_name == "axa.payment" for node in sql_result.nodes)
    assert any(edge.relation == "TOUCHES_TABLE" for edge in sql_result.edges)


def test_generic_parser_and_search_terms() -> None:
    text = "class PaymentGateway:\n    def authorize(self):\n        pass\n"
    result = GenericParser().analyze("gateway.py", text, content_hash(text))
    assert {node.name for node in result.nodes} >= {"PaymentGateway", "authorize"}
    assert "PaymentClient" in exact_search_terms("Add retry to PaymentClient")
    assert "Payment" in search_terms("PaymentClient")


@pytest.mark.parametrize(
    ("path", "source", "expected_symbol", "expected_import", "framework"),
    [
        (
            "api.py",
            "from fastapi import FastAPI\nclass UserService:\n    def get_user(self): pass\n",
            "UserService",
            "fastapi",
            "fastapi",
        ),
        (
            "handler.ts",
            "import express from 'express';\nexport function createUser() {}\n",
            "createUser",
            "express",
            "express",
        ),
        (
            "main.go",
            'package api\nimport "github.com/gin-gonic/gin"\nfunc CreateUser() {}\n',
            "CreateUser",
            "github.com/gin-gonic/gin",
            "gin",
        ),
        (
            "users.rs",
            "use actix_web::web;\npub struct UserService;\npub fn create_user() {}\n",
            "UserService",
            "actix_web.web",
            "actix",
        ),
        (
            "UsersController.cs",
            "using Microsoft.AspNetCore.Mvc;\nnamespace Api;\npublic class UsersController {}\n",
            "UsersController",
            "Microsoft.AspNetCore.Mvc",
            "aspnet-core",
        ),
    ],
)
def test_generic_parser_extracts_multiple_languages_and_framework_hints(
    path: str, source: str, expected_symbol: str, expected_import: str, framework: str
) -> None:
    result = GenericParser().analyze(path, source, content_hash(source))
    assert any(node.name == expected_symbol for node in result.nodes)
    assert any(node.qualified_name == expected_import for node in result.nodes)
    assert any(framework in node.metadata.get("frameworks", []) for node in result.nodes)


def test_configuration_validation(tmp_path: Path) -> None:
    assert load_config(tmp_path).schema_version == 1
    config_dir = tmp_path / ".athena"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text("unknown: true\n", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_config(tmp_path)


def test_markdown_chunks_follow_heading_boundaries() -> None:
    text = "# Intro\n" + "intro\n" * 5 + "## Authentication\n" + "auth\n" * 6
    chunks = build_chunks("guide.md", text, "markdown", (), 20, 2)
    assert [(chunk.start_line, chunk.end_line) for chunk in chunks] == [(1, 6), (7, 13)]
    assert "section:authentication" in chunks[1].tags
    assert chunks[1].content.startswith("## Authentication")
