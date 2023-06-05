FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

RUN pip install psycopg2

COPY ./app /app
