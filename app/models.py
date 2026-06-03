"""Modelos Pydantic da TODO API.

Mantidos simples de propósito: a validação aqui rende testes unitários
naturais (título vazio, título muito longo) usados no experimento de CI/CD.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

MAX_TITLE_LENGTH = 120


class TodoIn(BaseModel):
    """Payload de entrada para criar/atualizar um TODO."""

    title: str = Field(..., min_length=1, max_length=MAX_TITLE_LENGTH)
    done: bool = False

    @field_validator("title")
    @classmethod
    def title_nao_pode_ser_so_espaco(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("title não pode ser vazio ou só espaços")
        return stripped


class Todo(TodoIn):
    """TODO persistido, com identificador."""

    id: int
