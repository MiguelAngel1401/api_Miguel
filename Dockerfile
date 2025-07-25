FROM python:3.12-slim 

WORKDIR /app

COPY app ./app
COPY temp_clientes ./temp_clientes
COPY requirements.txt ./requirements.txt
COPY .env ./.env

RUN pip install -r requirements.txt



CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]