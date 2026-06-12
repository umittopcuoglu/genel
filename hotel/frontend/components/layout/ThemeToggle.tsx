"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

/** Açık/koyu tema anahtarı — tercih localStorage'da saklanır (docs/03 §1.2). */
export function ThemeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("theme");
    const prefers = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const isDark = stored ? stored === "dark" : prefers;
    setDark(isDark);
    document.documentElement.classList.toggle("dark", isDark);
  }, []);

  function toggle() {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("theme", next ? "dark" : "light");
  }

  return (
    <button
      onClick={toggle}
      aria-label={dark ? "Açık temaya geç" : "Koyu temaya geç"}
      className="rounded-md p-2 text-text-2 hover:bg-bg hover:text-text-1 focus:outline-none focus:ring-2 focus:ring-primary"
    >
      {dark ? <Sun className="h-4 w-4" aria-hidden /> : <Moon className="h-4 w-4" aria-hidden />}
    </button>
  );
}
