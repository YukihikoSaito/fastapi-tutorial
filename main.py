# FastAPIはStarletteから直接継承するクラスです
# Starletteのすべての機能を利用出来ます
# @see https://fastapi.tiangolo.com/tutorial/query-params-str-validations/
# @see https://fastapi.tiangolo.com/tutorial/path-params-numeric-validations/
# @see https://fastapi.tiangolo.com/tutorial/body-fields/
# @see https://fastapi.tiangolo.com/tutorial/header-params/
# @see https://fastapi.tiangolo.com/tutorial/response-status-code/
# @see https://fastapi.tiangolo.com/tutorial/handling-errors/
# @see https://fastapi.tiangolo.com/tutorial/security/first-steps/
from fastapi import FastAPI, Query, Path, Body, Header, status, \
    HTTPException, Depends
# @see https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# @see https://fastapi.tiangolo.com/tutorial/encoder/
from fastapi.encoders import jsonable_encoder
from enum import Enum
# @see https://fastapi.tiangolo.com/tutorial/body/
# @see https://fastapi.tiangolo.com/tutorial/extra-models/
from pydantic import BaseModel, HttpUrl, EmailStr
# @see https://fastapi.tiangolo.com/tutorial/body-nested-models/
from typing import Optional, List, Set


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


app = FastAPI()

items = {"foo": "The Foo Wrestlers"}
fake_db = {}
fake_users_db = {
    "john_doe": {
        "username": "john_doe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fake_hashed_secret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonder",
        "email": "alice@example.com",
        "hashed_password": "fake_hashed_secret2",
        "disabled": True,
    },
}
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


# DBに該当ユーザーが存在しているかチェック
async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# DBの値 (disabled == True) ならば拒否する
async def get_current_active_user(current_user: UserBase = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = make_fake_password_hash(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}


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


@app.get("/items/", tags=["items"])
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
