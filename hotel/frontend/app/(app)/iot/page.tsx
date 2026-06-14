"use client";

import { useState } from "react";
import { useTranslation } from "@/lib/i18n";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge } from "@/components/ui/Badge";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { useApiData } from "@/lib/useApiData";
import { MockBanner } from "@/components/ui/DataStates";
import { MOCK_IOT_DEVICES, MOCK_IOT_SCENES } from "@/lib/mock-faz34";

// Backend → ekran satır şekli normalizasyonu.
function normalizeDevices(raw: any[]) {
  return raw.map((d) => ({
    id: String(d.id),
    room: String(d.room_id ?? d.room ?? "—"),
    type: d.device_type ?? d.type ?? "—",
    vendor: d.vendor ?? "—",
    online: (d.status ?? d.online) === "online" || d.online === true,
    state: typeof d.state === "object" && d.state !== null
      ? (Object.keys(d.state).length ? Object.entries(d.state).map(([k, v]) => `${k}: ${v}`).join(", ").slice(0, 40) : "—")
      : (d.state ?? "—"),
  }));
}

function normalizeScenes(raw: any[]) {
  return raw.map((s) => ({
    id: String(s.id),
    name: s.name,
    trigger: s.trigger_type ?? s.trigger ?? "—",
    actions: Array.isArray(s.actions) ? s.actions.length : Number(s.actions ?? 0),
    active: s.is_active ?? s.active ?? false,
  }));
}

export default function IotPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"devices" | "scenes">("devices");

  const { data: devicesRaw, usingFallback: devicesFallback } = useApiData<any[]>({
    path: "/api/v1/iot/devices",
    fallback: MOCK_IOT_DEVICES,
  });
  const { data: scenesRaw, usingFallback: scenesFallback } = useApiData<any[]>({
    path: "/api/v1/iot/scenarios",
    fallback: MOCK_IOT_SCENES,
  });

  const devices = devicesFallback ? MOCK_IOT_DEVICES : normalizeDevices(devicesRaw);
  const scenes = scenesFallback ? MOCK_IOT_SCENES : normalizeScenes(scenesRaw);
  const usingFallback = devicesFallback || scenesFallback;

  const online = devices.filter((d) => d.online).length;

  return (
    <div className="space-y-6">
      <PageHeader title={t('iot.title')} subtitle={t('iot.subtitle')} />

      {usingFallback && <MockBanner />}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label={t('iot.devices')} value={String(devices.length)} />
        <StatCard label={t('iot.online')} value={`${online}/${devices.length}`} tone="success" />
        <StatCard label={t('iot.offline')} value={String(devices.length - online)} tone={online < devices.length ? "warning" : "default"} />
        <StatCard label="Active Scenes" value={String(scenes.filter((s) => s.active).length)} />
      </div>

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          {[["devices", t('iot.devices')], ["scenes", t('iot.scenes')]].map(([id, label]) => (
            <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id as any)}
              className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === id ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === "devices" ? (
        <SimpleTable rows={devices} columns={[
          { key: "room", header: t('iot.rooms') },
          { key: "type", header: t('common.status') },
          { key: "vendor", header: "Vendor" },
          { key: "state", header: t('iot.status') },
          { key: "online", header: "Connection", render: (d) => <Badge tone={d.online ? "success" : "danger"}>{d.online ? t('iot.online') : t('iot.offline')}</Badge> },
        ]} />
      ) : (
        <SimpleTable rows={scenes} columns={[
          { key: "name", header: t('iot.scenes') },
          { key: "trigger", header: "Trigger" },
          { key: "actions", header: "Actions", align: "right", render: (s) => `${s.actions} devices` },
          { key: "active", header: t('iot.status'), render: (s) => <Badge tone={s.active ? "success" : "neutral"}>{s.active ? "Active" : "Inactive"}</Badge> },
        ]} />
      )}
    </div>
  );
}
