import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import "./globals.css";
import { I18nProvider } from "@/components/providers/I18nProvider";

const inter = Inter({ subsets: ["latin", "latin-ext"], variable: "--font-sans", display: "swap" });
const playfair = Playfair_Display({ subsets: ["latin", "latin-ext"], variable: "--font-display", display: "swap" });

export const metadata: Metadata = {
  title: "HotelOps — AI-Destekli Otel Yönetim Sistemi",
  description: "Modüler, AI ajanları ile güçlendirilmiş PMS",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr" suppressHydrationWarning className={`${inter.variable} ${playfair.variable}`}>
      <body className="font-sans">
        <I18nProvider>{children}</I18nProvider>
      </body>
    </html>
  );
}
