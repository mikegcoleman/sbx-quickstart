import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DevBoard",
  description: "Developer issue and project tracker",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 min-h-screen text-gray-900 antialiased">
        {children}
      </body>
    </html>
  );
}
