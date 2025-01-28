import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from models import Base, Sale, UserModel
from datetime import date
from collections import defaultdict
import os

DATABASE_URL = os.environ.get("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)

db = SessionLocal()

if not db.query(Sale).first():
    initial_data = [
        Sale(sale_date=date(2024, 12, 31), quantity=4, item_id=1),
        Sale(sale_date=date(2025, 1, 1), quantity=2, item_id=1),
        Sale(sale_date=date(2025, 1, 2), quantity=7, item_id=1),
        Sale(sale_date=date(2025, 1, 3), quantity=11, item_id=1),
        Sale(sale_date=date(2025, 1, 4), quantity=5, item_id=1),
        Sale(sale_date=date(2025, 1, 5), quantity=7, item_id=1),
        Sale(sale_date=date(2025, 1, 6), quantity=3, item_id=1),
        Sale(sale_date=date(2025, 1, 7), quantity=2, item_id=1),
        Sale(sale_date=date(2025, 1, 8), quantity=1, item_id=1),
        Sale(sale_date=date(2025, 1, 9), quantity=9, item_id=1),
        Sale(sale_date=date(2025, 1, 10), quantity=10, item_id=1),
        Sale(sale_date=date(2025, 1, 11), quantity=7, item_id=1),
        Sale(sale_date=date(2025, 1, 12), quantity=6, item_id=1),
        Sale(sale_date=date(2025, 1, 13), quantity=1, item_id=1),
        Sale(sale_date=date(2025, 1, 14), quantity=3, item_id=1),
        Sale(sale_date=date(2025, 1, 15), quantity=2, item_id=1),
        Sale(sale_date=date(2025, 1, 16), quantity=4, item_id=1),
        Sale(sale_date=date(2025, 1, 17), quantity=12, item_id=1),
        Sale(sale_date=date(2025, 1, 18), quantity=8, item_id=1),
        Sale(sale_date=date(2025, 1, 19), quantity=6, item_id=1),
        Sale(sale_date=date(2025, 1, 20), quantity=3, item_id=1),
        Sale(sale_date=date(2025, 1, 21), quantity=2, item_id=1),
        Sale(sale_date=date(2024, 12, 31), quantity=6, item_id=2),
        Sale(sale_date=date(2025, 1, 1), quantity=4, item_id=2),
        Sale(sale_date=date(2025, 1, 2), quantity=8, item_id=2),
        Sale(sale_date=date(2025, 1, 3), quantity=5, item_id=2),
        Sale(sale_date=date(2025, 1, 4), quantity=3, item_id=2),
        Sale(sale_date=date(2025, 1, 5), quantity=5, item_id=2),
        Sale(sale_date=date(2025, 1, 6), quantity=8, item_id=2),
        Sale(sale_date=date(2025, 1, 7), quantity=2, item_id=2),
        Sale(sale_date=date(2025, 1, 8), quantity=9, item_id=2),
        Sale(sale_date=date(2025, 1, 9), quantity=5, item_id=2),
        Sale(sale_date=date(2025, 1, 10), quantity=2, item_id=2),
        Sale(sale_date=date(2025, 1, 11), quantity=7, item_id=2),
        Sale(sale_date=date(2025, 1, 12), quantity=2, item_id=2),
        Sale(sale_date=date(2025, 1, 13), quantity=5, item_id=2),
        Sale(sale_date=date(2025, 1, 14), quantity=2, item_id=2),
        Sale(sale_date=date(2025, 1, 15), quantity=8, item_id=2),
        Sale(sale_date=date(2025, 1, 16), quantity=10, item_id=2),
        Sale(sale_date=date(2025, 1, 17), quantity=2, item_id=2),
        Sale(sale_date=date(2025, 1, 18), quantity=4, item_id=2),
        Sale(sale_date=date(2025, 1, 19), quantity=3, item_id=2),
        Sale(sale_date=date(2025, 1, 20), quantity=1, item_id=2),
        Sale(sale_date=date(2025, 1, 21), quantity=9, item_id=2),
    ]

    db.bulk_save_objects(initial_data)
    db.commit()
    print("Инициализация базы данных завершена. Данные добавлены.")
else:
    print("База данных уже содержит данные. Инициализация пропущена.")


subq = (
    db.query(Sale.sale_date, Sale.item_id)
    .group_by(Sale.sale_date, Sale.item_id)
    .having(func.count(Sale.id) > 1)
    .subquery()
)


duplicates = (
    db.query(Sale)
    .join(
        subq,
        (Sale.sale_date == subq.c.sale_date)
        & (Sale.item_id == subq.c.item_id),
    )
    .order_by(Sale.sale_date, Sale.id, Sale.item_id)
    .all()
)

to_delete = []
seen_dates = set()

for sale in duplicates:
    if sale.sale_date in seen_dates:
        to_delete.append(sale)
    else:
        seen_dates.add(sale.sale_date)

if to_delete:
    for sale in to_delete:
        db.delete(sale)
    db.commit()
    print(f"Удалено дубликатов: {len(to_delete)}")
else:
    print("Дубликаты не найдены.")

db.close()

from sqlalchemy.orm import Session
from database import get_db

# def create_admin_user(db: Session):
#     admin_email = "admin@admin.ru"
#     admin_username = "admin"
#     admin_password = "admin"
#
#     # Проверяем, существует ли уже пользователь с таким именем или почтой
#     existing_user = db.query(UserModel).filter(
#         (UserModel.username == admin_username) |
#         (UserModel.email == admin_email)
#     ).first()
#
#     if not existing_user:
#         hashed_password = UserModel.set_password(admin_password)
#         admin_user = UserModel(
#             username=admin_username,
#             email=admin_email,
#             password_hash=hashed_password
#         )
#         db.add(admin_user)
#         db.commit()
#         print("Admin user created.")
#     else:
#         print("Admin user already exists.")

from models import Base, Sale, UserModel, RoleModel
from datetime import date
from database import get_db

DATABASE_URL = os.environ.get("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)

db = SessionLocal()


def create_admin_user(db: SessionLocal):
    admin_email = "admin@admin.ru"
    admin_username = "admin"
    admin_password = "admin"

    # Проверяем, существует ли роль "admin"
    admin_role = db.query(RoleModel).filter_by(name="admin").first()
    if not admin_role:
        admin_role = RoleModel(name="admin")
        db.add(admin_role)
        db.commit()

    existing_user = (
        db.query(UserModel)
        .filter(
            (UserModel.username == admin_username)
            | (UserModel.email == admin_email)
        )
        .first()
    )

    if not existing_user:
        admin_user = UserModel(
            username=admin_username,
            email=admin_email,
        )
        admin_user.set_password(admin_password)
        admin_user.roles.append(admin_role)
        db.add(admin_user)
        db.commit()
        print("Admin user created.")
    else:
        print("Admin user already exists.")


def init_db():
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)

    # Создаем сессию
    db = next(get_db())

    # Создаем администратора
    create_admin_user(db)
