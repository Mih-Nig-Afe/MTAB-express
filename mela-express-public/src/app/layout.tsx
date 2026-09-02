import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import { I18nProvider } from "@/lib/i18n";
import LanguageSyncer from "@/i18n/LanguageSyncer";
import { BrandProvider } from "@/components/BrandProvider";
import { brandFromEnv, displayName } from "@brand";
import { loadBrandFromApi } from "@/lib/brand";

async function resolveBrandName(): Promise<string> {
  const env = brandFromEnv(process.env, "NEXT_PUBLIC_");
  let name = displayName(env);
  if (!name && process.env.NEXT_PUBLIC_API_URL) {
    try {
      const fromApi = await loadBrandFromApi(process.env.NEXT_PUBLIC_API_URL);
      name = displayName(fromApi);
    } catch {
      /* API unreachable at build/SSR time */
    }
  }
  return name;
}

export async function generateMetadata(): Promise<Metadata> {
  const name = await resolveBrandName();
  return {
    title: name ? `${name} — Track Your Parcel` : "Track Your Parcel",
    description: name
      ? `Track your ${name} parcel in real time.`
      : "Track your parcel in real time.",
  };
}

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
          <BrandProvider>
            <LanguageSyncer />
            {children}
          </BrandProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
