# @see https://fastapi.tiangolo.com/tutorial/sql-databases/
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import SessionLocal, engine, database, notes
from .models import Note, NoteIn

# @see https://www.elastic.co/guide/en/apm/agent/python/master/starlette-support.html
from elasticapm.contrib.starlette import make_apm_client, ElasticAPM

# データベーステーブルを作成する
models.Base.metadata.create_all(bind=engine)

elastic_apm = make_apm_client({})
app = FastAPI()
app.add_middleware(ElasticAPM, client=elastic_apm)


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)
    try:
        request.state.db = SessionLocal()
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


# Dependency
# リクエストごとに独立したデータベースセッション/接続（）を用意し、
# すべてのリクエストで同じセッションを使用し、リクエストの終了後にセッションを閉じる
def get_db():
    db = None
    try:
        db = SessionLocal()
        yield db
    finally:
        # リクエスト後にデータベースセッションが常に閉じられるようにします。
        # リクエストの処理中に例外が発生した場合でも
        db.close()


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/items/", response_model=schemas.Item)
def create_item_for_user(
        user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
):
    return crud.create_user_item(db=db, item=item, user_id=user_id)


@app.get("/items/", response_model=List[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items


# @see https://fastapi.tiangolo.com/advanced/async-sql-databases/
@app.get("/notes/", response_model=List[Note])
async def read_notes():
    query = notes.select()
    return await database.fetch_all(query)


@app.post("/notes/", response_model=Note)
async def create_note(note: NoteIn):
    query = notes.insert().values(text=note.text, completed=note.completed)
    last_record_id = await database.execute(query)
    # `{**note.dict()}`
    # ↓
    # {
    #     "text": "Some note",
    #     "completed": False,
    # }
    #
    # ===================================
    #
    # {**note.dict(), "id": last_record_id}
    # ↓
    # {
    #     "id": 1,
    #     "text": "Some note",
    #     "completed": False,
    # }
    return {**note.dict(), "id": last_record_id}
