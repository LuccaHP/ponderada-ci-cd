"""Fixtures compartilhadas pelos testes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.routes import store


@pytest.fixture
def client() -> TestClient:
    # Garante isolamento entre testes limpando o store em memória.
    store.clear()
    return TestClient(create_app())
