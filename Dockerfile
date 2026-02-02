# 使用輕量的 Python 基礎映像檔
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /code

# 複製 Python 應用程式碼與依賴項文件
COPY ./app/requirements.txt /code/requirements.txt
COPY ./app /code/app

# 安裝依賴項
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 開放 80 port (Render 預設會連接到容器的 80 port)
EXPOSE 80

# 容器啟動時執行的命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]