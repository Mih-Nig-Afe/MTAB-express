import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import ClientLayout from "./client-layout";
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
    title: name ? `${name} Dashboard` : "Operations Dashboard",
    description: name ? `${name} operations dashboard` : "Parcel operations dashboard",
  };
}

// Some browser extensions (e.g. Edge/Bing "shopping" features) inject
// bis_skin_checked / bis_size attributes into the DOM before React hydrates,
// causing hydration-mismatch warnings. This pre-hydration guard strips them
// continuously for the first 15s after load, then disconnects.
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

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased bg-gray-50 text-gray-900 overflow-x-hidden" suppressHydrationWarning>
        <Script id="extension-hydration-guard" strategy="beforeInteractive">
          {EXTENSION_GUARD}
        </Script>
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  );
}
