from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    roles: List[str] = []

    class Config:
        orm_mode = True


class SaleCreate(BaseModel):
    sale_date: datetime
    quantity: int
    item_id: int
