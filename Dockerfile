FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["sh", "-c", "alembic upgrade head && fastapi run main.py --port 8000"]