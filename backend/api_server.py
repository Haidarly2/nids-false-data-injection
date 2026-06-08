from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import subprocess
import sys

app = FastAPI(title="NIDS Gateway API", version="1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOG_FILE = "log_hasil_nids.json"
# Variabel global untuk menyimpan status proses gateway_engine.py
engine_process = None


@app.get("/")
def home():
    return {"message": "NIDS API Server berjalan dengan baik!"}


@app.get("/api/engine/status")
def get_engine_status():
    global engine_process
    # Cek apakah proses ada dan masih berjalan
    if engine_process and engine_process.poll() is None:
        return {"status": "running"}
    return {"status": "stopped"}


@app.post("/api/engine/start")
def start_engine():
    global engine_process
    # Jika sudah berjalan, jangan jalankan lagi
    if engine_process and engine_process.poll() is None:
        return {"status": "success", "message": "Engine sudah berjalan"}

    try:
        # Menghapus log lama agar simulasi mulai dari nol
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)

        # Menjalankan gateway_engine.py di background Windows
        engine_process = subprocess.Popen(
            [sys.executable, "gateway_engine.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return {"status": "success", "message": "Engine berhasil dinyalakan"}
    except Exception as e:
        return {"status": "error", "pesan": str(e)}


@app.post("/api/engine/stop")
def stop_engine():
    global engine_process
    if engine_process and engine_process.poll() is None:
        engine_process.terminate()  # Matikan proses secara aman
        engine_process = None
        return {"status": "success", "message": "Engine berhasil dimatikan"}
    return {"status": "success", "message": "Engine memang sudah mati"}


@app.get("/api/data")
def get_nids_data():
    if not os.path.exists(LOG_FILE):
        return {"status": "menunggu_data", "data": []}

    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()

        total_aman = 0
        total_ancaman = 0

        for line in lines:
            if line.strip():
                item = json.loads(line.strip())
                if item.get("prediksi_ai") == 1:
                    total_ancaman += 1
                else:
                    total_aman += 1

        data_paket = []
        for line in lines[-100:]:
            if line.strip():
                data_paket.append(json.loads(line.strip()))

        return {
            "status": "sukses",
            "total_riwayat": len(lines),
            "summary_kumulatif": {
                "total_aman": total_aman,
                "total_ancaman": total_ancaman,
            },
            "data": data_paket,
        }
    except Exception as e:
        return {"status": "error", "pesan": str(e)}
