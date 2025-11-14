


import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
title: "Vector DB 기반 Q&A 챗봇",
description: "답변 반환하는 서버리스 AI 챗봇"
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
