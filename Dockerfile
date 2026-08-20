FROM python:3.10-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps (cached unless requirements.txt changes)
COPY requirements.txt /app/requirements.txt
RUN pip install -U pip && pip install -U -r requirements.txt

# App code + start script
COPY . /app

EXPOSE 8080

CMD ["sh", "start.sh"]
