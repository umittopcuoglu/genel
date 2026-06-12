"use client";

import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { StatCard } from "@/components/kpi/StatCard";
import { AIPanel } from "@/components/ai/AIPanel";
import { BarChart } from "@/components/charts/BarChart";
import { MOCK_OCCUPANCY_TREND, MOCK_REVENUE_TREND, MOCK_SOURCE_MIX } from "@/lib/mock-modules";

const TONE_BG: Record<string, string> = {
  primary: "bg-indigo-500",
  info: "bg-sky-500",
  success: "bg-emerald-500",
  warning: "bg-amber-500",
  neutral: "bg-zinc-400",
};

/**
 * Gelişmiş Analitik Dashboard — docs/03 §3. KPI + trend grafikleri + InsightAI.
 * Backend: GET /api/v1/dashboard/manager + /reports (TASK-010/13) bağlanınca canlanır.
 */
export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Analitik" subtitle="Doluluk, gelir ve kanal performansı" />

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Aylık Gelir" value="₺3.2M" hint="geçen aya göre ↑ %11" tone="success" />
        <StatCard label="Ort. Doluluk" value="%84" hint="son 7 gün" tone="success" />
        <StatCard label="ADR" value="₺2.450" hint="ortalama oda fiyatı" />
        <StatCard label="RevPAR" value="₺2.058" hint="doluluk × ADR" />
      </div>

      <AIPanel
        agent="InsightAI"
        suggestion="Hafta sonu doluluk %95'e ulaşıyor ancak OTA payı %34. Cumartesi için direkt kanal kampanyası ile komisyon maliyetini ₺18.000 azaltabilirsiniz."
        rationale="90 günlük tahmin · kanal karması analizi · komisyon oranları"
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card title="Haftalık Doluluk (%) — Bu yıl vs Geçen yıl">
          <BarChart
            data={MOCK_OCCUPANCY_TREND}
            format={(v) => `%${v}`}
            primaryLabel="Bu yıl"
            secondaryLabel="Geçen yıl"
          />
        </Card>

        <Card title="Aylık Gelir Trendi (₺)">
          <BarChart
            data={MOCK_REVENUE_TREND}
            format={(v) => `₺${(v / 1_000_000).toFixed(1)}M`}
            primaryLabel="Gelir"
          />
        </Card>
      </div>

      <Card title="Rezervasyon Kaynak Dağılımı">
        <div className="space-y-3">
          {MOCK_SOURCE_MIX.map((s) => (
            <div key={s.label} className="flex items-center gap-3">
              <span className="w-20 text-sm text-text-2">{s.label}</span>
              <div className="h-3 flex-1 overflow-hidden rounded-full bg-bg">
                <div className={`h-full rounded-full ${TONE_BG[s.tone]}`} style={{ width: `${s.value}%` }} />
              </div>
              <span className="w-10 text-right font-mono text-sm">%{s.value}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
