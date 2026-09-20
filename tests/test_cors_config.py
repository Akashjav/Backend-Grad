import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.core.config import cors_origins


@pytest.mark.parametrize("raw", [
    "https://frontend.example.com/ , https://other.example.com",
    '["https://frontend.example.com/", "https://other.example.com"]',
])
def test_production_cors_formats(raw):
    assert cors_origins(raw, True) == [
        "https://frontend.example.com", "https://other.example.com"
    ]


@pytest.mark.parametrize("raw", [
    "", "*", "http://localhost:5173", "https://*.example.com",
    "https://example.com/path", "https://example.com?token=secret",
    "https://user:secret@example.com", "https://", "[null]", "[broken",
    "https://example.com:invalid", "https://example.com/#fragment",
])
def test_production_rejects_invalid_origins_without_echoing_value(raw):
    with pytest.raises(RuntimeError, match="Invalid CORS_ORIGINS") as error:
        cors_origins(raw, True)
    assert "secret" not in str(error.value)


def test_development_keeps_local_frontend():
    assert cors_origins("http://localhost:5173", False) == ["http://localhost:5173"]


def test_invalid_config_exits_before_worker_start():
    environment = {**os.environ, "APP_ENV": "production", "CORS_ORIGINS": "http://localhost:5173"}
    result = subprocess.run(
        [sys.executable, "scripts/serve.py"],
        cwd=Path(__file__).resolve().parents[1], env=environment,
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 1
    assert "Startup configuration error: Invalid CORS_ORIGINS" in result.stderr
    assert "Started parent process" not in result.stderr
