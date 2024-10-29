FROM python:3.9 AS base

# Install dependencies only when needed
FROM base AS deps

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/* 

WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Rebuild the source code only when needed
FROM deps AS builder

WORKDIR /app

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]