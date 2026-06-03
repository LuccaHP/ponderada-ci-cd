"""Ponto de entrada da aplicação FastAPI."""

from __future__ import annotations

from fastapi import FastAPI

from app.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="TODO API - Experimento CI/CD", version="1.0.0")
    app.include_router(router)

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
