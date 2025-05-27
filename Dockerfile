FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

# Install system dependencies
RUN apt update && \
    apt install -y htop libgl1-mesa-glx libglib2.0-0 && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Copy and install requirements first (for better caching)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /app
WORKDIR /app

# Environment variables - PENTING: Kurangi worker dan timeout
ENV MODULE_NAME=main
ENV VARIABLE_NAME=app
ENV PORT=8001
ENV WORKERS_PER_CORE=0.25
ENV MAX_WORKERS=1
ENV WEB_CONCURRENCY=1
ENV TIMEOUT=300
ENV GRACEFUL_TIMEOUT=300
ENV KEEP_ALIVE=5

EXPOSE 8001