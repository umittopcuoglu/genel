'use client';

import { Globe } from 'lucide-react';
import { useI18n } from '@/components/providers/I18nProvider';

export function LanguageSwitcher() {
  const { language, setLanguage } = useI18n();

  return (
    <div className="flex items-center gap-2">
      <Globe className="h-4 w-4 text-text-2" aria-hidden />
      <select
        value={language}
        onChange={(e) => setLanguage(e.target.value as 'en' | 'tr')}
        className="rounded-md border border-line bg-surface px-2 py-1 text-sm outline-none focus:border-accent/60"
        aria-label="Dil seçimi"
      >
        <option value="tr">Türkçe</option>
        <option value="en">English</option>
      </select>
    </div>
  );
}
