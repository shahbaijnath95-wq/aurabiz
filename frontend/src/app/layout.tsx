import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { ErrorBoundary } from "@/components/error-boundary";
import FloatingChat from "@/components/FloatingChat";
import TokenInjector from "@/components/TokenInjector";

export const metadata: Metadata = {
  title: "AI WhatsApp Assistant",
  description: "Aapke business ka smart WhatsApp assistant",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="hi">
      <body className="bg-void text-bone antialiased">
        <ErrorBoundary>
          <TokenInjector />
          <Providers>{children}<FloatingChat /></Providers>
        </ErrorBoundary>
      </body>
    </html>
  );
}
