'use client';
// Side-effect-only component: keeps <html lang> in sync with the active UI
// language (a11y + correct Ethiopic font shaping). Renders nothing.
import { useLanguage } from './useLanguage';

export default function LanguageSyncer() {
  useLanguage();
  return null;
}
