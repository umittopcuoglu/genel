"use client";

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
  const completed = MOCK_CHECKIN_SESSIONS.filter((s) => s.status === "completed").length;

  return (
    <div className="space-y-6">
      <PageHeader title="Mobil Check-in" subtitle="Pasaport OCR · yüz tanıma · EGM bildirimi · NFC oda anahtarı (mock)" />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Oturum" value={String(MOCK_CHECKIN_SESSIONS.length)} />
        <StatCard label="Tamamlanan" value={String(completed)} tone="success" />
        <StatCard label="Devam Eden" value={String(MOCK_CHECKIN_SESSIONS.filter((s) => s.status !== "completed").length)} tone="warning" />
        <StatCard label="EGM Bildirimi" value={String(MOCK_CHECKIN_SESSIONS.filter((s) => s.egm === "submitted").length)} />
      </div>

      <SimpleTable rows={MOCK_CHECKIN_SESSIONS} columns={[
        { key: "guest", header: "Misafir" },
        { key: "room", header: "Oda" },
        { key: "ocr", header: "OCR", render: (s) => stepBadge(s.ocr) },
        { key: "face", header: "Yüz", render: (s) => stepBadge(s.face) },
        { key: "egm", header: "EGM", render: (s) => stepBadge(s.egm) },
        { key: "nfc", header: "NFC Anahtar", render: (s) => stepBadge(s.nfc) },
        { key: "status", header: "Durum", render: (s) => <Badge tone={s.status === "completed" ? "success" : "info"}>{s.status === "completed" ? "Tamamlandı" : s.status === "in_progress" ? "Devam ediyor" : "Başladı"}</Badge> },
      ]} />
    </div>
  );
}
