"""Testes unitários do InMemoryStore."""

from __future__ import annotations

import pytest

from app.models import TodoIn
from app.storage import InMemoryStore, TodoNotFoundError


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


def test_add_incrementa_id(store: InMemoryStore) -> None:
    a = store.add(TodoIn(title="a"))
    b = store.add(TodoIn(title="b"))
    assert a.id == 1
    assert b.id == 2


def test_get_existente(store: InMemoryStore) -> None:
    created = store.add(TodoIn(title="x"))
    assert store.get(created.id).title == "x"


def test_get_inexistente_levanta(store: InMemoryStore) -> None:
    with pytest.raises(TodoNotFoundError):
        store.get(123)


def test_list_retorna_todos(store: InMemoryStore) -> None:
    store.add(TodoIn(title="a"))
    store.add(TodoIn(title="b"))
    assert len(store.list()) == 2


def test_update_existente(store: InMemoryStore) -> None:
    created = store.add(TodoIn(title="velho"))
    updated = store.update(created.id, TodoIn(title="novo", done=True))
    assert updated.title == "novo"
    assert updated.done is True


def test_update_inexistente_levanta(store: InMemoryStore) -> None:
    with pytest.raises(TodoNotFoundError):
        store.update(99, TodoIn(title="x"))


def test_delete_existente(store: InMemoryStore) -> None:
    created = store.add(TodoIn(title="x"))
    store.delete(created.id)
    assert store.list() == []


def test_delete_inexistente_levanta(store: InMemoryStore) -> None:
    with pytest.raises(TodoNotFoundError):
        store.delete(99)


def test_clear_reseta_id(store: InMemoryStore) -> None:
    store.add(TodoIn(title="x"))
    store.clear()
    novo = store.add(TodoIn(title="y"))
    assert novo.id == 1
