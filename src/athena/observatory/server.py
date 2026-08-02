from __future__ import annotations

import json
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from athena.errors import AthenaError

from .registry import ProjectRegistry
from .service import ObservatoryService

_STATIC_TYPES = {
    "app.js": "text/javascript; charset=utf-8",
    "styles.css": "text/css; charset=utf-8",
}


class ObservatoryHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def run_observatory(
    root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = True,
    registry_path: Path | None = None,
) -> None:
    registry = ProjectRegistry(registry_path)
    registry.add(root)
    service = ObservatoryService(registry)
    handler = _handler(service)
    try:
        server = ObservatoryHTTPServer((host, port), handler)
    except OSError as exc:
        raise AthenaError(f"Could not start Athena Observatory on {host}:{port}: {exc}") from exc
    display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    url = f"http://{display_host}:{server.server_port}"
    print(f"Athena Observatory is live at {url}", flush=True)
    print(f"Registry: {registry.path}", flush=True)
    if open_browser:
        threading.Timer(0.35, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever(poll_interval=0.4)
    except KeyboardInterrupt:
        print("\nStopping Athena Observatory.", flush=True)
    finally:
        server.server_close()


def _handler(service: ObservatoryService) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "AthenaObservatory/0.1"

        def do_GET(self) -> None:
            if not self._trusted_request():
                return
            path = urlsplit(self.path).path
            if path == "/api/health":
                self._json({"status": "ok"})
                return
            if path == "/api/overview":
                self._json(service.overview())
                return
            if path.startswith("/api/projects/"):
                project_id = unquote(path.removeprefix("/api/projects/")).strip("/")
                try:
                    self._json(service.project(project_id))
                except KeyError:
                    self._json({"error": "Project not found"}, HTTPStatus.NOT_FOUND)
                return
            if path in {"", "/"}:
                self._static("index.html", "text/html; charset=utf-8")
                return
            name = path.lstrip("/")
            if name in _STATIC_TYPES:
                self._static(name, _STATIC_TYPES[name])
                return
            self._json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            if not self._trusted_request(mutating=True):
                return
            if urlsplit(self.path).path != "/api/projects":
                self._json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
                return
            try:
                payload = self._request_json()
                root_value = str(payload.get("root", "")).strip()
                if not root_value:
                    raise ValueError("A repository root is required.")
                database_value = str(payload.get("database", "")).strip()
                project = service.register(
                    Path(root_value), Path(database_value) if database_value else None
                )
                self._json(project, HTTPStatus.CREATED)
            except (AthenaError, OSError, ValueError, json.JSONDecodeError) as exc:
                self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

        def do_DELETE(self) -> None:
            if not self._trusted_request(mutating=True):
                return
            path = urlsplit(self.path).path
            if not path.startswith("/api/projects/"):
                self._json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
                return
            project_id = unquote(path.removeprefix("/api/projects/")).strip("/")
            if service.remove(project_id):
                self._json({"removed": project_id})
            else:
                self._json({"error": "Project not found"}, HTTPStatus.NOT_FOUND)

        def log_message(self, format: str, *args: object) -> None:
            if self.command != "GET" or not self.path.startswith("/api/"):
                super().log_message(format, *args)

        def _request_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 65_536:
                raise ValueError("Invalid request size.")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("A JSON object is required.")
            return payload

        def _trusted_request(self, *, mutating: bool = False) -> bool:
            host = self.headers.get("Host", "").casefold()
            hostname = host.rsplit(":", 1)[0].strip("[]")
            bound_address = self.server.server_address
            bound_host = str(bound_address[0] if isinstance(bound_address, tuple) else bound_address)
            bound_host = bound_host.casefold()
            allowed = {"localhost", "127.0.0.1", "::1", bound_host, "0.0.0.0"}
            if hostname not in allowed:
                self._json({"error": "Untrusted Host header"}, HTTPStatus.FORBIDDEN)
                return False
            origin = self.headers.get("Origin")
            if mutating and origin and urlsplit(origin).netloc.casefold() != host:
                self._json({"error": "Cross-origin mutation rejected"}, HTTPStatus.FORBIDDEN)
                return False
            return True

        def _json(
            self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK
        ) -> None:
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self._headers("application/json; charset=utf-8", len(body))
            self.end_headers()
            self.wfile.write(body)

        def _static(self, name: str, content_type: str) -> None:
            try:
                body = files("athena.observatory").joinpath("static", name).read_bytes()
            except (FileNotFoundError, ModuleNotFoundError):
                self._json({"error": "Dashboard asset not found"}, HTTPStatus.NOT_FOUND)
                return
            self.send_response(HTTPStatus.OK)
            self._headers(content_type, len(body))
            self.end_headers()
            self.wfile.write(body)

        def _headers(self, content_type: str, length: int) -> None:
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(length))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'",
            )

    return Handler
