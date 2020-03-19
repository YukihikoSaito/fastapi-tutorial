# @see https://fastapi.tiangolo.com/tutorial/sql-databases/
from typing import List

from pydantic import BaseModel


class ItemBase(BaseModel):
    title: str
    description: str = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


# API 返戻するときに使用する
# そのため、 password は含まない
class User(UserBase):
    id: int
    is_active: bool
    items: List[Item] = []

    """
    orm_mode = True
    ↑ True にすることにより
    ↓ どちらの方法でも取得可能になります
        - `id = data["id"]`
        - `id = data.id`
    """
    class Config:
        orm_mode = True
