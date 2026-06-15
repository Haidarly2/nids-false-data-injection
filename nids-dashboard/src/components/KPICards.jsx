import React from "react";
import { Activity, ShieldAlert, ShieldCheck, Zap, HardDrive, Target, Award } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function KPICards({
  summary,
  akurasiSaatIni,
  precisionSaatIni,
  recallSaatIni,
  f1SaatIni,
  kappaSaatIni,
  rekapAvg,
}) {
  return (
    <div className="space-y-6">
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
              Akurasi Deteksi
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-emerald-600">
              {akurasiSaatIni}%
            </div>
          </CardContent>
        </Card>
        <Card className="shadow-sm border-slate-200 border-l-4 border-l-teal-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500 flex items-center gap-1">
              <Target className="h-3 w-3 text-teal-500" /> Precision
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-teal-600">
              {precisionSaatIni}%
            </div>
          </CardContent>
        </Card>
        <Card className="shadow-sm border-slate-200 border-l-4 border-l-indigo-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500 flex items-center gap-1">
              <Award className="h-3 w-3 text-indigo-500" /> Recall
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-indigo-600">
              {recallSaatIni}%
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
            <div className="text-3xl font-bold text-blue-600">{f1SaatIni}%</div>
          </CardContent>
        </Card>
        <Card className="shadow-sm border-slate-200 border-l-4 border-l-amber-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500 flex items-center gap-1">
              <Activity className="h-3 w-3 text-amber-500" /> Kappa Statistic
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600">
              {kappaSaatIni}%
            </div>
          </CardContent>
        </Card>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="shadow-sm border-slate-200 border-l-4 border-l-orange-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">
              Rata-rata Latensi Deteksi
            </CardTitle>
            <Zap className="h-4 w-4 text-orange-400" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600">
              {rekapAvg.avg_latensi_ms}{" "}
              <span className="text-sm font-normal text-slate-500">
                ms / paket
              </span>
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-sm border-slate-200 border-l-4 border-l-purple-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">
              Rata-rata Konsumsi RAM
            </CardTitle>
            <HardDrive className="h-4 w-4 text-purple-400" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-600">
              {rekapAvg.avg_ram_mb}{" "}
              <span className="text-sm font-normal text-slate-500">MB</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
