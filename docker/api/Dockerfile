FROM python:3.11.5

LABEL org.opencontainers.image.source="https://hub.docker.com/_/python"

WORKDIR /usr/src/server
COPY requirements.txt .
# requirements.txtにリストされたパッケージをインストールする
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

# コンテナ起動後、FastAPIを実行し8000ポートで待機
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
