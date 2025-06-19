FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "while ! nc -z $DB_HOST $DB_PORT; do sleep 2; done && python -u main.py"]