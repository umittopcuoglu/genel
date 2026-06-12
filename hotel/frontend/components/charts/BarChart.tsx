/**
 * Bağımlılıksız dikey bar grafik (saf div + tailwind). Analitik ekranında
 * doluluk/gelir trendleri için kullanılır — ek kütüphane gerektirmez.
 */
export interface BarDatum {
  label: string;
  value: number;
  /** opsiyonel ikinci seri (örn. geçen yıl) */
  secondary?: number;
}

export function BarChart({
  data,
  height = 180,
  format = (v) => String(v),
  primaryLabel = "Bu dönem",
  secondaryLabel,
}: {
  data: BarDatum[];
  height?: number;
  format?: (v: number) => string;
  primaryLabel?: string;
  secondaryLabel?: string;
}) {
  const max = Math.max(1, ...data.flatMap((d) => [d.value, d.secondary ?? 0]));

  return (
    <div>
      <div className="flex gap-2" style={{ height }}>
        {data.map((d) => (
          <div key={d.label} className="flex h-full flex-1 flex-col items-center justify-end gap-1">
            <div className="flex w-full flex-1 items-end justify-center gap-1">
              {d.secondary !== undefined && (
                <div
                  className="w-3 rounded-t bg-line"
                  style={{ height: `${Math.max(2, (d.secondary / max) * 100)}%` }}
                  title={`${secondaryLabel ?? "Önceki"}: ${format(d.secondary)}`}
                />
              )}
              <div
                className="w-4 rounded-t bg-primary transition-all"
                style={{ height: `${Math.max(2, (d.value / max) * 100)}%` }}
                title={`${primaryLabel}: ${format(d.value)}`}
              />
            </div>
            <span className="text-[10px] text-text-2">{d.label}</span>
          </div>
        ))}
      </div>
      <div className="mt-3 flex items-center gap-4 text-xs text-text-2">
        <span className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-sm bg-primary" /> {primaryLabel}
        </span>
        {secondaryLabel && (
          <span className="flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-sm bg-line" /> {secondaryLabel}
          </span>
        )}
      </div>
    </div>
  );
}
