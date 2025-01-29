import pytest
from httpx import AsyncClient, ASGITransport, Headers

from main import app

@pytest.mark.asyncio
async def test_read_root():
    async with AsyncClient(transport=ASGITransport(app), base_url="http://testserver") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert "Прогноз продаж на следующие 20 дней" in response.text






