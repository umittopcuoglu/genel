"use client";

import { useState } from "react";
import { User, Sparkles } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { MOCK_HK_TASKS, type HousekeepingTask } from "@/lib/mock-modules";
import { useApiData } from "@/lib/useApiData";
import { LoadingState, MockBanner } from "@/components/ui/DataStates";

const TYPE_LABEL: Record<HousekeepingTask["type"], string> = {
  checkout_clean: "Çıkış Temizliği",
  stayover: "Konaklama Temizliği",
  deep_clean: "Derin Temizlik",
  inspection: "Kontrol",
};

const PRIORITY_TONE: Record<HousekeepingTask["priority"], BadgeTone> = {
  low: "neutral",
  normal: "info",
  high: "danger",
};

const COLUMNS: { status: HousekeepingTask["status"]; label: string; accent: string }[] = [
  { status: "pending", label: "Bekliyor", accent: "border-t-amber-500" },
  { status: "in_progress", label: "Devam Ediyor", accent: "border-t-sky-500" },
  { status: "done", label: "Tamamlandı", accent: "border-t-emerald-500" },
  { status: "inspected", label: "Kontrol Edildi", accent: "border-t-indigo-500" },
];

/**
 * Housekeeping Kanban panosu — duruma göre 4 kolon (docs/03 §4).
 * Backend: GET /api/v1/housekeeping/tasks (TASK-005) bağlanınca canlanır.
 */
export default function HousekeepingPage() {
  const { data: tasks, loading, usingFallback } = useApiData<HousekeepingTask[]>({
    path: "/api/v1/housekeeping/tasks",
    fallback: MOCK_HK_TASKS,
    responseKey: "data",
  });

  const counts = COLUMNS.map((c) => tasks.filter((t) => t.status === c.status).length);

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Housekeeping" subtitle="Yükleniyor..." />
        <LoadingState message="Housekeeping görevleri yükleniyor..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Housekeeping" subtitle={`${tasks.length} aktif görev${usingFallback ? " (mock)" : ""}`} />
      {usingFallback && <MockBanner />}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {COLUMNS.map((col, i) => {
          const colTasks = tasks.filter((t) => t.status === col.status);
          return (
            <div key={col.status} className={`rounded-xl border border-t-4 border-line bg-bg/40 ${col.accent}`}>
              <div className="flex items-center justify-between px-3 py-2.5">
                <h2 className="text-sm font-semibold">{col.label}</h2>
                <span className="rounded-full bg-surface px-2 py-0.5 text-xs text-text-2">{counts[i]}</span>
              </div>
              <div className="space-y-2 p-2">
                {colTasks.map((t) => (
                  <div key={t.id} className="rounded-lg border border-line bg-surface p-3">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-base font-semibold">{t.room_no}</span>
                      <Badge tone={PRIORITY_TONE[t.priority]}>{t.priority === "high" ? "Yüksek" : t.priority === "normal" ? "Normal" : "Düşük"}</Badge>
                    </div>
                    <div className="mt-1 text-xs text-text-2">{TYPE_LABEL[t.type]}</div>
                    <div className="mt-2 flex items-center gap-1.5 text-xs">
                      {t.assigned_to ? (
                        <>
                          <User className="h-3 w-3 text-text-2" aria-hidden />
                          <span className="text-text-1">{t.assigned_to}</span>
                        </>
                      ) : (
                        <span className="text-amber-600 dark:text-amber-400">Atanmadı</span>
                      )}
                    </div>
                    {t.note && (
                      <div className="mt-1 flex items-start gap-1.5 text-xs text-text-2">
                        <Sparkles className="h-3 w-3 mt-0.5 flex-shrink-0" aria-hidden />
                        <span>{t.note}</span>
                      </div>
                    )}
                  </div>
                ))}
                {colTasks.length === 0 && (
                  <div className="rounded-lg border border-dashed border-line p-6 text-center text-xs text-text-2">
                    Görev yok
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
