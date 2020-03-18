# FastAPIはStarletteから直接継承するクラスです
# Starletteのすべての機能を利用出来ます
# @see https://fastapi.tiangolo.com/tutorial/query-params-str-validations/
# @see https://fastapi.tiangolo.com/tutorial/path-params-numeric-validations/
from fastapi import FastAPI, Query, Path
from enum import Enum
# @see https://fastapi.tiangolo.com/tutorial/body/
from pydantic import BaseModel

from typing import Optional


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


# POST 等で受け取るデータ構造
class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None


app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
async def read_item(
        item_id: int = Path(..., title="The ID of the item to get", ge=0, le=1000),
        limit: Optional[int] = None
):
    return {"item_id": item_id, "limit": limit}


@app.get("/items/")
async def read_items(
        q: str = Query(
            None,
            description="Query string for the items to search in the database that have a good match",
            min_length=3,
            max_length=50,
            regex="^fixed_query$",
            deprecated=True,
        )
):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results


@app.post("/items/")
async def create_item(item: Item):
    return item


# パスの操作は順番に評価されます / 順番に注意
# @see https://fastapi.tiangolo.com/tutorial/path-params/
@app.get("/users/me")
async def read_user_me():
    return {"user_id": "the current user"}


@app.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id}


@app.get("/model/{model_name}")
async def get_model(model_name: ModelName):
    if model_name == ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}
    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}
    return {"model_name": model_name, "message": "Have some residuals"}
