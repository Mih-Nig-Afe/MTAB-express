import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mela Express — Track Your Parcel",
  description: "Track your Mela Express parcel in real time.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
