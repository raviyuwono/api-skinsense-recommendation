FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

RUN apt update && \
    apt install -y htop libgl1-mesa-glx libglib2.0-0

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /app
WORKDIR /app

ENV MODULE_NAME=main
ENV VARIABLE_NAME=app
ENV PORT=8001

EXPOSE 8001
