"""Armazenamento em memória dos TODOs.

Sem banco de dados para manter o experimento simples e determinístico.
As operações são puras o suficiente para gerar unitários rápidos.
"""

from __future__ import annotations

from app.models import Todo, TodoIn


class TodoNotFoundError(KeyError):
    """Levantado quando um TODO inexistente é acessado."""


class InMemoryStore:
    """Repositório simples de TODOs indexado por id incremental."""

    def __init__(self) -> None:
        self._items: dict[int, Todo] = {}
        self._next_id: int = 1

    def add(self, data: TodoIn) -> Todo:
        todo = Todo(id=self._next_id, **data.model_dump())
        self._items[todo.id] = todo
        self._next_id += 1
        return todo

    def get(self, todo_id: int) -> Todo:
        try:
            return self._items[todo_id]
        except KeyError as exc:
            raise TodoNotFoundError(todo_id) from exc

    def list(self) -> list[Todo]:
        return list(self._items.values())

    def update(self, todo_id: int, data: TodoIn) -> Todo:
        if todo_id not in self._items:
            raise TodoNotFoundError(todo_id)
        updated = Todo(id=todo_id, **data.model_dump())
        self._items[todo_id] = updated
        return updated

    def delete(self, todo_id: int) -> None:
        if todo_id not in self._items:
            raise TodoNotFoundError(todo_id)
        del self._items[todo_id]

    def clear(self) -> None:
        self._items.clear()
        self._next_id = 1
