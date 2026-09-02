import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import ClientLayout from "./client-layout";

export const metadata: Metadata = {
  title: "Mela Express Dashboard",
  description: "Mela Express Dashboard",
};

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
