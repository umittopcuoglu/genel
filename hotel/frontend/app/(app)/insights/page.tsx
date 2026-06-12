"use client";

import { useEffect, useState } from "react";
import { LineChart as LineIcon } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TONE: Record<string, string> = {
  warning: "bg-amber-100 text-amber-800",
  opportunity: "bg-emerald-100 text-emerald-800",
  risk: "bg-rose-100 text-rose-800",
};

export default function InsightsPage() {
  const [summary, setSummary] = useState<any>(null);
  const [mix, setMix] = useState<any[]>([]);
  const [actions, setActions] = useState<any[]>([]);

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : "";
    const headers = { Authorization: `Bearer ${token}` };
    Promise.all([
      fetch(`${API}/api/v1/insights/summary`, { headers }).then((r) => r.json()),
      fetch(`${API}/api/v1/insights/channel-mix`, { headers }).then((r) => r.json()),
      fetch(`${API}/api/v1/insights/actions`, { headers }).then((r) => r.json()),
    ]).then(([s, m, a]) => {
      setSummary(s);
      setMix(Array.isArray(m) ? m : []);
      setActions(Array.isArray(a) ? a : []);
    });
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        title="InsightAI"
        description="Gelir, doluluk, kanal mix ve kural-tabanlı aksiyon önerileri"
        icon={LineIcon}
      />

      {summary && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card className="p-4">
            <p className="text-xs uppercase text-slate-500">Toplam Gelir</p>
            <p className="text-2xl font-semibold">
              ₺{Number(summary.total_revenue).toLocaleString("tr-TR")}
            </p>
          </Card>
          <Card className="p-4">
            <p className="text-xs uppercase text-slate-500">ADR</p>
            <p className="text-2xl font-semibold">₺{summary.adr}</p>
          </Card>
          <Card className="p-4">
            <p className="text-xs uppercase text-slate-500">RevPAR</p>
            <p className="text-2xl font-semibold">₺{summary.revpar}</p>
          </Card>
          <Card className="p-4">
            <p className="text-xs uppercase text-slate-500">Doluluk</p>
            <p className="text-2xl font-semibold">%{summary.occupancy_percent}</p>
          </Card>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="p-6">
          <h3 className="mb-4 text-lg font-semibold">Kanal Dağılımı</h3>
          {mix.length === 0 && <p className="text-sm text-slate-500">Veri yok.</p>}
          <ul className="space-y-2">
            {mix.map((m) => (
              <li key={m.channel} className="flex items-center justify-between text-sm">
                <span>{m.channel}</span>
                <span className="text-slate-500">
                  {m.count} · %{m.share_percent}
                </span>
              </li>
            ))}
          </ul>
        </Card>
        <Card className="p-6">
          <h3 className="mb-4 text-lg font-semibold">Aksiyon Önerileri</h3>
          {actions.length === 0 && <p className="text-sm text-slate-500">Tüm KPI'lar normal.</p>}
          <ul className="space-y-3">
            {actions.map((a, i) => (
              <li key={i} className="rounded border p-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium">{a.title}</h4>
                  <Badge className={TONE[a.severity] || ""}>{a.severity}</Badge>
                </div>
                <p className="mt-1 text-sm text-slate-600">{a.message}</p>
                <p className="mt-1 text-xs text-slate-400">Aksiyon: {a.action}</p>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
