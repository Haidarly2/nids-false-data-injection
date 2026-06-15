import React from "react";
import {
  ShieldAlert,
  AlertOctagon,
  ShieldCheck,
  Play,
  Square,
} from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export default function HeaderControls({
  statusServer,
  engineStatus,
  isUnderAttack,
  toggleEngine,
  activeModel,
  handleModelSwitch,
}) {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 border-b pb-4 border-slate-200">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
            NIDS IoT Dasboard
          </h1>
          <p className="text-sm font-medium text-slate-500 mt-1">
            Status API: {statusServer}
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          {/* SAKELAR PEMILIH MODEL */}
          <select
            value={activeModel}
            onChange={(e) => handleModelSwitch(e.target.value)}
            disabled={engineStatus !== "running"}
            className="px-4 py-3 rounded-xl border border-slate-300 font-semibold bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          >
            <option value="incremental_demo">🟢 Mode Demo (Aman)</option>
            <option value="incremental_train">🧪 Mode Eksperimen (Training)</option>
            <option value="rf">🌳 Random Forest (Batch)</option>
            <option value="dnn">🕸️ Deep Learning (Batch)</option>
          </select>

          {/* TOMBOL ENGINE */}
          <button
            onClick={toggleEngine}
            className={`flex items-center justify-center gap-2 px-5 py-3 rounded-xl font-bold shadow-sm transition duration-200 text-white ${
              engineStatus === "running"
                ? "bg-red-600 hover:bg-red-500 shadow-red-600/10"
                : "bg-green-600 hover:bg-green-500 shadow-green-600/10"
            }`}
          >
            {engineStatus === "running" ? (
              <>
                <Square size={16} fill="white" /> Matikan Engine
              </>
            ) : (
              <>
                <Play size={16} fill="white" /> Aktifkan Engine
              </>
            )}
          </button>
        </div>
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
            Lalu lintas stabil. Model saat ini tidak mendeteksi adanya False
            Data Injection.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
