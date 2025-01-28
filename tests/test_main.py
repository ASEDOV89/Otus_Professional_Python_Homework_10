import pytest
from httpx import AsyncClient
from main import app
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Base
import asyncio

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def test_app():
    Base.metadata.create_all(bind=engine)
    yield app
    Base.metadata.drop_all(bind=engine)


@pytest.mark.asyncio
async def test_register_and_login(test_app):
    async with AsyncClient(app=test_app, base_url="http://testserver") as ac:
        response = await ac.post(
            "/register",
            data={
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "testpassword",
            },
        )
        assert (
            response.status_code == 303
        )  # Redirect после успешной регистрации

        response = await ac.post(
            "/login", data={"username": "testuser", "password": "testpassword"}
        )
        assert response.status_code == 303

        cookies = response.cookies.jar
        assert any(cookie.name == "access_token" for cookie in cookies)

        response = await ac.get("/", cookies=response.cookies)
        assert response.status_code == 200
        assert "Привет, testuser" in response.text


@pytest.mark.asyncio
async def test_access_protected_route(test_app):
    async with AsyncClient(app=test_app, base_url="http://testserver") as ac:
        response = await ac.post(
            "/add_sale",
            data={"sale_date": "2025-01-01", "quantity": 10, "item_id": 1},
        )
        assert response.status_code == 401

        await ac.post(
            "/login", data={"username": "testuser", "password": "testpassword"}
        )

        response = await ac.post(
            "/add_sale",
            data={"sale_date": "2025-01-01", "quantity": 10, "item_id": 1},
        )
        assert (
            response.status_code == 403
        )  # Forbidden, так как у пользователя нет роли admin


@pytest.mark.asyncio
async def test_admin_access(test_app):
    async with AsyncClient(app=test_app, base_url="http://testserver") as ac:
        response = await ac.post(
            "/login", data={"username": "admin", "password": "admin"}
        )
        assert response.status_code == 303

        response = await ac.post(
            "/add_sale",
            data={"sale_date": "2025-01-01", "quantity": 10, "item_id": 1},
        )
        assert response.status_code == 303

        response = await ac.get("/", cookies=response.cookies)
        assert "2025-01-01" in response.text


# import pytest
# from httpx import AsyncClient, ASGITransport
#
# from main import app
#
#
# @pytest.mark.asyncio
# async def test_read_root():
#     async with AsyncClient(
#         transport=ASGITransport(app), base_url="http://testserver"
#     ) as ac:
#         response = await ac.get("/")
#     assert response.status_code == 200
#     assert "Прогноз продаж на следующие 20 дней" in response.text
#
#
# @pytest.mark.asyncio
# async def test_add_sale():
#     sale_data = {"sale_date": "2025-01-22T00:00:00", "quantity": 5, "item_id": 1}
#     async with AsyncClient(
#         transport=ASGITransport(app), base_url="http://testserver"
#     ) as ac:
#         response = await ac.post("/sales", json=sale_data)
#     assert response.status_code == 200
#     assert response.json()["sale"]["quantity"] == 5
#     assert response.json()["sale"]["item_id"] == 1
