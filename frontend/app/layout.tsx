import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import ErrorBoundary from "@/components/ErrorBoundary";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "Cortex AI - Intelligent Assistant Platform",
    description: "Manage your AI chatbots with Cortex AI",
};

export const viewport: Viewport = {
    width: "device-width",
    initialScale: 1,
    maximumScale: 1,
    userScalable: false,
};

import { ToastProvider } from "@/components/ui/Toast";

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <body className={inter.className}>
                <ErrorBoundary>
                    <ToastProvider>
                        {children}
                    </ToastProvider>
                </ErrorBoundary>
            </body>
        </html>
    );
}
