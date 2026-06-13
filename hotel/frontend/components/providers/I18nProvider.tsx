'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { getLanguage, setLanguage } from '@/lib/i18n';

type Language = 'en' | 'tr';

interface I18nContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLang] = useState<Language>('en');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Get language from lib (which checks localStorage)
    const savedLang = getLanguage();
    setLang(savedLang);
    setMounted(true);
  }, []);

  const handleSetLanguage = (lang: Language) => {
    setLang(lang);
    setLanguage(lang);
  };

  if (!mounted) {
    return <>{children}</>;
  }

  return (
    <I18nContext.Provider value={{ language, setLanguage: handleSetLanguage }}>
      {children}
    </I18nContext.Provider>
  );
};

export const useI18n = () => {
  const context = useContext(I18nContext);
  if (context === undefined) {
    throw new Error('useI18n must be used within I18nProvider');
  }
  return context;
};
