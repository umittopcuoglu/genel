import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HotelOps — AI-Destekli Otel Yönetim Sistemi",
  description: "Modüler, AI ajanları ile güçlendirilmiş PMS",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
