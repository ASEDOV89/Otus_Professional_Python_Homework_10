import pytest
from httpx import AsyncClient, ASGITransport, Headers

from main import app

@pytest.mark.asyncio
async def test_read_root():
    async with AsyncClient(transport=ASGITransport(app), base_url="http://testserver") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert "Прогноз продаж на следующие 20 дней" in response.text


@pytest.mark.asyncio
async def test_register_and_login():
    async with AsyncClient(transport=ASGITransport(app), base_url="http://testserver") as ac:
        response = await ac.post(
            "/register",
            data={
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "testpassword"
            }
        )
        assert response.status_code == 303

        response = await ac.post(
            "/login",
            data={
                "username": "testuser",
                "password": "testpassword"
            }
        )
        assert response.status_code == 303

        cookies = response.cookies.jar
        assert any(cookie.name == "access_token" for cookie in cookies)

        response = await ac.get("/", cookies=response.cookies)
        assert response.status_code == 200
        assert "Привет, testuser" in response.text

#==========================================

import pytest
from httpx import AsyncClient
from asgi_lifespan import LifespanManager
from app import app, get_db
from app.models import UserModel, RoleModel, SaleCreate, Sale
from app.dependencies import get_current_user


@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
async def test_db(db: Session):
    # Настройка базы данных для тестов
    yield db
    # Очистка базы данных после тестов, если это нужно


@pytest.fixture
async def admin_role(test_db):
    role = RoleModel(name="admin")
    test_db.add(role)
    test_db.commit()
    return role


@pytest.fixture
async def user_role(test_db):
    role = RoleModel(name="user")
    test_db.add(role)
    test_db.commit()
    return role


@pytest.fixture
async def admin_user(test_db, admin_role):
    user = UserModel(username="admin", email="admin@example.com", password_hash="")
    user.set_password("adminpassword")
    user.roles.append(admin_role)
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture
async def normal_user(test_db, user_role):
    user = UserModel(username="user", email="user@example.com", password_hash="")
    user.set_password("userpassword")
    user.roles.append(user_role)
    test_db.add(user)
    test_db.commit()
    return user


def mock_get_current_user(user):
    return user


@pytest.mark.asyncio
async def test_create_sale_success(async_client, test_db, admin_user, monkeypatch):
    sale_data = {
        "sale_date": "2025-01-01",
        "quantity": 10,
        "item_id": 1,
    }

    # Подменяем зависимость get_current_user на mock-функцию для администратора
    monkeypatch.setattr("app.dependencies.get_current_user", lambda: admin_user)

    response = await async_client.post("/sales", json=sale_data)

    assert response.status_code == 200
    assert response.json() == {
        "message": "Продажа успешно добавлена.",
        "sale": {
            "sale_date": "2025-01-01",
            "quantity": 10,
            "item_id": 1,
        },
    }

    # Проверка, что запись была добавлена в базу данных
    sale = test_db.query(Sale).filter_by(item_id=1).first()
    assert sale is not None
    assert sale.sale_date == sale_data["sale_date"]
    assert sale.quantity == sale_data["quantity"]


@pytest.mark.asyncio
async def test_create_sale_forbidden(async_client, test_db, normal_user, monkeypatch):
    sale_data = {
        "sale_date": "2025-01-01",
        "quantity": 10,
        "item_id": 1,
    }

    # Подменяем зависимость get_current_user на mock-функцию для обычного пользователя
    monkeypatch.setattr("app.dependencies.get_current_user", lambda: normal_user)

    response = await async_client.post("/sales", json=sale_data)

    assert response.status_code == 403
    assert response.json() == {"detail": "Недостаточно прав"}


@pytest.mark.asyncio
async def test_create_sale_unauthorized(async_client):
    sale_data = {
        "sale_date": "2025-01-01",
        "quantity": 10,
        "item_id": 1,
    }

    response = await async_client.post("/sales", json=sale_data)

    assert response.status_code == 401  # Unauthorized

