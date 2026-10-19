from collections.abc import AsyncIterator

import httpx
import pytest

from app.main import create_app
from app.store import Store


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    # ASGITransport в этом httpx открывается только через async with.
    transport = httpx.ASGITransport(app=create_app(Store()))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


@pytest.fixture
async def seeded_client() -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=create_app(Store.with_seed()))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
