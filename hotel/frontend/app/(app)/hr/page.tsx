"use client";

import { useState } from "react";
import { useTranslation } from "@/lib/i18n";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { AIPanel } from "@/components/ai/AIPanel";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { MOCK_EMPLOYEES, MOCK_SHIFTS, MOCK_LEAVES } from "@/lib/mock-faz34";

const LEAVE_TONE: Record<string, BadgeTone> = { pending: "warning", approved: "success", rejected: "danger" };

export default function HrPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"employees" | "shifts" | "leaves">("employees");

  return (
    <div className="space-y-6">
      <PageHeader title={t('hr.title')} subtitle={`${MOCK_EMPLOYEES.length} çalışan · ${MOCK_SHIFTS.length} vardiya`} />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label={t('hr.employees')} value={String(MOCK_EMPLOYEES.length)} />
        <StatCard label="Bugün Vardiyada" value={String(MOCK_SHIFTS.reduce((s, x) => s + x.assigned, 0))} tone="success" />
        <StatCard label="Bekleyen İzin" value={String(MOCK_LEAVES.filter((l) => l.status === "pending").length)} tone="warning" />
        <StatCard label="Eksik Personel" value={String(MOCK_SHIFTS.filter((s) => s.assigned < s.min).length)} tone="danger" />
      </div>

      <AIPanel
        agent="ShiftAI"
        suggestion="Saturday occupancy forecast: 95%. Front desk evening shift has 2 staff but 3 recommended. Call in receptionist or flexible shift suggested."
        rationale="Occupancy forecast + workload model"
      />

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          {[["employees", t('hr.employees')], ["shifts", t('hr.shifts')], ["leaves", "İzin Talepleri"]].map(([id, label]) => (
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
          { key: "name", header: t('common.name') },
          { key: "dept", header: t('hr.department') },
          { key: "position", header: t('hr.position') },
          { key: "leave", header: t('hr.leaveBalance'), align: "right", render: (e) => `${e.leave} days` },
        ]} />
      )}
      {tab === "shifts" && (
        <SimpleTable rows={MOCK_SHIFTS} columns={[
          { key: "name", header: t('hr.shiftType') },
          { key: "dept", header: t('hr.department') },
          { key: "time", header: "Saat" },
          { key: "assigned", header: "Assigned / Min", align: "right", render: (s) => (
            <span className={s.assigned < s.min ? "text-danger" : ""}>{s.assigned} / {s.min}</span>
          ) },
        ]} />
      )}
      {tab === "leaves" && (
        <SimpleTable rows={MOCK_LEAVES} columns={[
          { key: "emp", header: t('hr.employeeName') },
          { key: "type", header: "Tür" },
          { key: "range", header: t('common.date') },
          { key: "days", header: "Gün", align: "right" },
          { key: "status", header: t('common.status'), render: (l) => <Badge tone={LEAVE_TONE[l.status]}>{l.status === "pending" ? "Pending" : l.status === "approved" ? "Approved" : "Rejected"}</Badge> },
        ]} />
      )}
    </div>
  );
}
