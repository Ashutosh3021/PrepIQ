import type { Metadata } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'
import { Analytics } from '@vercel/analytics/next'
import './globals.css'

const _geist = Geist({ subsets: ["latin"] });
const _geistMono = Geist_Mono({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: 'PrepIQ - AI-Powered Exam Preparation',
  description: 'AI-powered exam preparation platform that predicts questions with 80%+ accuracy',
  keywords: ['education', 'exam preparation', 'AI', 'question prediction', 'study tools'],
  authors: [{ name: 'PrepIQ Team' }],
  creator: 'PrepIQ',
  publisher: 'PrepIQ',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL('https://prepiq.vercel.app'),
  openGraph: {
    title: 'PrepIQ - AI-Powered Exam Preparation',
    description: 'AI-powered exam preparation platform that predicts questions with 80%+ accuracy',
    url: 'https://prepiq.vercel.app',
    siteName: 'PrepIQ',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'PrepIQ - AI-Powered Exam Preparation',
    description: 'AI-powered exam preparation platform that predicts questions with 80%+ accuracy',
  },
  icons: {
    icon: [
      {
        url: '/icons/favicon-32x32.png',
        sizes: '32x32',
        type: 'image/png',
      },
      {
        url: '/icons/favicon-16x16.png',
        sizes: '16x16',
        type: 'image/png',
      },
      {
        url: '/icon-light-32x32.png',
        media: '(prefers-color-scheme: light)',
      },
      {
        url: '/icon-dark-32x32.png',
        media: '(prefers-color-scheme: dark)',
      },
      {
        url: '/icon.svg',
        type: 'image/svg+xml',
      },
    ],
    apple: '/icons/apple-touch-icon.png',
    other: [
      {
        rel: 'manifest',
        url: '/icons/site.webmanifest'
      },
    ],
  },
  manifest: '/icons/site.webmanifest'
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={`font-sans antialiased`}>
        {children}
        <Analytics />

      </body>
    </html>
  )
}
