FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry==1.6.1
COPY backend/pyproject.toml backend/poetry.lock* ./
COPY ai_job_matcher ./ai_job_matcher
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

COPY backend /app/app
COPY scripts /app/scripts

EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
