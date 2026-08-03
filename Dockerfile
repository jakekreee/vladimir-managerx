FROM python:3.10-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Создаем папку для базы данных (если нужно)
RUN mkdir -p /app/data

# Запускаем бота
CMD ["python", "main.py"]
