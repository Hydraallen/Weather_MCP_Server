# Stage 1: Builder
FROM python:3.12.12-slim-bookworm as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runner
FROM python:3.12.12-slim-bookworm

WORKDIR /app
RUN useradd -m -u 1000 appuser

COPY --from=builder /install /usr/local
COPY src/ /app/src/

RUN chown -R appuser:appuser /app

USER appuser

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); result = s.connect_ex(('localhost', 8000)); exit(result)"

ENTRYPOINT ["python", "src/server.py"]
