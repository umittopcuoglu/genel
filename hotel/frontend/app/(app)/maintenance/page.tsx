"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { useTranslation } from "@/lib/i18n";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { AIPanel } from "@/components/ai/AIPanel";
import { MOCK_WORK_ORDERS, MOCK_ASSETS, type WorkOrderRow, type AssetRow } from "@/lib/mock-modules";
import { toast } from "@/components/ui/Toast";
import { useApiData } from "@/lib/useApiData";
import { LoadingState, MockBanner } from "@/components/ui/DataStates";

const WO_STATUS: Record<WorkOrderRow["status"], { tone: BadgeTone; label: string }> = {
  open: { tone: "warning", label: "Açık" },
  assigned: { tone: "info", label: "Atandı" },
  in_progress: { tone: "primary", label: "Devam Ediyor" },
  resolved: { tone: "success", label: "Çözüldü" },
  closed: { tone: "neutral", label: "Kapalı" },
};

const PRIORITY: Record<WorkOrderRow["priority"], { tone: BadgeTone; label: string }> = {
  low: { tone: "neutral", label: "Düşük" },
  normal: { tone: "info", label: "Normal" },
  high: { tone: "warning", label: "Yüksek" },
  urgent: { tone: "danger", label: "Acil" },
};

const ASSET_STATUS: Record<AssetRow["status"], { tone: BadgeTone; label: string }> = {
  active: { tone: "success", label: "Aktif" },
  maintenance: { tone: "warning", label: "Bakımda" },
  retired: { tone: "neutral", label: "Hizmet Dışı" },
};

/**
 * Bakım & Teknik Servis — iş emirleri + varlıklar + TechCare AI (docs/03 §4).
 * Backend: /api/v1/maintenance/* (TASK-015) bağlanınca canlanır.
 */
export default function MaintenancePage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"work-orders" | "assets">("work-orders");
  const { data: workOrders, loading: woLoading, usingFallback: woFallback } = useApiData<WorkOrderRow[]>({
    path: "/api/v1/maintenance/work-orders",
    fallback: MOCK_WORK_ORDERS,
    responseKey: "data",
  });
  const { data: assets, loading: assetsLoading, usingFallback: assetsFallback } = useApiData<AssetRow[]>({
    path: "/api/v1/maintenance/assets",
    fallback: MOCK_ASSETS,
    responseKey: "data",
  });
  const usingFallback = woFallback || assetsFallback;
  const loading = woLoading || assetsLoading;

  return (
    <div className="space-y-6">
      <PageHeader
        title={t('maintenance.title')}
        subtitle={`${workOrders.length} work orders · ${assets.length} assets${usingFallback ? " (mock)" : ""}`}
        action={
          <button
            onClick={() => toast.info("Coming soon")}
            className="flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-sm font-medium text-white hover:opacity-90"
          >
            <Plus className="h-4 w-4" aria-hidden /> {t('maintenance.newWorkOrder')}
          </button>
        }
      />

      {usingFallback && <MockBanner />}

      <AIPanel
        agent="TechCare AI"
        suggestion="AC failure in Room 305 reported 3 times this quarter. Compressor replacement recommended; planned replacement cost 40% less than repeated repairs."
        rationale="Asset history · 3 repeats/90 days · warranty expiring soon"
      />

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          <button
            role="tab"
            aria-selected={tab === "work-orders"}
            onClick={() => setTab("work-orders")}
            className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === "work-orders" ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}
          >
            {t('maintenance.workOrders')}
          </button>
          <button
            role="tab"
            aria-selected={tab === "assets"}
            onClick={() => setTab("assets")}
            className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === "assets" ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}
          >
            {t('maintenance.assets')}
          </button>
        </div>
      </div>

      {tab === "work-orders" && (
        <div className="overflow-x-auto rounded-lg border border-line">
          <table className="responsive-table w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-bg text-left text-xs uppercase tracking-wide text-text-2">
                <th className="px-4 py-3 font-medium">{t('maintenance.location')}</th>
                <th className="px-4 py-3 font-medium">{t('maintenance.category')}</th>
                <th className="px-4 py-3 font-medium">{t('maintenance.description')}</th>
                <th className="px-4 py-3 font-medium">{t('maintenance.priority')}</th>
                <th className="px-4 py-3 font-medium">{t('maintenance.assignedTo')}</th>
                <th className="px-4 py-3 font-medium">{t('common.status')}</th>
                <th className="px-4 py-3 font-medium">{t('maintenance.openedAt')}</th>
              </tr>
            </thead>
            <tbody>
              {workOrders.map((w) => (
                <tr key={w.id} className="border-b border-line last:border-0 hover:bg-bg/60">
                  <td className="px-4 py-3 font-mono" data-label={t('maintenance.location')}>{w.room_no}</td>
                  <td className="px-4 py-3" data-label={t('maintenance.category')}>{w.category}</td>
                  <td className="max-w-xs px-4 py-3 text-text-2" data-label={t('maintenance.description')}>{w.description}</td>
                  <td className="px-4 py-3" data-label={t('maintenance.priority')}><Badge tone={PRIORITY[w.priority].tone}>{PRIORITY[w.priority].label}</Badge></td>
                  <td className="px-4 py-3" data-label={t('maintenance.assignedTo')}>{w.assigned_to ?? <span className="text-amber-600 dark:text-amber-400">{t('maintenance.notAssigned')}</span>}</td>
                  <td className="px-4 py-3" data-label={t('common.status')}><Badge tone={WO_STATUS[w.status].tone}>{WO_STATUS[w.status].label}</Badge></td>
                  <td className="px-4 py-3 text-text-2" data-label={t('maintenance.openedAt')}>{w.opened_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === "assets" && (
        <div className="overflow-x-auto rounded-lg border border-line">
          <table className="responsive-table w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-bg text-left text-xs uppercase tracking-wide text-text-2">
                <th className="px-4 py-3 font-medium">Asset</th>
                <th className="px-4 py-3 font-medium">{t('maintenance.category')}</th>
                <th className="px-4 py-3 font-medium">{t('maintenance.location')}</th>
                <th className="px-4 py-3 font-medium">{t('maintenance.warrantyEnd')}</th>
                <th className="px-4 py-3 font-medium">{t('common.status')}</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((a) => (
                <tr key={a.id} className="border-b border-line last:border-0 hover:bg-bg/60">
                  <td className="px-4 py-3 font-medium" data-label="Asset">{a.name}</td>
                  <td className="px-4 py-3" data-label={t('maintenance.category')}>{a.category}</td>
                  <td className="px-4 py-3 text-text-2" data-label={t('maintenance.location')}>{a.location}</td>
                  <td className="px-4 py-3 font-mono text-text-2" data-label={t('maintenance.warrantyEnd')}>{a.warranty_end}</td>
                  <td className="px-4 py-3" data-label={t('common.status')}><Badge tone={ASSET_STATUS[a.status].tone}>{ASSET_STATUS[a.status].label}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
