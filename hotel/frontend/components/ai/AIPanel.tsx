"use client";

import { Sparkles, X } from "lucide-react";

/**
 * Standart AI öneri paneli — docs/03 §5.
 * Kural: AI asla otomatik uygulamaz; her zaman Düzenle / Kullan / Reddet.
 */
export function AIPanel({
  agent,
  suggestion,
  rationale,
  onAccept,
  onEdit,
  onReject,
  onClose,
}: {
  agent: string;
  suggestion: string;
  rationale?: string;
  onAccept?: () => void;
  onEdit?: () => void;
  onReject?: () => void;
  onClose?: () => void;
}) {
  return (
    <section
      aria-label={`${agent} önerisi`}
      className="card-lux relative overflow-hidden p-5"
    >
      <div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-accent via-accent/40 to-transparent" />
      <div className="mb-2.5 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/15">
            <Sparkles className="h-4 w-4 text-accent" aria-hidden />
          </span>
          {agent} önerisi
        </div>
        {onClose && (
          <button
            onClick={onClose}
            aria-label="Kapat"
            className="rounded p-1 text-text-2 hover:bg-bg focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <X className="h-4 w-4" aria-hidden />
          </button>
        )}
      </div>
      <p className="text-sm">{suggestion}</p>
      {rationale && (
        <p className="mt-2 border-t border-line pt-2 text-xs text-text-2">
          Gerekçe: {rationale}
        </p>
      )}
      <div className="mt-4 flex gap-2">
        <button
          onClick={onEdit}
          className="btn-navy !px-3 !py-1.5 focus:outline-none focus:ring-2 focus:ring-primary"
        >
          Düzenle
        </button>
        <button
          onClick={onAccept}
          className="btn-gold !px-4 !py-1.5 focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2"
        >
          Kullan
        </button>
        <button
          onClick={onReject}
          className="rounded-xl border border-line px-3 py-1.5 text-sm font-medium text-danger transition-colors duration-200 hover:border-danger/40 hover:bg-danger/[0.06] focus:outline-none focus:ring-2 focus:ring-danger"
        >
          Reddet
        </button>
      </div>
    </section>
  );
}
