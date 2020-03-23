# @see https://fastapi.tiangolo.com/tutorial/sql-databases/
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base
# @see https://fastapi.tiangolo.com/advanced/async-sql-databases/
from pydantic import BaseModel


class User(Base):
    __tablename__ = "users"

    # モデルの属性/列を作成
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    # relationship(関係) を作成
    items = relationship("Item", back_populates="owner")


class Item(Base):
    __tablename__ = "items"

    # モデルの属性/列を作成
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    # relationship(関係) を作成
    owner = relationship("User", back_populates="items")


# @see https://fastapi.tiangolo.com/advanced/async-sql-databases/
class NoteIn(BaseModel):
    text: str
    completed: bool


class Note(BaseModel):
    id: int
    text: str
    completed: bool
