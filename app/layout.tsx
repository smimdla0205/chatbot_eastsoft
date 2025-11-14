


import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "뉴스 AI 어시스턴트",
  description: "게임 기반 뉴스 이해력 퀴즈",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-background text-foreground">
        {children}
      </body>
    </html>
  );
}
