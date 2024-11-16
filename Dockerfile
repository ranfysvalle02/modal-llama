FROM python:3.10

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.com/install.sh | sh

RUN mkdir -p /root/.ollama/models

ENV OLLAMA_HOST=0.0.0.0

