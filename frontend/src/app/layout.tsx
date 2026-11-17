import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Prawira Tobacco Agent — Enterprise Document Intelligence & WhatsApp Action",
  description: "AI Agent with PDF RAG, Live Database Inventory Query, and WhatsApp Tool Calling for Prawira Tobacco",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="id">
      <body className="min-h-screen bg-[#0d0f14] text-slate-100 antialiased selection:bg-amber-500/30">
        {children}
      </body>
    </html>
  );
}
