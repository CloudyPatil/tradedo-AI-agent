// E:\tradedo\app\frontend\app\layout.tsx

import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Toaster } from "sonner";
import { CommandPalette } from "@/components/common/command-palette";
import { ErrorBoundary } from "@/components/common/error-boundary";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
});

export const metadata: Metadata = {
  title: "TRADEDO — AI Trading Terminal",
  description: "Autonomous AI trading agent. Real-time data. Smarter trades.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${inter.variable} ${jetbrainsMono.variable} ${spaceGrotesk.variable}`}
    >
      <body className="min-h-screen bg-background font-sans antialiased">
        <Providers>
          <ErrorBoundary>
            {children}
            <CommandPalette />
          </ErrorBoundary>
          <Toaster
            position="top-right"
            theme="system"
            richColors
            closeButton
          />
        </Providers>
      </body>
    </html>
  );
}