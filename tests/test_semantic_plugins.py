from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from athena.config import SemanticConfig
from athena.domain import GraphNode
from athena.indexing.common import content_hash
from athena.indexing.models import AnalysisResult
from athena.indexing.parsers import ParserRegistry
from athena.indexing.parsers.generic import GenericParser
from athena.indexing.semantic import SemanticPluginRegistry
from athena.orchestrator import AthenaRuntime


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


@pytest.mark.parametrize(
    ("path", "source", "contract", "framework"),
    [
        (
            "api.py",
            'from fastapi import FastAPI\napp = FastAPI()\n@app.get("/users/{user_id}")\n'
            "def user(user_id: str): pass\n",
            "GET /users/{}",
            "fastapi",
        ),
        (
            "routes.ts",
            "import express from 'express';\n"
            "function getUser() {}\nrouter.get('/users/:id', getUser);\n",
            "GET /users/{}",
            "express",
        ),
        (
            "controller.ts",
            "import { Controller, Get } from '@nestjs/common';\n"
            "@Controller('users')\nexport class UsersController {\n"
            "  @Get(':id')\n  findOne() {}\n}\n",
            "GET /users/{}",
            "nestjs",
        ),
        (
            "UsersController.cs",
            'using Microsoft.AspNetCore.Mvc;\n[Route("api/[controller]")]\n'
            'class UsersController {\n[HttpGet("{id}")]\npublic User Get(string id) => null;\n}\n',
            "GET /api/Users/{}",
            "aspnet-core",
        ),
        (
            "routes.go",
            'package api\nfunc Routes() { router.GET("/users/:id", getUser) }\nfunc getUser() {}\n',
            "GET /users/{}",
            "go-http",
        ),
        (
            "routes.rs",
            '#[get("/users/{id}")]\nasync fn get_user() {}\n',
            "GET /users/{}",
            "rust-http",
        ),
    ],
)
def test_framework_plugins_extract_canonical_http_endpoints(
    path: str,
    source: str,
    contract: str,
    framework: str,
) -> None:
    registry = ParserRegistry(SemanticConfig(load_entry_points=False))
    result = registry.parser_for(Path(path)).analyze(path, source, content_hash(source))
    endpoint = next(node for node in result.nodes if node.qualified_name == contract)
    assert endpoint.kind == "endpoint"
    assert endpoint.metadata["framework"] == framework
    assert any(
        edge.relation == "EXPOSES_ENDPOINT" and edge.target_id == endpoint.node_id
        for edge in result.edges
    )


@pytest.mark.parametrize(
    ("path", "source", "contract"),
    [
        ("client.py", 'result = httpx.get("/users/42")\n', "GET /users/42"),
        ("client.ts", "const result = await axios.get(`/users/${userId}`);\n", "GET /users/{}"),
        (
            "Client.java",
            'class Client { void load() { rest.getForObject("/users/42", String.class); } }',
            "GET /users/42",
        ),
        (
            "Client.cs",
            'class Client { Task Load() { return http.GetAsync("/users/42"); } }',
            "GET /users/42",
        ),
        ("client.go", 'package api\nfunc load() { http.Get("/users/42") }\n', "GET /users/42"),
    ],
)
def test_framework_plugins_extract_http_client_contracts(
    path: str,
    source: str,
    contract: str,
) -> None:
    registry = ParserRegistry(SemanticConfig(load_entry_points=False))
    result = registry.parser_for(Path(path)).analyze(path, source, content_hash(source))
    targets = {
        node.qualified_name
        for node in result.nodes
        if node.kind == "external_symbol" and node.metadata.get("external_kind") == "http_endpoint"
    }
    assert contract in targets
    assert any(edge.relation == "CALLS_ENDPOINT" for edge in result.edges)


def test_semantic_plugins_can_be_disabled() -> None:
    source = '@app.get("/users")\ndef users(): pass\n'
    registry = ParserRegistry(SemanticConfig(enabled=False))
    result = registry.parser_for(Path("api.py")).analyze("api.py", source, content_hash(source))
    assert not any(node.kind == "endpoint" for node in result.nodes)


def test_external_semantic_plugin_contract_is_versioned_and_failure_isolated() -> None:
    class CustomPlugin:
        api_version = "1"
        plugin_id = "example.custom"
        extensions = frozenset({".py"})

        def analyze(
            self,
            path: str,
            text: str,
            digest: str,
            structural: AnalysisResult,
        ) -> AnalysisResult:
            return AnalysisResult(
                (
                    GraphNode(
                        "custom::node",
                        "workflow",
                        "custom",
                        "custom",
                        path,
                        1,
                        1,
                    ),
                ),
                (),
                (),
            )

    class FailingPlugin(CustomPlugin):
        plugin_id = "example.failing"

        def analyze(
            self,
            path: str,
            text: str,
            digest: str,
            structural: AnalysisResult,
        ) -> AnalysisResult:
            raise RuntimeError("isolated")

    source = "def run(): pass\n"
    structural = GenericParser().analyze("app.py", source, content_hash(source))
    registry = SemanticPluginRegistry(
        SemanticConfig(load_entry_points=False),
        plugins=(CustomPlugin(), FailingPlugin()),
    )
    result = registry.enrich("app.py", source, content_hash(source), structural)

    assert any(node.node_id == "custom::node" for node in result.nodes)
    assert any("example.failing failed" in warning for warning in result.warnings)
    assert registry.status()["api_version"] == "1"


def test_cross_language_http_client_resolves_to_provider_incrementally(tmp_path: Path) -> None:
    provider = tmp_path / "provider.py"
    client = tmp_path / "client.ts"
    provider.write_text(
        'from fastapi import FastAPI\napp = FastAPI()\n@app.get("/users/{user_id}")\n'
        "def user(user_id: str): pass\n",
        encoding="utf-8",
    )
    client.write_text(
        "export async function load() {\n  return axios.get('/users/42');\n}\n",
        encoding="utf-8",
    )

    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        resolved = [
            edge
            for edge in runtime.store.all_edges()
            if edge["relation"] == "RESOLVED_CALLS_ENDPOINT"
        ]
        assert len(resolved) == 1
        assert runtime.store.node_by_id(str(resolved[0]["source_id"])).path == "client.ts"
        assert runtime.store.node_by_id(str(resolved[0]["target_id"])).path == "provider.py"

        provider.write_text(
            'from fastapi import FastAPI\napp = FastAPI()\n@app.get("/customers/{customer_id}")\n'
            "def customer(customer_id: str): pass\n",
            encoding="utf-8",
        )
        runtime.scan()
        assert not any(
            edge["relation"] == "RESOLVED_CALLS_ENDPOINT" for edge in runtime.store.all_edges()
        )

        client.write_text(
            "export async function load() {\n  return axios.get('/customers/99');\n}\n",
            encoding="utf-8",
        )
        runtime.scan()
        assert (
            sum(edge["relation"] == "RESOLVED_CALLS_ENDPOINT" for edge in runtime.store.all_edges())
            == 1
        )


def test_representative_semantic_fixture_resolves_two_language_boundaries(
    tmp_path: Path,
) -> None:
    fixture = Path(__file__).parents[1] / "examples" / "semantic-fixture"
    repository = tmp_path / "semantic-fixture"
    shutil.copytree(fixture, repository)

    with AthenaRuntime(repository) as runtime:
        runtime.scan()
        resolved = [
            edge
            for edge in runtime.store.all_edges()
            if edge["relation"] == "RESOLVED_CALLS_ENDPOINT"
        ]
        pairs = {
            (
                runtime.store.node_by_id(str(edge["source_id"])).path,
                runtime.store.node_by_id(str(edge["target_id"])).path,
            )
            for edge in resolved
        }
    assert pairs == {
        ("typescript/users_client.ts", "python/users_api.py"),
        ("go/health_client.go", "java/HealthController.java"),
    }


def test_new_provider_re_resolves_existing_literal_client(tmp_path: Path) -> None:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "athena@example.test")
    _git(tmp_path, "config", "user.name", "Athena Tests")
    (tmp_path / ".gitignore").write_text(".athena/\n", encoding="utf-8")
    (tmp_path / "client.ts").write_text(
        "export function load() { return axios.get('/users/42'); }\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "client")
    with AthenaRuntime(tmp_path) as runtime:
        runtime.scan()
        assert not any(
            edge["relation"] == "RESOLVED_CALLS_ENDPOINT" for edge in runtime.store.all_edges()
        )

        (tmp_path / "provider.py").write_text(
            '@app.get("/users/{user_id}")\ndef user(user_id: str): pass\n',
            encoding="utf-8",
        )
        _git(tmp_path, "add", ".")
        _git(tmp_path, "commit", "-m", "provider")
        runtime.scan()
        assert (
            sum(edge["relation"] == "RESOLVED_CALLS_ENDPOINT" for edge in runtime.store.all_edges())
            == 1
        )
