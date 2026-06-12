"use client";

import { useState } from "react";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { AIPanel } from "@/components/ai/AIPanel";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { MOCK_CV_INSPECTIONS, MOCK_CV_DEFECTS } from "@/lib/mock-faz34";

const INSP_TONE: Record<string, BadgeTone> = { completed: "info", review: "warning", passed: "success" };

export default function CvPage() {
  const [tab, setTab] = useState<"inspections" | "defects">("inspections");

  return (
    <div className="space-y-6">
      <PageHeader title="Görüntü Denetimi (Computer Vision)" subtitle="Oda kalite kontrolü · kusur tespiti (YOLOv8 mock)" />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Denetim" value={String(MOCK_CV_INSPECTIONS.length)} />
        <StatCard label="Ort. Skor" value={`${Math.round(MOCK_CV_INSPECTIONS.reduce((s, i) => s + i.score, 0) / MOCK_CV_INSPECTIONS.length)}`} tone="success" />
        <StatCard label="Tespit Kusur" value={String(MOCK_CV_DEFECTS.length)} tone="warning" />
        <StatCard label="Doğrulanan" value={String(MOCK_CV_DEFECTS.filter((d) => d.verified).length)} />
      </div>

      <AIPanel
        agent="VisionAI"
        suggestion="Oda 305 denetim skoru 76 — 3 kusur (havlu lekesi, eksik minibar) tespit edildi. Housekeeping'e otomatik iş emri ve yeniden denetim önerilir."
        rationale="YOLOv8 nesne tespiti · güven eşiği 0.70"
      />

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          {[["inspections", "Denetimler"], ["defects", "Kusurlar"]].map(([id, label]) => (
            <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id as any)}
              className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === id ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === "inspections" ? (
        <SimpleTable rows={MOCK_CV_INSPECTIONS} columns={[
          { key: "room", header: "Oda" },
          { key: "model", header: "Model" },
          { key: "score", header: "Skor", align: "right", render: (i) => <span className={i.score >= 90 ? "text-success" : i.score >= 80 ? "" : "text-warning"}>{i.score}</span> },
          { key: "defects", header: "Kusur", align: "right" },
          { key: "status", header: "Durum", render: (i) => <Badge tone={INSP_TONE[i.status]}>{i.status === "completed" ? "Tamamlandı" : i.status === "review" ? "İnceleme" : "Geçti"}</Badge> },
        ]} />
      ) : (
        <SimpleTable rows={MOCK_CV_DEFECTS} columns={[
          { key: "room", header: "Oda" },
          { key: "type", header: "Kusur" },
          { key: "confidence", header: "Güven", align: "right", render: (d) => `%${Math.round(d.confidence * 100)}` },
          { key: "verified", header: "Doğrulama", render: (d) => (d.verified ? <Badge tone="success">Doğrulandı</Badge> : <Badge tone="warning">Bekliyor</Badge>) },
        ]} />
      )}
    </div>
  );
}
