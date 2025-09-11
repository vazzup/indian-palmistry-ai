import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { OfflineIndicator } from "@/components/ui/OfflineIndicator";
import { InstallPrompt } from "@/components/ui/InstallPrompt";
import { PerformanceProvider } from "@/components/providers/PerformanceProvider";
import { SecurityProvider } from "@/components/providers/SecurityProvider";
import { AuthProvider } from "@/components/providers/AuthProvider";
import { LegalNotice } from "@/components/legal/LegalNotice";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Indian Palmistry AI - Traditional Palm Reading with AI",
  description: "Get authentic Indian palmistry readings powered by AI. Upload your palm images for instant insights based on traditional Hast Rekha Shastra principles.",
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
  authors: [{ name: "Indian Palmistry AI" }],
  creator: "Indian Palmistry AI",
  publisher: "Indian Palmistry AI",
  robots: "index, follow",
  openGraph: {
    type: "website",
    siteName: "Indian Palmistry AI",
    title: "Indian Palmistry AI - Traditional Palm Reading with AI",
    description: "Get authentic Indian palmistry readings powered by AI. Upload your palm images for instant insights based on traditional Hast Rekha Shastra principles.",
    url: process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Indian Palmistry AI - Palm Reading with AI",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Indian Palmistry AI - Traditional Palm Reading with AI",
    description: "Get authentic Indian palmistry readings powered by AI. Upload your palm images for instant insights based on traditional Hast Rekha Shastra principles.",
    images: ["/og-image.png"],
  },
  manifest: "/manifest.json",
  icons: {
    icon: [
      { url: "/icons/icon-192x192.png", sizes: "192x192", type: "image/png" },
      { url: "/icons/icon-512x512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [
      { url: "/icons/icon-152x152.png", sizes: "152x152", type: "image/png" },
    ],
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Palmistry AI",
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
        <link rel="apple-touch-icon" href="/icons/icon-152x152.png" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="Palmistry AI" />
        <meta name="format-detection" content="telephone=no" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="msapplication-config" content="/browserconfig.xml" />
        <meta name="msapplication-TileColor" content="#ff8000" />
        <meta name="msapplication-tap-highlight" content="no" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
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
