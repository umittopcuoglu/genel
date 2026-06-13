type Language = 'en' | 'tr';
type TranslationKey = string;

interface Translations {
  [key: string]: string | Translations;
}

const EMBEDDED_TRANSLATIONS: Record<Language, Translations> = {
  en: {},
  tr: {},
};

let currentLanguage: Language = 'tr';
let languageResolved = false;
let translations: Record<Language, Translations> = EMBEDDED_TRANSLATIONS;
let translationsLoaded = false;
const listeners: Set<() => void> = new Set();

export const loadTranslations = async (): Promise<void> => {
  if (translationsLoaded) return;
  try {
    const [en, tr] = await Promise.all([
      fetch('/locales/en/common.json').then(r => r.json()),
      fetch('/locales/tr/common.json').then(r => r.json()),
    ]);
    translations = { en, tr };
    translationsLoaded = true;
    listeners.forEach(l => l());
  } catch (error) {
    console.error('Failed to load translations:', error);
  }
};

function resolveLanguage(): Language {
  if (languageResolved) return currentLanguage;
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('language') as Language;
    if (saved && ['en', 'tr'].includes(saved)) {
      currentLanguage = saved;
    } else {
      const browserLang = navigator.language.split('-')[0];
      if (browserLang === 'en') {
        currentLanguage = 'en';
      }
    }
    languageResolved = true;
  }
  return currentLanguage;
}

export const getLanguage = (): Language => resolveLanguage();

export const setLanguage = (lang: Language) => {
  if (['en', 'tr'].includes(lang)) {
    currentLanguage = lang;
    languageResolved = true;
    if (typeof window !== 'undefined') {
      localStorage.setItem('language', lang);
    }
    listeners.forEach(l => l());
  }
};

export const subscribe = (listener: () => void): (() => void) => {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
};

const getNestedValue = (obj: any, path: string): any => {
  return path.split('.').reduce((current, prop) => current?.[prop], obj);
};

export const translate = (key: TranslationKey, params?: Record<string, string | number>): string => {
  const trans = translations[currentLanguage] || translations.en;
  const value = getNestedValue(trans, key);
  if (typeof value !== 'string') {
    const fallback = getNestedValue(translations.en, key);
    if (typeof fallback === 'string') return interpolate(fallback, params);
    return key;
  }
  return interpolate(value, params);
};

const interpolate = (template: string, params?: Record<string, string | number>): string => {
  if (!params) return template;
  return template.replace(/\{(\w+)\}/g, (_, key) => String(params[key] ?? `{${key}}`));
};

import { useState, useEffect, useCallback } from 'react';

export const useTranslation = () => {
  const [mounted, setMounted] = useState(false);
  const [, forceUpdate] = useState(0);

  useEffect(() => {
    resolveLanguage();
    loadTranslations();
    setMounted(true);
    const unsubscribe = subscribe(() => forceUpdate(v => v + 1));
    return unsubscribe;
  }, []);

  const t = useCallback((key: TranslationKey, params?: Record<string, string | number>): string => {
    return translate(key, params);
  }, []);

  return {
    t,
    language: mounted ? currentLanguage : ('tr' as Language),
    setLanguage,
  };
};

export const getTranslation = (lang: Language, key: TranslationKey): string => {
  const trans = translations[lang] || translations.en;
  const value = getNestedValue(trans, key);
  return typeof value === 'string' ? value : key;
};
