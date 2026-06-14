"use client";

import { useEffect, useState, useRef } from "react";
import { Moon, Sun, Palette, Check } from "lucide-react";

const THEMES = [
  { id: "grand", label: "Grand", desc: "Navy & gold luks" },
  { id: "modern", label: "Modern", desc: "Cool blue, minimal" },
  { id: "sade", label: "Sade", desc: "Notr, sicak tonlar" },
  { id: "neon", label: "Neon", desc: "Canli, parlak aksanlar" },
] as const;

type ThemeId = (typeof THEMES)[number]["id"];

function applyTheme(themeId: ThemeId, dark: boolean) {
  const el = document.documentElement;
  el.setAttribute("data-theme", themeId);
  el.classList.toggle("dark", dark);
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<ThemeId>("grand");
  const [dark, setDark] = useState(false);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const storedTheme = (localStorage.getItem("hotelops-theme") || "grand") as ThemeId;
    const storedMode = localStorage.getItem("theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const isDark = storedMode ? storedMode === "dark" : prefersDark;

    setTheme(storedTheme);
    setDark(isDark);
    applyTheme(storedTheme, isDark);
  }, []);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function selectTheme(id: ThemeId) {
    setTheme(id);
    localStorage.setItem("hotelops-theme", id);
    applyTheme(id, dark);
  }

  function toggleDark() {
    const next = !dark;
    setDark(next);
    localStorage.setItem("theme", next ? "dark" : "light");
    applyTheme(theme, next);
  }

  return (
    <div ref={ref} className="relative flex items-center gap-1">
      <button
        onClick={toggleDark}
        aria-label={dark ? "Acik temaya gec" : "Koyu temaya gec"}
        className="rounded-md p-2 text-text-2 hover:bg-bg hover:text-text-1 focus:outline-none focus:ring-2 focus:ring-primary"
      >
        {dark ? <Sun className="h-4 w-4" aria-hidden /> : <Moon className="h-4 w-4" aria-hidden />}
      </button>

      <button
        onClick={() => setOpen(!open)}
        aria-label="Tema sec"
        aria-expanded={open}
        className="rounded-md p-2 text-text-2 hover:bg-bg hover:text-text-1 focus:outline-none focus:ring-2 focus:ring-primary"
      >
        <Palette className="h-4 w-4" aria-hidden />
      </button>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-2 w-52 rounded-xl border border-line bg-surface p-1.5 shadow-lg">
          {THEMES.map((t) => (
            <button
              key={t.id}
              onClick={() => {
                selectTheme(t.id);
                setOpen(false);
              }}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors hover:bg-bg"
            >
              <ThemeSwatch themeId={t.id} />
              <div className="flex-1">
                <div className="font-medium text-text-1">{t.label}</div>
                <div className="text-xs text-text-2">{t.desc}</div>
              </div>
              {theme === t.id && <Check className="h-4 w-4 text-accent" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function ThemeSwatch({ themeId }: { themeId: string }) {
  const colors: Record<string, [string, string]> = {
    grand: ["#17335C", "#C0984A"],
    modern: ["#3B82F6", "#6366F1"],
    sade: ["#57534E", "#A88E65"],
    neon: ["#8B5CF6", "#EC4899"],
  };
  const [c1, c2] = colors[themeId] || ["#888", "#aaa"];
  return (
    <div className="flex h-6 w-6 shrink-0 overflow-hidden rounded-full border border-line">
      <div className="h-full w-1/2" style={{ background: c1 }} />
      <div className="h-full w-1/2" style={{ background: c2 }} />
    </div>
  );
}
