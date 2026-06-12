"use client";

import { useEffect, useRef, useState } from "react";

/**
 * KPI kartı — animasyonlu sayaç: sayısal kısım 0'dan hedefe ease-out ile sayar.
 * Hover'da altın kenarlık + yumuşak yükselme (card-lux).
 */
export function StatCard({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "default" | "success" | "warning" | "danger";
}) {
  const toneClass = {
    default: "text-text-1",
    success: "text-success",
    warning: "text-warning",
    danger: "text-danger",
  }[tone];

  const toneBar = {
    default: "from-accent/70",
    success: "from-success/70",
    warning: "from-warning/70",
    danger: "from-danger/70",
  }[tone];

  return (
    <div className="card-lux group relative overflow-hidden p-5">
      <div
        className={`absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r ${toneBar} to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100`}
      />
      <div className="text-[13px] font-medium text-text-2">{label}</div>
      <div className={`tabular mt-1.5 font-display text-[28px] font-semibold leading-none ${toneClass}`}>
        <AnimatedValue value={value} />
      </div>
      {hint && <div className="mt-2 text-xs text-text-2">{hint}</div>}
    </div>
  );
}

/** "%82", "₺145.200", "12/45" gibi metinlerdeki sayıları ease-out ile animasyonlu sayar. */
function AnimatedValue({ value }: { value: string }) {
  const [display, setDisplay] = useState(value);
  const raf = useRef<number>();

  useEffect(() => {
    const matches = Array.from(value.matchAll(/\d[\d.,]*/g));
    if (matches.length === 0) {
      setDisplay(value);
      return;
    }
    const start = performance.now();
    const DURATION = 900;

    function frame(now: number) {
      const t = Math.min((now - start) / DURATION, 1);
      const ease = 1 - Math.pow(1 - t, 3);
      let out = "";
      let last = 0;
      for (const m of matches) {
        out += value.slice(last, m.index);
        const raw = m[0];
        const numeric = parseFloat(raw.replace(/\./g, "").replace(",", "."));
        if (isNaN(numeric)) {
          out += raw;
        } else {
          const current = numeric * ease;
          // Orijinal biçimi koru: binlik ayraçlı tam sayı olarak yaz
          const isInt = !raw.includes(",");
          out += isInt
            ? Math.round(current).toLocaleString("tr-TR")
            : current.toLocaleString("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }
        last = (m.index ?? 0) + raw.length;
      }
      out += value.slice(last);
      setDisplay(out);
      if (t < 1) raf.current = requestAnimationFrame(frame);
    }
    raf.current = requestAnimationFrame(frame);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
  }, [value]);

  return <span>{display}</span>;
}
