import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import { I18nProvider } from "@/lib/i18n";
import LanguageSyncer from "@/i18n/LanguageSyncer";

export const metadata: Metadata = {
  title: "Mela Express — Track Your Parcel",
  description: "Track your Mela Express parcel in real time.",
};

// Pre-hydration guard against browser-extension DOM injections
// (bis_skin_checked etc. cause hydration-mismatch warnings).
const EXTENSION_GUARD = `
(function () {
  var clean = function () {
    document.querySelectorAll('[bis_skin_checked],[bis_size]').forEach(function (el) {
      el.removeAttribute('bis_skin_checked');
      el.removeAttribute('bis_size');
    });
  };
  var obs = new MutationObserver(clean);
  var start = function () {
    clean();
    obs.observe(document.documentElement, { attributes: true, childList: true, subtree: true });
    setTimeout(function () { obs.disconnect(); }, 15000);
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="overflow-x-hidden" suppressHydrationWarning>
        <Script id="extension-hydration-guard" strategy="beforeInteractive">
          {EXTENSION_GUARD}
        </Script>
        <I18nProvider>
          <LanguageSyncer />
          {children}
        </I18nProvider>
      </body>
    </html>
  );
}
