FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml README.md ./
RUN pip install --upgrade pip && pip install .
COPY app ./app
COPY migrations ./migrations
COPY knowledge ./knowledge
COPY scripts ./scripts
COPY tests ./tests
COPY render.yaml ./
EXPOSE 10000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
