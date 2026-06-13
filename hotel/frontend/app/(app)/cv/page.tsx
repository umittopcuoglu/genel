"use client";

import { useState } from "react";
import { useTranslation } from "@/lib/i18n";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/kpi/StatCard";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { AIPanel } from "@/components/ai/AIPanel";
import { SimpleTable } from "@/components/ui/SimpleTable";
import { MOCK_CV_INSPECTIONS, MOCK_CV_DEFECTS } from "@/lib/mock-faz34";

const INSP_TONE: Record<string, BadgeTone> = { completed: "info", review: "warning", passed: "success" };

export default function CvPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"inspections" | "defects">("inspections");

  return (
    <div className="space-y-6">
      <PageHeader title={t('cv.title')} subtitle={t('cv.subtitle')} />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label={t('cv.inspection')} value={String(MOCK_CV_INSPECTIONS.length)} />
        <StatCard label="Avg Score" value={`${Math.round(MOCK_CV_INSPECTIONS.reduce((s, i) => s + i.score, 0) / MOCK_CV_INSPECTIONS.length)}`} tone="success" />
        <StatCard label={t('cv.issues')} value={String(MOCK_CV_DEFECTS.length)} tone="warning" />
        <StatCard label="Verified" value={String(MOCK_CV_DEFECTS.filter((d) => d.verified).length)} />
      </div>

      <AIPanel
        agent="VisionAI"
        suggestion="Room 305 inspection score 76 — 3 defects detected (towel stain, missing minibar). Auto work order to housekeeping and re-inspection recommended."
        rationale="YOLOv8 object detection · confidence threshold 0.70"
      />

      <div className="border-b border-line" role="tablist">
        <div className="flex gap-1">
          {[["inspections", t('cv.inspection')], ["defects", t('cv.issues')]].map(([id, label]) => (
            <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id as any)}
              className={`rounded-t-md px-4 py-2 text-sm font-medium ${tab === id ? "border-b-2 border-primary text-primary" : "text-text-2 hover:text-text-1"}`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === "inspections" ? (
        <SimpleTable rows={MOCK_CV_INSPECTIONS} columns={[
          { key: "room", header: t('cv.room') },
          { key: "model", header: "Model" },
          { key: "score", header: "Score", align: "right", render: (i) => <span className={i.score >= 90 ? "text-success" : i.score >= 80 ? "" : "text-warning"}>{i.score}</span> },
          { key: "defects", header: t('cv.issues'), align: "right" },
          { key: "status", header: t('common.status'), render: (i) => <Badge tone={INSP_TONE[i.status]}>{i.status === "completed" ? "Completed" : i.status === "review" ? "Review" : "Passed"}</Badge> },
        ]} />
      ) : (
        <SimpleTable rows={MOCK_CV_DEFECTS} columns={[
          { key: "room", header: t('cv.room') },
          { key: "type", header: "Defect" },
          { key: "confidence", header: "Confidence", align: "right", render: (d) => `%${Math.round(d.confidence * 100)}` },
          { key: "verified", header: "Verification", render: (d) => (d.verified ? <Badge tone="success">Verified</Badge> : <Badge tone="warning">Pending</Badge>) },
        ]} />
      )}
    </div>
  );
}
