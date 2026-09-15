FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git curl ca-certificates \
 && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt-get install -y nodejs \
 && npm install -g pagefind && apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /srv
CMD ["python3", "/opt/skill/deploy/runner.py"]
