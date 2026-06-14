"use client";

import { useTranslation } from "@/lib/i18n";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { useApiData } from "@/lib/useApiData";
import { MockBanner } from "@/components/ui/DataStates";
import { MOCK_CHECKIN_SESSIONS } from "@/lib/mock-faz34";

const STEP_TONE = (v: string): BadgeTone =>
  v === "passed" || v === "matched" || v === "submitted" || v === "issued" || v === "completed"
    ? "success"
    : v === "pending" || v === "in_progress" || v === "started"
    ? "warning"
    : "neutral";

const stepBadge = (v: string) => (v === "—" ? <span className="text-text-2">—</span> : <Badge tone={STEP_TONE(v)}>{v}</Badge>);

// Backend (mobile_checkin.CheckinSessionResponse) → ekran satır şekli normalizasyonu.
// Session yanıtı yalnızca reservation_id/guest_id/status içerir; adım alanları yoktur → "—".
type CheckinRow = { id: string; guest: string; room: string; ocr: string; face: string; egm: string; nfc: string; status: string };

function normalizeSessions(raw: any[]): CheckinRow[] {
  return raw.map((s) => ({
    id: String(s.id),
    guest: String(s.guest_id ?? "—"),
    room: "—",
    ocr: "—",
    face: "—",
    egm: "—",
    nfc: "—",
    status: s.status,
  }));
}

export default function MobileCheckinPage() {
  const { t } = useTranslation();

  const { data: sessionsRaw, usingFallback } = useApiData<any[]>({
    path: "/api/v1/mobile/checkin/sessions",
    fallback: MOCK_CHECKIN_SESSIONS,
  });

  const sessions = usingFallback ? MOCK_CHECKIN_SESSIONS : normalizeSessions(sessionsRaw);
  const completed = sessions.filter((s) => s.status === "completed").length;

  return (
    <div className="space-y-6">
      <PageHeader title={t('mobileCheckin.title')} subtitle={t('mobileCheckin.subtitle')} />

      {usingFallback && <MockBanner />}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Sessions" value={String(sessions.length)} />
        <StatCard label={t('mobileCheckin.completed')} value={String(completed)} tone="success" />
        <StatCard label="In Progress" value={String(sessions.filter((s) => s.status !== "completed").length)} tone="warning" />
        <StatCard label={t('mobileCheckin.egmNotification')} value={String(sessions.filter((s) => s.egm === "submitted").length)} />
      </div>

      <SimpleTable rows={sessions} columns={[
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
