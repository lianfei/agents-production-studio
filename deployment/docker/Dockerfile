FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SOURCE_ROOT=/app \
    OUTPUT_DIR=/app/tmp \
    HOST=0.0.0.0 \
    PORT=8765

WORKDIR /app

COPY pyproject.toml README.md LICENSE requirements.txt ./
COPY agents_corpus_workflow ./agents_corpus_workflow
COPY docs ./docs
COPY deployment ./deployment
COPY examples ./examples

RUN python -m pip install --upgrade pip \
    && python -m pip install .

RUN useradd --create-home --shell /bin/bash appuser \
    && mkdir -p /app/tmp \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8765
VOLUME ["/app/tmp"]

CMD ["sh", "-lc", "agents-corpus serve-api --source-root \"$SOURCE_ROOT\" --output-dir \"$OUTPUT_DIR\" --host \"$HOST\" --port \"$PORT\""]
