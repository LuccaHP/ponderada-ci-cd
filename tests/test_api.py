"""Testes de integração da API via TestClient."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_list_vazio(client: TestClient) -> None:
    resp = client.get("/todos")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_todo(client: TestClient) -> None:
    resp = client.post("/todos", json={"title": "Estudar CI/CD"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] == 1
    assert body["title"] == "Estudar CI/CD"
    assert body["done"] is False


def test_create_e_listar(client: TestClient) -> None:
    client.post("/todos", json={"title": "A"})
    client.post("/todos", json={"title": "B"})
    resp = client.get("/todos")
    assert resp.status_code == 200
    assert [t["title"] for t in resp.json()] == ["A", "B"]


def test_get_todo(client: TestClient) -> None:
    created = client.post("/todos", json={"title": "X"}).json()
    resp = client.get(f"/todos/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "X"


def test_get_inexistente_404(client: TestClient) -> None:
    resp = client.get("/todos/999")
    assert resp.status_code == 404


def test_update_todo(client: TestClient) -> None:
    created = client.post("/todos", json={"title": "antigo"}).json()
    resp = client.put(f"/todos/{created['id']}", json={"title": "novo", "done": True})
    assert resp.status_code == 200
    assert resp.json()["title"] == "novo"
    assert resp.json()["done"] is True


def test_update_inexistente_404(client: TestClient) -> None:
    resp = client.put("/todos/999", json={"title": "x"})
    assert resp.status_code == 404


def test_delete_todo(client: TestClient) -> None:
    created = client.post("/todos", json={"title": "del"}).json()
    resp = client.delete(f"/todos/{created['id']}")
    assert resp.status_code == 204
    assert client.get(f"/todos/{created['id']}").status_code == 404


def test_delete_inexistente_404(client: TestClient) -> None:
    resp = client.delete("/todos/999")
    assert resp.status_code == 404


def test_create_titulo_vazio_422(client: TestClient) -> None:
    resp = client.post("/todos", json={"title": ""})
    assert resp.status_code == 422


def test_create_titulo_so_espacos_422(client: TestClient) -> None:
    resp = client.post("/todos", json={"title": "   "})
    assert resp.status_code == 422
