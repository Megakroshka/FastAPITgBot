FROM python:3.10

WORKDIR /code

# Устанавливаем netcat (он находится в пакете netcat-openbsd)
RUN apt-get update && apt-get install -y netcat-openbsd dos2unix && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app

# Копируем наш НОВЫЙ скрипт ожидания
COPY ./wait-for-db.sh /code/wait-for-db.sh

# Исправляем переносы строк и делаем скрипт исполняемым
RUN dos2unix /code/wait-for-db.sh
RUN chmod +x /code/wait-for-db.sh

# Запускаем uvicorn через скрипт ожидания. Обратите внимание, мы передаем только "db"
CMD ["/code/wait-for-db.sh", "db", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

