'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { getLanguage, setLanguage as setLangLib, subscribe, loadTranslations } from '@/lib/i18n';

type Language = 'en' | 'tr';

interface I18nContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLang] = useState<Language>('tr');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Ensure translations are loaded
    loadTranslations();

    // Get current language from lib (which checks localStorage)
    setLang(getLanguage());
    setMounted(true);

    // Subscribe to language changes for re-renders
    const unsubscribe = subscribe(() => {
      setLang(getLanguage());
    });
    return unsubscribe;
  }, []);

  const handleSetLanguage = (lang: Language) => {
    setLangLib(lang);
    setLang(lang);
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
    // Allow usage outside provider for non-critical UI
    return { language: 'tr' as Language, setLanguage: () => {} };
  }
  return context;
};
