"use client";

import { useState } from "react";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { AIPanel } from "@/components/ai/AIPanel";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { MOCK_EMPLOYEES, MOCK_SHIFTS, MOCK_LEAVES } from "@/lib/mock-faz34";

const LEAVE_TONE: Record<string, BadgeTone> = { pending: "warning", approved: "success", rejected: "danger" };

export default function HrPage() {
  const [tab, setTab] = useState<"employees" | "shifts" | "leaves">("employees");

  return (
    <div className="space-y-6">
      <PageHeader title="İK & Vardiya" subtitle={`${MOCK_EMPLOYEES.length} çalışan · ${MOCK_SHIFTS.length} vardiya`} />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Çalışan" value={String(MOCK_EMPLOYEES.length)} />
        <StatCard label="Bugün Vardiyada" value={String(MOCK_SHIFTS.reduce((s, x) => s + x.assigned, 0))} tone="success" />
        <StatCard label="Bekleyen İzin" value={String(MOCK_LEAVES.filter((l) => l.status === "pending").length)} tone="warning" />
        <StatCard label="Eksik Personel" value={String(MOCK_SHIFTS.filter((s) => s.assigned < s.min).length)} tone="danger" />
      </div>

      <AIPanel
        agent="ShiftAI"
        suggestion="Cumartesi doluluk %95 öngörülüyor; Ön Büro akşam vardiyası 2 kişi ama önerilen 3. Bir resepsiyonist çağrılması veya esnek vardiya önerilir."
        rationale="TASK-009 doluluk tahmini + iş yükü modeli"
      />

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          {[["employees", "Çalışanlar"], ["shifts", "Vardiyalar"], ["leaves", "İzin Talepleri"]].map(([id, label]) => (
            <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id as any)}
              className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === id ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === "employees" && (
        <SimpleTable rows={MOCK_EMPLOYEES} columns={[
          { key: "code", header: "Kod" },
          { key: "name", header: "Ad" },
          { key: "dept", header: "Departman" },
          { key: "position", header: "Pozisyon" },
          { key: "leave", header: "İzin Bakiye", align: "right", render: (e) => `${e.leave} gün` },
        ]} />
      )}
      {tab === "shifts" && (
        <SimpleTable rows={MOCK_SHIFTS} columns={[
          { key: "name", header: "Vardiya" },
          { key: "dept", header: "Departman" },
          { key: "time", header: "Saat" },
          { key: "assigned", header: "Atanan / Min", align: "right", render: (s) => (
            <span className={s.assigned < s.min ? "text-danger" : ""}>{s.assigned} / {s.min}</span>
          ) },
        ]} />
      )}
      {tab === "leaves" && (
        <SimpleTable rows={MOCK_LEAVES} columns={[
          { key: "emp", header: "Çalışan" },
          { key: "type", header: "Tür" },
          { key: "range", header: "Tarih" },
          { key: "days", header: "Gün", align: "right" },
          { key: "status", header: "Durum", render: (l) => <Badge tone={LEAVE_TONE[l.status]}>{l.status === "pending" ? "Bekliyor" : l.status === "approved" ? "Onaylı" : "Reddedildi"}</Badge> },
        ]} />
      )}
    </div>
  );
}
