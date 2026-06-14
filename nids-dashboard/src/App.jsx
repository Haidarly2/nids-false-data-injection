import React, { useState, useEffect } from "react";
import { ArrowRight, Shield } from "lucide-react";
import HeaderControls from "./components/HeaderControls";
import KPICards from "./components/KPICards";
import Charts from "./components/Charts";

export default function App() {
  const [view, setView] = useState("portal");
  const [dataNids, setDataNids] = useState([]);
  const [attackLogs, setAttackLogs] = useState([]);
  const [statusServer, setStatusServer] = useState("Menghubungkan ke API...");
  const [engineStatus, setEngineStatus] = useState("stopped");
  const [activeModel, setActiveModel] = useState("incremental");
  const [isUnderAttack, setIsUnderAttack] = useState(false);
  const [summary, setSummary] = useState({
    total: 0,
    paketAman: 0,
    paketAncaman: 0,
  });

  useEffect(() => {
    if (view !== "dashboard") return;

    const fetchData = async () => {
      try {
        const response = await fetch("http://127.0.0.1:8888/api/data");
        const result = await response.json();

        if (result.status === "sukses" && result.data.length > 0) {
          setStatusServer("Terhubung (Real-time Sync) 🟢");

          if (result.active_model && result.active_model !== activeModel) {
            setActiveModel(result.active_model);
          }

          const formattedData = result.data.map((item) => {
            const isAttack = item.prediksi_ai === 1;
            return {
              paket: item.paket_ke,
              trafik_normal: isAttack ? 0 : 1,
              trafik_serangan: isAttack ? 1 : 0,
              latensi: item.resource?.latensi_ms || 0,
              ram: item.resource?.ram_mb || 0,
              akurasi: item.metrik?.akurasi || 0,
              f1_score: item.metrik?.f1_score || 0,
            };
          });

          setDataNids(formattedData);

          const recentPackets = result.data.slice(-50);
          const detectedAttack = result.data
            .slice(-5)
            .some((item) => item.prediksi_ai === 1);
          setIsUnderAttack(detectedAttack);

          const logs = recentPackets
            .filter((item) => item.prediksi_ai === 1)
            .reverse()
            .slice(0, 5);
          setAttackLogs(logs);

          setSummary({
            total: result.total_riwayat,
            paketAman: result.summary_kumulatif.total_aman,
            paketAncaman: result.summary_kumulatif.total_ancaman,
          });
        } else {
          setStatusServer("Terhubung. Menunggu data jaringan... ⏳");
        }

        const statusRes = await fetch(
          "http://127.0.0.1:8888/api/engine/status",
        );
        const statusData = await statusRes.json();
        setEngineStatus(statusData.status);
      } catch (error) {
        setStatusServer("Backend Terputus / API Mati 🔴");
      }
    };

    fetchData();
    const intervalId = setInterval(fetchData, 2000);
    return () => clearInterval(intervalId);
  }, [view, activeModel]);

  const toggleEngine = async () => {
    const endpoint = engineStatus === "running" ? "stop" : "start";
    try {
      const res = await fetch(`http://127.0.0.1:8888/api/engine/${endpoint}`, {
        method: "POST",
      });
      const data = await res.json();
      if (data.status === "success") {
        setEngineStatus(engineStatus === "running" ? "stopped" : "running");
        if (endpoint === "start") {
          setDataNids([]);
          setAttackLogs([]);
          setSummary({ total: 0, paketAman: 0, paketAncaman: 0 });
        }
      }
    } catch (e) {
      alert("Gagal berkomunikasi dengan API Server");
    }
  };

  const handleModelSwitch = async (newModel) => {
    try {
      setStatusServer("Mengganti Model AI... 🔄");
      const res = await fetch(`http://127.0.0.1:8888/api/engine/switch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model_name: newModel }),
      });
      const data = await res.json();
      if (data.status === "success") {
        setActiveModel(newModel);
      }
    } catch (e) {
      alert("Gagal mengganti model: " + e.message);
    }
  };

  const dataTerbaru =
    dataNids.length > 0 ? dataNids[dataNids.length - 1] : null;

  if (view === "portal") {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-100 p-6 font-sans">
        <div className="max-w-md w-full text-center space-y-8 p-10 bg-slate-900 rounded-2xl border border-slate-800 shadow-2xl">
          <div className="flex justify-center">
            <div className="p-4 bg-blue-500/10 rounded-full border border-blue-500/30 text-blue-400 animate-pulse">
              <Shield size={48} />
            </div>
          </div>
          <div className="space-y-2">
            <h1 className="text-2xl font-extrabold tracking-tight">
              NIDS Dasboard IoT
            </h1>
            <p className="text-sm text-slate-400">
              Sistem Deteksi Serangan False Data Injection Berbasis Incremental
              Learning pada Perangkat IoT
            </p>
          </div>
          <button
            onClick={() => setView("dashboard")}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 px-4 rounded-xl transition duration-200 group shadow-lg shadow-blue-600/20"
          >
            Masuk Ke Dasboard
            <ArrowRight
              size={18}
              className="transform group-hover:translate-x-1 transition-transform"
            />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-8 text-slate-900 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        <HeaderControls
          statusServer={statusServer}
          engineStatus={engineStatus}
          isUnderAttack={isUnderAttack}
          toggleEngine={toggleEngine}
          activeModel={activeModel}
          handleModelSwitch={handleModelSwitch}
        />

        <KPICards
          summary={summary}
          akurasiSaatIni={dataTerbaru?.akurasi || 0}
          f1SaatIni={dataTerbaru?.f1_score || 0}
        />

        {/* DI SINI LETAK KOMPONEN CHARTS KITA */}
        <Charts
          dataNids={dataNids}
          activeModel={activeModel}
          attackLogs={attackLogs}
        />
      </div>
    </div>
  );
}
