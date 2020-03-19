# @see https://fastapi.tiangolo.com/tutorial/sql-databases/
from sqlalchemy.orm import Session

from . import models, schemas


# user_id から単一のユーザーを読み取ります
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


# mail_addr から単一のユーザーを読み取ります
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


# 複数のユーザーを取得します
def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.password + "notreallyhashed"
    # SQLAlchemyモデルインスタンスを作成します
    db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
    # インスタンスオブジェクトをデータベースセッションに追加します
    db.add(db_user)
    # データベースへのコミット(保存)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()


def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
