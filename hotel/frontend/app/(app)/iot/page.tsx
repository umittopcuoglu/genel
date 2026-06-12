"use client";

import { useState } from "react";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge } from "@/components/ui/Badge";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { MOCK_IOT_DEVICES, MOCK_IOT_SCENES } from "@/lib/mock-faz34";

export default function IotPage() {
  const [tab, setTab] = useState<"devices" | "scenes">("devices");
  const online = MOCK_IOT_DEVICES.filter((d) => d.online).length;

  return (
    <div className="space-y-6">
      <PageHeader title="IoT / Akıllı Oda" subtitle="Nest · KNX · Philips Hue (mock-first)" />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Cihaz" value={String(MOCK_IOT_DEVICES.length)} />
        <StatCard label="Çevrimiçi" value={`${online}/${MOCK_IOT_DEVICES.length}`} tone="success" />
        <StatCard label="Çevrimdışı" value={String(MOCK_IOT_DEVICES.length - online)} tone={online < MOCK_IOT_DEVICES.length ? "warning" : "default"} />
        <StatCard label="Aktif Sahne" value={String(MOCK_IOT_SCENES.filter((s) => s.active).length)} />
      </div>

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          {[["devices", "Cihazlar"], ["scenes", "Sahneler"]].map(([id, label]) => (
            <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id as any)}
              className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === id ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === "devices" ? (
        <SimpleTable rows={MOCK_IOT_DEVICES} columns={[
          { key: "room", header: "Oda" },
          { key: "type", header: "Tür" },
          { key: "vendor", header: "Üretici" },
          { key: "state", header: "Durum" },
          { key: "online", header: "Bağlantı", render: (d) => <Badge tone={d.online ? "success" : "danger"}>{d.online ? "Çevrimiçi" : "Çevrimdışı"}</Badge> },
        ]} />
      ) : (
        <SimpleTable rows={MOCK_IOT_SCENES} columns={[
          { key: "name", header: "Sahne" },
          { key: "trigger", header: "Tetikleyici" },
          { key: "actions", header: "Aksiyon", align: "right", render: (s) => `${s.actions} cihaz` },
          { key: "active", header: "Durum", render: (s) => <Badge tone={s.active ? "success" : "neutral"}>{s.active ? "Aktif" : "Pasif"}</Badge> },
        ]} />
      )}
    </div>
  );
}
