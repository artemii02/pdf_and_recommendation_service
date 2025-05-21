FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копирование proto файлов и requirements.txt
COPY proto/ ./proto/
COPY requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY src/ ./src/

# Генерация proto файлов
RUN cd /app && python -m grpc_tools.protoc \
    -I./proto \
    --python_out=. \
    --grpc_python_out=. \
    ./proto/service.proto

# Установка переменных окружения
ENV PYTHONPATH=/app/src

WORKDIR /app/src

# Создание директории для временных файлов
RUN mkdir -p /app/temp

# Запуск сервера
CMD ["python", "app/server.py"] 