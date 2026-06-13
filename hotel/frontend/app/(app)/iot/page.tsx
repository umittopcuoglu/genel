"use client";

import { useState } from "react";
import { useTranslation } from "@/lib/i18n";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge } from "@/components/ui/Badge";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { MOCK_IOT_DEVICES, MOCK_IOT_SCENES } from "@/lib/mock-faz34";

export default function IotPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"devices" | "scenes">("devices");
  const online = MOCK_IOT_DEVICES.filter((d) => d.online).length;

  return (
    <div className="space-y-6">
      <PageHeader title={t('iot.title')} subtitle={t('iot.subtitle')} />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label={t('iot.devices')} value={String(MOCK_IOT_DEVICES.length)} />
        <StatCard label={t('iot.online')} value={`${online}/${MOCK_IOT_DEVICES.length}`} tone="success" />
        <StatCard label={t('iot.offline')} value={String(MOCK_IOT_DEVICES.length - online)} tone={online < MOCK_IOT_DEVICES.length ? "warning" : "default"} />
        <StatCard label="Active Scenes" value={String(MOCK_IOT_SCENES.filter((s) => s.active).length)} />
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
        <SimpleTable rows={MOCK_IOT_DEVICES} columns={[
          { key: "room", header: t('iot.rooms') },
          { key: "type", header: t('common.status') },
          { key: "vendor", header: "Vendor" },
          { key: "state", header: t('iot.status') },
          { key: "online", header: "Connection", render: (d) => <Badge tone={d.online ? "success" : "danger"}>{d.online ? t('iot.online') : t('iot.offline')}</Badge> },
        ]} />
      ) : (
        <SimpleTable rows={MOCK_IOT_SCENES} columns={[
          { key: "name", header: t('iot.scenes') },
          { key: "trigger", header: "Trigger" },
          { key: "actions", header: "Actions", align: "right", render: (s) => `${s.actions} devices` },
          { key: "active", header: t('iot.status'), render: (s) => <Badge tone={s.active ? "success" : "neutral"}>{s.active ? "Active" : "Inactive"}</Badge> },
        ]} />
      )}
    </div>
  );
}
