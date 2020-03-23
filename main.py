# FastAPIはStarletteから直接継承するクラスです
# Starletteのすべての機能を利用出来ます
# @see https://fastapi.tiangolo.com/tutorial/query-params-str-validations/
# @see https://fastapi.tiangolo.com/tutorial/path-params-numeric-validations/
# @see https://fastapi.tiangolo.com/tutorial/body-fields/
# @see https://fastapi.tiangolo.com/tutorial/header-params/
# @see https://fastapi.tiangolo.com/tutorial/response-status-code/
# @see https://fastapi.tiangolo.com/tutorial/handling-errors/
# @see https://fastapi.tiangolo.com/tutorial/security/first-steps/
# @see https://fastapi.tiangolo.com/tutorial/middleware/
import time
from fastapi import FastAPI, Query, Path, Body, Header, status, \
    HTTPException, Depends, Request
# @see https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# @see https://fastapi.tiangolo.com/tutorial/encoder/
from fastapi.encoders import jsonable_encoder
# @see https://fastapi.tiangolo.com/tutorial/cors/
from fastapi.middleware.cors import CORSMiddleware
from enum import Enum
# @see https://fastapi.tiangolo.com/tutorial/body/
# @see https://fastapi.tiangolo.com/tutorial/extra-models/
from pydantic import BaseModel, HttpUrl, EmailStr
# @see https://fastapi.tiangolo.com/tutorial/body-nested-models/
from typing import Optional, List, Set

# @see https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
from datetime import datetime, timedelta
import jwt
from jwt import PyJWTError
from passlib.context import CryptContext

# @see https://www.elastic.co/guide/en/apm/agent/python/master/starlette-support.html
from elasticapm.contrib.starlette import make_apm_client, ElasticAPM

# @see https://fastapi.tiangolo.com/tutorial/debugging/
import uvicorn

# このような文字列を取得するには↓を実行
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


class Image(BaseModel):
    url: HttpUrl
    name: str


# POST 等で受け取るデータ構造
class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None
    tags: Set[str] = []
    images: List[Image] = None


# ユーザー情報のベース(雛形)
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


# ユーザーから受け付けるデータ構造
class UserIn(UserBase):
    password: str


# ユーザーに返戻するデータ構造 (class UserBase と同一)
class UserOut(UserBase):
    pass


# 内部データベースで持つデータ構造
class UserInDB(UserBase):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str = None


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def make_fake_password_hash(raw_password: str):
    return "fake_hashed_" + raw_password


def fake_save_user(user_in: UserIn):
    hashed_password = make_fake_password_hash(user_in.password)
    user_in_db = UserInDB(**user_in.dict(), hashed_password=hashed_password)
    print("User saved! ..not really")
    return user_in_db


def fake_decode_token(token):
    # これはチュートリアル用実装のため、セキュリティの意味をなしてないです
    # 商用環境では適切な修正を行います
    user = get_user(fake_users_db, token)
    return user


elastic_apm = make_apm_client({})
app = FastAPI()
app.add_middleware(ElasticAPM, client=elastic_apm)


items = {"foo": "The Foo Wrestlers"}
fake_db = {}
fake_users_db = {
    "john_doe": {
        "username": "john_doe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(fake_db_param, username: str, password: str):
    user = get_user(fake_db_param, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(*, data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# DBに該当ユーザーが存在しているかチェック
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except PyJWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


# DBの値 (disabled == True) ならば拒否する
async def get_current_active_user(current_user: UserBase = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/items-header/{item_id}", tags=["items"])
async def read_item_header(item_id: str):
    if item_id not in items:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
            headers={"X-Error": "There goes my error"},
        )
    return {"item": items[item_id]}


@app.get("/items/{item_id}", tags=["items"])
async def read_item(
        item_id: int = Path(..., title="The ID of the item to get", ge=0, le=1000),
        limit: Optional[int] = None
):
    return {"item_id": item_id, "limit": limit}


@app.put("/items/{item_id}", tags=["items"])
def update_item(item_id: str, item: Item):
    update_item_encoded = jsonable_encoder(item)
    items[item_id] = update_item_encoded
    return update_item_encoded


# http://127.0.0.1:8000/docs#/items/some_specific_id_you_define
# http://127.0.0.1:8000/redoc#operation/some_specific_id_you_define
# ↑ この url で参照出来るようになる
@app.get("/items/", tags=["items"], operation_id="some_specific_id_you_define")
async def read_items(
        q: str = Query(
            None,
            description="Query string for the items to search in the database that have a good match",
            min_length=3,
            max_length=50,
            regex="^fixed_query$",
            deprecated=True,
        ),
        user_agent: str = Header(None)
):
    results = {
        "items": [
            {"item_id": "Foo"},
            {"item_id": "Bar"}
        ],
        "User-Agent": user_agent
    }
    if q:
        results.update({"q": q})
    return results


# docstring での説明にも対応します
@app.post("/items/", status_code=status.HTTP_201_CREATED, tags=["items"], response_model=Item, summary="Create an item")
async def create_item(
        item: Item = Body(
            ...,
            example={
                "name": "Foo",
                "description": "A very nice Item",
                "price": 35.4,
                "tax": 3.2,
                "tags": [
                    "rock",
                    "metal"
                ],
                "images": [
                    {
                        "url": "http://example.com/baz.jpg",
                        "name": "The Foo live"
                    }
                ]
            },
        )
):
    """
    Create an item with all the information:

    - **name**: each item must have a name
    - **description**: a long description
    - **price**: required
    - **tax**: if the item doesn't have tax, you can omit this
    - **tags**: a set of unique tag strings for this item
    """
    return item


# パスの操作は順番に評価されます / 順番に注意
# @see https://fastapi.tiangolo.com/tutorial/path-params/
# @see https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
@app.get("/users/me", tags=["users"])
async def read_user_me(current_user: UserBase = Depends(get_current_active_user)):
    return current_user


# @see https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
@app.get("/users/me/items/", tags=["users"])
async def read_own_items(current_user: UserBase = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]


@app.get("/users/{user_id}", tags=["users"])
async def read_user(user_id: str):
    return {"user_id": user_id}


@app.post("/user/", response_model=UserOut, tags=["users"])
async def create_user(*, user_in: UserIn):
    user_saved = fake_save_user(user_in)
    return user_saved


@app.get("/model/{model_name}")
async def get_model(model_name: ModelName):
    if model_name == ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}
    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}
    return {"model_name": model_name, "message": "Have some residuals"}


@app.get("/elements/", tags=["items"], deprecated=True)
async def read_elements():
    return [{"item_id": "Foo"}]


# python main.py と呼ばれた時に実行されます
# ↓ 次のように、別のファイルがインポートするときには実行されません
# from main import app
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
