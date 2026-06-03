"""Testes unitários dos modelos Pydantic."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models import MAX_TITLE_LENGTH, Todo, TodoIn


def test_todoin_padrao_done_false() -> None:
    todo = TodoIn(title="ler")
    assert todo.done is False


def test_todoin_faz_strip_no_titulo() -> None:
    todo = TodoIn(title="  espaço  ")
    assert todo.title == "espaço"


def test_todoin_titulo_vazio_invalido() -> None:
    with pytest.raises(ValidationError):
        TodoIn(title="")


def test_todoin_titulo_so_espacos_invalido() -> None:
    with pytest.raises(ValidationError):
        TodoIn(title="    ")


def test_todoin_titulo_muito_longo_invalido() -> None:
    with pytest.raises(ValidationError):
        TodoIn(title="a" * (MAX_TITLE_LENGTH + 1))


def test_todo_tem_id() -> None:
    todo = Todo(id=7, title="x")
    assert todo.id == 7
