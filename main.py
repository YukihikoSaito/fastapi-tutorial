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
    HTTPException, Depends, Request, Security
# @see https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
# @see https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
# @see https://fastapi.tiangolo.com/tutorial/encoder/
# @see https://fastapi.tiangolo.com/tutorial/cors/
from fastapi.middleware.cors import CORSMiddleware
# @see https://fastapi.tiangolo.com/advanced/middleware/
# from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
# from fastapi.middleware.trustedhost import TrustedHostMiddleware
# @see https://fastapi.tiangolo.com/advanced/additional-status-codes/
# @see https://fastapi.tiangolo.com/advanced/custom-response/
from fastapi.responses import JSONResponse, RedirectResponse, \
    StreamingResponse

# @see https://fastapi.tiangolo.com/advanced/templates/
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# @see https://fastapi.tiangolo.com/advanced/extending-openapi/
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)


from enum import Enum
# @see https://fastapi.tiangolo.com/tutorial/body/
# @see https://fastapi.tiangolo.com/tutorial/extra-models/
# @see https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/
from pydantic import BaseModel, HttpUrl, EmailStr, ValidationError
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


# authorize する時に受け取るデータ構造
class AuthorizeIn(BaseModel):
    client_id: str
    client_secret: str
    grant_type: str
    username: str
    password: str
    scope: str


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
    scopes: List[str] = []


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


# elastic_apm = make_apm_client({})
app = FastAPI(docs_url=None, redoc_url=None)
# app.add_middleware(ElasticAPM, client=elastic_apm)
# app.add_middleware(HTTPSRedirectMiddleware)
# app.add_middleware(
#     TrustedHostMiddleware, allowed_hosts=["example.com", "*.example.com"]
# )


# @see https://fastapi.tiangolo.com/advanced/templates/
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


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
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/token",
    scopes={"me": "Read information about the current user.", "items": "Read items."},
)


# @see https://fastapi.tiangolo.com/advanced/events/
@app.on_event("shutdown")
def shutdown_event():
    with open("application.log", mode="a") as log:
        log.write("Application shutdown")


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
async def get_current_user(
        security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)
):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = f"Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(scopes=token_scopes, username=username)
    except (PyJWTError, ValidationError):
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user


# DBの値 (disabled == True) ならば拒否する
async def get_current_active_user(
        current_user: UserBase = Security(get_current_user, scopes=["me"])
):
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


async def fake_video_streamer():
    for i in range(10):
        yield b"some fake video bytes"


# @see https://fastapi.tiangolo.com/advanced/extending-openapi/
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="OpenAPI Custom title",
        version="2.5.0",
        description="This is a very custom OpenAPI schema",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.post(
    "/v1/auth/authorize", tags=["auth"], response_model=AuthorizeIn,
    summary="ユーザー認証処理を行い、API実行時に必要なaccess_tokenを取得します",
    deprecated=True,
)
async def auth_authorize(
        authorize_in: AuthorizeIn = Body(
            ...,
            example={
                "client_id": "41ab74278288",
                "client_secret": "be7202161f16be5c2e69ddba5c208bad",
                "grant_type": "password",
                "username": "user@example.com",
                "password": "top_secret",
                "scope": "use",
            },
        )
):
    """
    リクエスト情報:

    - **client_id**: 認証用クライアントID
    - **client_secret**: 認証用クライアントシークレット

    レスポンス情報:

    - **access_token**: 認可トークン
    - **token_type**: トークンタイプ
    - **expires_in**: トークン有効期限 [sec]
    - **refresh_token**: トークンのリフレッシュに使用します
    - **scope**: 認可されたスコープ(複数存在する場合はカンマ区切り)
    """

    ret_item = {
        "access_token": "0596de32-df84-4293-8f3c-9b3d2a93b61b",
        "token_type": "Bearer",
        "expires_in": 2592000,
        "refresh_token": "a1c8f3a7-de7e-4271-912d-79ed9f971722",
        "scope": "use,agency",
    }
    return ret_item


@app.post(
    "/v2/auth/authorize", tags=["auth"], response_model=AuthorizeIn,
    summary="ユーザー認証処理を行い、API実行時に必要なaccess_tokenを取得します",
)
async def auth_authorize(
        authorize_in: AuthorizeIn = Body(
            ...,
            example={
                "client_id": "41ab74278288",
                "client_secret": "be7202161f16be5c2e69ddba5c208bad",
                "grant_type": "password",
                "username": "user@example.com",
                "password": "secret_secret",
                "scope": "use",
            },
        )
):
    """
    リクエスト情報:

    - **client_id**: 認証用クライアントID
    - **client_secret**: 認証用クライアントシークレット
    - **grant_type**: 認証方式
    - **username**: ユーザーメールアドレス
    - **password**: ユーザーパスワード
    - **scope**: 認可したいスコープ (複数指定する場合はカンマ区切り)

    レスポンス情報:

    - **access_token**: 認可トークン
    - **token_type**: トークンタイプ
    - **expires_in**: トークン有効期限 [sec]
    - **refresh_token**: トークンのリフレッシュに使用します
    - **scope**: 認可されたスコープ(複数存在する場合はカンマ区切り)
    """

    ret_item = {
        "access_token": "0596de32-df84-4293-8f3c-9b3d2a93b61b",
        "token_type": "Bearer",
        "expires_in": 2592000,
        "refresh_token": "a1c8f3a7-de7e-4271-912d-79ed9f971722",
        "scope": "use,agency",
    }
    return ret_item


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
        data={"sub": user.username, "scopes": form_data.scopes},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/typer")
async def read_typer():
    return RedirectResponse("https://typer.tiangolo.com")


@app.get("/fake-video-streamer")
async def main():
    return StreamingResponse(fake_video_streamer())


@app.get("/items-header/{item_id}", tags=["items"])
async def read_item_header(item_id: str):
    if item_id not in items:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
            headers={"X-Error": "There goes my error"},
        )
    return {"item": items[item_id]}


@app.get("/items-template/{item_id}")
async def read_item(request: Request, item_id: str):
    return templates.TemplateResponse("item.html", {"request": request, "item_id": item_id})


@app.get("/items/{item_id}", tags=["items"])
async def read_item(
        item_id: int = Path(..., title="The ID of the item to get", ge=0, le=1000),
        limit: Optional[int] = None
):
    return {"item_id": item_id, "limit": limit}


@app.put("/items/{item_id}", tags=["items"])
async def upsert_item(item_id: str, name: str = Body(None), size: int = Body(None)):
    if item_id in items:
        item = items[item_id]
        item["name"] = name
        item["size"] = size
        return item
    else:
        item = {"name": name, "size": size}
        items[item_id] = item
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=item)


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
