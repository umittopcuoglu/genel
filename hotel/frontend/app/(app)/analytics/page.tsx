"use client";

import { useTranslation } from "@/lib/i18n";
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

export default function AnalyticsPage() {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <PageHeader title={t('analytics.title')} subtitle={t('analytics.subtitle')} />

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Monthly Revenue" value="₺3.2M" hint="vs last month ↑ 11%" tone="success" />
        <StatCard label={t('analytics.occupancyTrend')} value="84%" hint="last 7 days" tone="success" />
        <StatCard label={t('dashboard.adr')} value="₺2.450" hint="average room rate" />
        <StatCard label={t('dashboard.revpar')} value="₺2.058" hint="occupancy × ADR" />
      </div>

      <AIPanel
        agent="InsightAI"
        suggestion="Weekend occupancy reaches 95% but OTA share is 34%. Direct channel campaign on Saturday could reduce commission costs by ₺18,000."
        rationale="90-day forecast · channel mix analysis · commission rates"
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card title="Weekly Occupancy (%) — This year vs Last year">
          <BarChart
            data={MOCK_OCCUPANCY_TREND}
            format={(v) => `%${v}`}
            primaryLabel="This year"
            secondaryLabel="Last year"
          />
        </Card>

        <Card title="Monthly Revenue Trend (₺)">
          <BarChart
            data={MOCK_REVENUE_TREND}
            format={(v) => `₺${(v / 1_000_000).toFixed(1)}M`}
            primaryLabel="Revenue"
          />
        </Card>
      </div>

      <Card title="Reservation Source Distribution">
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
