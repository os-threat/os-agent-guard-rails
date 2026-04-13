from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import yaml


class OpenAPIParseError(ValueError):
    """Raised when an OpenAPI document cannot be parsed or validated."""


class OpenAPIFetchError(ValueError):
    """Raised when an OpenAPI URL cannot be fetched."""


@dataclass(frozen=True)
class OpenAPIAuth:
    mode: str = "none"  # none | bearer | basic
    token: str | None = None
    username: str | None = None
    password: str | None = None

    def headers(self) -> dict[str, str]:
        if self.mode == "none":
            return {}
        if self.mode == "bearer":
            if not self.token:
                raise OpenAPIFetchError("Bearer auth requires token")
            return {"Authorization": f"Bearer {self.token}"}
        if self.mode == "basic":
            if self.username is None or self.password is None:
                raise OpenAPIFetchError("Basic auth requires username and password")
            raw = f"{self.username}:{self.password}"
            encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
            return {"Authorization": f"Basic {encoded}"}
        raise OpenAPIFetchError(f"Unsupported auth mode: {self.mode}")


def load_openapi_text(source: str, auth: OpenAPIAuth | None = None) -> str:
    """Load OpenAPI text from inline string, file path, or HTTP(S) URL."""
    auth = auth or OpenAPIAuth()
    parsed = urlparse(source)
    if parsed.scheme in {"http", "https"}:
        req = Request(source, headers=auth.headers())
        try:
            with urlopen(req) as response:  # nosec B310 - explicit user-provided source
                return response.read().decode("utf-8")
        except Exception as exc:  # noqa: BLE001
            raise OpenAPIFetchError(f"Failed to fetch OpenAPI URL: {source}") from exc

    path = Path(source)
    if path.exists() and path.is_file():
        return path.read_text(encoding="utf-8")

    return source


def parse_openapi_document(text: str) -> dict[str, Any]:
    doc: Any
    try:
        doc = json.loads(text)
    except json.JSONDecodeError:
        try:
            doc = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise OpenAPIParseError("OpenAPI document is not valid JSON or YAML") from exc

    if not isinstance(doc, dict):
        raise OpenAPIParseError("OpenAPI document root must be an object")

    openapi_version = doc.get("openapi")
    if not isinstance(openapi_version, str):
        raise OpenAPIParseError("OpenAPI document missing 'openapi' version string")

    if "paths" not in doc or not isinstance(doc["paths"], dict):
        raise OpenAPIParseError("OpenAPI document missing required 'paths' object")

    info = doc.get("info")
    if not isinstance(info, dict) or not info.get("title"):
        raise OpenAPIParseError("OpenAPI document missing required 'info.title'")

    return doc
