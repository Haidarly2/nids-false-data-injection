from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import subprocess
import sys
import shutil
from datetime import datetime

app = FastAPI(title="NIDS Gateway API - Switchable", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOG_FILE = "log_hasil_nids.json"
ARSIP_DIR = "arsip_log_server_pusat"
engine_process = None
model_saat_ini = "incremental_demo"  # Default saat pertama nyala


class SwitchModelRequest(BaseModel):
    model_name: str  # 'incremental', 'rf', 'dnn'


def arsipkan_log():
    if not os.path.exists(ARSIP_DIR):
        os.makedirs(ARSIP_DIR)
    if os.path.exists(LOG_FILE):
        waktu_arsip = datetime.now().strftime("%Y%m%d_%H%M%S")
        nama_arsip = f"arsip_log_{waktu_arsip}.json"
        shutil.copy(LOG_FILE, os.path.join(ARSIP_DIR, nama_arsip))
        os.remove(LOG_FILE)


@app.get("/")
def home():
    return {"message": "API Server Siap!"}


@app.get("/api/engine/status")
def get_engine_status():
    global engine_process, model_saat_ini
    if engine_process and engine_process.poll() is None:
        return {"status": "running", "active_model": model_saat_ini}
    return {"status": "stopped", "active_model": model_saat_ini}


@app.post("/api/engine/start")
def start_engine():
    global engine_process, model_saat_ini
    if engine_process and engine_process.poll() is None:
        return {"status": "success", "message": "Engine sudah berjalan"}
    try:
        arsipkan_log()
        engine_process = subprocess.Popen(
            [
                sys.executable,
                "gateway_engine_copy.py",
                model_saat_ini,
            ],  # <--- Lempar argumen model
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return {
            "status": "success",
            "message": f"Engine dinyalakan dengan model {model_saat_ini}",
        }
    except Exception as e:
        return {"status": "error", "pesan": str(e)}


@app.post("/api/engine/stop")
def stop_engine():
    global engine_process
    if engine_process and engine_process.poll() is None:
        engine_process.terminate()
        engine_process = None
        return {"status": "success", "message": "Engine berhasil dimatikan"}
    return {"status": "success"}


@app.post("/api/engine/switch")
def switch_engine(req: SwitchModelRequest):
    global engine_process, model_saat_ini

    if req.model_name not in ["incremental_demo", "incremental_train", "rf", "dnn"]:
        return {"status": "error", "pesan": "Model tidak valid"}

    model_saat_ini = req.model_name

    if engine_process and engine_process.poll() is None:
        engine_process.terminate()
        engine_process.wait()

    engine_process = subprocess.Popen(
        [sys.executable, "gateway_engine_copy.py", model_saat_ini],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return {
        "status": "success",
        "message": f"Berhasil pindah ke model {model_saat_ini}",
    }


@app.get("/api/data")
def get_nids_data():
    if not os.path.exists(LOG_FILE):
        return {"status": "menunggu_data", "data": []}
    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()

        total_aman = 0
        total_ancaman = 0
        sum_latensi = 0.0
        sum_ram = 0.0
        count_valid = 0
        for line in lines:
            if line.strip():
                try:
                    item = json.loads(line.strip())
                    if item.get("prediksi_ai") == 1:
                        total_ancaman += 1
                    else:
                        total_aman += 1

                    # Agregasi untuk nilai Rata-rata
                    res = item.get("resource", {})
                    sum_latensi += res.get("latensi_ms", 0)
                    sum_ram += res.get("ram_mb", 0)
                    count_valid += 1
                except:
                    continue

        data_paket = [json.loads(line.strip()) for line in lines[-100:] if line.strip()]
        avg_latensi = sum_latensi / count_valid if count_valid > 0 else 0
        avg_ram = sum_ram / count_valid if count_valid > 0 else 0

        return {
            "status": "sukses",
            "active_model": model_saat_ini,  # Kirim nama model ke frontend agar tahu status
            "total_riwayat": len(lines),
            "summary_kumulatif": {
                "total_aman": total_aman,
                "total_ancaman": total_ancaman,
            },
            "rekap_rata_rata": {
                "avg_latensi_ms": round(avg_latensi, 4),
                "avg_ram_mb": round(avg_ram, 2),
            },
            "data": data_paket,
        }
    except Exception as e:
        return {"status": "error", "pesan": str(e)}
