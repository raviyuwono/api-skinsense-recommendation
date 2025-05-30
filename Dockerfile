FROM python:3.8-slim

# Set environment variables to disable AVX optimizations
ENV TF_CPP_MIN_LOG_LEVEL=2
ENV TF_ENABLE_ONEDNN_OPTS=0

RUN apt update && \
    apt install -y htop libgl1-mesa-glx libglib2.0-0 && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt

# Install packages with specific configurations
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /app
WORKDIR /app
EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]