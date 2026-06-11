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
      className="rounded-xl border border-line bg-surface p-4"
    >
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-medium">
          <Sparkles className="h-4 w-4 text-primary" aria-hidden />
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
      <div className="mt-3 flex gap-2">
        <button
          onClick={onEdit}
          className="rounded-md border border-line px-3 py-1.5 text-sm hover:bg-bg focus:outline-none focus:ring-2 focus:ring-primary"
        >
          Düzenle
        </button>
        <button
          onClick={onAccept}
          className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
        >
          Kullan
        </button>
        <button
          onClick={onReject}
          className="rounded-md border border-line px-3 py-1.5 text-sm text-danger hover:bg-bg focus:outline-none focus:ring-2 focus:ring-danger"
        >
          Reddet
        </button>
      </div>
    </section>
  );
}
