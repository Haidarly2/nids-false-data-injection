# Menggunakan OS Alpine Linux super ringan
FROM python:3.9-alpine

# Menyiapkan folder kerja
WORKDIR /app

# Menyalin skrip sensor ke dalam kontainer
COPY normal_sensor.py .

# Menjalankan skrip secara terus-menerus
CMD ["python", "-u", "normal_sensor.py"]