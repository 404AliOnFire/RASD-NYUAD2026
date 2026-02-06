import { useCallback, useEffect, useState } from "react";
import { Language, t as translate } from "./translations";

const STORAGE_KEY = "rasd_lang";

export function useLanguage() {
  // Default to Arabic
  const [lang, setLang] = useState<Language>(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as Language | null;
    return stored ?? "ar";
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, lang);
    document.documentElement.setAttribute("dir", lang === "ar" ? "rtl" : "ltr");
    document.documentElement.setAttribute("lang", lang);
  }, [lang]);

  const toggleLang = useCallback(() => {
    setLang((prev) => (prev === "ar" ? "en" : "ar"));
  }, []);

  return {
    lang,
    dir: lang === "ar" ? "rtl" : "ltr",
    fontClass: lang === "ar" ? "font-arabic" : "font-sans",
    t: (key: Parameters<typeof translate>[0]) => translate(key, lang),
    toggleLang
  };
}
