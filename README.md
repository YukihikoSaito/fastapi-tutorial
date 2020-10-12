# fastapi-tutorial
https://github.com/tiangolo/fastapi の入門

# 環境構築
## 必須要件
venv で Python3.9 系
https://docs.python.org/ja/3.9/library/venv.html
```
% python --version
Python 3.9.0
```

https://www.starlette.io/
```shell script
% pip3 --version
pip 19.0.3 from ~/fastapi-tutorial/venv/lib/python3.7/site-packages/pip-19.0.3-py3.7.egg/pip (python 3.7)

% pip3 install starlette
Installing collected packages: starlette
Successfully installed starlette-0.13.2
```

https://pydantic-docs.helpmanual.io/install/
```shell script
% pip3 install pydantic 
Installing collected packages: pydantic
Successfully installed pydantic-1.4
```

## install
https://github.com/tiangolo/fastapi
```shell script
% pip3 install fastapi 
Installing collected packages: fastapi
Successfully installed fastapi-0.52.0
```

http://www.uvicorn.org/
```shell script
% pip3 install uvicorn
Installing collected packages: httptools, h11, uvloop, click, websockets, uvicorn
Successfully installed click-7.1.1 h11-0.9.0 httptools-0.1.1 uvicorn-0.11.3 uvloop-0.14.0 websockets-8.1
```

requirements
```shell script
% pip3 freeze > requirements.txt
```

## Example

Create a file `main.py`

https://fastapi.tiangolo.com/async/#in-a-hurry
`async def構文` のドキュメント

非同期コード、同時実行性、および並列処理に関する情報

- 他のものと通信して応答するのを待つ必要がない場合は、を使用します`async def`
- 応答を待つ必要がある場合 normal `def` ←こちらを使います

## Run it
```
% uvicorn main:app --reload
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [57472]
INFO:     Started server process [57475]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

- `main`: ファイル `main.py` のこと
- `app`: `main.py` ファイルの `app = FastAPI()` オブジェクトのこと
- `--reload`: コードの変更後にサーバーを再起動するために必要。開発環境のみで使用。本番環境では使わない

## Check it
http://127.0.0.1:8000/items/5?q=somequery

JSON response が返戻されるはず
```json
{"item_id": 5, "q": "somequery"}
```


## Interactive API docs
http://127.0.0.1:8000/docs
- https://github.com/swagger-api/swagger-ui ベースのAPIドキュメント

http://127.0.0.1:8000/redoc
- https://github.com/Redocly/redoc ベースのAPIドキュメント




