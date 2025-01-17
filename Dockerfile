# Gunakan base image yang mendukung Uvicorn dan Gunicorn untuk Python 3.10
FROM tiangolo/uvicorn-gunicorn:python3.10

# Update paket sistem dan instal dependensi tambahan yang diperlukan
RUN apt update && \
    apt install -y htop libgl1-mesa-glx libglib2.0-0

# Salin file requirements.txt ke dalam container
COPY requirements.txt /tmp/requirements.txt

# Instal dependensi Python yang diperlukan
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Salin seluruh kode aplikasi ke dalam direktori kerja container
COPY . /app

# Tentukan direktori kerja container
WORKDIR /app

# Ekspose port 8001 agar aplikasi dapat diakses
EXPOSE 8001

# Perintah untuk menjalankan aplikasi
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8001"]
