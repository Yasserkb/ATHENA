import athena


def test_runtime_version_prefers_container_release_metadata(monkeypatch) -> None:
    monkeypatch.setenv("ATHENA_VERSION", "0.2.0")
    monkeypatch.setattr(athena, "version", lambda _distribution: "0.1.0")

    assert athena._runtime_version() == "0.2.0"


def test_runtime_version_uses_installed_package_metadata(monkeypatch) -> None:
    monkeypatch.delenv("ATHENA_VERSION", raising=False)
    monkeypatch.setattr(athena, "version", lambda _distribution: "0.2.0")

    assert athena._runtime_version() == "0.2.0"
