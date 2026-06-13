"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { AIPanel } from "@/components/ai/AIPanel";
import { MOCK_WORK_ORDERS, MOCK_ASSETS, type WorkOrderRow, type AssetRow } from "@/lib/mock-modules";
import { toast } from "@/components/ui/Toast";

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
  const [tab, setTab] = useState<"work-orders" | "assets">("work-orders");

  return (
    <div className="space-y-6">
      <PageHeader
        title="Bakım & Teknik Servis"
        subtitle={`${MOCK_WORK_ORDERS.length} iş emri · ${MOCK_ASSETS.length} varlık`}
        action={
          <button
            onClick={() => toast.info("Yeni iş emri formu yakında eklenecek")}
            className="flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-sm font-medium text-white hover:opacity-90"
          >
            <Plus className="h-4 w-4" aria-hidden /> Yeni İş Emri
          </button>
        }
      />

      <AIPanel
        agent="TechCare AI"
        suggestion="305 nolu odadaki klima arızası bu çeyrekte 3. kez bildirildi. Kompresör değişimi öneriliyor; geçici onarım yerine planlı değişim maliyeti %40 düşürür."
        rationale="Varlık geçmişi · 3 tekrar/90 gün · garanti süresi dolmak üzere"
      />

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          <button
            role="tab"
            aria-selected={tab === "work-orders"}
            onClick={() => setTab("work-orders")}
            className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === "work-orders" ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}
          >
            İş Emirleri
          </button>
          <button
            role="tab"
            aria-selected={tab === "assets"}
            onClick={() => setTab("assets")}
            className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === "assets" ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}
          >
            Varlıklar
          </button>
        </div>
      </div>

      {tab === "work-orders" && (
        <div className="overflow-x-auto rounded-lg border border-line">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-bg text-left text-xs uppercase tracking-wide text-text-2">
                <th className="px-4 py-3 font-medium">Lokasyon</th>
                <th className="px-4 py-3 font-medium">Kategori</th>
                <th className="px-4 py-3 font-medium">Açıklama</th>
                <th className="px-4 py-3 font-medium">Öncelik</th>
                <th className="px-4 py-3 font-medium">Atanan</th>
                <th className="px-4 py-3 font-medium">Durum</th>
                <th className="px-4 py-3 font-medium">Açılış</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_WORK_ORDERS.map((w) => (
                <tr key={w.id} className="border-b border-line last:border-0 hover:bg-bg/60">
                  <td className="px-4 py-3 font-mono">{w.room_no}</td>
                  <td className="px-4 py-3">{w.category}</td>
                  <td className="max-w-[260px] px-4 py-3 text-text-2">{w.description}</td>
                  <td className="px-4 py-3"><Badge tone={PRIORITY[w.priority].tone}>{PRIORITY[w.priority].label}</Badge></td>
                  <td className="px-4 py-3">{w.assigned_to ?? <span className="text-amber-600 dark:text-amber-400">Atanmadı</span>}</td>
                  <td className="px-4 py-3"><Badge tone={WO_STATUS[w.status].tone}>{WO_STATUS[w.status].label}</Badge></td>
                  <td className="px-4 py-3 text-text-2">{w.opened_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === "assets" && (
        <div className="overflow-x-auto rounded-lg border border-line">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-bg text-left text-xs uppercase tracking-wide text-text-2">
                <th className="px-4 py-3 font-medium">Varlık</th>
                <th className="px-4 py-3 font-medium">Kategori</th>
                <th className="px-4 py-3 font-medium">Lokasyon</th>
                <th className="px-4 py-3 font-medium">Garanti Bitiş</th>
                <th className="px-4 py-3 font-medium">Durum</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_ASSETS.map((a) => (
                <tr key={a.id} className="border-b border-line last:border-0 hover:bg-bg/60">
                  <td className="px-4 py-3 font-medium">{a.name}</td>
                  <td className="px-4 py-3">{a.category}</td>
                  <td className="px-4 py-3 text-text-2">{a.location}</td>
                  <td className="px-4 py-3 font-mono text-text-2">{a.warranty_end}</td>
                  <td className="px-4 py-3"><Badge tone={ASSET_STATUS[a.status].tone}>{ASSET_STATUS[a.status].label}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
