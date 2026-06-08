# Menggunakan Miniconda3 sebagai pondasi (Sama persis seperti environment Anda di Windows)
FROM continuumio/miniconda3

# Menentukan folder kerja di dalam kontainer
WORKDIR /app

# Menggunakan Conda Forge untuk menarik versi pustaka yang SUDAH MATANG (Pre-compiled)
# Trik ini melewati (bypass) seluruh masalah "Failed building wheel" pada pip
RUN conda install -y -c conda-forge fastapi uvicorn river numpy psutil

# Menyalin seluruh file skrip NIDS Anda (gateway_engine.py & api_server.py)
COPY . .

# Membuka port untuk komunikasi
EXPOSE 8080
EXPOSE 9999

# Menjalankan mesin API
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8080"]