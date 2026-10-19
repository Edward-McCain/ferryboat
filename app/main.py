from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.errors import register
from app.routes import router
from app.store import Store


def create_app(store: Store | None = None) -> FastAPI:
    app = FastAPI(
        title="Рейс",
        summary="Лист ночных рейсов парома.",
        version="0.1.0",
    )
    app.state.store = store if store is not None else Store.with_seed()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register(app)
    app.include_router(router)
    _mount_ui(app)
    return app


def _mount_ui(app: FastAPI) -> None:
    # Каталог появляется после сборки Vite. Пока его нет, интерфейс открывается своим сервером.
    dist = Path(__file__).resolve().parent.parent / "web" / "dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="web")


app = create_app()
