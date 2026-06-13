// i18n language management - client-side
type Language = 'en' | 'tr';
type TranslationKey = string;

interface Translations {
  [key: string]: string | Translations;
}

// Embedded translations (preloaded to avoid async loading flicker)
// These get hydrated synchronously
const EMBEDDED_TRANSLATIONS: Record<Language, Translations> = {
  en: {},
  tr: {},
};

let currentLanguage: Language = 'tr'; // Default Turkish
let translations: Record<Language, Translations> = EMBEDDED_TRANSLATIONS;
let translationsLoaded = false;
const listeners: Set<() => void> = new Set();

// Load translations dynamically
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

// Initialize on first load
if (typeof window !== 'undefined') {
  // Check localStorage for saved language preference
  const saved = localStorage.getItem('language') as Language;
  if (saved && ['en', 'tr'].includes(saved)) {
    currentLanguage = saved;
  } else {
    // Default to browser language if available
    const browserLang = navigator.language.split('-')[0];
    if (browserLang === 'en') {
      currentLanguage = 'en';
    }
  }
  // Load translations immediately
  loadTranslations();
}

export const getLanguage = (): Language => currentLanguage;

export const setLanguage = (lang: Language) => {
  if (['en', 'tr'].includes(lang)) {
    currentLanguage = lang;
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

// Nested key access: "nav.reservations" -> translations[lang]["nav"]["reservations"]
const getNestedValue = (obj: any, path: string): any => {
  return path.split('.').reduce((current, prop) => current?.[prop], obj);
};

// Translate with parameter interpolation: t("hello", { name: "John" }) → "Hello, John"
export const translate = (key: TranslationKey, params?: Record<string, string | number>): string => {
  const trans = translations[currentLanguage] || translations.en;
  const value = getNestedValue(trans, key);
  if (typeof value !== 'string') {
    // Fallback to English
    const fallback = getNestedValue(translations.en, key);
    if (typeof fallback === 'string') return interpolate(fallback, params);
    return key; // Return key if no translation found
  }
  return interpolate(value, params);
};

const interpolate = (template: string, params?: Record<string, string | number>): string => {
  if (!params) return template;
  return template.replace(/\{(\w+)\}/g, (_, key) => String(params[key] ?? `{${key}}`));
};

// React hook
import { useState, useEffect, useCallback } from 'react';

export const useTranslation = () => {
  const [, forceUpdate] = useState(0);

  useEffect(() => {
    const unsubscribe = subscribe(() => forceUpdate(v => v + 1));
    return unsubscribe;
  }, []);

  const t = useCallback((key: TranslationKey, params?: Record<string, string | number>): string => {
    return translate(key, params);
  }, []);

  return { t, language: currentLanguage, setLanguage };
};

// Server-side helper
export const getTranslation = (lang: Language, key: TranslationKey): string => {
  const trans = translations[lang] || translations.en;
  const value = getNestedValue(trans, key);
  return typeof value === 'string' ? value : key;
};
