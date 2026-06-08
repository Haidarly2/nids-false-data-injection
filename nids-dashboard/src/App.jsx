import React, { useState, useEffect } from "react";
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  Activity,
  ShieldAlert,
  AlertOctagon,
  ShieldCheck,
  Cpu,
  Terminal,
  Shield,
  ArrowRight,
  Play,
  Square,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

function App() {
  const [view, setView] = useState("portal");
  const [dataNids, setDataNids] = useState([]);
  const [attackLogs, setAttackLogs] = useState([]);
  const [statusServer, setStatusServer] = useState("Menghubungkan ke API...");
  const [engineStatus, setEngineStatus] = useState("stopped");
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
        const response = await fetch("http://127.0.0.1:8080/api/data");
        const result = await response.json();

        if (result.status === "sukses" && result.data.length > 0) {
          setStatusServer("Terhubung (Real-time Sync) 🟢");

          const formattedData = result.data.map((item) => {
            const isAttack = item.prediksi_ai === 1;
            return {
              paket: item.paket_ke,
              trafik_normal: isAttack ? 0 : 1,
              trafik_serangan: isAttack ? 1 : 0,
              latensi: item.resource?.latensi_ms || 0,
              ram: item.resource?.ram_mb || 0,
              // Penambahan metrik akurasi dan f1-score
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
          "http://127.0.0.1:8080/api/engine/status",
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
  }, [view]);

  const toggleEngine = async () => {
    const endpoint = engineStatus === "running" ? "stop" : "start";
    try {
      const res = await fetch(`http://127.0.0.1:8080/api/engine/${endpoint}`, {
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

  // Ekstraksi untuk Indikator KPI Angka
  const dataTerbaru =
    dataNids.length > 0 ? dataNids[dataNids.length - 1] : null;
  const akurasiSaatIni = dataTerbaru?.akurasi || 0;
  const f1SaatIni = dataTerbaru?.f1_score || 0;

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
              NIDS COMMAND CENTER
            </h1>
            <p className="text-sm text-slate-400">
              Sistem Deteksi Serangan False Data Injection Berbasis Incremental
              Learning pada Perangkat Medical IoT
            </p>
          </div>
          <button
            onClick={() => setView("dashboard")}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 px-4 rounded-xl transition duration-200 group shadow-lg shadow-blue-600/20"
          >
            Masuk Ke Command Center
            <ArrowRight
              size={18}
              className="transform group-hover:translate-x-1 transition-transform"
            />
          </button>
          <div className="text-xs text-slate-500 font-mono pt-4 border-t border-slate-800">
            Secure Portal Session v1.1
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-8 text-slate-900 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* HEADER & TOMBOL CONTROL ENGINE */}
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 border-b pb-4 border-slate-200">
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
                NIDS Medical IoT Command Center
              </h1>
              <p className="text-sm font-medium text-slate-500 mt-1">
                Status API: {statusServer}
              </p>
            </div>

            <button
              onClick={toggleEngine}
              className={`flex items-center gap-2 px-5 py-3 rounded-xl font-bold shadow-sm transition duration-200 text-white ${
                engineStatus === "running"
                  ? "bg-red-600 hover:bg-red-500 shadow-red-600/10"
                  : "bg-green-600 hover:bg-green-500 shadow-green-600/10"
              }`}
            >
              {engineStatus === "running" ? (
                <>
                  <Square size={16} fill="white" /> Matikan Engine NIDS
                </>
              ) : (
                <>
                  <Play size={16} fill="white" /> Aktifkan Engine NIDS
                </>
              )}
            </button>
          </div>

          {isUnderAttack ? (
            <Alert
              variant="destructive"
              className="animate-pulse border-red-600 bg-red-50 text-red-900"
            >
              <AlertOctagon className="h-5 w-5" />
              <AlertTitle className="text-lg font-bold">
                PERINGATAN KRITIS: SERANGAN FDI TERDETEKSI!
              </AlertTitle>
              <AlertDescription className="text-sm font-medium">
                Mesin AI mendeteksi anomali injeksi data pada aliran jaringan.
                Segera periksa log sistem.
              </AlertDescription>
            </Alert>
          ) : (
            <Alert className="border-green-500 bg-green-50 text-green-900">
              <ShieldCheck className="h-5 w-5 stroke-green-600" />
              <AlertTitle className="text-lg font-bold text-green-800">
                STATUS JARINGAN AMAN
              </AlertTitle>
              <AlertDescription className="text-sm font-medium text-green-700">
                Lalu lintas stabil. Model Incremental Learning tidak mendeteksi
                adanya False Data Injection.
              </AlertDescription>
            </Alert>
          )}
        </div>

        {/* KARTU KPI METRIK LALU LINTAS */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-500">
                Total Request Masuk
              </CardTitle>
              <Activity className="h-4 w-4 text-slate-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {summary.total.toLocaleString()}
              </div>
            </CardContent>
          </Card>
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-500">
                Paket Aman (Normal)
              </CardTitle>
              <ShieldCheck className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">
                {summary.paketAman.toLocaleString()}
              </div>
            </CardContent>
          </Card>
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-500">
                Anomali / Serangan FDI
              </CardTitle>
              <ShieldAlert className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-red-600">
                {summary.paketAncaman.toLocaleString()}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* KARTU KPI PERFORMA AI */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="shadow-sm border-slate-200 border-l-4 border-l-emerald-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-500">
                Akurasi Deteksi AI
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-emerald-600">
                {akurasiSaatIni}%
              </div>
            </CardContent>
          </Card>
          <Card className="shadow-sm border-slate-200 border-l-4 border-l-blue-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-500">
                F1-Score Keseluruhan
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">
                {f1SaatIni}%
              </div>
            </CardContent>
          </Card>
        </div>

        {/* GRAFIK CONCEPT DRIFT & AKURASI */}
        <Card className="shadow-sm border-slate-200">
          <CardHeader>
            <CardTitle className="text-xl text-slate-800">
              Pemantauan Performa Adaptif (Concept Drift Monitor)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 w-full mt-4">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={dataNids}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                    stroke="#e2e8f0"
                  />
                  <XAxis
                    dataKey="paket"
                    tick={{ fontSize: 12, fill: "#64748b" }}
                  />
                  <YAxis
                    domain={[0, 100]}
                    tick={{ fontSize: 12, fill: "#64748b" }}
                  />
                  <Tooltip
                    contentStyle={{
                      borderRadius: "8px",
                      border: "none",
                      boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                    }}
                  />
                  <Legend verticalAlign="top" height={36} />
                  <Line
                    type="monotone"
                    dataKey="akurasi"
                    name="Akurasi (%)"
                    stroke="#10b981"
                    strokeWidth={3}
                    dot={false}
                    isAnimationActive={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="f1_score"
                    name="F1-Score (%)"
                    stroke="#3b82f6"
                    strokeWidth={3}
                    dot={false}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* GRAFIK UTAMA TRAFIK */}
        <Card className="shadow-sm border-slate-200">
          <CardHeader>
            <CardTitle className="text-xl text-slate-800">
              Pemantauan Lalu Lintas Jaringan (Real-Time)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-72 w-full mt-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={dataNids}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                    stroke="#e2e8f0"
                  />
                  <XAxis
                    dataKey="paket"
                    tick={{ fontSize: 12, fill: "#64748b" }}
                  />
                  <YAxis tick={{ fontSize: 12, fill: "#64748b" }} />
                  <Tooltip
                    contentStyle={{
                      borderRadius: "8px",
                      border: "none",
                      boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                    }}
                  />
                  <Legend verticalAlign="top" height={36} />
                  <Area
                    type="step"
                    dataKey="trafik_normal"
                    stackId="1"
                    stroke="#16a34a"
                    fill="#bbf7d0"
                    name="Trafik Normal"
                  />
                  <Area
                    type="step"
                    dataKey="trafik_serangan"
                    stackId="1"
                    stroke="#dc2626"
                    fill="#fecaca"
                    name="Trafik Serangan (FDI)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* KESEHATAN RESOURCE & LOG EVENT */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="shadow-sm border-slate-200">
            <CardHeader>
              <CardTitle className="text-lg text-slate-800 flex items-center gap-2">
                <Cpu className="h-5 w-5 text-slate-500" /> Performa Gateway AI
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64 w-full mt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={dataNids}>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      vertical={false}
                      stroke="#e2e8f0"
                    />
                    <XAxis
                      dataKey="paket"
                      tick={{ fontSize: 12, fill: "#64748b" }}
                    />
                    <YAxis
                      yAxisId="left"
                      tick={{ fontSize: 12, fill: "#64748b" }}
                      width={40}
                    />
                    <YAxis
                      yAxisId="right"
                      orientation="right"
                      tick={{ fontSize: 12, fill: "#64748b" }}
                      width={40}
                    />
                    <Tooltip
                      contentStyle={{
                        borderRadius: "8px",
                        border: "none",
                        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                      }}
                    />
                    <Legend verticalAlign="bottom" height={36} />
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="latensi"
                      stroke="#ea580c"
                      strokeWidth={2}
                      dot={false}
                      name="Latensi (ms)"
                      isAnimationActive={false}
                    />
                    <Line
                      yAxisId="right"
                      type="step"
                      dataKey="ram"
                      stroke="#8b5cf6"
                      strokeWidth={2}
                      dot={false}
                      name="RAM (MB)"
                      isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-sm border-slate-200 bg-slate-900 text-slate-50">
            <CardHeader className="border-b border-slate-800 pb-4">
              <CardTitle className="text-lg font-mono flex items-center gap-2 text-slate-100">
                <Terminal className="h-5 w-5 text-slate-400" /> Log Ancaman
                Terakhir
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              {attackLogs.length > 0 ? (
                <div className="space-y-3">
                  {attackLogs.map((log, index) => (
                    <div
                      key={index}
                      className="bg-slate-800 p-3 rounded-md border border-slate-700 flex flex-col gap-1"
                    >
                      <div className="flex justify-between items-center text-xs font-mono text-slate-400">
                        <span>Paket ID: #{log.paket_ke}</span>
                      </div>
                      <div className="text-sm text-red-400 font-semibold">
                        [ALERT] Indikasi Serangan False Data Injection (FDI)
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-full flex items-center justify-center text-sm font-mono text-slate-500 py-10">
                  &gt;_ Menunggu log serangan masuk...
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default App;
