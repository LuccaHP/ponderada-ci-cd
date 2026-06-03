"""Rotas CRUD da TODO API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

from app.models import Todo, TodoIn
from app.storage import InMemoryStore, TodoNotFoundError

router = APIRouter(prefix="/todos", tags=["todos"])

# Store único compartilhado pelo processo (suficiente para o experimento).
store = InMemoryStore()


@router.post("", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(payload: TodoIn) -> Todo:
    return store.add(payload)


@router.get("", response_model=list[Todo])
def list_todos() -> list[Todo]:
    return store.list()


@router.get("/{todo_id}", response_model=Todo)
def get_todo(todo_id: int) -> Todo:
    try:
        return store.get(todo_id)
    except TodoNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TODO não encontrado") from exc


@router.put("/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, payload: TodoIn) -> Todo:
    try:
        return store.update(todo_id, payload)
    except TodoNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TODO não encontrado") from exc


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_todo(todo_id: int) -> Response:
    try:
        store.delete(todo_id)
    except TodoNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TODO não encontrado") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
