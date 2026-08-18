import es from "../../lang/es.json";
import en from "../../lang/en.json";

type Translations = typeof es;
type TranslationKey = keyof Translations;

const locales: Record<string, Translations> = { es, en };

let _currentLanguage = $state<string>("es");

export function currentLanguage(): string {
  return _currentLanguage;
}

export function setLanguage(lang: string): void {
  if (lang in locales) {
    _currentLanguage = lang;
  }
}

export function t(
  key: string,
  params?: Record<string, string | number>,
): string {
  const translations = locales[_currentLanguage] ?? locales.es;
  const value =
    translations[key as TranslationKey] ?? locales.es[key as TranslationKey] ?? key;

  if (!params) return value;

  return Object.entries(params).reduce<string>(
    (result, [paramKey, paramValue]) =>
      result.replace(new RegExp(`\\{${paramKey}\\}`, "g"), String(paramValue)),
    value,
  );
}
