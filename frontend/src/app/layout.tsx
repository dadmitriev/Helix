import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";

const inter = Inter({ subsets: ["latin", "cyrillic"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "Helix — Система анализа риска диабета",
  description: "Лабораторная информационная система для выявления риска сахарного диабета 2 типа",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className={`${inter.variable} h-full`}>
      <body className="min-h-full bg-[#F8F9FA] font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
