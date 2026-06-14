'use client';

import { useTranslation } from '@/lib/i18n';
import { StatCard } from "@/components/kpi/StatCard";
import { AIPanel } from "@/components/ai/AIPanel";
import { PageHeader } from "@/components/ui/PageHeader";

const MOCK = {
  occupancy: "78%",
  adr: "₺2.450",
  revpar: "₺1.911",
  arrivals: "12 / 18",
  departures: "9 / 14",
  ooo: "3",
};

export default function DashboardPage() {
  const { t } = useTranslation();

  return (
    <div className="space-y-6">
      <PageHeader
        title={t('dashboard.title')}
        subtitle={t('dashboard.subtitle')}
        mock={false}
      />

      <div className="stagger grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
        <StatCard label={t('dashboard.occupancy')} value={MOCK.occupancy} hint={t('dashboard.last7Days')} tone="success" />
        <StatCard label={t('dashboard.adr')} value={MOCK.adr} />
        <StatCard label={t('dashboard.revpar')} value={MOCK.revpar} />
        <StatCard label={t('dashboard.arrivals')} value={MOCK.arrivals} hint={t('dashboard.expected')} />
        <StatCard label={t('dashboard.departures')} value={MOCK.departures} hint={t('dashboard.expected')} />
        <StatCard label={t('dashboard.oooRooms')} value={MOCK.ooo} tone="danger" />
      </div>

      <div className="max-w-xl">
        <AIPanel
          agent="InsightAI"
          suggestion="Next weekend occupancy forecast: 91%. Consider BAR increase of 8% for Fri-Sat."
          rationale="90-day forecast model · concert event in city · competitor rates increased"
        />
      </div>
    </div>
  );
}
