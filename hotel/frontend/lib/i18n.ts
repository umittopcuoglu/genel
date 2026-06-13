// i18n language management
type Language = 'en' | 'tr';
type TranslationKey = string;

interface Translations {
  [key: string]: string | Translations;
}

let currentLanguage: Language = 'en';
let translations: { [key: string]: Translations } = {};

// Load translations
const loadTranslations = async () => {
  try {
    const en = await fetch('/locales/en/common.json').then(r => r.json());
    const tr = await fetch('/locales/tr/common.json').then(r => r.json());
    translations = { en, tr };
  } catch (error) {
    console.error('Failed to load translations:', error);
  }
};

// Initialize on first load
if (typeof window !== 'undefined') {
  loadTranslations();
  // Check localStorage for saved language preference
  const saved = localStorage.getItem('language') as Language;
  if (saved && ['en', 'tr'].includes(saved)) {
    currentLanguage = saved;
  } else {
    // Default to browser language if available
    const browserLang = navigator.language.split('-')[0];
    if (browserLang === 'tr') {
      currentLanguage = 'tr';
    }
  }
}

export const getLanguage = (): Language => currentLanguage;

export const setLanguage = (lang: Language) => {
  if (['en', 'tr'].includes(lang)) {
    currentLanguage = lang;
    if (typeof window !== 'undefined') {
      localStorage.setItem('language', lang);
    }
  }
};

// Nested key access: "nav.reservations" -> translations[lang]["nav"]["reservations"]
const getNestedValue = (obj: any, path: string): string => {
  return path.split('.').reduce((current, prop) => current?.[prop], obj) || path;
};

export const useTranslation = (lang?: Language) => {
  const language = lang || currentLanguage;
  const t = (key: TranslationKey): string => {
    const trans = translations[language] || translations['en'];
    return getNestedValue(trans, key);
  };
  return { t, language };
};

// Server-side helper (for layout, metadata, etc)
export const getTranslation = (lang: Language, key: TranslationKey): string => {
  const trans = translations[lang] || translations['en'];
  return getNestedValue(trans, key);
};
