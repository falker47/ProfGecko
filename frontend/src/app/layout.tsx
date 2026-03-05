import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Prof. Gallade - Esperto Pokemon",
  description: "Chatbot AI esperto di Pokemon. Chiedi qualsiasi cosa su tipi, statistiche, evoluzioni e mosse!",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="it">
      <body className="bg-gray-50 text-gray-900 antialiased">{children}</body>
    </html>
  );
}
