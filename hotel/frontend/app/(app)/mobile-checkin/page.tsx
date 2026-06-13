"use client";

import { useTranslation } from "@/lib/i18n";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { MOCK_CHECKIN_SESSIONS } from "@/lib/mock-faz34";

const STEP_TONE = (v: string): BadgeTone =>
  v === "passed" || v === "matched" || v === "submitted" || v === "issued" || v === "completed"
    ? "success"
    : v === "pending" || v === "in_progress" || v === "started"
    ? "warning"
    : "neutral";

const stepBadge = (v: string) => (v === "—" ? <span className="text-text-2">—</span> : <Badge tone={STEP_TONE(v)}>{v}</Badge>);

export default function MobileCheckinPage() {
  const { t } = useTranslation();
  const completed = MOCK_CHECKIN_SESSIONS.filter((s) => s.status === "completed").length;

  return (
    <div className="space-y-6">
      <PageHeader title={t('mobileCheckin.title')} subtitle={t('mobileCheckin.subtitle')} />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Sessions" value={String(MOCK_CHECKIN_SESSIONS.length)} />
        <StatCard label={t('mobileCheckin.completed')} value={String(completed)} tone="success" />
        <StatCard label="In Progress" value={String(MOCK_CHECKIN_SESSIONS.filter((s) => s.status !== "completed").length)} tone="warning" />
        <StatCard label={t('mobileCheckin.egmNotification')} value={String(MOCK_CHECKIN_SESSIONS.filter((s) => s.egm === "submitted").length)} />
      </div>

      <SimpleTable rows={MOCK_CHECKIN_SESSIONS} columns={[
        { key: "guest", header: "Guest" },
        { key: "room", header: t('cv.room') },
        { key: "ocr", header: t('mobileCheckin.scanPassport'), render: (s) => stepBadge(s.ocr) },
        { key: "face", header: "Face", render: (s) => stepBadge(s.face) },
        { key: "egm", header: t('mobileCheckin.egmNotification'), render: (s) => stepBadge(s.egm) },
        { key: "nfc", header: "NFC Key", render: (s) => stepBadge(s.nfc) },
        { key: "status", header: t('common.status'), render: (s) => <Badge tone={s.status === "completed" ? "success" : "info"}>{s.status === "completed" ? "Completed" : s.status === "in_progress" ? "In Progress" : "Started"}</Badge> },
      ]} />
    </div>
  );
}
