import React from "react";
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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Cpu, Terminal, AlertOctagon } from "lucide-react";

export default function Charts({ dataNids, attackLogs }) {
  return (
    <>
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
                {/* F1-Score hanya dimunculkan jika model Incremental yang sedang aktif */}
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

      {/* KESEHATAN RESOURCE & LOG EVENT TERAKHIR */}
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

        <Card className="shadow-sm border-slate-200 bg-white text-slate-800">
          <CardHeader className="border-b border-slate-100 pb-4">
            <CardTitle className="text-lg font-mono flex items-center gap-2 text-slate-800">
              <Terminal className="h-5 w-5 text-slate-500" /> Log Ancaman
              Terakhir
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4 overflow-y-auto max-h-75">
            {attackLogs.length > 0 ? (
              <div className="space-y-4">
                {attackLogs.map((log, index) => (
                  <div
                    key={index}
                    className="bg-red-50 p-4 rounded-lg border border-red-100 flex flex-col gap-2"
                  >
                    <div className="flex justify-between items-center text-xs font-mono text-red-800/70 border-b border-red-100 pb-2">
                      <span className="font-bold">
                        Paket ID: #{log.paket_ke}
                      </span>
                      <span>{log.timestamp || "Baru saja"}</span>
                    </div>

                    <div className="flex items-start gap-2">
                      <AlertOctagon className="h-4 w-4 text-red-600 mt-0.5" />
                      <div className="text-sm text-red-700 font-bold">
                        False Data Injection Terdeteksi!
                      </div>
                    </div>

                    {/* EKSTRAKSI DATA MENTAH DARI JSON LOG */}
                    {log.data_mentah && (
                      <div className="mt-1 grid grid-cols-2 gap-x-4 gap-y-1 text-xs font-mono text-slate-600 bg-white/60 p-2 rounded border border-red-50">
                        <div>
                          <span className="font-semibold text-slate-400">
                            SRC Port:
                          </span>{" "}
                          {log.data_mentah.L4_SRC_PORT || "N/A"}
                        </div>
                        <div>
                          <span className="font-semibold text-slate-400">
                            DST Port:
                          </span>{" "}
                          {log.data_mentah.L4_DST_PORT || "N/A"}
                        </div>
                        <div>
                          <span className="font-semibold text-slate-400">
                            Protocol:
                          </span>{" "}
                          {log.data_mentah.PROTOCOL === 6
                            ? "TCP"
                            : log.data_mentah.PROTOCOL === 17
                              ? "UDP"
                              : log.data_mentah.PROTOCOL}
                        </div>
                        <div>
                          <span className="font-semibold text-slate-400">
                            IN_BYTES:
                          </span>{" "}
                          <span className="text-red-500 font-bold">
                            {log.data_mentah.IN_BYTES}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-sm font-mono text-slate-400 py-10">
                &gt;_ Menunggu log serangan masuk...
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
