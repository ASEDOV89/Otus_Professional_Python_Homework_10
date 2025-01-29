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

from sqlalchemy.orm import Session
from models import UserModel, RoleModel
from authenticate import create_access_token
from datetime import timedelta, datetime



def create_test_admin(db: Session, username: str = "admin", password: str = "adminpass", role_name: str = "admin"):
    role = RoleModel(name=role_name)
    db.add(role)
    db.commit()
    db.refresh(role)

    admin = UserModel(username=username)
    admin.set_password(password)
    admin.roles.append(role)
    db.add(admin)
    db.commit()
    db.refresh(admin)

    return admin


def create_test_user(db: Session, username: str = "testuser", password: str = "testpassword", role_name: str = "some_role"):
    role = RoleModel(name=role_name)
    db.add(role)
    db.commit()
    db.refresh(role)

    user = UserModel(username=username)
    user.set_password(password)
    user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)

    return user

@pytest.fixture
async def create_admin(db):
    admin = create_test_admin(db)
    yield admin

@pytest.fixture
async def create_user(db):
    user = create_test_user(db)
    yield user

@pytest.mark.asyncio
async def test_access_protected_route(create_user):
    async with AsyncClient(transport=ASGITransport(app), base_url="http://testserver") as ac:
        user = create_user
        response = await ac.post(
            "/login",
            data={
                "username": user.username,
                "password": user.password_hash
            }
        )

        response = await ac.post("/add_sale", data={
            "sale_date": "2025-01-01",
            "quantity": 10,
            "item_id": 1
        }, cookies=response.cookies)
        assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
async def test_admin_access(create_admin):
    async with AsyncClient(transport=ASGITransport(app), base_url="http://testserver") as ac:
        admin = create_admin
        response = await ac.post(
            "/login",
            data={
                "username": admin.username,
                "password": admin.password_hash
            }
        )
        assert response.status_code == 303

        response = await ac.post("/add_sale", data={
            "sale_date": "2025-01-01",
            "quantity": 10,
            "item_id": 1
        })
        assert response.status_code == 303

        response = await ac.get("/", cookies=response.cookies)
        assert "2025-01-01" in response.text

