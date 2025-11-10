FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1


WORKDIR /app


RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates openssl curl poppler-utils tzdata \
 && update-ca-certificates \
 && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .


ENV GRPC_VERBOSITY=NONE
ENV GRPC_TRACE=""
ENV ABSL_LOGGING_STDERR_THRESHOLD=fatal


EXPOSE 8080


CMD ["gunicorn", "-w", "4", "-k", "gthread", "--threads", "6", "-t", "300", "app.main:app", "--bind", "0.0.0.0:8080", "--log-level", "info", "--capture-output", "--reload"]
