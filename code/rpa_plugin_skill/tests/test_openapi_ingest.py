from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rpa_plugin_skill.core.openapi_ingest import (
    OpenAPIAuth,
    OpenAPIFetchError,
    OpenAPIParseError,
    load_openapi_text,
    parse_openapi_document,
)

JSON_SPEC = """
{
  "openapi": "3.0.3",
  "info": {"title": "Financial API", "version": "1.0.0"},
  "paths": {
    "/clients": {"get": {"responses": {"200": {"description": "ok"}}}}
  }
}
"""

YAML_SPEC = """
openapi: 3.0.3
info:
  title: Medical API
  version: 1.0.0
paths:
  /patients:
    get:
      responses:
        "200":
          description: ok
"""


class OpenApiIngestTests(unittest.TestCase):
    def test_parse_json_spec(self) -> None:
        doc = parse_openapi_document(JSON_SPEC)
        self.assertEqual(doc["info"]["title"], "Financial API")
        self.assertIn("/clients", doc["paths"])

    def test_parse_yaml_spec(self) -> None:
        doc = parse_openapi_document(YAML_SPEC)
        self.assertEqual(doc["info"]["title"], "Medical API")

    def test_missing_paths_is_error(self) -> None:
        bad = '{"openapi":"3.0.3","info":{"title":"x","version":"1"}}'
        with self.assertRaises(OpenAPIParseError):
            parse_openapi_document(bad)

    def test_load_from_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "openapi.yaml"
            p.write_text(YAML_SPEC, encoding="utf-8")
            text = load_openapi_text(str(p))
            self.assertIn("openapi: 3.0.3", text)

    def test_basic_auth_requires_credentials(self) -> None:
        auth = OpenAPIAuth(mode="basic", username="user", password=None)
        with self.assertRaises(OpenAPIFetchError):
            auth.headers()

    def test_bearer_auth_header(self) -> None:
        auth = OpenAPIAuth(mode="bearer", token="abc")
        self.assertEqual(auth.headers()["Authorization"], "Bearer abc")


if __name__ == "__main__":
    unittest.main()
