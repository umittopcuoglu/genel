"use client";

import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { LoadingState, MockBanner } from "@/components/ui/DataStates";
import { useApiData } from "@/lib/useApiData";
import {
  MOCK_INSIGHT_SUMMARY,
  MOCK_CHANNEL_MIX,
  MOCK_INSIGHT_ACTIONS,
  type InsightSummary,
  type ChannelMix,
  type InsightAction,
} from "@/lib/mock-modules";

const TONE: Record<string, string> = {
  warning: "bg-amber-100 text-amber-800",
  opportunity: "bg-emerald-100 text-emerald-800",
  risk: "bg-rose-100 text-rose-800",
};

export default function InsightsPage() {
  const {
    data: summary,
    loading: loadingSummary,
    usingFallback: fbSummary,
  } = useApiData<InsightSummary>({
    path: "/api/v1/insights/summary",
    fallback: MOCK_INSIGHT_SUMMARY,
  });

  const {
    data: mix,
    loading: loadingMix,
    usingFallback: fbMix,
  } = useApiData<ChannelMix[]>({
    path: "/api/v1/insights/channel-mix",
    fallback: MOCK_CHANNEL_MIX,
  });

  const {
    data: actions,
    loading: loadingActions,
    usingFallback: fbActions,
  } = useApiData<InsightAction[]>({
    path: "/api/v1/insights/actions",
    fallback: MOCK_INSIGHT_ACTIONS,
  });

  const anyLoading = loadingSummary || loadingMix || loadingActions;
  const anyFallback = fbSummary || fbMix || fbActions;

  return (
    <div className="space-y-6">
      <PageHeader
        title="InsightAI"
        subtitle="Gelir, doluluk, kanal mix ve kural-tabanli aksiyon onerileri"
      />

      {anyFallback && <MockBanner />}
      {anyLoading && <LoadingState message="Insight verileri yukleniyor..." />}

      {summary && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card className="p-4">
            <p className="text-xs uppercase text-slate-500">Toplam Gelir</p>
            <p className="text-2xl font-semibold">
              {Number(summary.total_revenue).toLocaleString("tr-TR")} TL
            </p>
          </Card>
          <Card className="p-4">
            <p className="text-xs uppercase text-slate-500">ADR</p>
            <p className="text-2xl font-semibold">{summary.adr} TL</p>
          </Card>
          <Card className="p-4">
            <p className="text-xs uppercase text-slate-500">RevPAR</p>
            <p className="text-2xl font-semibold">{summary.revpar} TL</p>
          </Card>
          <Card className="p-4">
            <p className="text-xs uppercase text-slate-500">Doluluk</p>
            <p className="text-2xl font-semibold">%{summary.occupancy_percent}</p>
          </Card>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="p-6">
          <h3 className="mb-4 text-lg font-semibold">Kanal Dagilimi</h3>
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
          <h3 className="mb-4 text-lg font-semibold">Aksiyon Onerileri</h3>
          {actions.length === 0 && <p className="text-sm text-slate-500">Tum KPI'lar normal.</p>}
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
