import type { Metadata, Viewport } from "next";
import { Inter, Playfair_Display, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { OfflineIndicator } from "@/components/ui/OfflineIndicator";
import { InstallPrompt } from "@/components/ui/InstallPrompt";
import { PerformanceProvider } from "@/components/providers/PerformanceProvider";
import { SecurityProvider } from "@/components/providers/SecurityProvider";
import { AuthProvider } from "@/components/providers/AuthProvider";
import { LegalNotice } from "@/components/legal/LegalNotice";

const inter = Inter({
  variable: "--font-primary",
  subsets: ["latin"],
});

const playfairDisplay = Playfair_Display({
  variable: "--font-secondary",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PalmistTalk - Traditional Palm Reading with AI | PalmistTalk.com",
  description: "Get authentic Indian palmistry readings powered by AI at PalmistTalk.com. Upload your palm images for instant insights based on traditional Hast Rekha Shastra principles.",
  keywords: [
    "palmistry", 
    "palm reading", 
    "Indian palmistry", 
    "Hast Rekha Shastra", 
    "AI palmistry", 
    "fortune telling", 
    "life line", 
    "heart line", 
    "head line",
    "palm analysis"
  ],
  authors: [{ name: "PalmistTalk" }],
  creator: "PalmistTalk",
  publisher: "PalmistTalk",
  robots: "index, follow",
  openGraph: {
    type: "website",
    siteName: "PalmistTalk",
    title: "PalmistTalk - Traditional Palm Reading with AI | PalmistTalk.com",
    description: "Get authentic Indian palmistry readings powered by AI at PalmistTalk.com. Upload your palm images for instant insights based on traditional Hast Rekha Shastra principles.",
    url: process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "PalmistTalk - Palm Reading with AI",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "PalmistTalk - Traditional Palm Reading with AI | PalmistTalk.com",
    description: "Get authentic Indian palmistry readings powered by AI at PalmistTalk.com. Upload your palm images for instant insights based on traditional Hast Rekha Shastra principles.",
    images: ["/og-image.png"],
  },
  manifest: "/manifest.json",
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/icon.svg", sizes: "32x32", type: "image/svg+xml" },
    ],
    apple: [
      { url: "/apple-touch-icon.svg", sizes: "180x180", type: "image/svg+xml" },
    ],
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "PalmistTalk",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#ff8000",
  colorScheme: "light",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <meta name="csrf-token" content="" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.svg" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="shortcut icon" href="/favicon.svg" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="PalmistTalk" />
        <meta name="format-detection" content="telephone=no" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="msapplication-config" content="/browserconfig.xml" />
        <meta name="msapplication-TileColor" content="#ff8000" />
        <meta name="msapplication-tap-highlight" content="no" />
      </head>
      <body
        className={`${inter.variable} ${playfairDisplay.variable} ${jetbrainsMono.variable} antialiased`}
      >
        <AuthProvider>
          <SecurityProvider>
            <PerformanceProvider>
              {children}
              <OfflineIndicator />
              <InstallPrompt />
            </PerformanceProvider>
          </SecurityProvider>
        </AuthProvider>
        
        {/* Global Footer */}
        <footer className="mt-8 py-6 border-t border-gray-100 bg-gray-50/50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <LegalNotice variant="footer" />
          </div>
        </footer>
      </body>
    </html>
  );
}
