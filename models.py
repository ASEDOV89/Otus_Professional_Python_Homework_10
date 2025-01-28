from sqlalchemy import (
    Column,
    Integer,
    Date,
    String,
    DateTime,
    UniqueConstraint,
    ForeignKey,
    Table,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import bcrypt


Base = declarative_base()


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    sale_date = Column(Date, nullable=False)
    quantity = Column(Integer, nullable=False)
    item_id = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("sale_date", "item_id", name="unique_sale_date_item"),
    )


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
)


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    roles = relationship(
        "RoleModel", secondary=user_roles, back_populates="users"
    )

    def set_password(self, password: str):
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )


class RoleModel(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

    users = relationship(
        "UserModel", secondary=user_roles, back_populates="roles"
    )
