import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Mela Express — Track Your Parcel",
  description: "Track your Mela Express parcel in real time.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
